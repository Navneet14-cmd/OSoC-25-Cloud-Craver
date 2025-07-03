
import unittest
from unittest.mock import patch, MagicMock

from src.pdp import engine


class TestPDP(unittest.TestCase):
    @patch("src.pdp.engine.OPAClient")
    def test_policy_evaluation(self, mock_opa_client):
        mock_opa_instance = MagicMock()
        mock_opa_client.return_value = mock_opa_instance
        mock_opa_instance.get_policy_decision.return_value = {"result": True}

        policy_engine = engine.PolicyEngine()
        result = policy_engine.evaluate_policy(
            policy_path="/v1/data/myapi/policy",
            input_data={"input": {"user": "test_user"}},
        )
        self.assertTrue(result["result"])


if __name__ == "__main__":
    unittest.main()
