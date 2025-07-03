import abc
import os
from typing import Any, Dict, List, Optional
from jinja2 import Environment, FileSystemLoader
import networkx as nx

class TemplateMetadata:
    """
    Represents metadata for a cloud template.

    Attributes:
        version (str): The version of the template.
        description (str): A brief description of the template.
        tags (List[str]): A list of tags associated with the template.
    """
    def __init__(self, version: str, description: str, tags: Optional[List[str]] = None):
        self.version = version
        self.description = description
        self.tags = tags if tags is not None else []

class BaseTemplate(abc.ABC):
    """
    Abstract base class for cloud template management.

    Defines the interface for template generation, validation, and rendering,
    along with methods for variable handling and output management.
    """
    def __init__(self, name: str, metadata: TemplateMetadata, template_name: str, base_template_root_dir: str, variables: Optional[Dict[str, Any]] = None):
        """
        Initializes the BaseTemplate with a name, metadata, template name, base template root directory, and optional variables.

        Args:
            name (str): The name of the template.
            metadata (TemplateMetadata): Metadata for the template.
            template_name (str): The name of the template file relative to the base_template_root_dir.
            base_template_root_dir (str): The root directory where all templates are located.
            variables (Optional[Dict[str, Any]]): Initial template variables.
        """
        self.name = name
        self.metadata = metadata
        self.template_name = template_name
        self._variables = variables if variables is not None else {}
        self._output = None

        # Set up Jinja2 environment with caching
        self.env = Environment(
            loader=FileSystemLoader(base_template_root_dir),
            cache_size=500,  # Cache up to 500 compiled templates
            auto_reload=True # Reload templates when they change (useful during development)
        )

        # Add custom filters
        self.env.filters['to_upper'] = lambda s: s.upper()

        self.template = self.env.get_template(template_name)

    def resolve_dependencies(self, resources: Dict[str, List[str]]) -> List[str]:
        """
        Resolves the order of resources based on their dependencies using a directed graph.

        Args:
            resources (Dict[str, List[str]]): A dictionary where keys are resource names
                                               and values are lists of their dependencies.

        Returns:
            List[str]: A topologically sorted list of resource names.

        Raises:
            ValueError: If a circular dependency is detected.
        """
        graph = nx.DiGraph()
        for resource, dependencies in resources.items():
            graph.add_node(resource)
            for dep in dependencies:
                graph.add_edge(dep, resource)

        try:
            return list(nx.topological_sort(graph))
        except nx.NetworkXNoCycle:
            raise ValueError("Circular dependency detected in resources.")

    @abc.abstractmethod
    def generate_context(self) -> Dict[str, Any]:
        """
        Generates the context dictionary for Jinja2 rendering.

        This method should be implemented by subclasses to provide
        provider-specific data and logic to the template.

        Returns:
            Dict[str, Any]: The context dictionary for Jinja2.
        """
        pass

    def render(self) -> str:
        """
        Renders the template using Jinja2, applying variables and context.

        Returns:
            str: The rendered template content.
        """
        context = self.generate_context()
        context.update(self._variables)  # Allow variables to override context
        self._output = self.template.render(context)
        return self._output

    @abc.abstractmethod
    def validate(self) -> bool:
        """
        Validates the generated template content against provider-specific rules.

        Returns:
            bool: True if the template is valid, False otherwise.
        """
        pass

    def set_variable(self, key: str, value: Any) -> None:
        """
        Sets a single variable for the template.

        Args:
            key (str): The name of the variable.
            value (Any): The value of the variable.
        """
        self._variables[key] = value

    def get_variable(self, key: str) -> Any:
        """
        Retrieves the value of a template variable.

        Args:
            key (str): The name of the variable.

        Returns:
            Any: The value of the variable.

        Raises:
            KeyError: If the variable is not found.
        """
        if key not in self._variables:
            raise KeyError(f"Variable '{key}' not found.")
        return self._variables[key]

    def get_all_variables(self) -> Dict[str, Any]:
        """
        Retrieves all variables set for the template.

        Returns:
            Dict[str, Any]: A dictionary of all template variables.
        """
        return self._variables

    def get_output(self) -> Optional[str]:
        """
        Retrieves the last generated or rendered output of the template.

        Returns:
            Optional[str]: The template output, or None if not yet generated/rendered.
        """
        return self._output


