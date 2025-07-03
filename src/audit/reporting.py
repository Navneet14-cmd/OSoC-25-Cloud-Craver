
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from rich.console import Console
from rich.table import Table

from audit.logger import AUDIT_LOG_FILE, AuditEvent

console = Console()


class ComplianceReporter:
    """
    Generates compliance reports from the audit log.
    """

    def __init__(self, audit_log_file: str = AUDIT_LOG_FILE):
        self.log_file = audit_log_file

    def _load_audit_data(self) -> List[Dict]:
        """Load and parse the audit log file."""
        try:
            with open(self.log_file, "r") as f:
                return [json.loads(line) for line in f]
        except FileNotFoundError:
            console.print(f"[yellow]Audit log file not found at '{self.log_file}'.[/yellow]")
            return []
        except json.JSONDecodeError:
            console.print(f"[red]Error decoding JSON from audit log file.[/red]")
            return []

    def generate_activity_report(
        self,
        days: int = 7,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ):
        """
        Generate a report of all activities within a given time frame.
        """
        data = self._load_audit_data()
        if not data:
            return

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Filter by time
        end_date = datetime.now(df["timestamp"].dt.tz)
        start_date = end_date - timedelta(days=days)
        df = df[df["timestamp"] >= start_date]

        # Filter by user and event type
        if user_id:
            df = df[df["actor_id"] == user_id]
        if event_type:
            df = df[df["event"] == event_type]

        if df.empty:
            console.print("[yellow]No matching audit events found for the given criteria.[/yellow]")
            return

        # Create a rich table for display
        table = Table(title=f"Audit Activity Report (Last {days} Days)")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Event", style="magenta")
        table.add_column("Actor ID", style="green")
        table.add_column("Target ID", style="yellow")
        table.add_column("Status", style="blue")
        table.add_column("Details", style="red")

        for _, row in df.iterrows():
            table.add_row(
                str(row["timestamp"]),
                row["event"],
                row["actor_id"],
                str(row["target_id"]),
                row["status"],
                json.dumps(row["details"]),
            )

        console.print(table)

    def generate_permission_change_report(self, days: int = 30):
        """
        Generate a report of all role and permission changes.
        """
        permission_events = [
            AuditEvent.ROLE_ASSIGNED.value,
            AuditEvent.ROLE_REMOVED.value,
        ]
        self.generate_activity_report(days=days, event_type="|".join(permission_events))
