"""
fix_generator.py
----------------
Uses LangChain + Groq to analyse an error and produce a concrete fix.

The module first checks the ErrorMemory database for a cached successful fix.
Only if no cached fix exists does it call the LLM (saving API cost and time).

Get your free Groq API key at: https://console.groq.com

Returned fix dict
-----------------
{
    "fix_command"  : str   – the shell command to run (e.g. "pip install pandas")
    "explanation"  : str   – human-readable explanation from the LLM
    "confidence"   : str   – "high" | "medium" | "low"
    "from_cache"   : bool  – True if retrieved from ErrorMemory (no LLM call)
}
"""

import os
import json
import re
from typing import Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from memory_db import ErrorMemory
from logger import get_logger

load_dotenv()
log = get_logger(__name__)


# ---------------------------------------------------------------------------
# System prompt for the LLM
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """You are an expert Python developer and DevOps engineer.
Your job is to analyse developer error messages and produce precise, minimal fixes.

When given an error report you MUST respond with a valid JSON object and NOTHING else.
The JSON must have EXACTLY these keys:
  "fix_command"   – shell command OR the sentinel "_CODE_PATCH_" (see rules below)
  "explanation"   – a concise English explanation of what went wrong and why the fix works
  "confidence"    – one of: "high", "medium", "low"
  "code_patch"    – ONLY include this key when fix_command is "_CODE_PATCH_", otherwise omit it entirely

Rules:

CASE 1 — The fix is a shell command (package install, file creation etc.):
• Set fix_command to the shell command. Do NOT include code_patch.
• Environment is Windows cmd.exe. Do NOT use PowerShell commands like Out-File.
• For ModuleNotFoundError: use "pip install <exact_module_name>".
• For FileNotFoundError: use python -c "open('<filename>', 'w').write('{}')".

CASE 2 — The fix requires editing code (SyntaxError, TypeError, NameError, KeyError, ZeroDivisionError, logic bug, missing line):
• Set fix_command to the sentinel string "_CODE_PATCH_".
• Add a "code_patch" key that is an object with:
    "file"    – the Python filename from the traceback (basename only, e.g. "app.py")
    "search"  – the exact buggy line(s) from the file — must match verbatim including indentation
    "replace" – the corrected line(s) to substitute in

Example for a SyntaxError (missing colon on def):
{
  "fix_command": "_CODE_PATCH_",
  "explanation": "The function definition is missing a colon at the end.",
  "confidence": "high",
  "code_patch": {
    "file": "demo_syntax_error.py",
    "search": "def greet(name)",
    "replace": "def greet(name):"
  }
}

Example for a TypeError (string + int):
{
  "fix_command": "_CODE_PATCH_",
  "explanation": "Cannot concatenate str and int. Wrap sum(scores) with str().",
  "confidence": "high",
  "code_patch": {
    "file": "demo_type_error.py",
    "search": "summary = total_label + sum(scores)",
    "replace": "summary = total_label + str(sum(scores))"
  }
}

• Never wrap your JSON in markdown fences.
• Never include keys other than the four listed above.
• fix_command must NEVER be empty — use "_CODE_PATCH_" if a code change is needed.
"""

_HUMAN_TEMPLATE = """Developer command: {command}

Error type: {error_type}

Error message:
{error_message}

Full traceback (if available):
{traceback}

Source file content (if available):
{source_code}

Provide the fix JSON now:"""


