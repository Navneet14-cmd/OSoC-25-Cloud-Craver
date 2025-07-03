import os
import sys
import unittest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from templates.base import AWSTemplate, TemplateMetadata

class TestTemplateEngine(unittest.TestCase):

    def setUp(self):
        self.template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../terraform_templates/aws'))
        self.template_path = os.path.join(self.template_dir, 'simple.tf.j2')
        self.metadata = TemplateMetadata(
            version="1.0.0",
            description="A simple AWS S3 and optional DynamoDB template"
        )

    def test_aws_template_rendering_s3_only(self):
        template = AWSTemplate(
            name="test-s3-template",
            metadata=self.metadata,
            template_path=self.template_path,
            variables={
                "bucket_name": "my-unique-test-bucket",
                "environment": "testing",
                "create_dynamodb": False
            }
        )
        rendered_content = template.render()

        self.assertIn('resource "aws_s3_bucket" "MY-UNIQUE-TEST-BUCKET"', rendered_content)
        self.assertIn('bucket = "MY-UNIQUE-TEST-BUCKET"', rendered_content)
        self.assertIn('Environment = "testing"', rendered_content)
        self.assertNotIn('resource "aws_dynamodb_table"', rendered_content)

    def test_aws_template_rendering_s3_and_dynamodb(self):
        template = AWSTemplate(
            name="test-s3-dynamodb-template",
            metadata=self.metadata,
            template_path=self.template_path,
            variables={
                "bucket_name": "another-unique-bucket",
                "environment": "production",
                "create_dynamodb": True,
                "dynamodb_table_name": "my-test-dynamodb-table",
                "s3_bucket_dependency": True
            }
        )
        rendered_content = template.render()

        self.assertIn('resource "aws_s3_bucket" "ANOTHER-UNIQUE-BUCKET"', rendered_content)
        self.assertIn('bucket = "ANOTHER-UNIQUE-BUCKET"', rendered_content)
        self.assertIn('Environment = "production"', rendered_content)
        self.assertIn('resource "aws_dynamodb_table" "MY-TEST-DYNAMODB-TABLE"', rendered_content)
        self.assertIn('name         = "MY-TEST-DYNAMODB-TABLE"', rendered_content)
        self.assertIn('Environment = "production"', rendered_content)
        self.assertIn('depends_on = [aws_s3_bucket.ANOTHER-UNIQUE-BUCKET]', rendered_content)

    def test_aws_template_dependency_resolution(self):
        template = AWSTemplate(
            name="test-dependency-template",
            metadata=self.metadata,
            template_path=self.template_path,
            variables={
                "bucket_name": "dep-bucket",
                "create_dynamodb": True,
                "dynamodb_table_name": "dep-dynamodb",
                "s3_bucket_dependency": True
            }
        )
        # Access the resolved order from the context, not directly from the rendered content
        context = template.generate_context()
        resolved_order = context.get("resolved_resource_order")

        self.assertIsNotNone(resolved_order)
        self.assertIsInstance(resolved_order, list)
        self.assertIn('aws_s3_bucket.dep-bucket', resolved_order)
        self.assertIn('aws_dynamodb_table.dep-dynamodb', resolved_order)
        self.assertTrue(resolved_order.index('aws_s3_bucket.dep-bucket') < resolved_order.index('aws_dynamodb_table.dep-dynamodb'))

    def test_aws_template_rendering_with_module(self):
        template = AWSTemplate(
            name="test-module-template",
            metadata=self.metadata,
            template_path=self.template_path,
            variables={
                "bucket_name": "module-test-bucket",
                "environment": "development",
                "include_module": True,
                "module_name": "my_vpc",
                "module_source": "terraform-aws-modules/vpc/aws",
                "module_version": "3.18.0",
                "module_inputs": {
                    "name": "my-vpc",
                    "cidr_block": "10.0.0.0/16"
                }
            }
        )
        rendered_content = template.render()
        print(rendered_content)
        self.assertIn('module "MY_VPC" {', rendered_content)
        self.assertIn('source = "terraform-aws-modules/vpc/aws"', rendered_content)
        self.assertIn('version = "3.18.0"', rendered_content)
        self.assertIn('name = "my-vpc"\n\n  cidr_block = "10.0.0.0/16"', rendered_content)

if __name__ == '__main__':
    unittest.main()