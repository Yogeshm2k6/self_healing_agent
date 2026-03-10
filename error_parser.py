"""
error_parser.py
---------------
Analyses the raw output from command_runner and extracts structured
error information.  It classifies the error type so that fix_generator
can make smarter, more targeted prompts.

No external dependencies — pure Python.
"""

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Known error patterns with friendly labels
# ---------------------------------------------------------------------------
_ERROR_PATTERNS = [
    # Python exceptions / import issues
    (r"ModuleNotFoundError: No module named '([^']+)'", "ModuleNotFoundError"),
    (r"ImportError:.*'([^']+)'",                         "ImportError"),
    (r"SyntaxError: (.+)",                               "SyntaxError"),
    (r"IndentationError: (.+)",                          "IndentationError"),
    (r"NameError: name '([^']+)' is not defined",        "NameError"),
    (r"TypeError: (.+)",                                 "TypeError"),
    (r"AttributeError: (.+)",                            "AttributeError"),
    (r"FileNotFoundError: (.+)",                         "FileNotFoundError"),
    (r"PermissionError: (.+)",                           "PermissionError"),
    (r"ValueError: (.+)",                                "ValueError"),
    (r"KeyError: (.+)",                                  "KeyError"),
    (r"IndexError: (.+)",                                "IndexError"),
    (r"RuntimeError: (.+)",                              "RuntimeError"),
    (r"OSError: (.+)",                                   "OSError"),
    # pip errors
    (r"ERROR: (.+)",                                     "PipError"),
    # Generic traceback tail
    (r"([A-Z][a-zA-Z]+Error): (.+)",                    "PythonError"),
]

# Lines that mark the start of a Python traceback
_TRACEBACK_START = re.compile(r"Traceback \(most recent call last\)")


def parse_error(result: dict) -> dict:
    """
    Parse the result dict returned by ``command_runner.run_command``.

    Parameters
    ----------
    result : dict  – the raw result from run_command()

    Returns
    -------
    dict with keys:
        has_error     – bool
        error_type    – classified error label (e.g. "ModuleNotFoundError")
        error_message – concise human-readable message extracted from stderr
        traceback     – full traceback block if present, else ""
        raw_stderr    – original stderr string (unchanged)
        missing_module – module name for import errors, else None
    """

    # If the command succeeded there is nothing to parse
    if result.get("success", False):
        return {
            "has_error": False,
            "error_type": None,
            "error_message": "",
            "traceback": "",
            "raw_stderr": result.get("stderr", ""),
            "missing_module": None,
        }

    stderr: str = result.get("stderr", "") or ""
    stdout: str = result.get("stdout", "") or ""

    # Sometimes Python writes tracebacks to stdout (e.g. when stderr is
    # redirected), so we search both.
    combined = stderr + "\n" + stdout

    error_type = "UnknownError"
    error_message = stderr.strip() or "Non-zero exit code with no stderr output."
    traceback_block = ""
    missing_module: Optional[str] = None

    # -----------------------------------------------------------------------
    # 1. Extract the traceback block
    # -----------------------------------------------------------------------
    lines = combined.splitlines()
    tb_start_idx = None
    for i, line in enumerate(lines):
        if _TRACEBACK_START.search(line):
            tb_start_idx = i
            break

    if tb_start_idx is not None:
        traceback_block = "\n".join(lines[tb_start_idx:])
    else:
        # SyntaxError has no 'Traceback ...' header — use the full stderr as traceback
        traceback_block = combined

    # Extract file path from 'File "...", line N' for use by fix_generator
    file_path = ""
    error_line_no = None
    _file_match = re.search(r'File ["\']([^"\'\']+\.py)["\'],\s*line\s*(\d+)', combined)
    if _file_match:
        file_path = _file_match.group(1)
        error_line_no = int(_file_match.group(2))

    # -----------------------------------------------------------------------
    # 2. Match against known patterns
    # -----------------------------------------------------------------------
    for pattern, label in _ERROR_PATTERNS:
        m = re.search(pattern, combined)
        if m:
            error_type = label
            error_message = m.group(0)  # full matched line
            # Capture missing module for import errors
            if label in ("ModuleNotFoundError", "ImportError"):
                missing_module = m.group(1)
            break

    # -----------------------------------------------------------------------
    # 3. Fallback: use last non-empty line of stderr as message
    # -----------------------------------------------------------------------
    if error_type == "UnknownError" and stderr.strip():
        last_lines = [l for l in stderr.splitlines() if l.strip()]
        if last_lines:
            error_message = last_lines[-1].strip()

    return {
        "has_error": True,
        "error_type": error_type,
        "error_message": error_message,
        "traceback": traceback_block,
        "raw_stderr": stderr,
        "missing_module": missing_module,
        "file": file_path,
        "error_line": error_line_no,
    }


def summarise_error(parsed: dict, max_traceback_lines: int = 15) -> str:
    """
    Return a compact text summary suitable for display in the CLI.
    """
    lines = [f"Error Type : {parsed['error_type']}",
             f"Message    : {parsed['error_message']}"]

    if parsed.get("missing_module"):
        lines.append(f"Module     : {parsed['missing_module']}")

    if parsed.get("traceback"):
        tb_lines = parsed["traceback"].splitlines()[:max_traceback_lines]
        lines.append("\nTraceback (truncated):")
        lines.extend(f"  {l}" for l in tb_lines)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    fake_result = {
        "success": False,
        "returncode": 1,
        "stderr": (
            "Traceback (most recent call last):\n"
            "  File 'app.py', line 1, in <module>\n"
            "    import pandas as pd\n"
            "ModuleNotFoundError: No module named 'pandas'\n"
        ),
        "stdout": "",
    }
    parsed = parse_error(fake_result)
    print(summarise_error(parsed))
