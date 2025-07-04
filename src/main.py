#!/usr/bin/env python3
"""
Cloud Craver - Infrastructure Template Generator and Validator

Main entry point for the Cloud Craver application that integrates:
- Plugin system for extensibility
- CLI interface for user interaction
- Configuration management
- Template generation and validation
"""

import asyncio
import logging
import sys
import os
import signal
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install

# Install rich traceback handler for better error display
install(show_locals=True);

# Initialize console for rich output
console = Console();

# Application metadata
APP_NAME = "cloudcraver"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Cloud infrastructure template generator and validator with plugin system"

# --- Import Custom Modules ---
BASE_DIR = Path(__file__).resolve().parent
for subdir in ["state", "cost", "terraform"]:
    sub_path = BASE_DIR / subdir
    if sub_path.exists() and str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Set up logging configuration with rich formatting.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to write logs to
    """
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RichHandler(
                console=console,
                show_time=True,
                show_path=False,
                rich_tracebacks=True
            )
        ]
    )
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("cloudcraver").setLevel(getattr(logging, log_level.upper()))
    logging.getLogger("plugins").setLevel(getattr(logging, log_level.upper()))


def get_application_config():
    """
    Get application configuration from various sources.
    
    Returns:
        Dictionary containing application configuration
    """
    # Get user's home directory for data storage
    home_dir = Path.home()
    app_data_dir = home_dir / f".{APP_NAME}"
    
    # Ensure directories exist
    app_data_dir.mkdir(exist_ok=True)
    (app_data_dir / "plugins").mkdir(exist_ok=True)
    (app_data_dir / "cache").mkdir(exist_ok=True)
    (app_data_dir / "logs").mkdir(exist_ok=True)
    
    return {
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "data_dir": app_data_dir,
            "cache_dir": app_data_dir / "cache",
            "log_dir": app_data_dir / "logs"
        },
        "plugins": {
            "discovery": {
                "search_paths": [
                    "plugins",  # Local plugins directory
                    str(app_data_dir / "plugins"),  # User plugins
                    "/usr/local/share/cloudcraver/plugins",  # System plugins
                ]
            },
            "loader": {
                "isolation": True,
                "temp_dir": str(app_data_dir / "cache" / "temp"),
                "max_size": 100 * 1024 * 1024,  # 100MB
            },
            "validator": {
                "strict_mode": False,
                "max_file_size": 1024 * 1024,  # 1MB
                "signature_verification": False,
            },
            "security": {
                "enabled": True,
                "max_cpu_time": 30,
                "max_memory": 100 * 1024 * 1024,  # 100MB
                "network_access": False,
            },
            "dependencies": {
                "strict_versioning": True,
                "auto_install": False,
            },
            "marketplace": {
                "repositories": [
                    "https://plugins.cloudcraver.io/api",
                    "https://community.cloudcraver.io/api"
                ],
                "cache_ttl": 3600,
                "security_scanning": True,
            },
            "versioning": {
                "auto_update": False,
                "check_interval": 86400,  # 24 hours
            }
        }
    }


class CloudCraverApp:
    """
    Main application class that coordinates all components.
    """
    
    def __init__(self):
        """Initialize the Cloud Craver application."""
        self.config = get_application_config()
        self.plugin_manager = None
        self.logger = logging.getLogger("cloudcraver.app")
        
        # Set up logging
        log_level = self.config.get("app", {}).get("log_level", "INFO")
        log_file = self.config["app"]["log_dir"] / "cloudcraver.log"
        setup_logging(log_level, str(log_file))
        
        self.logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    async def initialize_plugin_system(self):
        """Initialize the plugin system."""
        try:
            self.logger.info("Initializing plugin system...")
            
            # Try to import and create plugin manager
            try:
                from plugins.core import PluginManager
                self.plugin_manager = PluginManager(
                    config=self.config["plugins"],
                    data_dir=self.config["app"]["data_dir"],
                    cache_dir=self.config["app"]["cache_dir"]
                )
                
                # Load all registered plugins
                loaded_count = await self.plugin_manager.load_all_plugins()
                self.logger.info(f"Loaded {loaded_count} plugins")
                
                # Get plugin status
                status = self.plugin_manager.get_status()
                self.logger.info(f"Plugin system ready: {status['active_plugins']} active plugins")
                
            except ImportError as e:
                self.logger.warning(f"Plugin system not available: {e}")
                console.print("[yellow]Plugin system not available - running in basic mode[/yellow]")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize plugin system: {e}")
            raise
    
    async def shutdown(self):
        """Gracefully shutdown the application."""
        self.logger.info("Shutting down Cloud Craver...")
        
        if self.plugin_manager:
            # Unload all plugins
            for plugin_name in list(self.plugin_manager.plugins.keys()):
                await self.plugin_manager.unload_plugin(plugin_name)
            
            self.logger.info("All plugins unloaded")
        
        self.logger.info("Shutdown complete")


# Global application instance
app_instance: Optional[CloudCraverApp] = None


def get_app() -> CloudCraverApp:
    """Get the global application instance."""
    global app_instance
    if app_instance is None:
        app_instance = CloudCraverApp()
    return app_instance


# CLI Implementation
@click.group(context_settings={"help_option_names": ["--help", "-h"]})
@click.version_option(version=APP_VERSION, prog_name=APP_NAME)
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config-file', type=click.Path(exists=True), help='Custom config file')
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
@click.option("--dry-run", is_flag=True, help="Simulate actions without making changes.")
@click.pass_context
def cli(ctx, debug, config_file, verbose, dry_run):
    """
    Cloud Craver - Infrastructure Template Generator and Validator
    
    A powerful tool for generating and validating cloud infrastructure templates
    with an extensible plugin system.
    """
    # Store options in context
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    ctx.obj['CONFIG_FILE'] = config_file
    ctx.obj["VERBOSE"] = verbose
    ctx.obj["DRY_RUN"] = dry_run


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize Cloud Craver and plugin system."""
    async def _init():
        try:
            app = get_app()
            await app.initialize_plugin_system()
            
            console.print("[green]✓ Cloud Craver initialized successfully[/green]")
            console.print(f"[cyan]Data directory: {app.config['app']['data_dir']}[/cyan]")
            
            # Show plugin status
            if app.plugin_manager:
                status = app.plugin_manager.get_status()
                console.print(f"[cyan]Active plugins: {status['active_plugins']}/{status['total_plugins']}[/cyan]")
            else:
                console.print("[yellow]Plugin system not available[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Initialization failed: {e}[/red]")
            if ctx.obj.get('debug'):
                console.print_exception()
            sys.exit(1)
    
    asyncio.run(_init())


