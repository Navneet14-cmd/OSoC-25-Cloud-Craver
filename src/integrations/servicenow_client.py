
import os
import requests
from typing import Dict, Optional

from rich.console import Console

console = Console()


class ServiceNowClient:
    """
    A client for interacting with the ServiceNow API.
    """

    def __init__(
        self,
        instance: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.instance = instance or os.environ.get("SERVICENOW_INSTANCE")
        self.username = username or os.environ.get("SERVICENOW_USERNAME")
        self.password = password or os.environ.get("SERVICENOW_PASSWORD")

        if not all([self.instance, self.username, self.password]):
            raise ValueError(
                "ServiceNow instance, username, and password must be provided "
                "either as arguments or environment variables."
            )

        self.base_url = f"https://{self.instance}.service-now.com/api/now/table"
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

        # Test connection
        try:
            response = self.session.get(f"{self.base_url}/incident", params={"sysparm_limit": 1})
            response.raise_for_status()
            console.print("[green]Successfully connected to ServiceNow.[/green]")
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Failed to connect to ServiceNow: {e}[/red]")
            raise

    def create_change_request(
        self,
        short_description: str,
        description: str,
        assignment_group: str,
    ) -> Optional[Dict]:
        """
        Creates a new change request in ServiceNow.
        """
        url = f"{self.base_url}/change_request"
        payload = {
            "short_description": short_description,
            "description": description,
            "assignment_group": assignment_group,
        }

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            change_request = response.json().get("result", {})
            console.print(
                f"[green]Successfully created ServiceNow change request: "
                f"{change_request.get('number')}[/green]"
            )
            return {
                "number": change_request.get("number"),
                "sys_id": change_request.get("sys_id"),
            }
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Failed to create ServiceNow change request: {e}[/red]")
            return None
