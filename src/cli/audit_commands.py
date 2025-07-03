
import click
from rich.console import Console

from audit.reporting import ComplianceReporter
from auth.rbac import Permission
from cli.auth_commands import rbac_engine, current_user
from audit.logger import audit_logger, AuditEvent

console = Console()


def add_audit_commands(cli):
    """
    Adds audit and compliance commands to the CLI.
    """

    @cli.group()
    def audit():
        """Generate audit and compliance reports."""
        pass

    @audit.command()
    @click.option("--days", default=7, help="Number of days to include in the report.")
    @click.option("--user-id", help="Filter report by a specific user ID.")
    @click.option("--event-type", help="Filter report by a specific event type.")
    def report(days, user_id, event_type):
        """Generate a general activity report."""
        actor_id = current_user["id"]
        if not rbac_engine.has_permission(actor_id, Permission.VIEW_AUDIT_LOGS):
            console.print("[red]Permission denied. You need 'VIEW_AUDIT_LOGS' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.VIEW_AUDIT_LOGS},
            )
            return

        reporter = ComplianceReporter()
        reporter.generate_activity_report(days=days, user_id=user_id, event_type=event_type)

    @audit.command()
    @click.option("--days", default=30, help="Number of days to include in the report.")
    def permission_report(days):
        """Generate a report of permission changes."""
        actor_id = current_user["id"]
        if not rbac_engine.has_permission(actor_id, Permission.VIEW_AUDIT_LOGS):
            console.print("[red]Permission denied. You need 'VIEW_AUDIT_LOGS' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.VIEW_AUDIT_LOGS},
            )
            return

        reporter = ComplianceReporter()
        reporter.generate_permission_change_report(days=days)