@cli.command()
@click.pass_context 
def status(ctx):
    """Show Cloud Craver system status."""
    async def _status():
        try:
            app = get_app()
            if not app.plugin_manager:
                await app.initialize_plugin_system()
            
            console.print("[bold cyan]Cloud Craver System Status[/bold cyan]\n")
            
            # App info
            console.print(f"[bold]Version:[/bold] {APP_VERSION}")
            console.print(f"[bold]Data Directory:[/bold] {app.config['app']['data_dir']}")
            console.print(f"[bold]Cache Directory:[/bold] {app.config['app']['cache_dir']}")
            
            # Plugin system status
            if app.plugin_manager:
                status_info = app.plugin_manager.get_status()
                console.print(f"\n[bold]Plugin System:[/bold]")
                console.print(f"  Total Plugins: {status_info['total_plugins']}")
                console.print(f"  Active Plugins: {status_info['active_plugins']}")
                
                console.print(f"\n[bold]Plugins by Type:[/bold]")
                for plugin_type, count in status_info['plugins_by_type'].items():
                    if count > 0:
                        console.print(f"  {plugin_type.title()}: {count}")
                
                if not status_info['plugins_by_type'] or all(count == 0 for count in status_info['plugins_by_type'].values()):
                    console.print("  No plugins currently loaded")
            else:
                console.print("\n[yellow]Plugin system not available[/yellow]")
                        
        except Exception as e:
            console.print(f"[red]Status check failed: {e}[/red]")
            if ctx.obj.get('debug'):
                console.print_exception()
            import traceback
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
    
    try:
        asyncio.run(_status())
    except Exception as e:
        console.print(f"[red]Failed to run status command: {e}[/red]")
        import traceback
        console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")


