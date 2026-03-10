"""
code_generator.py
-----------------
Detects whether the user's input is a natural-language description
(e.g. "make a file that calculates compound interest") or an actual
shell command (e.g. "python app.py"), and handles each accordingly.

Natural language → LLM generates Python code → saved to a .py file → run it.
Shell command    → passed directly to the agent runner.
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from logger import get_logger

load_dotenv()
log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Heuristic: shell command prefixes that we recognise as real commands
# ---------------------------------------------------------------------------
_SHELL_PREFIXES = (
    "python", "py ", "pip", "node", "npm", "npx", "git", "cd ", "ls", "dir",
    "echo", "cat", "type ", "mkdir", "del ", "rm ", "mv ", "cp ", "curl",
    "streamlit", "pytest", "java ", "javac", "gcc", "go ", "ruby", "perl",
    "php ", "bash", "sh ", "cmd", "powershell", "start ", ".\\ ", "./ ",
    "run ", "ask ", "edit ", "memory", "test ",
)

# ---------------------------------------------------------------------------
# System prompt for code generation
# ---------------------------------------------------------------------------
_CODE_GEN_SYSTEM = """You are an expert developer.
The user will describe a program they want you to write.
Your ONLY output must be valid, runnable {language} code — nothing else.
Do NOT include markdown fences (```), explanations, or comments outside the code.
The code must:
 - Be self-contained (no external inputs required to run)
 - Print its output clearly to stdout or be visually testable
 - Include useful output so the user can verify it works
 - Use only standard library or commonly installed packages
 - NEVER use the `input()` function or equivalent blocking calls. ALWAYS use hardcoded example values. The agent runs these scripts in a background subprocess, so blocking calls will cause it to hang until it times out.
"""

_CODE_GEN_HUMAN = "Write a {language} program that: {description}"

# ---------------------------------------------------------------------------
# System prompt for editing existing code
# ---------------------------------------------------------------------------
_CODE_EDIT_SYSTEM = """You are an expert developer.
The user wants to modify an existing file.
You will be provided with the current file contents and their requested changes or instructions.
Your ONLY output must be the complete, modified, valid, runnable code — nothing else.
Do NOT include markdown fences (```), explanations, or comments outside the code.
Do NOT output only the diff or changed parts. You MUST return the ENTIRE file updated with the changes.
"""

_CODE_EDIT_HUMAN = """Modify the following file according to this instruction:
Instruction: {instruction}

Current code:
{code}
"""


def is_edit_command(text: str) -> tuple[bool, str, str]:
    """
    Check if the user typed an 'edit' natural language command.
    Returns (True, filename, instruction). Empty strings if missing.
    """
    text_lower = text.strip().lower()
    if text_lower == "edit":
        return True, "", ""
        
    if text_lower.startswith("edit "):
        # try specific parsing first (e.g. "edit app.py to add a route")
        m = re.match(r"^edit\s+(?:file\s+)?(?:the\s+)?([^\s]+)(?:\s+(?:to\s+)?(.+))?$", text.strip(), flags=re.IGNORECASE)
        if m:
            filename = m.group(1)
            instruction = m.group(2) or ""
            return True, filename, instruction
            
        # fallback if regex failed but it starts with "edit "
        instruction = text.strip()[5:].strip()
        return True, "", instruction
        
    return False, "", ""


def is_natural_language(text: str) -> bool:
    """
    Return True if *text* looks like a natural language description,
    False if it looks like a real shell command.
    """
    stripped = text.strip().lower()
    # If it starts with a known shell prefix → it's a command
    for prefix in _SHELL_PREFIXES:
        if stripped.startswith(prefix):
            return False
    # If it contains a file extension like .py, .js, .html it's a command
    if re.search(r"\.(py|js|ts|sh|html|css|json|txt)\b", stripped):
        return False
    # If it contains path separators, it's a shell path
    if "/" in stripped or "\\" in stripped:
        return False
    # Single words with no spaces are treated as commands too
    if " " not in stripped:
        return False
    return True


def generate_code_from_description(description: str, language: str = "Python") -> str:
    """
    Call the Groq LLM to write code matching *description* in the target *language*.
    Returns the raw source code as a string.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    model   = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

    if not api_key:
        log.error("GROQ_API_KEY not set.")
        return ""

    log.info(f"Generating code for: '{description[:60]}…'")

    llm = ChatGroq(model=model, temperature=0.2, groq_api_key=api_key)

    response = llm.invoke([
        SystemMessage(content=_CODE_GEN_SYSTEM.format(language=language)),
        HumanMessage(content=_CODE_GEN_HUMAN.format(language=language, description=description)),
    ])

    code = response.content.strip()
    # Strip accidental markdown fences
    code = re.sub(r"^```(?:python)?\s*", "", code)
    code = re.sub(r"\s*```$", "", code)
    return code.strip()


