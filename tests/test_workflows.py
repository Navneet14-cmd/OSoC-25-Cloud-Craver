
import unittest
from unittest.mock import MagicMock

from src.workflows import approval
from src.auth import rbac


class TestWorkflows(unittest.TestCase):
    def setUp(self):
        self.rbac_engine = rbac.RBACEngine()
        self.approval_workflow = approval.ApprovalWorkflow(self.rbac_engine)
        self.requester_id = "test_requester"
        self.approver_id = "test_approver"
        self.rbac_engine.assign_role_to_user(self.approver_id, "Approver")

    def test_approval_request_creation(self):
        request = approval.ApprovalRequest(
            requester_id=self.requester_id,
            change_summary="Test change",
            change_details={"key": "value"},
        )
        self.approval_workflow.create_request(request)
        self.assertIn(request.id, self.approval_workflow.requests)

    def test_approval_request_approval(self):
        request = approval.ApprovalRequest(
            requester_id=self.requester_id,
            change_summary="Test change",
            change_details={"key": "value"},
        )
        self.approval_workflow.create_request(request)
        self.approval_workflow.approve_request(request.id, self.approver_id)
        self.assertEqual(self.approval_workflow.requests[request.id].status, approval.ApprovalStatus.APPROVED)


if __name__ == "__main__":
    unittest.main()