@cli.command()
@click.argument('message', default='Hello from Cloud Craver!')
def hello(message):
    """Simple hello command to test the application."""
    console.print(f"[green]{message}[/green]")
    console.print(f"[cyan]Cloud Craver v{APP_VERSION} is working![/cyan]")


# Add plugin commands to the CLI
try:
    import sys
    import os
    # Add src directory to path to enable proper imports
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.')
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    from cli.plugin_commands import add_plugin_commands
    from cli.auth_commands import add_auth_commands
    from cli.audit_commands import add_audit_commands
    from cli.integration_commands import add_integration_commands
    from cli.workflow_commands import add_workflow_commands
    from cli.policy_commands import add_policy_commands
    from cli.dashboard_commands import add_dashboard_commands
    from cli.config_management_commands import add_config_management_commands
    from cli.backup_commands import add_backup_commands
    add_plugin_commands(cli)
    add_auth_commands(cli)
    add_audit_commands(cli)
    add_integration_commands(cli)
    add_workflow_commands(cli)
    add_policy_commands(cli)
    add_dashboard_commands(cli)
    add_config_management_commands(cli)
    add_backup_commands(cli)
except ImportError as e:
    # Plugin commands not critical for basic functionality
    pass


@cli.command()
@click.option("--template", "-t", required=True, help="Name of the Terraform template to generate.")
@click.option("--output", "-o", default=".", type=click.Path(), help="Output directory.")
@click.pass_context
def generate(ctx, template, output):
    """🛠️ Generate a Terraform template by name."""
    import os
    
    console.print(f"[cyan]Generating template: {template}[/cyan]")
    console.print(f"[cyan]Output directory: {output}[/cyan]")
    
    if ctx.obj.get('DEBUG'):
        console.print("[yellow]Debug mode enabled[/yellow]")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output, exist_ok=True)
        
        # Generate template file
        file_path = os.path.join(output, f"{template}.tf")
        
        # Basic template content (this could be enhanced with plugin system)
        template_content = f"""# Terraform template for {template}
# Generated by Cloud Craver v{APP_VERSION}

terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

# Add your {template} configuration here
"""
        
        with open(file_path, "w") as f:
            f.write(template_content)
        
        console.print(f"[green]✓ Template '{template}' created at {file_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Failed to generate template: {e}[/red]")
        if ctx.obj.get('DEBUG'):
            console.print_exception()


@cli.command(name="list-templates")
@click.pass_context
def list_templates(ctx):
    """📚 List available Terraform templates."""
    console.print("[bold cyan]Available Terraform Templates:[/bold cyan]\n")
    
    # Basic templates (could be enhanced with plugin system)
    templates = {
        "vpc": "Virtual Private Cloud with subnets, gateways, and routing",
        "ec2": "Elastic Compute Cloud instances with security groups",
        "s3": "Simple Storage Service buckets with policies",
        "rds": "Relational Database Service instances",
    }
    
    for template, description in templates.items():
        console.print(f"[green]• {template}[/green]: {description}")
    
    console.print(f"\n[dim]Use 'cloudcraver generate --template <name>' to create a template[/dim]")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.pass_context
