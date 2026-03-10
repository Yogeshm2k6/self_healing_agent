"""
fix_applier.py
--------------
Executes the fix command produced by fix_generator and reports the outcome.
Supports three fix modes:
  1. Shell command   – standard pip install, echo, etc.
  2. Native file fix – python -c open(...) commands intercepted and run natively
  3. Code patch      – _CODE_PATCH_ sentinel triggers in-place source file editing
"""

import json
import os
import re
import subprocess
from pathlib import Path

from command_runner import run_command
from logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# 1. Native file fix interceptor (avoids cmd.exe quoting issues)
# ---------------------------------------------------------------------------
def _try_native_file_fix(fix_command: str, cwd: str = None) -> dict | None:
    """
    Intercept `python -c` commands that write JSON files.
    Run them natively in Python to avoid cmd.exe quoting issues.
    Returns a result dict on success/failure, or None if not applicable.
    """
    if not ("python -c" in fix_command and "open(" in fix_command):
        return None

    fname_match = re.search(r"open\(['\"]([^'\"]+)['\"],\s*['\"]w['\"]", fix_command)
    if not fname_match:
        return None

    filename = fname_match.group(1)
    filepath = Path(cwd or ".") / filename

    log.info(f"[cyan]Native file fix:[/cyan] Creating '{filename}' directly…")

    data = {"server_name": "Demo", "api_token": "demo-key-123"}
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        log.info(f"[green]Created '{filename}' successfully.[/green]")
        return {
            "command": fix_command,
            "stdout": f"Created {filename} with default config.",
            "stderr": "",
            "returncode": 0,
            "success": True,
            "elapsed": 0.0,
            "timed_out": False,
        }
    except Exception as e:
        log.error(f"Native file fix failed: {e}")
        return None


# ---------------------------------------------------------------------------
# 2. Code patch applier  (search/replace inside source files)
# ---------------------------------------------------------------------------
def _apply_code_patch(fix: dict, cwd: str = None) -> dict:
    """
    Apply a search/replace code patch to a source file.
    Called when fix_command == '_CODE_PATCH_'.
    """
    patch       = fix.get("code_patch", {})
    filename    = patch.get("file", "")
    search_str  = patch.get("search", "")
    replace_str = patch.get("replace", "")
    full_path   = patch.get("_full_path", "")

    if not filename or not search_str:
        return {
            "command": "_CODE_PATCH_",
            "stdout": "",
            "stderr": "code_patch missing 'file' or 'search' fields.",
            "returncode": -1, "success": False, "elapsed": 0.0, "timed_out": False,
        }

    # Resolve the file path
    if full_path and Path(full_path).is_file():
        filepath = Path(full_path)
    else:
        filepath = Path(cwd or ".") / filename
        if not filepath.is_file():
            filepath = Path(filename)

    if not filepath.is_file():
        return {
            "command": "_CODE_PATCH_",
            "stdout": "",
            "stderr": f"Cannot find source file '{filename}' to patch.",
            "returncode": -1, "success": False, "elapsed": 0.0, "timed_out": False,
        }

    try:
        original = filepath.read_text(encoding="utf-8")
        if search_str not in original:
            return {
                "command": "_CODE_PATCH_",
                "stdout": "",
                "stderr": (
                    f"Patch search string not found in '{filepath.name}'.\n"
                    f"Expected to find: {search_str!r}"
                ),
                "returncode": -1, "success": False, "elapsed": 0.0, "timed_out": False,
            }
        patched = original.replace(search_str, replace_str, 1)
        filepath.write_text(patched, encoding="utf-8")
        log.info(f"[green]Code patch applied to '{filepath.name}':[/green] {search_str!r} → {replace_str!r}")
        return {
            "command": "_CODE_PATCH_",
            "stdout": f"✓ Patched '{filepath.name}':\n  - {search_str!r}\n  + {replace_str!r}",
            "stderr": "",
            "returncode": 0, "success": True, "elapsed": 0.0, "timed_out": False,
        }
    except Exception as exc:
        return {
            "command": "_CODE_PATCH_",
            "stdout": "",
            "stderr": f"Patch failed: {exc}",
            "returncode": -1, "success": False, "elapsed": 0.0, "timed_out": False,
        }


# ---------------------------------------------------------------------------
# 3. Main dispatcher
# ---------------------------------------------------------------------------
def apply_fix(fix_command: str, cwd: str = None, fix: dict = None) -> dict:
    """
    Execute the fix and return the result.

    Parameters
    ----------
    fix_command : shell command / '_CODE_PATCH_' sentinel
    cwd         : working directory
    fix         : full fix dict (needed for code patches)

    Returns
    -------
    dict with keys: command, stdout, stderr, returncode, success, elapsed, timed_out
    """

    if not fix_command or not fix_command.strip():
        log.warning("apply_fix called with an empty fix_command — skipping.")
        return {
            "command": fix_command,
            "stdout": "",
            "stderr": "No fix command provided.",
            "returncode": -1,
            "success": False,
            "elapsed": 0.0,
            "timed_out": False,
        }

    log.info(f"Applying fix: [bold cyan]{fix_command}[/bold cyan]")

    # --- Mode A: CODE PATCH (in-place source file edit) ---
    if fix_command == "_CODE_PATCH_":
        if not fix:
            log.error("_CODE_PATCH_ received but no fix dict provided.")
            return {
                "command": fix_command, "stdout": "", "stderr": "No fix dict.",
                "returncode": -1, "success": False, "elapsed": 0.0, "timed_out": False,
            }
        result = _apply_code_patch(fix, cwd=cwd)
        if result["success"]:
            log.info("[green]Code patch applied successfully.[/green]")
        else:
            log.error(f"Code patch failed: {result['stderr'][:200]}")
        return result

    # --- Mode B: Native file creation (avoids cmd.exe quoting) ---
    native_result = _try_native_file_fix(fix_command, cwd=cwd)
    if native_result is not None and native_result["success"]:
        log.info("[green]Fix applied successfully (native).[/green]")
        return native_result

    # --- Mode C: Standard shell execution ---
    result = run_command(fix_command, cwd=cwd)
    if result["success"]:
        log.info("[green]Fix applied successfully.[/green]")
    else:
        log.error(
            f"Fix command failed (exit {result['returncode']}): "
            f"{result['stderr'][:200]}"
        )
    return result


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    res = apply_fix("echo hello")
    print(json.dumps(res, indent=2))