class AWSTemplate(BaseTemplate):
    """
    AWS-specific implementation of BaseTemplate for CloudFormation templates.
    """
    def __init__(self, name: str, metadata: TemplateMetadata, template_path: str, variables: Optional[Dict[str, Any]] = None):
        template_name = os.path.basename(template_path)
        base_template_root_dir = os.path.dirname(template_path)
        super().__init__(name, metadata, template_name, base_template_root_dir, variables)

    def generate_context(self) -> Dict[str, Any]:
        # Define resource dependencies for this template
        resources = {
            f"aws_s3_bucket.{self._variables.get('bucket_name', f'{self.name}-s3-bucket')}": [],
            f"aws_dynamodb_table.{self._variables.get('dynamodb_table_name', f'{self.name}-dynamodb-table')}": [
                f"aws_s3_bucket.{self._variables.get('bucket_name', f'{self.name}-s3-bucket')}"
            ] if self._variables.get("s3_bucket_dependency", False) else []
        }

        # Resolve dependencies
        try:
            resolved_order = self.resolve_dependencies(resources)
        except ValueError as e:
            print(f"Error resolving dependencies: {e}")
            resolved_order = [] # Handle circular dependency or other errors

        # Context for AWS Terraform templates
        return {
            "bucket_name": self._variables.get("bucket_name", f"{self.name}-s3-bucket"),
            "environment": self._variables.get("environment", "development"),
            "create_s3": self._variables.get("create_s3", True), # Default to True for existing templates
            "create_dynamodb": self._variables.get("create_dynamodb", False),
            "dynamodb_table_name": self._variables.get("dynamodb_table_name", f"{self.name}-dynamodb-table"),
            "s3_bucket_dependency": self._variables.get("s3_bucket_dependency", False),
            "resolved_resource_order": resolved_order, # Pass resolved order to template
            "include_module": self._variables.get("include_module", False),
            "module_name": self._variables.get("module_name", "example_module"),
            "module_source": self._variables.get("module_source", "terraform-aws-modules/vpc/aws"),
            "module_version": self._variables.get("module_version", "3.18.0"),
            "module_inputs": self._variables.get("module_inputs", {})
        }

    def validate(self) -> bool:
        # Placeholder for AWS CloudFormation validation logic
        print(f"Validating AWS template {self.name}...")
        return True  # Simulate successful validation


class AzureTemplate(BaseTemplate):
    """
    Azure-specific implementation of BaseTemplate for ARM templates.
    """
    def __init__(self, name: str, metadata: TemplateMetadata, template_path: str, variables: Optional[Dict[str, Any]] = None):
        template_name = os.path.basename(template_path)
        base_template_root_dir = os.path.dirname(template_path)
        super().__init__(name, metadata, template_name, base_template_root_dir, variables)

    def generate_context(self) -> Dict[str, Any]:
        # Example context for Azure. This will be expanded later.
        return {
            "template_name": self.name,
            "description": self.metadata.description,
            "variables": self._variables
        }

    def validate(self) -> bool:
        # Placeholder for Azure ARM validation logic
        print(f"Validating Azure template {self.name}...")
        return True  # Simulate successful validation


class GCPTemplate(BaseTemplate):
    """
    GCP-specific implementation of BaseTemplate for Deployment Manager templates.
    """
    def __init__(self, name: str, metadata: TemplateMetadata, template_path: str, variables: Optional[Dict[str, Any]] = None):
        template_name = os.path.basename(template_path)
        base_template_root_dir = os.path.dirname(template_path)
        super().__init__(name, metadata, template_name, base_template_root_dir, variables)

    def generate_context(self) -> Dict[str, Any]:
        # Example context for GCP. This will be expanded later.
        return {
            "template_name": self.name,
            "description": self.metadata.description,
            "variables": self._variables
        }

    def validate(self) -> bool:
        # Placeholder for GCP Deployment Manager validation logic
        print(f"Validating GCP template {self.name}...")
        return True  # Simulate successful validation
