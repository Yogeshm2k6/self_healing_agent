"""
code_analyzer.py
----------------
Uses Groq LLM to perform a structured analysis of Python source code.

Reports:
  1. Bugs / errors found (including runtime issues)
  2. Missing pieces (unimplemented features, missing variables, etc.)
  3. Improvement suggestions (style, performance, best practices)
  4. A fixed / improved version of the code (optional)
"""

import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from logger import get_logger

load_dotenv()
log = get_logger(__name__)

# ---------------------------------------------------------------------------
# System prompt for analysis
# ---------------------------------------------------------------------------
_ANALYSIS_SYSTEM = """You are a senior code reviewer.
When given source code, produce a structured analysis in EXACTLY this format
(use these exact headers, separated by blank lines):

## 🐛 BUGS FOUND
List each bug as: • [line or area] – description of the bug

## 🔧 WHAT IS MISSING
List each missing piece as: • description

## 💡 IMPROVEMENTS SUGGESTED
List each improvement as: • description

## ✅ FIXED CODE
 Provide the complete corrected and improved code.
The fixed code must:
- Be fully self-contained and runnable without user input (use hardcoded example values)
- Print all results clearly to stdout or display sensibly
- Include proper error handling
- Have clear comments

Do NOT use markdown fences around any section except inside FIXED CODE section where you MUST wrap the code in standard markdown language blocks (e.g. ```python ... ```).
"""

_ANALYSIS_HUMAN = """Analyse this code file named `{filename}`:

{code}
"""


def analyze_code(code: str, filename: str = "script.py") -> dict:
    """
    Analyse *code* and return a structured dict.

    Returns
    -------
    dict:
        bugs         – list of bug descriptions
        missing      – list of missing features/variables
        improvements – list of improvement suggestions
        fixed_code   – corrected full code string
        raw          – raw LLM response text
        success      – bool
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    model   = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

    if not api_key:
        log.error("GROQ_API_KEY not set — cannot analyse code.")
        return {"success": False, "bugs": [], "missing": [], "improvements": [], "fixed_code": "", "raw": ""}

    log.info(f"Analysing code in '{filename}' ({len(code.splitlines())} lines)…")

    llm = ChatGroq(model=model, temperature=0.1, groq_api_key=api_key)

    response = llm.invoke([
        SystemMessage(content=_ANALYSIS_SYSTEM),
        HumanMessage(content=_ANALYSIS_HUMAN.format(filename=filename, code=code)),
    ])

    raw = response.content.strip()
    log.debug(f"LLM analysis raw:\n{raw}")

    return {**_parse_analysis(raw), "raw": raw, "success": True}


def _parse_section(raw: str, header: str) -> list:
    """Extract bullet points under a given ## header."""
    pattern = re.compile(
        rf"##\s*{re.escape(header)}.*?\n(.*?)(?=\n##|\Z)", re.DOTALL | re.IGNORECASE
    )
    m = pattern.search(raw)
    if not m:
        return []
    block = m.group(1)
    bullets = re.findall(r"[•\-\*]\s+(.+)", block)
    return [b.strip() for b in bullets if b.strip()]


def _parse_fixed_code(raw: str) -> str:
    """Extract the fixed code block."""
    # Try fenced block first
    m = re.search(r"```[a-zA-Z]*\s*(.*?)```", raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fallback: everything after "## ✅ FIXED CODE"
    m = re.search(r"##\s*.*?FIXED CODE.*?\n(.*)", raw, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip().lstrip("`").rstrip("`").strip()
    return ""


def _parse_analysis(raw: str) -> dict:
    return {
        "bugs":         _parse_section(raw, "🐛 BUGS FOUND"),
        "missing":      _parse_section(raw, "🔧 WHAT IS MISSING"),
        "improvements": _parse_section(raw, "💡 IMPROVEMENTS SUGGESTED"),
        "fixed_code":   _parse_fixed_code(raw),
    }
