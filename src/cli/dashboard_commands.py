
import subprocess
import sys

import click
from rich.console import Console

console = Console()


def add_dashboard_commands(cli):
    """
    Adds dashboard commands to the CLI.
    """

    @cli.command()
    def dashboard():
        """
        Launch the enterprise reporting and analytics dashboard.
        """
        try:
            console.print("[cyan]Launching the dashboard...[/cyan]")
            subprocess.run(
                [sys.executable, "-m", "streamlit", "run", "src/dashboard/app.py"],
                check=True,
            )
        except FileNotFoundError:
            console.print("[red]Error: 'streamlit' command not found.[/red]")
            console.print("[yellow]Please ensure that Streamlit is installed.[/yellow]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error launching dashboard: {e}[/red]")
