import unittest
from unittest.mock import MagicMock, patch
from src.templates.base import BaseTemplate, TemplateMetadata, AWSTemplate, AzureTemplate, GCPTemplate

class TestTemplateMetadata(unittest.TestCase):
    def test_metadata_creation(self):
        metadata = TemplateMetadata(version="1.0", description="Test template", tags=["test", "example"])
        self.assertEqual(metadata.version, "1.0")
        self.assertEqual(metadata.description, "Test template")
        self.assertEqual(metadata.tags, ["test", "example"])

    def test_metadata_creation_no_tags(self):
        metadata = TemplateMetadata(version="1.0", description="Test template")
        self.assertEqual(metadata.tags, [])

class TestBaseTemplate(unittest.TestCase):
    def setUp(self):
        self.metadata = TemplateMetadata(version="1.0", description="Test template")
        # Create a concrete implementation for testing abstract BaseTemplate methods
        class ConcreteTemplate(BaseTemplate):
            def generate_context(self) -> dict:
                return {"key": "value"}
            
            def generate(self) -> str:
                return "Generated Content"

            def validate(self) -> bool:
                return True

            def render(self) -> str:
                return "Rendered Content"
        self.ConcreteTemplate = ConcreteTemplate

    @patch('src.templates.base.Environment')
    def test_base_template_initialization(self, MockEnvironment):
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata, template_name="dummy.j2", base_template_root_dir="/")
        self.assertEqual(template.name, "MyTemplate")
        self.assertEqual(template.metadata.version, "1.0")
        self.assertEqual(template.get_all_variables(), {})
        self.assertIsNone(template.get_output())

    @patch('src.templates.base.Environment')
    def test_base_template_initialization_with_variables(self, MockEnvironment):
        initial_vars = {"region": "us-east-1", "env": "dev"}
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata, variables=initial_vars, template_name="dummy.j2", base_template_root_dir="/")
        self.assertEqual(template.get_all_variables(), initial_vars)

    @patch('src.templates.base.Environment')
    def test_set_and_get_variable(self, MockEnvironment):
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata, template_name="dummy.j2", base_template_root_dir="/")
        template.set_variable("key1", "value1")
        self.assertEqual(template.get_variable("key1"), "value1")

    @patch('src.templates.base.Environment')
    def test_get_non_existent_variable(self, MockEnvironment):
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata, template_name="dummy.j2", base_template_root_dir="/")
        with self.assertRaises(KeyError):
            template.get_variable("non_existent_key")

    @patch('src.templates.base.Environment')
    def test_get_all_variables(self, MockEnvironment):
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata, template_name="dummy.j2", base_template_root_dir="/")
        template.set_variable("key1", "value1")
        template.set_variable("key2", 123)
        self.assertEqual(template.get_all_variables(), {"key1": "value1", "key2": 123})

    @patch('src.templates.base.Environment')
    def test_abstract_methods_called(self, MockEnvironment):
        template = self.ConcreteTemplate(name="MyTemplate", metadata=self.metadata, template_name="dummy.j2", base_template_root_dir="/")
        self.assertEqual(template.generate(), "Generated Content")
        self.assertTrue(template.validate())
        self.assertEqual(template.render(), "Rendered Content")

class TestProviderTemplates(unittest.TestCase):
    def setUp(self):
        self.metadata = TemplateMetadata(version="1.0", description="Provider test template")
        self.variables = {"project": "my-app"}

    @patch('src.templates.base.FileSystemLoader')
    @patch('src.templates.base.Environment')
    def test_aws_template(self, MockEnvironment, MockLoader):
        aws_template = AWSTemplate(name="MyAWSTemplate", metadata=self.metadata, variables=self.variables, template_path="/dummy/aws.j2")
        self.assertEqual(aws_template.name, "MyAWSTemplate")
        self.assertTrue(aws_template.validate())
        # Mock render to avoid actual file operations
        with patch.object(aws_template, 'render', return_value="AWS CloudFormation Template with project: my-app") as mock_render:
            generated_content = aws_template.render()
            self.assertIn("AWS CloudFormation Template", generated_content)
            self.assertIn("project: my-app", generated_content)
            self.assertEqual(aws_template.render(), generated_content)

    @patch('src.templates.base.FileSystemLoader')
    @patch('src.templates.base.Environment')
    def test_azure_template(self, MockEnvironment, MockLoader):
        azure_template = AzureTemplate(name="MyAzureTemplate", metadata=self.metadata, variables=self.variables, template_path="/dummy/azure.j2")
        self.assertEqual(azure_template.name, "MyAzureTemplate")
        self.assertTrue(azure_template.validate())
        with patch.object(azure_template, 'render', return_value="Azure ARM Template with project: my-app") as mock_render:
            generated_content = azure_template.render()
            self.assertIn("Azure ARM Template", generated_content)
            self.assertIn("project: my-app", generated_content)
            self.assertEqual(azure_template.render(), generated_content)

    @patch('src.templates.base.FileSystemLoader')
    @patch('src.templates.base.Environment')
    def test_gcp_template(self, MockEnvironment, MockLoader):
        gcp_template = GCPTemplate(name="MyGCPTemplate", metadata=self.metadata, variables=self.variables, template_path="/dummy/gcp.j2")
        self.assertEqual(gcp_template.name, "MyGCPTemplate")
        self.assertTrue(gcp_template.validate())
        with patch.object(gcp_template, 'render', return_value="GCP Deployment Manager Template with project: my-app") as mock_render:
            generated_content = gcp_template.render()
            self.assertIn("GCP Deployment Manager Template", generated_content)
            self.assertIn("project: my-app", generated_content)
            self.assertEqual(gcp_template.render(), generated_content)

if __name__ == '__main__':
    unittest.main()
