import click
import os

def register_cli(cli):
    @cli.command("generate")
    @click.option('--provider', required=True, type=click.Choice(['aws', 'azure'], case_sensitive=False), help="Cloud provider to use")
    @click.option('--template', required=True, type=str, help="Template name to generate")
    def generate(provider, template):
        """
        Generate cloud infrastructure templates based on provider and template name.
        """
        output_dir = os.path.join(".output", provider.lower(), template)
        os.makedirs(output_dir, exist_ok=True)

        # Simulated generation logic
        file_path = os.path.join(output_dir, f"{template}.tf")
        with open(file_path, "w") as f:
            f.write(f"# Terraform template for {provider.upper()} - {template}\n")

        click.echo(f"✅ Template '{template}' for provider '{provider.upper()}' generated at '{output_dir}'")
