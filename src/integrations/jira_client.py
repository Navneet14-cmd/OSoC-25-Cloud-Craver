
import os
from typing import Dict, Optional

from jira import JIRA, JIRAError
from rich.console import Console

console = Console()


class JiraClient:
    """
    A client for interacting with the JIRA API.
    """

    def __init__(
        self,
        server: Optional[str] = None,
        username: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        self.server = server or os.environ.get("JIRA_SERVER")
        self.username = username or os.environ.get("JIRA_USERNAME")
        self.api_token = api_token or os.environ.get("JIRA_API_TOKEN")

        if not all([self.server, self.username, self.api_token]):
            raise ValueError(
                "JIRA server, username, and API token must be provided "
                "either as arguments or environment variables."
            )

        try:
            self.client = JIRA(server=self.server, basic_auth=(self.username, self.api_token))
            # Test connection
            self.client.server_info()
            console.print("[green]Successfully connected to JIRA.[/green]")
        except JIRAError as e:
            console.print(f"[red]Failed to connect to JIRA: {e.message}[/red]")
            raise

    def create_ticket(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
    ) -> Optional[Dict]:
        """
        Creates a new ticket in a JIRA project.
        """
        try:
            issue_dict = {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
            }
            new_issue = self.client.create_issue(fields=issue_dict)
            console.print(f"[green]Successfully created JIRA ticket: {new_issue.key}[/green]")
            return {"key": new_issue.key, "url": new_issue.permalink()}
        except JIRAError as e:
            console.print(f"[red]Failed to create JIRA ticket: {e.text}[/red]")
            return None
