# Cloud Craver

Cloud Craver is a command-line tool designed to simplify cloud resource management and deployment. It provides a unified interface for interacting with various cloud providers and services, offering features like cost optimization, security scanning, and automated workflows.

## Features

*   **Multi-Cloud Support:** Manage resources across different cloud providers.
*   **Cost Management:** Analyze and optimize your cloud spending.
*   **Security & Compliance:** Scan for vulnerabilities and enforce security policies.
*   **IaC Automation:** Automate infrastructure provisioning using Terraform.
*   **Extensible Plugin System:** Extend functionality with custom plugins.
*   **Interactive Dashboard:** Visualize your cloud environment and resource usage.

## Requirements

*   Python 3.8+
*   Terraform
*   The dependencies listed in `requirements.txt`:
    ```
    ansible
    azure-identity
    azure-keyvault-secrets
    azure-mgmt-compute
    azure-mgmt-network
    azure-mgmt-resource
    azure-mgmt-sql
    azure-mgmt-storage
    boto3
    click
    google-api-python-client
    jira
    kubernetes
    msal
    openai
    pandas
    pyfiglet
    PyGithub
    python-hcl2
    pytz
    PyYAML
    requests
    rich
    scikit-learn
    semver
    servicenow-api
    tabulate
    termcolor
    tqdm
    ```

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/OSoC-25-Cloud-Craver.git
    cd OSoC-25-Cloud-Craver
    ```
2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

The main entry point for the application is `cloudcraver.py`. You can run it with the following command:

```bash
python cloudcraver.py [COMMAND] [OPTIONS]
```

## Commands

Here is a list of the available commands and their descriptions:

### Core Commands

*   `init`: Initialize Cloud Craver and the plugin system.
*   `status`: Show the Cloud Craver system status.
*   `hello [MESSAGE]`: A simple command to test the application.
*   `generate`: Generate a Terraform template by name.
    *   `--template, -t`: Name of the Terraform template to generate (required).
    *   `--output, -o`: Output directory (default: current directory).
*   `list-templates`: List available Terraform templates.
*   `validate <PATH>`: Validate Terraform templates in the given directory.
*   `interactive-generate`: An interactive workflow to generate Terraform templates.

### State Management (`state`)

*   `state configure-backend <PROVIDER> <BUCKET>`: Configure the Terraform backend.
    *   `--region`: Cloud region.
*   `state create-workspace <WORKSPACE>`: Create a new Terraform workspace.
*   `state switch-workspace <WORKSPACE>`: Switch to a different Terraform workspace.
*   `state delete-workspace <WORKSPACE>`: Delete a Terraform workspace.
*   `state migrate <BACKEND>`: Migrate the Terraform state to a different backend.
*   `state detect-drift <PATH>`: Detect drift in the Terraform state.
*   `state cleanup <PATH>`: Clean up Terraform state files.
*   `state use-environment <ENV>`: Use a specific environment's state configuration.

### Cost Management (`cost`)

*   `cost estimate <PROVIDER>`: Estimate the cost of a Terraform plan.
    *   `--tfplan`: Path to the Terraform plan file (required).
*   `cost optimize`: Suggest cost optimizations based on usage patterns.
    *   `--usage-pattern`: Path to the usage pattern JSON file (required).
*   `cost compare`: Compare costs across different cloud providers.
    *   `--tfplan`: Path to the Terraform plan file (required).
*   `cost forecast`: Forecast future costs based on a Terraform plan.
    *   `--tfplan`: Path to the Terraform plan file (required).
*   `cost report`: Generate a cost report.
    *   `--output`: Output file path for the report (required).

### Terraform Commands (`terraform`)

*   `terraform plan-generate`: Generate a Terraform plan in JSON format.
    *   `--directory`: Terraform configuration directory (default: current directory).
    *   `--out-file`: Output JSON file name (default: `plan.out`).

### Other Commands

*   `audit`: Commands for auditing your cloud environment.
*   `auth`: Commands for managing authentication and authorization.
*   `backup`: Commands for managing backups.
*   `config`: Commands for managing configuration.
*   `dashboard`: Commands for launching the dashboard.
*   `integration`: Commands for managing integrations with third-party services.
*   `plugin`: Commands for managing plugins.
*   `policy`: Commands for managing policies.
*   `workflow`: Commands for managing workflows.

To get more information about a specific command, you can use the `--help` flag:

```bash
python cloudcraver.py [COMMAND] --help
```