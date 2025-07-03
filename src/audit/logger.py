
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

# --- Audit Event Definitions ---

class AuditEvent(Enum):
    """
    Defines standardized audit event types.
    """
    # Authentication Events
    USER_LOGIN_SUCCESS = "user.login.success"
    USER_LOGIN_FAILURE = "user.login.failure"
    USER_LOGOUT = "user.logout"

    # RBAC Events
    ROLE_ASSIGNED = "rbac.role.assigned"
    ROLE_REMOVED = "rbac.role.removed"
    PERMISSION_DENIED = "rbac.permission.denied"

    # Infrastructure Events
    INFRA_CHANGE_REQUESTED = "infra.change.requested"
    INFRA_CHANGE_APPROVED = "infra.change.approved"
    INFRA_CHANGE_REJECTED = "infra.change.rejected"
    INFRA_APPLY_SUCCESS = "infra.apply.success"
    INFRA_APPLY_FAILURE = "infra.apply.failure"

    # Policy Events
    POLICY_EVALUATION = "policy.evaluation"

    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


# --- Audit Logger ---

class AuditLogger:
    """
    A centralized logger for creating structured audit trails.
    """
    def __init__(self, logger_name: str = "audit", log_file: Optional[str] = None):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Prevent audit logs from appearing in the main console

        # Remove existing handlers to avoid duplication
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Create a dedicated file handler for the audit log
        if log_file:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            # If no file is provided, log to a null handler to avoid errors
            self.logger.addHandler(logging.NullHandler())

    def log(
        self,
        event: AuditEvent,
        actor_id: str,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ):
        """
        Creates a structured audit log entry.

        Args:
            event: The type of event that occurred.
            actor_id: The ID of the user or system component performing the action.
            target_id: The ID of the resource being acted upon (e.g., user, VM).
            details: A dictionary of additional context-specific information.
            status: The outcome of the event (e.g., 'success', 'failure', 'pending').
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event.value,
            "actor_id": actor_id,
            "target_id": target_id,
            "status": status,
            "details": details or {},
        }
        self.logger.info(json.dumps(log_entry))


# --- Global Audit Logger Instance ---

# In a real application, you would configure the log file path from your main config.
# For this example, we'll use a default path.
AUDIT_LOG_FILE = "audit.log"
audit_logger = AuditLogger(log_file=AUDIT_LOG_FILE)


# --- Decorator for Auditing Function Calls ---

def auditable(event: AuditEvent, target_arg: Optional[str] = None):
    """
    Decorator to automatically log an audit event when a function is called.

    Assumes the decorated function is a method of a class that has a `current_user_id`
    attribute and that the global `audit_logger` is configured.

    Args:
        event: The audit event to log.
        target_arg: The name of the argument that holds the target ID.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(self, *args, **kwargs):
            # This assumes the user ID is stored in the instance
            actor_id = getattr(self, "current_user_id", "system")
            
            target_id = None
            if target_arg:
                if target_arg in kwargs:
                    target_id = kwargs[target_arg]
                else:
                    # Find the argument by position
                    try:
                        arg_index = func.__code__.co_varnames.index(target_arg) - 1
                        if arg_index < len(args):
                            target_id = args[arg_index]
                    except (ValueError, IndexError):
                        pass

            try:
                result = func(self, *args, **kwargs)
                audit_logger.log(event, actor_id=actor_id, target_id=target_id, status="success")
                return result
            except Exception as e:
                details = {"error": str(e), "type": type(e).__name__}
                audit_logger.log(event, actor_id=actor_id, target_id=target_id, status="failure", details=details)
                raise
        return wrapper
    return decorator
