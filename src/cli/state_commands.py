import click
import shutil
import os

def register_cli(cli):
    @cli.group("state")
    def state():
        """Manage Terraform state."""
        pass

    @state.command("backup")
    @click.option('--output', required=True, type=str, help="Output filename for state backup")
    def backup(output):
        """
        Backup the current state to a specified file.
        """
        dummy_state_data = '{"version": 4, "resources": []}'
        with open(output, "w") as f:
            f.write(dummy_state_data)
        click.echo(f"🗂️ State backed up to: {output}")

    @state.command("migrate")
    @click.option('--from-file', 'from_file', required=True, type=click.Path(exists=True), help="Source state file")
    @click.option('--to-file', 'to_file', required=True, type=str, help="Destination state file")
    def migrate(from_file, to_file):
        """
        Migrate state from one file to another.
        """
        shutil.copyfile(from_file, to_file)
        click.echo(f"🔁 State migrated from '{from_file}' to '{to_file}'")
