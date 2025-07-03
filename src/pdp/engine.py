
from typing import Any, Dict, Optional

from rich.console import Console
from opa_client.opa import OpaClient as OPAClient

console = Console()


class PolicyEngine:
    """
    A client for interacting with an Open Policy Agent (OPA) instance.
    """

    def __init__(self, host: str = "localhost", port: int = 8181, version: str = "v1"):
        self.client = OPAClient(host=host, port=port, version=version)
        try:
            # Test connection
            self.client.check_connection()
            console.print("[green]Successfully connected to OPA.[/green]")
        except Exception as e:
            console.print(f"[red]Failed to connect to OPA: {e}[/red]")
            raise

    def evaluate_policy(
        self, policy_path: str, input_data: Dict[str, Any]
    ) -> Optional[Dict]:
        """
        Evaluates a policy with the given input data.
        """
        try:
            result = self.client.get_policy_decision(
                policy_path=policy_path, input_data=input_data
            )
            return result
        except Exception as e:
            console.print(f"[red]Failed to evaluate policy: {e}[/red]")
            return None
