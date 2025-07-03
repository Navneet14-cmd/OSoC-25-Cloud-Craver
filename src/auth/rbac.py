
import json
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# --- Role and Permission Definitions ---

class Role:
    """
    Represents a role with a set of permissions.
    """
    def __init__(self, name: str, permissions: Optional[Set[str]] = None):
        self.name = name
        self.permissions = permissions or set()

    def has_permission(self, permission: str) -> bool:
        """Check if the role has a specific permission."""
        return permission in self.permissions

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the role to a dictionary."""
        return {"name": self.name, "permissions": sorted(list(self.permissions))}


class Permission:
    """
    Defines constants for common permissions.
    """
    # Infrastructure Actions
    CREATE_INFRA = "infrastructure:create"
    READ_INFRA = "infrastructure:read"
    UPDATE_INFRA = "infrastructure:update"
    DELETE_INFRA = "infrastructure:delete"

    # Approval Workflows
    APPROVE_CHANGES = "approvals:approve"
    REJECT_CHANGES = "approvals:reject"

    # Policy Management
    CREATE_POLICY = "policy:create"
    MANAGE_POLICY = "policy:manage"

    # User and Role Management
    MANAGE_USERS = "users:manage"
    MANAGE_ROLES = "roles:manage"

    # System Administration
    VIEW_AUDIT_LOGS = "system:view_audit_logs"
    ADMIN_ACCESS = "system:admin"


# --- Default Roles ---

DEFAULT_ROLES = {
    "Admin": Role(
        "Admin",
        {
            Permission.ADMIN_ACCESS,
            Permission.MANAGE_USERS,
            Permission.MANAGE_ROLES,
            Permission.VIEW_AUDIT_LOGS,
        },
    ),
    "Developer": Role(
        "Developer",
        {
            Permission.CREATE_INFRA,
            Permission.READ_INFRA,
            Permission.UPDATE_INFRA,
        },
    ),
    "Auditor": Role("Auditor", {Permission.VIEW_AUDIT_LOGS, Permission.READ_INFRA}),
    "Approver": Role("Approver", {Permission.APPROVE_CHANGES, Permission.REJECT_CHANGES}),
}


# --- RBAC Engine ---

class RBACEngine:
    """
    Manages roles, user-role assignments, and permission checks.
    """
    def __init__(self, roles: Optional[Dict[str, Role]] = None):
        self.roles = roles or DEFAULT_ROLES
        self.user_roles: Dict[str, Set[str]] = {}  # Maps user_id to a set of role names

    def add_role(self, role: Role):
        """Add a new role to the engine."""
        if role.name in self.roles:
            raise ValueError(f"Role '{role.name}' already exists.")
        self.roles[role.name] = role
        logger.info(f"Role '{role.name}' added.")

    def assign_role_to_user(self, user_id: str, role_name: str):
        """Assign a role to a user."""
        if role_name not in self.roles:
            raise ValueError(f"Role '{role_name}' does not exist.")
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        self.user_roles[user_id].add(role_name)
        logger.info(f"Assigned role '{role_name}' to user '{user_id}'.")

    def remove_role_from_user(self, user_id: str, role_name: str):
        """Remove a role from a user."""
        if user_id in self.user_roles and role_name in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role_name)
            logger.info(f"Removed role '{role_name}' from user '{user_id}'.")

    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a given user."""
        user_role_names = self.user_roles.get(user_id, set())
        permissions = set()
        for role_name in user_role_names:
            role = self.roles.get(role_name)
            if role:
                permissions.update(role.permissions)
        return permissions

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission."""
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions

    def save_state(self, file_path: str):
        """Save the current RBAC state (user-role assignments) to a file."""
        state = {
            "user_roles": {user_id: list(roles) for user_id, roles in self.user_roles.items()}
        }
        with open(file_path, "w") as f:
            json.dump(state, f, indent=2)
        logger.info(f"RBAC state saved to {file_path}")

    def load_state(self, file_path: str):
        """Load RBAC state from a file."""
        try:
            with open(file_path, "r") as f:
                state = json.load(f)
            self.user_roles = {
                user_id: set(roles) for user_id, roles in state.get("user_roles", {}).items()
            }
            logger.info(f"RBAC state loaded from {file_path}")
        except FileNotFoundError:
            logger.warning(f"RBAC state file not found at {file_path}. Starting with empty state.")
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to load RBAC state from {file_path}: {e}")


# --- Decorator for Permission Checks ---

def requires_permission(permission: str):
    """
    Decorator to protect a function by checking for a specific permission.
    
    Assumes the decorated function is a method of a class that has an `rbac_engine`
    and a `current_user_id` attribute.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, "rbac_engine") or not isinstance(getattr(self, "rbac_engine"), RBACEngine):
                raise TypeError("Decorated object must have an 'rbac_engine' attribute of type RBACEngine.")
            
            if not hasattr(self, "current_user_id") or not isinstance(getattr(self, "current_user_id"), str):
                raise TypeError("Decorated object must have a 'current_user_id' attribute of type str.")

            user_id = self.current_user_id
            if not self.rbac_engine.has_permission(user_id, permission):
                logger.warning(f"User '{user_id}' attempted to perform action '{func.__name__}' without permission '{permission}'.")
                raise PermissionError(f"You do not have the required permission: {permission}")
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
