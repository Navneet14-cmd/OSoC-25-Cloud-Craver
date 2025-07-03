
import click
from rich.console import Console

from integrations.jira_client import JiraClient
from integrations.servicenow_client import ServiceNowClient
from auth.rbac import Permission
from cli.auth_commands import rbac_engine, current_user
from audit.logger import audit_logger, AuditEvent

console = Console()


def add_integration_commands(cli):
    """
    Adds integration commands to the CLI.
    """

    @cli.group()
    def integrations():
        """Manage integrations with enterprise tools."""
        pass

    @integrations.group()
    def jira():
        """Manage JIRA integration."""
        pass

    @jira.command()
    @click.option("--project-key", required=True, help="JIRA project key.")
    @click.option("--summary", required=True, help="Ticket summary.")
    @click.option("--description", required=True, help="Ticket description.")
    @click.option("--issue-type", default="Task", help="Issue type (e.g., Task, Bug).")
    def create_ticket(project_key, summary, description, issue_type):
        """Create a JIRA ticket."""
        actor_id = current_user["id"]
        if not rbac_engine.has_permission(actor_id, Permission.CREATE_INFRA):
            console.print("[red]Permission denied. You need 'CREATE_INFRA' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.CREATE_INFRA},
            )
            return

        try:
            client = JiraClient()
            ticket = client.create_ticket(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type,
            )
            if ticket:
                audit_logger.log(
                    AuditEvent.INFRA_CHANGE_REQUESTED,
                    actor_id=actor_id,
                    details={"ticket_system": "jira", "ticket_key": ticket["key"]},
                )
        except Exception as e:
            console.print(f"[red]Failed to create JIRA ticket: {e}[/red]")

    @integrations.group()
    def servicenow():
        """Manage ServiceNow integration."""
        pass

    @servicenow.command()
    @click.option("--short-description", required=True, help="Short description.")
    @click.option("--description", required=True, help="Change request description.")
    @click.option("--assignment-group", required=True, help="Assignment group.")
    def create_change_request(short_description, description, assignment_group):
        """Create a ServiceNow change request."""
        actor_id = current_user["id"]
        if not rbac_engine.has_permission(actor_id, Permission.CREATE_INFRA):
            console.print("[red]Permission denied. You need 'CREATE_INFRA' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.CREATE_INFRA},
            )
            return

        try:
            client = ServiceNowClient()
            change_request = client.create_change_request(
                short_description=short_description,
                description=description,
                assignment_group=assignment_group,
            )
            if change_request:
                audit_logger.log(
                    AuditEvent.INFRA_CHANGE_REQUESTED,
                    actor_id=actor_id,
                    details={
                        "ticket_system": "servicenow",
                        "ticket_number": change_request["number"],
                    },
                )
        except Exception as e:
            console.print(f"[red]Failed to create ServiceNow change request: {e}[/red]")
