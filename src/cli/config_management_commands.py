
import json
import click
from rich.console import Console

from integrations.config_management.ansible_client import AnsibleClient
from auth.rbac import Permission
from cli.auth_commands import rbac_engine, current_user
from audit.logger import audit_logger, AuditEvent

console = Console()


def add_config_management_commands(cli):
    """
    Adds configuration management commands to the CLI.
    """

    @cli.group()
    def config_management():
        """Manage configuration management integrations."""
        pass

    @config_management.group()
    def ansible():
        """Manage Ansible integration."""
        pass

    @ansible.command()
    @click.option("--playbook", required=True, help="Path to the Ansible playbook.")
    @click.option("--inventory", required=True, help="Path to the Ansible inventory.")
    @click.option("--extra-vars", help="Extra variables for the playbook (JSON string).")
    def run_playbook(playbook, inventory, extra_vars):
        """Run an Ansible playbook."""
        actor_id = current_user["id"]
        if not rbac_engine.has_permission(actor_id, Permission.UPDATE_INFRA):
            console.print("[red]Permission denied. You need 'UPDATE_INFRA' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.UPDATE_INFRA},
            )
            return

        try:
            client = AnsibleClient()
            extra_vars_dict = json.loads(extra_vars) if extra_vars else None
            success = client.run_playbook(
                playbook=playbook,
                inventory=inventory,
                extra_vars=extra_vars_dict,
            )
            if success:
                audit_logger.log(
                    AuditEvent.INFRA_APPLY_SUCCESS,
                    actor_id=actor_id,
                    details={"playbook": playbook},
                )
            else:
                audit_logger.log(
                    AuditEvent.INFRA_APPLY_FAILURE,
                    actor_id=actor_id,
                    details={"playbook": playbook},
                )
        except json.JSONDecodeError:
            console.print("[red]Error: Invalid JSON format for extra variables.[/red]")
        except Exception as e:
            console.print(f"[red]Failed to run playbook: {e}[/red]")
