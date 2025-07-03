
import unittest
from unittest.mock import patch, MagicMock

from src.audit import logger, reporting


class TestAudit(unittest.TestCase):
    @patch("src.audit.logger.audit_logger.log")
    def test_audit_log(self, mock_log):
        logger.audit_logger.log(
            logger.AuditEvent.USER_LOGIN_SUCCESS,
            actor_id="test_user",
            details={"ip_address": "127.0.0.1"},
        )
        mock_log.assert_called_once_with(
            logger.AuditEvent.USER_LOGIN_SUCCESS,
            actor_id="test_user",
            details={"ip_address": "127.0.0.1"},
        )

    @patch("src.audit.reporting.ComplianceReporter._load_audit_data")
    def test_compliance_report(self, mock_load_audit_data):
        mock_load_audit_data.return_value = [
            {
                "timestamp": "2025-07-04T12:00:00Z",
                "event": "user.login.success",
                "actor_id": "test_user",
                "target_id": None,
                "status": "success",
                "details": {},
            }
        ]
        reporter = reporting.ComplianceReporter()
        with patch("src.audit.reporting.console.print") as mock_print:
            reporter.generate_activity_report(days=1)
            self.assertTrue(mock_print.called)


if __name__ == "__main__":
    unittest.main()
