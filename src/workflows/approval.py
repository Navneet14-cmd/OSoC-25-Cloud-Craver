
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

from rich.console import Console
from rich.table import Table

from audit.logger import audit_logger, AuditEvent
from auth.rbac import Permission, RBACEngine

console = Console()


class ApprovalStatus(Enum):
    """
    Defines the possible statuses of an approval request.
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalRequest:
    """
    Represents a request for an infrastructure change that requires approval.
    """

    def __init__(
        self,
        requester_id: str,
        change_summary: str,
        change_details: Dict,
        approver_role: str = "Approver",
    ):
        self.id = str(uuid4())
        self.requester_id = requester_id
        self.change_summary = change_summary
        self.change_details = change_details
        self.approver_role = approver_role
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.approver_id: Optional[str] = None
        self.comments: List[Dict] = []

    def to_dict(self) -> Dict:
        """Serialize the approval request to a dictionary."""
        return {
            "id": self.id,
            "requester_id": self.requester_id,
            "change_summary": self.change_summary,
            "change_details": self.change_details,
            "approver_role": self.approver_role,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "approver_id": self.approver_id,
            "comments": self.comments,
        }


class ApprovalWorkflow:
    """
    Manages the lifecycle of approval requests.
    """

    def __init__(self, rbac_engine: RBACEngine, storage_file: str = "approvals.json"):
        self.rbac_engine = rbac_engine
        self.storage_file = storage_file
        self.requests: Dict[str, ApprovalRequest] = self._load_requests()

    def _load_requests(self) -> Dict[str, ApprovalRequest]:
        """Load approval requests from the storage file."""
        try:
            with open(self.storage_file, "r") as f:
                data = json.load(f)
            requests = {}
            for req_id, req_data in data.items():
                req = ApprovalRequest(
                    requester_id=req_data["requester_id"],
                    change_summary=req_data["change_summary"],
                    change_details=req_data["change_details"],
                )
                req.id = req_id
                req.status = ApprovalStatus(req_data["status"])
                # ... (load other fields)
                requests[req_id] = req
            return requests
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_requests(self):
        """Save the current state of approval requests to the storage file."""
        with open(self.storage_file, "w") as f:
            json.dump({req_id: req.to_dict() for req_id, req in self.requests.items()}, f, indent=2)

    def create_request(self, request: ApprovalRequest):
        """Create a new approval request."""
        self.requests[request.id] = request
        self._save_requests()
        audit_logger.log(
            AuditEvent.INFRA_CHANGE_REQUESTED,
            actor_id=request.requester_id,
            target_id=request.id,
            details=request.change_summary,
        )
        console.print(f"[green]Approval request '{request.id}' created.[/green]")

    def approve_request(self, request_id: str, approver_id: str, comment: Optional[str] = None):
        """Approve an approval request."""
        if request_id not in self.requests:
            raise ValueError("Approval request not found.")

        request = self.requests[request_id]
        if not self.rbac_engine.has_permission(approver_id, Permission.APPROVE_CHANGES):
            raise PermissionError("You do not have permission to approve changes.")

        request.status = ApprovalStatus.APPROVED
        request.approver_id = approver_id
        request.updated_at = datetime.now(timezone.utc)
        if comment:
            request.comments.append({"user_id": approver_id, "comment": comment})

        self._save_requests()
        audit_logger.log(
            AuditEvent.INFRA_CHANGE_APPROVED,
            actor_id=approver_id,
            target_id=request_id,
            details={"comment": comment},
        )
        console.print(f"[green]Approval request '{request_id}' approved.[/green]")

    def list_pending_requests(self):
        """List all pending approval requests."""
        pending_requests = [req for req in self.requests.values() if req.status == ApprovalStatus.PENDING]

        if not pending_requests:
            console.print("[yellow]No pending approval requests.[/yellow]")
            return

        table = Table(title="Pending Approval Requests")
        table.add_column("ID", style="cyan")
        table.add_column("Requester", style="green")
        table.add_column("Summary", style="magenta")
        table.add_column("Created At", style="yellow")

        for req in pending_requests:
            table.add_row(req.id, req.requester_id, req.change_summary, str(req.created_at))

        console.print(table)
