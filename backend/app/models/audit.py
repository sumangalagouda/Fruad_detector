from datetime import datetime, timezone
import uuid
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    case_id = db.Column(db.String(36), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    tool = db.Column(db.String(100), nullable=True, index=True)
    tool_arguments = db.Column(db.JSON, nullable=True)
    result_status = db.Column(db.String(50), nullable=False, default="SUCCESS")
    ip_address = db.Column(db.String(50), nullable=True)
    details = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "case_id": self.case_id,
            "action": self.action,
            "tool": self.tool,
            "tool_arguments": self.tool_arguments,
            "result_status": self.result_status,
            "ip_address": self.ip_address,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