def description_to_filename(description: str, language: str = "Python") -> str:
    """
    Convert a natural-language description into a safe snake_case filename.
    E.g. "calculate compound interest" → "calculate_compound_interest.py"
    """
    words = re.sub(r"[^a-z0-9 ]", "", description.lower()).split()
    # Use first 5 meaningful words max
    name = "_".join(words[:5]) or "generated_script"
    
    ext_map = {
        "python": ".py",
        "html": ".html",
        "react": ".jsx",
        "javascript": ".js",
        "node": ".js",
        "bash": ".sh"
    }
    ext = ext_map.get(language.lower(), f".{language[:3].lower()}")
    return f"{name}{ext}"


def handle_natural_language(
    description: str,
    language: str = "Python",
    output_dir: str = ".",
) -> dict:
    """
    Full pipeline: description → code → file → return info dict.

    Returns
    -------
    dict:
        filename    – path to the saved file
        code        – the generated source code
        command     – the shell command to run it ("python <filename>")
        success     – True if file was saved successfully
    """
    code = generate_code_from_description(description, language=language)
    if not code:
        return {"filename": "", "code": "", "command": "", "success": False}

    filename = description_to_filename(description, language=language)
    filepath = Path(output_dir) / filename

    filepath.write_text(code, encoding="utf-8")
    log.info(f"Code saved to: {filepath}")

    # Determine command to run based on extension
    run_cmd = "type" if os.name == "nt" else "cat"
    if filename.endswith(".py"):
        run_cmd = f"python {filename}"
    elif filename.endswith(".js") or filename.endswith(".jsx"):
        run_cmd = f"node {filename}"
    elif filename.endswith(".html"):
        run_cmd = f"echo 'Open {filename} in a browser'"
    elif filename.endswith(".sh"):
        run_cmd = f"bash {filename}"

    return {
        "filename": str(filepath),
        "code": code,
        "command": run_cmd,
        "success": True,
    }


def handle_edit_command(filepath: str, instruction: str) -> dict:
    """
    Read the existing file, ask the LLM to modify it according to the instruction,
    and save it back. Returns a dict similar to `handle_natural_language`.
    """
    if not os.path.isfile(filepath):
        log.error(f"Cannot edit {filepath} — file does not exist.")
        return {"filename": filepath, "code": "", "command": "", "success": False, "error": f"File not found: {filepath}"}

    try:
        current_code = Path(filepath).read_text(encoding="utf-8")
    except Exception as e:
        log.error(f"Cannot read {filepath}: {e}")
        return {"filename": filepath, "code": "", "command": "", "success": False, "error": str(e)}

    api_key = os.getenv("GROQ_API_KEY", "")
    model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

    if not api_key:
        log.error("GROQ_API_KEY not set.")
        return {"filename": filepath, "code": "", "command": "", "success": False, "error": "GROQ_API_KEY not set"}

    log.info(f"Editing code in '{filepath}' — instruction: '{instruction[:50]}…'")

    llm = ChatGroq(model=model, temperature=0.1, groq_api_key=api_key)

    response = llm.invoke([
        SystemMessage(content=_CODE_EDIT_SYSTEM),
        HumanMessage(content=_CODE_EDIT_HUMAN.format(instruction=instruction, code=current_code)),
    ])

    code = response.content.strip()
    code = re.sub(r"^```(?:[a-zA-Z]+)?\s*", "", code)
    code = re.sub(r"\s*```$", "", code)
    code = code.strip()

    if not code:
        return {"filename": filepath, "code": "", "command": "", "success": False, "error": "LLM returned empty code."}

    Path(filepath).write_text(code, encoding="utf-8")
    log.info(f"Modified code saved back to: {filepath}")

    # Determine command to run based on extension (re-using logic)
    run_cmd = "type" if os.name == "nt" else "cat"
    if filepath.endswith(".py"):
        run_cmd = f"python {filepath}"
    elif filepath.endswith((".js", ".jsx")):
        run_cmd = f"node {filepath}"
    elif filepath.endswith(".html"):
        run_cmd = f"echo 'Open {filepath} in a browser'"
    elif filepath.endswith(".sh"):
        run_cmd = f"bash {filepath}"

    return {
        "filename": filepath,
        "code": code,
        "command": run_cmd,
        "success": True,
    }