def _parse_llm_json(raw: str) -> dict:
    """
    Extract clean JSON from LLM output (handles occasional markdown wrapping).
    """
    # Strip markdown code fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: try to extract the first {...} block
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def generate_fix(
    command: str,
    error_info: dict,
    memory: Optional[ErrorMemory] = None,
) -> dict:
    """
    Generate a fix for the given error.

    Parameters
    ----------
    command    : the original developer command that failed
    error_info : dict from error_parser.parse_error()
    memory     : ErrorMemory instance (optional – skips cache check if None)

    Returns
    -------
    dict with keys: fix_command, explanation, confidence, from_cache
    """

    error_type = error_info.get("error_type", "UnknownError")
    error_message = error_info.get("error_message", "")
    traceback = error_info.get("traceback", "")
    error_line_no = error_info.get("error_line")

    # Extract source file — error_parser now provides 'file' directly
    source_code = "(not available)"
    file_path = error_info.get("file", "")
    if not file_path:
        # Fallback: try to extract from raw_stderr or traceback
        import re as _re
        for text in [error_info.get("raw_stderr", ""), traceback or ""]:
            m = _re.search(r'File ["\']([^"\']+\.py)["\']', text)
            if m:
                file_path = m.group(1)
                break
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as _f:
                raw_lines = _f.readlines()
            # Add line numbers and highlight the error line
            numbered = []
            for i, line in enumerate(raw_lines, start=1):
                prefix = f">>>" if (error_line_no and i == error_line_no) else f"   "
                numbered.append(f"{prefix} {i:4d}: {line.rstrip()}")
            source_code = "\n".join(numbered)
        except Exception:
            source_code = "(could not read source file)"

    # ------------------------------------------------------------------
    # 1. Check the memory cache first
    # ------------------------------------------------------------------
    if memory:
        cached = memory.lookup(error_type, error_message)
        if cached:
            log.info(
                f"[green]Cache hit[/green] for error type '{error_type}' "
                f"— using stored fix: {cached['fix_command']}"
            )
            return {
                "fix_command": cached["fix_command"],
                "explanation": cached.get("explanation", ""),
                "confidence": "high",
                "from_cache": True,
            }

    # ------------------------------------------------------------------
    # 2. Call the LLM
    # ------------------------------------------------------------------
    api_key = os.getenv("GROQ_API_KEY", "")
    model_name = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

    if not api_key:
        log.warning("GROQ_API_KEY not set — returning placeholder fix.")
        return {
            "fix_command": "",
            "explanation": "No API key configured. Please set GROQ_API_KEY in your .env file.",
            "confidence": "low",
            "from_cache": False,
        }

    log.info(f"Calling Groq LLM ({model_name}) to analyse '{error_type}'…")

    llm = ChatGroq(
        model=model_name,
        temperature=0,
        groq_api_key=api_key,
    )

    human_msg = _HUMAN_TEMPLATE.format(
        command=command,
        error_type=error_type,
        error_message=error_message,
        traceback=traceback or "(none)",
        source_code=source_code[:3000] if len(source_code) > 3000 else source_code,
    )

    try:
        response = llm.invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=human_msg),
        ])
        raw_content = response.content
        log.debug(f"LLM raw response: {raw_content}")

        fix_data = _parse_llm_json(raw_content)
        fix_data["from_cache"] = False

        # Ensure required keys exist
        fix_data.setdefault("fix_command", "")
        fix_data.setdefault("explanation", "")
        fix_data.setdefault("confidence", "medium")
        # Pass through code_patch and the resolved file_path if present
        if fix_data.get("fix_command") == "_CODE_PATCH_":
            if "code_patch" in fix_data and file_path:
                fix_data["code_patch"]["_full_path"] = file_path

        return fix_data

    except Exception as exc:  # noqa: BLE001
        log.error(f"LLM call failed: {exc}")
        return {
            "fix_command": "",
            "explanation": f"LLM error: {exc}",
            "confidence": "low",
            "from_cache": False,
        }


# ---------------------------------------------------------------------------
# Quick test (no real LLM call — just checks parsing)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    fake_error = {
        "error_type": "ModuleNotFoundError",
        "error_message": "ModuleNotFoundError: No module named 'pandas'",
        "traceback": "",
        "missing_module": "pandas",
    }
    result = generate_fix("python app.py", fake_error, memory=None)
    print(result)
