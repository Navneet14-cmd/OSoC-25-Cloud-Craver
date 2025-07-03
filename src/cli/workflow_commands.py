
import click
from rich.console import Console

from workflows.approval import ApprovalWorkflow, ApprovalRequest
from auth.rbac import Permission
from cli.auth_commands import rbac_engine, current_user
from audit.logger import audit_logger, AuditEvent

console = Console()

# In a real application, you would initialize the workflow engine
# with the RBAC engine and a persistent storage file.
approval_workflow = ApprovalWorkflow(rbac_engine=rbac_engine)


def add_workflow_commands(cli):
    """
    Adds workflow commands to the CLI.
    """

    @cli.group()
    def workflow():
        """Manage approval workflows."""
        pass

    @workflow.command()
    @click.option("--summary", required=True, help="Summary of the change.")
    @click.option("--details", required=True, help="Detailed description of the change.")
    def request_approval(summary, details):
        """Request approval for an infrastructure change."""
        actor_id = current_user["id"]
        if not rbac_engine.has_permission(actor_id, Permission.CREATE_INFRA):
            console.print("[red]Permission denied. You need 'CREATE_INFRA' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.CREATE_INFRA},
            )
            return

        request = ApprovalRequest(
            requester_id=actor_id,
            change_summary=summary,
            change_details={"description": details},
        )
        approval_workflow.create_request(request)

    @workflow.command()
    @click.argument("request_id")
    @click.option("--comment", help="Optional comment.")
    def approve(request_id, comment):
        """Approve a pending request."""
        actor_id = current_user["id"]
        try:
            approval_workflow.approve_request(request_id, actor_id, comment)
        except (ValueError, PermissionError) as e:
            console.print(f"[red]Error: {e}[/red]")

    @workflow.command()
    def list_pending():
        """List all pending approval requests."""
        actor_id = current_user["id"]
        if not rbac_engine.has_permission(actor_id, Permission.APPROVE_CHANGES):
            console.print("[red]Permission denied. You need 'APPROVE_CHANGES' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.APPROVE_CHANGES},
            )
            return

        approval_workflow.list_pending_requests()
