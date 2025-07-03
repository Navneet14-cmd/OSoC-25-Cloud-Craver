import click, os

def register_cli(cli):
    @cli.command("generate")
    @click.option("--provider", "-p", required=True, type=click.Choice(["aws", "azure", "gcp"], case_sensitive=False), help="Cloud provider")
    @click.option("--template", "-t", required=True, help="Template name")
    @click.option("--output", "-o", default=".output", type=click.Path(), help="Output directory root")
    def generate(provider, template, output):
        out_dir = os.path.join(output, provider.lower(), template)
        os.makedirs(out_dir, exist_ok=True)
        file_path = os.path.join(out_dir, f"{template}.tf")
        with open(file_path, "w") as f:
            f.write(f"# Dummy template for {provider}/{template}\n")
        click.echo(f"Generated template at {file_path}")
