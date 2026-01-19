import json
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.tree import Tree

from . import LOG_FILE
from .schema import DecisionRecord

def replay_decision(decision_id: str) -> bool:
    """
    Finds and displays a decision record in a human-readable format.

    Args:
        decision_id: The UUID of the decision to replay.

    Returns:
        True if the record was found and displayed, False otherwise.
    """
    if not LOG_FILE.exists():
        print(f"Error: Log file not found at '{LOG_FILE}'.")
        return False

    console = Console(record=True, highlight=False)

    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                record_data = json.loads(line)
                if record_data.get("decision_id") == decision_id:
                    record = DecisionRecord.parse_obj(record_data)
                    _display_record(console, record)
                    return True
            except json.JSONDecodeError:
                # Skip corrupted lines
                continue
    
    console.print(f"[bold red]Decision ID '{decision_id}' not found.[/bold red]")
    return False

def _display_record(console: Console, record: DecisionRecord):
    """Uses rich to display the record in a structured, readable way."""
    
    # Main tree
    tree = Tree(
        f"[bold cyan]Decision Replay: {record.decision_id}[/bold cyan]",
        guide_style="bold bright_blue",
    )

    # Core Info
    core_info_tree = tree.add("[bold]Core Information[/bold]")
    core_info_tree.add(f"🕰️ [bold]Timestamp:[/bold] {record.timestamp}")
    core_info_tree.add(f"🤖 [bold]Model:[/bold] {record.model}")
    
    # Model Config
    config_json = json.dumps(record.config, indent=2)
    config_syntax = Syntax(config_json, "json", theme="monokai", line_numbers=False)
    core_info_tree.add(Panel(config_syntax, title="[green]Model Config[/green]", border_style="green"))

    # Prompt
    prompt_panel = Panel(Text(record.prompt), title="[yellow]Prompt[/yellow]", border_style="yellow")
    tree.add(prompt_panel)

    # Output
    output_panel = Panel(Text(record.output), title="[magenta]Output[/magenta]", border_style="magenta")
    tree.add(output_panel)

    # Context & Risk
    meta_tree = tree.add("[bold]Metadata[/bold]")
    meta_tree.add(f"📚 [bold]Context Sources:[/bold] {', '.join(record.context_sources)}")
    meta_tree.add(f"🤔 [bold]Confidence:[/bold] {record.confidence if record.confidence is not None else 'N/A'}")
    
    risk_flags_str = ", ".join(record.risk_flags) if record.risk_flags else "None"
    meta_tree.add(f"🚩 [bold]Risk Flags:[/bold] [yellow]{risk_flags_str}[/yellow]")
    
    # Integrity Chain
    integrity_tree = tree.add("[bold]Integrity Chain[/bold]")
    integrity_tree.add(f"🔗 [bold]Previous Hash:[/bold] {record.prev_hash}")
    integrity_tree.add(f"🔐 [bold]Record Hash:[/bold] [bold green]{record.hash}[/bold green]")
    
    console.print(tree)
