"""
agent.py
--------
The SelfHealingAgent class — the central orchestrator that implements the
Observe → Reason → Act loop.

Flow
----
1. Run the developer command            (Observe)
2. Parse the output for errors          (Observe)
3. Look up ErrorMemory for a cached fix (Reason)
4. If no cache hit, call the LLM        (Reason)
5. Present fix to the user & get approval (Act gate)
6. Apply the fix                        (Act)
7. Record the fix in ErrorMemory        (Memory)
8. Re-run the original command          (Verify)
9. Report success or escalate           (Report)

Up to MAX_RETRIES attempts are made before the agent gives up.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich import box

from command_runner import run_command
from error_parser import parse_error, summarise_error
from fix_generator import generate_fix
from fix_applier import apply_fix
from memory_db import ErrorMemory
from logger import get_logger

load_dotenv()
log = get_logger(__name__)
console = Console()

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))


class SelfHealingAgent:
    """
    AI-powered self-healing agent.

    Parameters
    ----------
    auto_apply : bool  – skip user approval and apply fixes automatically
                         (useful for batch / CI mode)
    memory     : ErrorMemory instance (created fresh if not provided)
    cwd        : working directory for command execution
    """

    def __init__(
        self,
        auto_apply: bool = False,
        memory: Optional[ErrorMemory] = None,
        cwd: Optional[str] = None,
    ):
        self.auto_apply = auto_apply
        self.memory = memory or ErrorMemory()
        self.cwd = cwd
        self._attempt = 0

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, command: str) -> dict:
        """
        Execute *command* and attempt to self-heal any errors.

        Returns
        -------
        dict:
            command        – original command
            success        – True if the command eventually succeeded
            attempts       – number of fix attempts made
            fix_applied    – the fix command that was applied (or None)
            final_result   – last run_command result dict
        """
        self._attempt = 0
        original_command = command

        console.rule(f"[bold blue]Self-Healing Agent[/bold blue]")
        console.print(f"\n[bold]▶  Running:[/bold]  [cyan]{command}[/cyan]\n")

        result = run_command(command, cwd=self.cwd)
        self._print_run_result(result)

        if result["success"]:
            console.print("[bold green]✓ Command succeeded on first run![/bold green]\n")
            return self._summary(original_command, True, 0, None, result)

        # ── Error detected — enter the heal loop ─────────────────────────
        last_fix = None

        for attempt in range(1, MAX_RETRIES + 1):
            self._attempt = attempt
            console.rule(f"[yellow]Attempt {attempt}/{MAX_RETRIES}[/yellow]")

            # Step 1: Parse error
            error_info = parse_error(result)
            if not error_info["has_error"]:
                console.print("[red]Non-zero exit but no parseable error. Aborting.[/red]")
                break

            self._print_error_panel(error_info)

            # Step 2: Generate fix
            console.print("[dim]Consulting the LLM…[/dim]")
            fix = generate_fix(original_command, error_info, memory=self.memory)
            self._print_fix_panel(fix)

            if not fix.get("fix_command"):
                console.print(
                    "[red]No executable fix command was generated. "
                    "Manual intervention required.[/red]"
                )
                break

            # Step 3: Get user approval (unless auto_apply)
            approved = self._ask_approval(fix)
            if not approved:
                console.print("[yellow]Fix rejected by user. Stopping.[/yellow]")
                break

            # Step 4: Apply fix
            fix_result = apply_fix(fix["fix_command"], cwd=self.cwd, fix=fix)
            last_fix = fix["fix_command"]

            if not fix_result["success"]:
                console.print(
                    f"[red]Fix command failed (exit {fix_result['returncode']}).[/red]\n"
                    f"stderr: {fix_result['stderr'][:300]}"
                )
                # Store as a failed attempt so the agent avoids it next time
                self.memory.store(
                    error_info["error_type"],
                    error_info.get("error_message", ""),
                    original_command,
                    fix["fix_command"],
                    fix.get("explanation", ""),
                    success=False,
                )
                continue  # try again

            # Step 5: Re-run original command
            console.print(f"\n[bold]▶  Re-running:[/bold] [cyan]{original_command}[/cyan]\n")
            result = run_command(original_command, cwd=self.cwd)
            self._print_run_result(result)

            # Step 6: Store in memory
            self.memory.store(
                error_info["error_type"],
                error_info.get("error_message", ""),
                original_command,
                fix["fix_command"],
                fix.get("explanation", ""),
                success=result["success"],
            )

            if result["success"]:
                console.print(
                    f"\n[bold green]✓ Command succeeded after {attempt} fix attempt(s)![/bold green]\n"
                )
                return self._summary(original_command, True, attempt, last_fix, result)

            console.print("[yellow]Command still failing. Trying another round…[/yellow]\n")

        console.print(
            f"\n[bold red]✗ Agent could not fix the problem after "
            f"{self._attempt} attempt(s).[/bold red]\n"
        )
        return self._summary(original_command, False, self._attempt, last_fix, result)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ask_approval(self, fix: dict) -> bool:
        """Ask user via console whether to apply the fix."""
        if self.auto_apply:
            log.info("auto_apply=True — skipping approval prompt.")
            return True
        return Confirm.ask("\n[bold yellow]Apply this fix?[/bold yellow]", default=True)

    def _print_run_result(self, result: dict) -> None:
        status = "[green]SUCCESS[/green]" if result["success"] else "[red]FAILED[/red]"
        console.print(
            f"  Status : {status}  |  "
            f"Exit : {result['returncode']}  |  "
            f"Time : {result['elapsed']}s"
        )
        if result["stdout"].strip():
            console.print(Panel(result["stdout"].strip(), title="stdout", border_style="dim"))
        if result["stderr"].strip():
            console.print(Panel(result["stderr"].strip(), title="stderr", border_style="red dim"))

    def _print_error_panel(self, error_info: dict) -> None:
        summary = summarise_error(error_info)
        console.print(
            Panel(
                summary,
                title="[bold red]Error Detected[/bold red]",
                border_style="red",
                box=box.ROUNDED,
            )
        )

    def _print_fix_panel(self, fix: dict) -> None:
        source = "[green]memory cache[/green]" if fix.get("from_cache") else "[magenta]LLM[/magenta]"
        confidence_color = {"high": "green", "medium": "yellow", "low": "red"}.get(
            fix.get("confidence", "medium"), "white"
        )
        content = (
            f"[bold]Fix Command :[/bold] [cyan]{fix.get('fix_command', '(none)')}[/cyan]\n"
            f"[bold]Confidence  :[/bold] [{confidence_color}]{fix.get('confidence', '?')}[/{confidence_color}]\n"
            f"[bold]Source      :[/bold] {source}\n\n"
            f"[dim]{fix.get('explanation', '')}[/dim]"
        )
        console.print(
            Panel(
                content,
                title="[bold cyan]Suggested Fix[/bold cyan]",
                border_style="cyan",
                box=box.ROUNDED,
            )
        )

    @staticmethod
    def _summary(command, success, attempts, fix_applied, final_result) -> dict:
        return {
            "command": command,
            "success": success,
            "attempts": attempts,
            "fix_applied": fix_applied,
            "final_result": final_result,
        }

    # ------------------------------------------------------------------
    # Convenience: display memory contents
    # ------------------------------------------------------------------

    def show_memory(self) -> None:
        records = self.memory.get_all()
        if not records:
            console.print("[dim]No records in error memory yet.[/dim]")
            return

        table = Table(title="Error Memory Database", box=box.SIMPLE_HEAVY)
        table.add_column("ID", style="dim", width=4)
        table.add_column("Error Type", style="yellow")
        table.add_column("Fix Command", style="cyan")
        table.add_column("Success", style="green")
        table.add_column("Applied At", style="dim")

        for r in records:
            table.add_row(
                str(r["id"]),
                r["error_type"],
                r["fix_command"],
                "✓" if r["success"] else "✗",
                r["applied_at"][:19],
            )

        console.print(table)