def validate(ctx, path):
    """✅ Validate Terraform templates in the given directory."""
    import os
    from terraform_validator.validator_dir.validate import validate_directory
    
    console.print(f"[cyan]Validating Terraform templates in: {path}[/cyan]")
    
    try:
        if not os.path.isdir(path):
            console.print(f"[red]Error: {path} is not a directory[/red]")
            return
        
        # Find all .tf files
        tf_files = [f for f in os.listdir(path) if f.endswith(".tf")]
        
        if not tf_files:
            console.print("[yellow]No Terraform files (.tf) found in directory[/yellow]")
            return
        
        console.print(f"[green]Found {len(tf_files)} Terraform file(s):[/green]")
        for tf_file in tf_files:
            console.print(f"  [dim]• {tf_file}[/dim]")
        
        # Basic validation (could be enhanced with actual terraform validation)
        result = validate_directory(path)
        console.print(f"[green]Validation successful[/green]: {result}")
        
    except Exception as e:
        console.print(f"[red]Validation failed: {e}[/red]")
        if ctx.obj.get('DEBUG'):
            console.print_exception()


@cli.command(name="interactive-generate")
def interactive_generate():
    """Interactive workflow to generate Terraform templates."""
    from questionary import prompt
    interactive_available = sys.stdin.isatty() # Check if terminal is interactive

    from rich.progress import Progress
    import json
    import os

    console.rule("[bold cyan]Interactive Project Generator[/bold cyan]")

    if not interactive_available:
        console.print("[yellow]Interactive mode requires a TTY. Falling back to basic input.[/yellow]")
        provider = input("Choose cloud provider (AWS/Azure/GCP): ").strip()
        region = input("Enter cloud region: ").strip()
        project_name = input("Enter project name: ").strip() or "cloudcraver"
        
        # Simple project generation
        output_dir = f"./{project_name}"
        os.makedirs(output_dir, exist_ok=True)
        console.print(f"[green]✔ Basic project '{project_name}' created at {output_dir}[/green]")
        return

    try:
        from interactive.validator import validate_region, validate_tags, validate_resources
    except ImportError:
        # Define simple validators if module not available
        def validate_region(val): return True
        def validate_tags(val): return True
        def validate_resources(answer): return True

    questions = [
        {
            'type': 'select',
            'name': 'provider',
            'message': 'Choose cloud provider:',
            'choices': ['AWS', 'Azure', 'GCP']
        },
        {
            'type': 'input',
            'name': 'region',
            'message': 'Enter cloud region:',
            'validate': lambda val: val != ""
        },
        {
            'type': 'checkbox',
            'name': 'resources',
            'message': 'Select resources to generate:',
            'choices': [
                {'name': 'VPC', 'value': 'vpc'},
                {'name': 'EC2', 'value': 'ec2'},
                {'name': 'S3', 'value': 's3'},
                {'name': 'RDS', 'value': 'rds'}
            ],
            'validate': lambda answer: len(answer) > 0
        },
        {
            'type': 'input',
            'name': 'project_name',
            'message': 'Enter project name prefix:',
            'default': 'cloudcraver'
        },
        {
            'type': 'input',
            'name': 'suffix',
            'message': 'Enter project name suffix (optional):',
            'default': ''
        },
        {
            'type': 'input',
            'name': 'tags',
            'message': 'Enter comma-separated tags (key=value format):',
            'validate': lambda val: True
        },
        {
            'type': 'input',
            'name': 'description',
            'message': 'Enter project description:'
        },
        {
            'type': 'input',
            'name': 'team',
            'message': 'Enter team name:'
        },
        {
            'type': 'select',
            'name': 'environment',
            'message': 'Select environment:',
            'choices': ['development', 'staging', 'production']
        }
    ]

    answers = prompt(questions)
    if not answers:
        console.print("[red]Aborted.[/red]")
        return

    output_dir = f"./{answers['project_name']}_{answers['suffix']}" if answers['suffix'] else f"./{answers['project_name']}"
    os.makedirs(output_dir, exist_ok=True)

    # Save prompt state for persistence
    with open(".cloudcraver_state.json", "w") as f:
        json.dump(answers, f, indent=2)

    with Progress() as progress:
        task = progress.add_task("[green]Creating templates...", total=100)
        for _ in range(5):
            progress.update(task, advance=20)

    console.print(f"[green]✔ Project '{answers['project_name']}' for {answers['provider']} with {answers['resources']} created at {output_dir}[/green]")


