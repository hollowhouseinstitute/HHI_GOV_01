"""CLI commands for governance runtime.

Provides user-facing interface for:
- Creating governance artifacts
- Validating integrity
- Replaying governance state
- Testing adversarial resilience
"""

import click
import json
import time
import hashlib
from pathlib import Path
from typing import Optional

from runtime.event_store import EventStore, GovernanceEvent, EventType
from runtime.reducer import replay_from_store, export_state_to_json
from runtime.agents import BuilderAgent, ValidatorAgent, AdversaryAgent, GovernorAgent


class GovernanceContext:
    """Context for CLI commands."""
    
    def __init__(self):
        self.event_store = EventStore()
        self.builder = BuilderAgent(self.event_store)
        self.validator = ValidatorAgent(self.event_store)
        self.adversary = AdversaryAgent(self.event_store)
        self.governor = GovernorAgent(self.event_store)


@click.group()
@click.pass_context
def cli(ctx):
    """HHI Governance Runtime
    
    Execution-time AI governance framework for runtime accountability,
    Decision Boundaries, Stop Authority, and governance telemetry.
    
    Implements HHI-GOV-01 specification.
    """
    ctx.ensure_object(dict)
    ctx.obj['governance'] = GovernanceContext()


@cli.command()
@click.argument('artifact_id')
@click.option('--authority', default='builder', help='Authority declaring the artifact')
@click.option('--file', type=click.Path(exists=True), help='File to create artifact from')
@click.pass_context
def create(ctx, artifact_id: str, authority: str, file: Optional[str]):
    """Create a new governance artifact.
    
    Emits ARTIFACT_CREATED event to the governance ledger.
    
    Example:
        hhi create HHI_A001 --authority builder
        hhi create HHI_A002 --file path/to/artifact.json
    """
    governance = ctx.obj['governance']
    
    try:
        # Builder agent creates artifact
        result = governance.builder.create_artifact(
            artifact_id=artifact_id,
            authority=authority,
            file_path=file
        )
        
        click.echo(click.style("✓ Artifact Created", fg='green', bold=True))
        click.echo(f"  ID: {result['artifact_id']}")
        click.echo(f"  Hash: {result['hash'][:16]}...")
        click.echo(f"  Event ID: {result['event_id'][:16]}...")
        click.echo(f"  Timestamp: {result['timestamp']}")
        
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red', bold=True))
        ctx.exit(1)


@cli.command()
@click.option('--artifact-id', help='Validate specific artifact')
@click.pass_context
def validate(ctx, artifact_id: Optional[str]):
    """Validate governance artifacts.
    
    Checks SHA256 hashes against canonical registry.
    Emits VALIDATION_PASSED or VALIDATION_FAILED events.
    
    Example:
        hhi validate
        hhi validate --artifact-id HHI_A001
    """
    governance = ctx.obj['governance']
    
    try:
        results = governance.validator.validate_artifacts(
            artifact_id=artifact_id
        )
        
        click.echo(click.style("Validation Results", fg='blue', bold=True))
        
        if not results['validations']:
            click.echo("  No artifacts to validate.")
            return
        
        passed = sum(1 for v in results['validations'].values() if v['valid'])
        total = len(results['validations'])
        
        click.echo(f"  Artifacts: {total}")
        click.echo(f"  Passed: {passed}")
        click.echo(f"  Failed: {total - passed}")
        
        if results['validations']:
            click.echo("\n  Details:")
            for aid, validation in results['validations'].items():
                status = click.style("✓", fg='green') if validation['valid'] else click.style("✗", fg='red')
                click.echo(f"    {status} {aid}: {validation.get('reason', 'OK')}")
        
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red', bold=True))
        ctx.exit(1)


@cli.command()
@click.option('--output', type=click.Path(), default='governance_state.json', help='Output file')
@click.pass_context
def replay(ctx, output: str):
    """Replay governance state from event log.
    
    Deterministically reconstructs state by replaying all events
    in chronological order.
    
    Demonstrates:
    - Event sourcing
    - Deterministic replay
    - State reconstruction
    - Drift detection
    
    Example:
        hhi replay
        hhi replay --output state.json
    """
    governance = ctx.obj['governance']
    
    try:
        state = replay_from_store(governance.event_store)
        
        click.echo(click.style("Governance State (Replayed)", fg='blue', bold=True))
        click.echo(f"  Total Events: {state.total_events}")
        click.echo(f"  Artifacts: {len(state.artifacts)}")
        click.echo(f"  Violations: {len(state.violations)}")
        click.echo(f"  Last Event: {state.last_event_timestamp}")
        
        click.echo("\n" + click.style("Drift Indicators", fg='yellow', bold=True))
        for indicator, value in state.drift_indicators.items():
            click.echo(f"  {indicator}: {value:.4f}")
        
        # Export to file
        export_state_to_json(state, output)
        click.echo(f"\n  State exported to: {output}")
        
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red', bold=True))
        ctx.exit(1)


