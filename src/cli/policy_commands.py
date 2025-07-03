
import json
import click
from rich.console import Console

from pdp.engine import PolicyEngine
from auth.rbac import Permission
from cli.auth_commands import rbac_engine, current_user
from audit.logger import audit_logger, AuditEvent

console = Console()


def add_policy_commands(cli):
    """
    Adds policy commands to the CLI.
    """

    @cli.group()
    def policy():
        """Manage and evaluate policies."""
        pass

    @policy.command()
    @click.option("--policy-path", required=True, help="Path to the policy to evaluate.")
    @click.option("--input-data", required=True, help="Input data for the policy (JSON string).")
    def evaluate(policy_path, input_data):
        """Evaluate a policy with the given input data."""
        actor_id = current_user["id"]
        if not rbac_engine.has_permission(actor_id, Permission.MANAGE_POLICY):
            console.print("[red]Permission denied. You need 'MANAGE_POLICY' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.MANAGE_POLICY},
            )
            return

        try:
            engine = PolicyEngine()
            input_dict = json.loads(input_data)
            result = engine.evaluate_policy(policy_path, input_dict)
            if result:
                console.print("[green]Policy evaluation result:[/green]")
                console.print(json.dumps(result, indent=2))
                audit_logger.log(
                    AuditEvent.POLICY_EVALUATION,
                    actor_id=actor_id,
                    details={"policy_path": policy_path, "result": result},
                )
        except json.JSONDecodeError:
            console.print("[red]Error: Invalid JSON format for input data.[/red]")
        except Exception as e:
            console.print(f"[red]Failed to evaluate policy: {e}[/red]")
