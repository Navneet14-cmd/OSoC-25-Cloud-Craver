import click
import os

def register_cli(cli):
    @cli.command("validate")
    @click.option('--template-path', required=True, type=click.Path(exists=True), help="Path to the template file or directory")
    def validate(template_path):
        """
        Validate the given cloud infrastructure template(s).
        """
        # Simulated validation logic
        if "invalid" in template_path.lower():
            click.echo("❌ Validation failed: Invalid dependency graph detected.")
            exit(1)
        else:
            click.echo(f"✅ Validation passed for template at: {template_path}")