@cli.command()
@click.argument('artifact_id')
@click.option('--mutation-rate', type=float, default=0.1, help='Mutation rate (0.0-1.0)')
@click.pass_context
def adversary(ctx, artifact_id: str, mutation_rate: float):
    """Test adversarial resilience.
    
    Injects mutations into artifact and tests detection.
    Emits ADVERSARY_DETECTED events.
    
    Demonstrates:
    - Mutation injection
    - Integrity detection
    - Adversarial testing
    
    Example:
        hhi adversary HHI_A001
        hhi adversary HHI_A001 --mutation-rate 0.25
    """
    governance = ctx.obj['governance']
    
    if not (0.0 <= mutation_rate <= 1.0):
        click.echo(click.style("✗ Mutation rate must be between 0.0 and 1.0", fg='red'))
        ctx.exit(1)
    
    try:
        result = governance.adversary.test_artifact(
            artifact_id=artifact_id,
            mutation_rate=mutation_rate
        )
        
        click.echo(click.style("Adversarial Test Results", fg='blue', bold=True))
        click.echo(f"  Artifact: {artifact_id}")
        click.echo(f"  Mutation Rate: {mutation_rate:.2%}")
        click.echo(f"  Original Hash: {result['original_hash'][:16]}...")
        click.echo(f"  Mutated Hash: {result['mutated_hash'][:16]}...")
        click.echo(f"  Detected: {click.style('Yes', fg='green' if result['detected'] else 'red')}")
        
        if result['detected']:
            click.echo(f"\n  ✓ Governance resilience verified")
        else:
            click.echo(f"\n  ✗ Mutation bypassed detection")
        
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red', bold=True))
        ctx.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show governance runtime status.
    
    Displays:
    - Event log statistics
    - Artifact registry
    - Governance violations
    - System health
    
    Example:
        hhi status
    """
    governance = ctx.obj['governance']
    
    try:
        state = replay_from_store(governance.event_store)
        
        click.echo(click.style("HHI Governance Runtime Status", fg='cyan', bold=True))
        click.echo()
        
        # Event statistics
        click.echo(click.style("Event Log", fg='blue', bold=True))
        click.echo(f"  Total Events: {state.total_events}")
        click.echo(f"  Ledger Integrity: {click.style('PASS' if governance.event_store.verify_integrity() else 'FAIL', fg='green' if governance.event_store.verify_integrity() else 'red')}")
        
        # Artifacts
        click.echo("\n" + click.style("Artifact Registry", fg='blue', bold=True))
        click.echo(f"  Total Artifacts: {len(state.artifacts)}")
        valid = sum(1 for a in state.artifacts.values() if a.get('valid'))
        click.echo(f"  Valid: {valid}")
        click.echo(f"  Invalid: {len(state.artifacts) - valid}")
        
        # Governance health
        click.echo("\n" + click.style("Governance Health", fg='blue', bold=True))
        click.echo(f"  Violations: {len(state.violations)}")
        click.echo(f"  Validation Pass Rate: {state.drift_indicators['validation_pass_rate']:.2%}")
        click.echo(f"  Governance Breach Rate: {state.drift_indicators['governance_breach_rate']:.4f}")
        
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red', bold=True))
        ctx.exit(1)


@cli.command()
@click.pass_context
def logs(ctx):
    """Show recent governance events.
    
    Displays latest events from the governance ledger.
    
    Example:
        hhi logs
    """
    governance = ctx.obj['governance']
    
    try:
        events = governance.event_store.load_all()
        
        if not events:
            click.echo("No events in ledger.")
            return
        
        click.echo(click.style("Recent Governance Events", fg='blue', bold=True))
        
        # Show last 10 events
        for event in events[-10:]:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(event.timestamp))
            click.echo(f"  {timestamp} | {event.event_type:20s} | {event.artifact_id:15s} | {event.authority}")
        
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red', bold=True))
        ctx.exit(1)


if __name__ == '__main__':
    cli(obj={})
