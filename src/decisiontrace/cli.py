import json
import click
from pathlib import Path

from . import logger, replay as replay_module, hasher
from .__init__ import __version__

@click.group()
@click.version_option(__version__)
def cli():
    """
    DecisionTrace: An append-only audit log for AI decisions.
    
    This CLI provides tools to log and replay AI decisions, ensuring they
    can be audited later. Integrity is maintained through a hash chain.
    """
    pass

@cli.command()
@click.argument('decision_file', type=click.Path(exists=True, dir_okay=False, readable=True))
def log(decision_file: str):
    """
    Log a new decision from a JSON file.
    
    The JSON file must contain the core fields for a decision:
    model, config, prompt, context_sources, output, confidence, risk_flags.
    """
    try:
        with open(decision_file, 'r') as f:
            data = json.load(f)

        # Basic validation of input file
        required_fields = ["model", "config", "prompt", "context_sources", "output"]
        if not all(field in data for field in required_fields):
            missing = set(required_fields) - set(data.keys())
            raise click.BadParameter(f"Input JSON is missing required fields: {', '.join(missing)}")

        record = logger.log_decision(
            model=data["model"],
            config=data["config"],
            prompt=data["prompt"],
            context_sources=data["context_sources"],
            output=data["output"],
            confidence=data.get("confidence"),
            risk_flags=data.get("risk_flags")
        )
        
        click.secho("Decision successfully logged.", fg="green")
        click.echo(f"  Decision ID: {record.decision_id}")
        click.echo(f"  Record Hash: {record.hash}")
        
    except json.JSONDecodeError:
        raise click.BadParameter("The provided file is not valid JSON.")
    except Exception as e:
        click.secho(f"An error occurred: {e}", fg="red")
        raise click.Abort()


@cli.command()
@click.argument('decision_id', type=str)
def replay(decision_id: str):
    """

    Replay a recorded decision by its ID.
    
    Searches the audit log and displays the full decision record in a
    human-readable format if found.
    """
    if not replay_module.replay_decision(decision_id):
        raise click.Abort()

@cli.command()
def verify():
    """
    Verify the integrity of the entire decision log.

    Checks the hash chain and recalculates hashes for all records to
    detect tampering or corruption.
    """
    click.echo("Verifying integrity of the decision log...")
    is_valid = hasher.verify_chain()
    if is_valid:
        click.secho("✅ Success: The decision log is intact and the hash chain is valid.", fg="green")
    else:
        click.secho("🔥 Critical: The decision log has been tampered with or is corrupt.", fg="red")
        click.secho("Review the errors above to identify the point of failure.", fg="red")
        raise click.Abort()

if __name__ == '__main__':
    cli()
