"""
tools.py
--------
Defines LangChain Tool objects that wrap the project's core functions.
These tools can be used directly by a LangChain Agent or called
programmatically by agent.py.

Each tool accepts a plain string (LangChain convention) and returns
a string result.
"""

import json
from langchain.tools import Tool

from command_runner import run_command as _run_command
from error_parser import parse_error as _parse_error
from fix_applier import apply_fix as _apply_fix


# ---------------------------------------------------------------------------
# Tool 1 – Run Command
# ---------------------------------------------------------------------------

def _run_command_tool(cmd: str) -> str:
    """Execute a shell command and return the JSON-serialised result."""
    result = _run_command(cmd.strip())
    return json.dumps(result, indent=2)


run_command_tool = Tool(
    name="run_command",
    func=_run_command_tool,
    description=(
        "Execute a shell / developer command. "
        "Input: the command string (e.g. 'python app.py'). "
        "Output: JSON with stdout, stderr, returncode, success, elapsed."
    ),
)


# ---------------------------------------------------------------------------
# Tool 2 – Parse Error
# ---------------------------------------------------------------------------

def _parse_error_tool(result_json: str) -> str:
    """
    Parse a command result JSON string and return structured error info.
    Input is the JSON string produced by run_command_tool.
    """
    try:
        result = json.loads(result_json)
    except json.JSONDecodeError:
        return json.dumps({"has_error": False, "error": "Invalid JSON input"})
    parsed = _parse_error(result)
    return json.dumps(parsed, indent=2)


parse_error_tool = Tool(
    name="parse_error",
    func=_parse_error_tool,
    description=(
        "Parse the JSON output of run_command and extract structured error info. "
        "Input: JSON string from run_command. "
        "Output: JSON with has_error, error_type, error_message, traceback."
    ),
)


# ---------------------------------------------------------------------------
# Tool 3 – Apply Fix
# ---------------------------------------------------------------------------

def _apply_fix_tool(fix_command: str) -> str:
    """Run the suggested fix command and return the JSON-serialised result."""
    result = _apply_fix(fix_command.strip())
    return json.dumps(result, indent=2)


apply_fix_tool = Tool(
    name="apply_fix",
    func=_apply_fix_tool,
    description=(
        "Apply a suggested fix by running the fix command. "
        "Input: the fix command string (e.g. 'pip install pandas'). "
        "Output: JSON with success, stdout, stderr."
    ),
)


# ---------------------------------------------------------------------------
# All tools in a convenient list
# ---------------------------------------------------------------------------
ALL_TOOLS = [run_command_tool, parse_error_tool, apply_fix_tool]
