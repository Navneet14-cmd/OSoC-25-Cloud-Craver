
import click
from rich.console import Console

from backup.manager import BackupManager
from auth.rbac import Permission
from cli.auth_commands import rbac_engine, current_user
from audit.logger import audit_logger, AuditEvent

console = Console()


def add_backup_commands(cli):
    """
    Adds backup and disaster recovery commands to the CLI.
    """

    @cli.group()
    def backup():
        """Manage backups and disaster recovery."""
        pass

    @backup.command()
    @click.option("--data-path", required=True, help="Path to the application data directory.")
    def create(data_path):
        """Create a backup of the application data."""
        actor_id = current_user["id"]
        if not rbac_engine.has_permission(actor_id, Permission.ADMIN_ACCESS):
            console.print("[red]Permission denied. You need 'ADMIN_ACCESS' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.ADMIN_ACCESS},
            )
            return

        try:
            manager = BackupManager()
            backup_key = manager.create_backup(data_path)
            if backup_key:
                audit_logger.log(
                    AuditEvent.INFRA_APPLY_SUCCESS,
                    actor_id=actor_id,
                    details={"backup_key": backup_key},
                )
        except Exception as e:
            console.print(f"[red]Failed to create backup: {e}[/red]")

    @backup.command()
    @click.option("--backup-key", required=True, help="S3 key of the backup to restore.")
    @click.option("--restore-path", required=True, help="Path to restore the backup to.")
    def restore(backup_key, restore_path):
        """Restore a backup from S3."""
        actor_id = current_user["id"]
        if not rbac_engine.has_permission(actor_id, Permission.ADMIN_ACCESS):
            console.print("[red]Permission denied. You need 'ADMIN_ACCESS' permission.[/red]")
            audit_logger.log(
                AuditEvent.PERMISSION_DENIED,
                actor_id=actor_id,
                details={"permission": Permission.ADMIN_ACCESS},
            )
            return

        try:
            manager = BackupManager()
            manager.restore_backup(backup_key, restore_path)
            audit_logger.log(
                AuditEvent.INFRA_APPLY_SUCCESS,
                actor_id=actor_id,
                details={"backup_key": backup_key},
            )
        except Exception as e:
            console.print(f"[red]Failed to restore backup: {e}[/red]")
