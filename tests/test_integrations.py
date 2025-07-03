
import unittest
from unittest.mock import patch, MagicMock

from src.integrations import jira_client, servicenow_client


class TestIntegrations(unittest.TestCase):
    @patch("src.integrations.jira_client.JIRA")
    def test_jira_ticket_creation(self, mock_jira):
        mock_jira_instance = MagicMock()
        mock_jira.return_value = mock_jira_instance
        mock_jira_instance.create_issue.return_value.key = "TEST-123"
        mock_jira_instance.create_issue.return_value.permalink.return_value = (
            "https://jira.example.com/browse/TEST-123"
        )

        client = jira_client.JiraClient(
            server="https://jira.example.com",
            username="user",
            api_token="token",
        )
        ticket = client.create_ticket(
            project_key="TEST",
            summary="Test ticket",
            description="This is a test ticket.",
        )
        self.assertEqual(ticket["key"], "TEST-123")

    @patch("src.integrations.servicenow_client.requests.Session")
    def test_servicenow_change_request_creation(self, mock_session):
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"number": "CHG12345", "sys_id": "12345"}
        }
        mock_session_instance.post.return_value = mock_response

        client = servicenow_client.ServiceNowClient(
            instance="dev12345",
            username="user",
            password="password",
        )
        change_request = client.create_change_request(
            short_description="Test change request",
            description="This is a test change request.",
            assignment_group="Test Group",
        )
        self.assertEqual(change_request["number"], "CHG12345")


if __name__ == "__main__":
    unittest.main()
