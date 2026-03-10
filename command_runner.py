"""
command_runner.py
-----------------
Responsible for executing shell / developer commands in a subprocess and
capturing the full output (stdout, stderr, return code, elapsed time).

This module is intentionally side-effect free: it only runs what it is told
and returns a structured dict. No LLM calls happen here.
"""

import subprocess
import time
import shlex
import sys
import os
import threading
from typing import Optional


def run_command(cmd: str, timeout: Optional[int] = 300, cwd: Optional[str] = None) -> dict:
    """
    Execute *cmd* in a subprocess and return a structured result dict.

    Parameters
    ----------
    cmd     : The shell command to run, e.g. "python app.py"
    timeout : Seconds to wait before killing the process (default 60).
    cwd     : Working directory in which to run the command (optional).

    Returns
    -------
    dict with keys:
        command     – original command string
        stdout      – captured standard output
        stderr      – captured standard error
        returncode  – process exit code  (0 = success)
        success     – True if returncode == 0
        elapsed     – wall-clock seconds taken
        timed_out   – True if the process was killed due to timeout
    """
    start = time.time()
    timed_out = False

    try:
        # Use shell=True on Windows so that built-ins like "pip" work correctly.
        # On POSIX we split the command for safety; on Windows we pass it raw.
        use_shell = sys.platform == "win32"
        args = cmd if use_shell else shlex.split(cmd)

        # Build env with UTF-8 encoding forced so scripts with emoji don't crash
        # and UNBUFFERED so prompts like input() appear immediately.
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["PYTHONUNBUFFERED"] = "1"

        def stream_reader(pipe, dest_list, sys_stream):
            while True:
                char = pipe.read(1)
                if not char:
                    break
                sys_stream.write(char)
                sys_stream.flush()
                dest_list.append(char)

        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            shell=use_shell,
            env=env,
        )

        stdout_chars = []
        stderr_chars = []

        t_out = threading.Thread(target=stream_reader, args=(proc.stdout, stdout_chars, sys.stdout))
        t_err = threading.Thread(target=stream_reader, args=(proc.stderr, stderr_chars, sys.stderr))

        t_out.start()
        t_err.start()

        try:
            returncode = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            returncode = -1
            timed_out = True

        t_out.join()
        t_err.join()

        stdout = "".join(stdout_chars)
        stderr = "".join(stderr_chars)

    except FileNotFoundError as exc:
        stdout = ""
        stderr = str(exc)
        returncode = 127  # POSIX convention: command not found

    except Exception as exc:  # noqa: BLE001
        stdout = ""
        stderr = f"Unexpected error running command: {exc}"
        returncode = -2

    elapsed = round(time.time() - start, 3)

    return {
        "command": cmd,
        "stdout": stdout,
        "stderr": stderr,
        "returncode": returncode,
        "success": returncode == 0,
        "elapsed": elapsed,
        "timed_out": timed_out,
    }


# ---------------------------------------------------------------------------
# Quick CLI test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    test_cmd = "python --version"
    result = run_command(test_cmd)
    print(json.dumps(result, indent=2))
