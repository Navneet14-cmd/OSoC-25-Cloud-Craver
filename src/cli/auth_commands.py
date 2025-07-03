
import click
from rich.console import Console

from auth.saml import perform_saml_login
from config.saml_config import get_saml_settings
from auth.rbac import RBACEngine, Permission
from audit.logger import audit_logger, AuditEvent

console = Console()

# In a real application, you would have a way to manage the current user's session
# and load the RBAC engine state from a persistent store.
# For this example, we'll use a simple global instance.
rbac_engine = RBACEngine()
# This would be set upon successful login
current_user = {"id": None, "roles": []}


def add_auth_commands(cli):
    """
    Adds authentication and authorization commands to the CLI.
    """

    @cli.group()
    def auth():
        """Manage authentication and user roles."""
        pass

    @auth.command()
    def login():
        """Initiate SSO login."""
        try:
            saml_settings = get_saml_settings()
            user_data = perform_saml_login(saml_settings)

            if user_data:
                console.print("[green]SSO login successful![/green]")
                current_user["id"] = user_data["name_id"]
                audit_logger.log(AuditEvent.USER_LOGIN_SUCCESS, actor_id=current_user["id"])
                # In a real app, you would map SAML groups to RBAC roles here
                # For now, we'll assign a default role for demonstration
                rbac_engine.assign_role_to_user(current_user["id"], "Developer")
                console.print(f"User '{current_user['id']}' assigned default 'Developer' role.")
            else:
                console.print("[red]SSO login failed.[/red]")
                audit_logger.log(AuditEvent.USER_LOGIN_FAILURE, actor_id="unknown")
        except ImportError:
            console.print("[red]Error: Missing required modules for SSO login.[/red]")
            console.print("[yellow]Please ensure 'python3-saml' is installed.[/yellow]")
        except Exception as e:
            console.print(f"[red]An unexpected error occurred during login: {e}[/red]")
            audit_logger.log(AuditEvent.USER_LOGIN_FAILURE, actor_id="unknown", details={"error": str(e)})

    @auth.command()
    @click.argument("user_id")
    @click.argument("role_name")
    def assign_role(user_id, role_name):
        """Assign a role to a user."""
        actor_id = current_user["id"]
        # This is a protected action, so we check for permission
        if not rbac_engine.has_permission(actor_id, Permission.MANAGE_ROLES):
            console.print("[red]Permission denied. You need 'MANAGE_ROLES' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.MANAGE_ROLES},
            )
            return

        try:
            rbac_engine.assign_role_to_user(user_id, role_name)
            audit_logger.log(
                AuditEvent.ROLE_ASSIGNED,
                actor_id=actor_id,
                target_id=user_id,
                details={"role": role_name},
            )
            console.print(f"Role '{role_name}' assigned to user '{user_id}'.")
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")

    @auth.command()
    @click.argument("user_id")
    def show_permissions(user_id):
        """Show the permissions for a given user."""
        actor_id = current_user["id"]
        if not rbac_engine.has_permission(actor_id, Permission.MANAGE_USERS):
            console.print("[red]Permission denied. You need 'MANAGE_USERS' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.MANAGE_USERS},
            )
            return

        permissions = rbac_engine.get_user_permissions(user_id)
        if permissions:
            console.print(f"Permissions for user '{user_id}':")
            for perm in sorted(list(permissions)):
                console.print(f"  - {perm}")
        else:
            console.print(f"User '{user_id}' has no assigned permissions.")
