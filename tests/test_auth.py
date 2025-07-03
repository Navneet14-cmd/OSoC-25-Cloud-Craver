
import unittest
from unittest.mock import patch, MagicMock

from src.auth import rbac
from src.auth import saml


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.rbac_engine = rbac.RBACEngine()
        self.user_id = "test_user"

    def test_role_creation(self):
        new_role = rbac.Role("test_role", {"test_permission"})
        self.rbac_engine.add_role(new_role)
        self.rbac_engine.assign_role_to_user(self.user_id, "test_role")
        self.assertTrue(self.rbac_engine.has_permission(self.user_id, "test_permission"))

    def test_permission_check(self):
        self.rbac_engine.assign_role_to_user(self.user_id, "Admin")
        self.assertTrue(self.rbac_engine.has_permission(self.user_id, rbac.Permission.ADMIN_ACCESS))
        self.assertFalse(self.rbac_engine.has_permission(self.user_id, "invalid_permission"))

    # @patch("src.auth.saml.perform_saml_login")
# def test_saml_login(self, mock_perform_saml_login):
#     mock_perform_saml_login.return_value = {
#         "name_id": "test_user",
#         "attributes": {"role": "Admin"},
#     }
#     user_data = saml.perform_saml_login({})
#     self.assertEqual(user_data["name_id"], "test_user")


if __name__ == "__main__":
    unittest.main()
