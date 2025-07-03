
import os
import tempfile
from typing import Dict, List, Optional

import ansible_runner
from rich.console import Console

console = Console()


class AnsibleClient:
    """
    A client for running Ansible playbooks.
    """

    def __init__(self, private_data_dir: Optional[str] = None):
        self.private_data_dir = private_data_dir or tempfile.mkdtemp()

    def run_playbook(
        self,
        playbook: str,
        inventory: str,
        extra_vars: Optional[Dict] = None,
    ) -> bool:
        """
        Runs an Ansible playbook.
        """
        if not os.path.exists(playbook):
            console.print(f"[red]Playbook not found at '{playbook}'[/red]")
            return False

        if not os.path.exists(inventory):
            console.print(f"[red]Inventory not found at '{inventory}'[/red]")
            return False

        r = ansible_runner.run(
            private_data_dir=self.private_data_dir,
            playbook=playbook,
            inventory=inventory,
            extravars=extra_vars,
        )

        if r.status == "successful":
            console.print("[green]Playbook executed successfully.[/green]")
            return True
        else:
            console.print(f"[red]Playbook execution failed with status: {r.status}[/red]")
            console.print(f"  RC: {r.rc}")
            console.print(f"  Logs: {r.stdout.read()}")
            return False