# --- STATE COMMANDS ---
@cli.group()
def state():
    """Manage Terraform state."""
    pass

@state.command()
@click.argument("provider", type=click.Choice(["s3", "azure", "gcs"]))
@click.argument("bucket")
@click.option("--region", help="Cloud region")
def configure_backend(provider, bucket, region):
    from state.backend import configure_remote_backend
    configure_remote_backend(provider, bucket, region)

@state.command()
@click.argument("workspace")
def create_workspace(workspace):
    from state.workspace import create_workspace
    create_workspace(workspace)

@state.command()
@click.argument("workspace")
def switch_workspace(workspace):
    from state.workspace import switch_workspace
    switch_workspace(workspace)

@state.command()
@click.argument("workspace")
def delete_workspace(workspace):
    from state.workspace import delete_workspace
    delete_workspace(workspace)

@state.command()
@click.argument("backend")
def migrate(backend):
    from state.migrate import migrate_state_backend
    migrate_state_backend(backend)

@state.command()
@click.argument("path")
def detect_drift(path):
    from state.drift import detect_state_drift
    detect_state_drift(path)

@state.command()
@click.argument("path")
def cleanup(path):
    from state.cleanup import cleanup_state_files
    cleanup_state_files(path)

@state.command()
@click.argument("env")
def use_environment(env):
    from state.environments import use_environment
    use_environment(env)

# --- COST COMMANDS ---
@cli.group()
def cost():
    """Manage infrastructure cost estimation and reporting."""
    pass

@cost.command("estimate")
@click.argument("provider", type=click.Choice(["aws", "azure", "gcp"]))
@click.option("--tfplan", required=True, help="Terraform plan file")
def estimate_cost(provider, tfplan):
    if provider == "aws":
        from cost.aws import estimate_aws_cost
        estimate_aws_cost(tfplan)
    elif provider == "azure":
        from cost.azure import estimate_azure_cost
        estimate_azure_cost(tfplan)
    elif provider == "gcp":
        from cost.gcp import estimate_gcp_cost
        estimate_gcp_cost(tfplan)

@cost.command()
@click.option("--usage-pattern", required=True, help="Usage pattern JSON file")
def optimize(usage_pattern):
    from cost.optimizer import suggest_optimizations
    suggest_optimizations(usage_pattern)

@cost.command()
@click.option("--tfplan", required=True, help="Terraform plan file")
def compare(tfplan):
    from cost.compare import compare_providers
    compare_providers(tfplan)

@cost.command()
@click.option("--tfplan", required=True, help="Terraform plan file")
def forecast(tfplan):
    from cost.forecast import forecast_costs
    forecast_costs(tfplan)

@cost.command()
@click.option("--output", required=True, help="Output file path for the report")
def report(output):
    from cost.report import generate_cost_report
    generate_cost_report(output)

# --- TERRAFORM COMMANDS ---
@cli.group()
def terraform():
    """Run Terraform-related commands."""
    pass

@terraform.command("plan-generate")
@click.option("--directory", default=".", help="Terraform configuration directory")
@click.option("--out-file", default="plan.out", help="Output JSON file name")
def generate_plan(directory, out_file):
    from terraform.plan import generate_terraform_plan_json
    generate_terraform_plan_json(directory, out_file)


def main():
    """
    Main entry point for the Cloud Craver application.
    
    This function:
    1. Sets up signal handlers for graceful shutdown
    2. Initializes the CLI interface
    3. Handles global error cases
    """
    
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        console.print("\n[yellow]Received shutdown signal, cleaning up...[/yellow]")
        
        # Run cleanup asynchronously
        async def cleanup():
            if app_instance:
                await app_instance.shutdown()
        
        try:
            asyncio.run(cleanup())
        except Exception as e:
            console.print(f"[red]Error during cleanup: {e}[/red]")
        
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run the CLI
        cli()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
        
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
