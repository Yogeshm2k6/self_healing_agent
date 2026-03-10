"""
main.py
-------
CLI entry point for the Self-Healing Developer Agent.

Usage
-----
  python main.py                       # interactive prompt
  python main.py "python app.py"       # pass command as argument
  python main.py --auto "python app.py"  # auto-apply fixes without prompt
  python main.py --memory              # display past fixes from memory DB
  python main.py --help
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich import box

from agent import SelfHealingAgent
from code_generator import (
    is_natural_language, handle_natural_language,
    is_edit_command, handle_edit_command
)
from project_generator import is_project_command, generate_project, description_to_project_name
from chat_handler import handle_chat
from code_analyzer import analyze_code
from logger import get_logger

load_dotenv()
log = get_logger(__name__)
console = Console()


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
BANNER = """\
[bold cyan]
  ╔═══════════════════════════════════════════╗
  ║     🤖  Self-Healing Developer Agent       ║
  ║   Observe  →  Reason  →  Act  →  Verify   ║
  ╚═══════════════════════════════════════════╝
[/bold cyan]"""


def print_banner() -> None:
    console.print(BANNER)
    console.print(
        "[dim]Powered by LangChain + Groq  |  "
        "Type [bold]exit[/bold] or [bold]quit[/bold] to stop[/dim]\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_command(cmd: str, agent: SelfHealingAgent) -> None:
    """Process a single command string, which could be a raw shell command or a natural language instruction."""
    if not cmd:
        return

    if cmd.lower() == "memory":
        agent.show_memory()
        return

    if cmd.lower() == "help":
        console.print(
            Panel(
                "Commands:\n"
                "  [cyan]<shell command>[/cyan]           – run it through the agent\n"
                "    e.g. [green]python app.py[/green]\n"
                "  [cyan]<natural language>[/cyan]        – generate + run a Python file\n"
                "    e.g. [green]calculate compound interest[/green]\n"
                "  [cyan]edit <file> to <action>[/cyan]   – modify an existing file\n"
                "    e.g. [green]edit calc.py to add a new function[/green]\n"
                "  [cyan]project <description>[/cyan]      – generate a multi-file project\n"
                "  [cyan]run <folder or file>[/cyan]         – auto-run a project folder or file\n"
                "  [cyan]test <folder>[/cyan]               – run ALL files and check for errors\n"
                "  [cyan]ask <question>[/cyan]             – ask the AI a general question\n"
                "  [cyan]memory[/cyan]                    – show fix history\n"
                "  [cyan]exit / quit[/cyan]               – exit the agent",
                title="Help",
                box=box.SIMPLE,
            )
        )
        return

    # ── Detect if it's an "ask" question ──────────────────────────────
    if cmd.lower().startswith("ask "):
        question = cmd[4:].strip()
        console.print(f"\n[bold magenta]✦ Answering question:[/bold magenta] {question}")
        answer = handle_chat(question)
        console.print(Panel(answer, title="[bold cyan]Agent Reply[/bold cyan]", border_style="magenta", box=box.ROUNDED))
        return

    # ── Detect if it's an "edit file" command ─────────────────────────
    is_edit, edit_file, edit_instr = is_edit_command(cmd)
    if is_edit:
        if not edit_file:
            edit_file = Prompt.ask("\n[bold cyan]Which file do you want to edit?[/bold cyan]").strip()
            
        if not edit_instr:
            edit_instr = Prompt.ask(
                f"\n[bold cyan]What should I change in {edit_file}?[/bold cyan] (e.g. 'add a new function')",
                default="Fix and improve this file"
            ).strip()

        console.print(
            f"\n[bold magenta]✦ Edit command detected![/bold magenta] "
            f"[dim]Modifying [bold]{edit_file}[/bold]…[/dim]\n"
        )
        gen = handle_edit_command(edit_file, edit_instr)
        if not gen["success"]:
            console.print(f"[red]Code edit failed: {gen.get('error', 'Unknown error')}[/red]")
            return

        console.print(
            Panel(
                gen["code"],
                title=f"[bold cyan]Modified: {gen['filename']}[/bold cyan]",
                border_style="magenta",
                box=box.ROUNDED,
            )
        )
        console.print(f"[dim]File saved \u2192 [cyan]{gen['filename']}[/cyan][/dim]\n")
        cmd = gen["command"]  # run the modified file through the agent

    # ── Detect if it's a "create project" command ─────────────────────
    is_proj, proj_desc = is_project_command(cmd)
    if hasattr(is_proj, 'startswith'): pass # Hack for Python scope bug
    if is_edit: pass # Avoid duplicate if edit matched

    # ── Handle "test <folder>" – fast syntax check + entry point run ──────
    if not is_edit and cmd.lower().startswith("test "):
        import subprocess as _sp
        from rich.table import Table
        target_path_str = cmd[5:].strip()
        target_path = Path(target_path_str)

        if not target_path.is_dir():
            console.print(f"[red]Directory not found: {target_path_str}[/red]")
            return

        py_files = sorted(target_path.glob("*.py"))
        if not py_files:
            console.print(f"[yellow]No Python files found in {target_path_str}[/yellow]")
            return

        console.print(f"\n[bold cyan]⚡ Quick-checking {len(py_files)} file(s) in [green]{target_path_str}[/green]...[/bold cyan]\n")

        results_table = Table(title=f"Project Test Report: {target_path_str}", box=box.ROUNDED)
        results_table.add_column("File", style="cyan")
        results_table.add_column("Check", justify="center")
        results_table.add_column("Error", style="dim")

        passed, failed = 0, 0
        _env = os.environ.copy()
        _env["PYTHONIOENCODING"] = "utf-8"

        for py_file in py_files:
            # Fast syntax-only check using py_compile — use just filename since cwd is already target_path
            try:
                proc = _sp.run(
                    ["python", "-m", "py_compile", py_file.name],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    cwd=str(target_path.resolve()), env=_env, timeout=10
                )
                if proc.returncode == 0:
                    results_table.add_row(py_file.name, "[bold green]✓ OK[/bold green]", "")
                    passed += 1
                else:
                    err = (proc.stderr or "syntax error").strip().splitlines()[-1][:80]
                    results_table.add_row(py_file.name, "[bold red]✗ SYNTAX ERR[/bold red]", err)
                    failed += 1
            except Exception as _e:
                results_table.add_row(py_file.name, "[bold yellow]? ERROR[/bold yellow]", str(_e)[:80])
                failed += 1

        console.print(results_table)

        # --- Also do a real run of the entry point with short timeout ----
        entry_points = ["main.py", "app.py", "run.py", "index.py"]
        entry = next((target_path / ep for ep in entry_points if (target_path / ep).is_file()), None)
        if not entry:
            entry = py_files[0]

        console.print(f"\n[dim]Running entry point [cyan]{entry.name}[/cyan] (15s timeout)...[/dim]")
        try:
            run_proc = _sp.run(
                ["python", entry.name],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=str(target_path.resolve()), env=_env, timeout=15
            )
            if run_proc.returncode == 0:
                console.print(f"[bold green]✓ Entry point ran successfully![/bold green]")
                if run_proc.stdout.strip():
                    console.print(Panel(run_proc.stdout.strip()[:500], title="Output", border_style="green", box=box.ROUNDED))
            else:
                console.print(f"[bold red]✗ Entry point failed![/bold red]")
                err_out = (run_proc.stderr or run_proc.stdout or "").strip()[:500]
                console.print(Panel(err_out, title="Error Output", border_style="red", box=box.ROUNDED))
                console.print(f"[dim]Tip: use [cyan]run {target_path_str}[/cyan] to auto-heal this error.[/dim]")
        except _sp.TimeoutExpired:
            console.print(f"[yellow]⚠ Entry point timed out after 15s (it may need user input or be a long-running server).[/yellow]")
            console.print(f"[dim]Tip: use [cyan]run {target_path_str}[/cyan] to run it through the full agent loop.[/dim]")
        except Exception as _e:
            console.print(f"[red]Failed to run entry point: {_e}[/red]")

        console.print(
            f"\n[bold]Syntax check result:[/bold] "
            f"[bold green]{passed} OK[/bold green]  "
            f"[bold red]{failed} errors[/bold red]  "
            f"out of {len(py_files)} files\n"
        )
        return

    # ── Handle "run <name>" ───────────────────────────────────────────
    if not is_edit and cmd.lower().startswith("run "):
        target_path_str = cmd[4:].strip()
        target_path = Path(target_path_str)
        
        if not target_path.exists():
            console.print(f"[red]Path not found: {target_path_str}[/red]")
            return

        run_file = None
        target_dir = None

        if target_path.is_file():
            run_file = target_path.name
            target_dir = str(target_path.parent) or "."
        else:
            target_dir = target_path_str
            # Find entry point
            entry_points = ["main.py", "app.py", "run.py", "index.js", "server.js", "server.py", "index.html"]
            for ep in entry_points:
                if (target_path / ep).is_file():
                    run_file = ep
                    break
                    
            if not run_file:
                # Fallback to the first python or js file found
                for ext in ["*.py", "*.js", "*.html"]:
                    files = list(target_path.glob(ext))
                    if files:
                        run_file = files[0].name
                        break

            if not run_file:
                console.print(f"[red]Could not find a clear entry point (like main.py or index.js) in {target_dir}.[/red]")
                return
                
            console.print(f"\n[bold magenta]✦ Auto-detecting entry point...[/bold magenta] Found [bold]{run_file}[/bold]\n")
        
        # Determine the right runner prefix based on file extension
        if run_file.endswith(".py"):
            exec_cmd = f'python "{run_file}"'
        elif run_file.endswith(".js"):
            exec_cmd = f'node "{run_file}"'
        elif run_file.endswith(".html"):
            # Open in browser — just use start (no agent loop needed)
            import subprocess as _sp2
            _sp2.Popen(["start", run_file], shell=True, cwd=str(Path(target_dir).resolve()))
            console.print(f"[bold green]✓ Opening [cyan]{run_file}[/cyan] in your default browser...[/bold green]")
            return
        elif run_file.endswith(".sh"):
            exec_cmd = f'bash "{run_file}"'
        else:
            exec_cmd = f'python "{run_file}"'

        # Use agent.cwd so the subprocess actually starts IN the project folder
        # (Windows cd && chaining is unreliable in shell=True mode)
        old_cwd = agent.cwd
        agent.cwd = str(Path(target_dir).resolve())
        result = agent.run(exec_cmd)
        agent.cwd = old_cwd  # restore after run
        _print_final_summary(result)
        console.print()
        return

    # ── Handle project generation ─────────────────────────────────────
    if not is_edit and is_proj:
         proj_name = Prompt.ask(
             "\n[bold cyan]What should we name the project folder?[/bold cyan]",
             default=description_to_project_name(proj_desc)
         ).strip()

         console.print(
             f"\n[bold magenta]✦ Project requested![/bold magenta] "
             f"[dim]Generating files in [bold]./{proj_name}/[/bold]…[/dim]\n"
         )
         
         gen_proj = generate_project(proj_desc, proj_name)
         
         if not gen_proj["success"]:
             console.print(f"[red]Project generation failed: {gen_proj.get('error')}[/red]")
             return
             
         console.print(f"[bold green]✓ Created {len(gen_proj['files'])} files:[/bold green]")
         for fp in gen_proj['files']:
             console.print(f"  - [cyan]{fp}[/cyan]")
         
         console.print(f"\n[dim]To test the project, cd into {proj_name} and run it.[/dim]")
         return

    # ── Detect if it's a general natural language idea ────────────────
    elif not is_edit and is_natural_language(cmd):
        language = Prompt.ask(
            "\n[bold cyan]What language/framework should this be in?[/bold cyan] (e.g. Python, HTML, React, Node)",
            default="Python"
        ).strip()

        console.print(
            f"\n[bold magenta]✦ Natural language detected![/bold magenta] "
            f"[dim]Generating [bold]{language}[/bold] code for:[/dim] [italic]{cmd}[/italic]\n"
        )
        gen = handle_natural_language(cmd, language=language)
        if not gen["success"]:
            console.print("[red]Code generation failed. Check your GROQ_API_KEY.[/red]")
            return

        # Show generated code
        console.print(
            Panel(
                gen["code"],
                title=f"[bold cyan]Generated: {gen['filename']}[/bold cyan]",
                border_style="magenta",
                box=box.ROUNDED,
            )
        )
        console.print(f"[dim]File saved \u2192 [cyan]{gen['filename']}[/cyan][/dim]\n")

        # ── Code Analysis ─────────────────────────────────────────────
        console.print("[bold yellow]\U0001f50d Analysing code for bugs and improvements\u2026[/bold yellow]\n")
        analysis = _run_analysis(gen["filename"], gen["code"])

        if analysis and analysis["success"]:
            _print_analysis(analysis)

            # If the LLM produced a fixed version, offer to apply it
            if analysis.get("fixed_code"):
                apply = Confirm.ask(
                    "\n[bold yellow]Apply the improved version?[/bold yellow]",
                    default=True,
                )
                if apply:
                    Path(gen["filename"]).write_text(
                        analysis["fixed_code"], encoding="utf-8"
                    )
                    console.print(
                        f"[green]\u2713 Improved code saved to[/green] [cyan]{gen['filename']}[/cyan]\n"
                    )
                    console.print(
                        Panel(
                            analysis["fixed_code"],
                            title="[bold green]Improved Code[/bold green]",
                            border_style="green",
                            box=box.ROUNDED,
                        )
                    )

        cmd = gen["command"]  # run the (possibly improved) file

    result = agent.run(cmd)
    _print_final_summary(result)
    console.print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="self-healing-agent",
        description="AI-powered developer assistant that auto-fixes command errors.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        default=None,
        help="Developer command to run (e.g. 'python app.py'). "
             "If omitted, the agent enters interactive mode.",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Apply suggested fixes automatically without user approval.",
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Display all stored fixes in the error memory database and exit.",
    )
    parser.add_argument(
        "--cwd",
        default=None,
        help="Working directory to run commands in.",
    )

    args = parser.parse_args()

    print_banner()

    agent = SelfHealingAgent(auto_apply=args.auto, cwd=args.cwd)

    # ── Show memory and exit ────────────────────────────────────────────
    if args.memory:
        agent.show_memory()
        sys.exit(0)

    # ── Single command mode ─────────────────────────────────────────────
    if args.command:
        full_command = " ".join(args.command)
        process_command(full_command, agent)
        sys.exit(0)

    # ── Interactive / REPL mode ─────────────────────────────────────────
    console.print("[bold]Interactive mode[/bold] — enter a command to run it.\n")
    while True:
        try:
            cmd = console.input("[bold green]agent>[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not cmd:
            continue

        if cmd.lower() in {"exit", "quit", "q"}:
            console.print("[dim]Goodbye![/dim]")
            break

        process_command(cmd, agent)



def _print_final_summary(result: dict) -> None:
    """Print a compact summary card after each run."""
    success = result["success"]
    color = "green" if success else "red"
    icon = "✓" if success else "✗"
    status = "FIXED & PASSING" if success else "COULD NOT HEAL"

    lines = [
        f"[bold]Command  :[/bold] [cyan]{result['command']}[/cyan]",
        f"[bold]Status   :[/bold] [{color}]{icon}  {status}[/{color}]",
        f"[bold]Attempts :[/bold] {result['attempts']}",
    ]
    if result.get("fix_applied"):
        lines.append(f"[bold]Fix Used :[/bold] [cyan]{result['fix_applied']}[/cyan]")

    console.print(
        Panel(
            "\n".join(lines),
            title="[bold]Session Summary[/bold]",
            border_style=color,
            box=box.ROUNDED,
        )
    )


def _run_analysis(filename: str, code: str) -> dict:
    """Call code_analyzer and return the result dict (or None on failure)."""
    try:
        return analyze_code(code, filename=filename)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Analysis failed: {exc}[/red]")
        return None


def _print_analysis(analysis: dict) -> None:
    """Render a colour-coded analysis panel in the terminal."""
    bugs         = analysis.get("bugs", [])
    missing      = analysis.get("missing", [])
    improvements = analysis.get("improvements", [])

    lines = []

    if bugs:
        lines.append("[bold red]🐛 BUGS FOUND[/bold red]")
        for b in bugs:
            lines.append(f"  [red]• {b}[/red]")
        lines.append("")

    if missing:
        lines.append("[bold yellow]🔧 WHAT IS MISSING[/bold yellow]")
        for m in missing:
            lines.append(f"  [yellow]• {m}[/yellow]")
        lines.append("")

    if improvements:
        lines.append("[bold cyan]💡 IMPROVEMENTS SUGGESTED[/bold cyan]")
        for i in improvements:
            lines.append(f"  [cyan]• {i}[/cyan]")

    if not lines:
        lines.append("[green]✓ No major issues found![/green]")

    console.print(
        Panel(
            "\n".join(lines),
            title="[bold]Code Analysis Report[/bold]",
            border_style="yellow",
            box=box.ROUNDED,
        )
    )


if __name__ == "__main__":
    main()
