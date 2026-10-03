from datetime import datetime, timezone
import uuid
from app.extensions import db


class Investigation(db.Model):
    __tablename__ = "investigations"

    investigation_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255), default="Investigation Session", nullable=False)
    status = db.Column(db.String(50), default="ACTIVE", nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = db.relationship("Case")
    user = db.relationship("User")
    messages = db.relationship("InvestigationMessage", back_populates="investigation", cascade="all, delete-orphan", order_by="InvestigationMessage.created_at")

    def to_dict(self):
        return {
            "investigation_id": self.investigation_id,
            "case_id": self.case_id,
            "user_id": self.user_id,
            "title": self.title,
            "status": self.status,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InvestigationMessage(db.Model):
    __tablename__ = "investigation_messages"

    message_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = db.Column(db.String(36), db.ForeignKey("investigations.investigation_id"), nullable=False, index=True)
    sender = db.Column(db.String(20), nullable=False)  # user, assistant
    user_question = db.Column(db.Text, nullable=True)
    response_text = db.Column(db.Text, nullable=False)

    # Structured investigative fields from Section 59
    facts = db.Column(db.JSON, nullable=True)
    detected_patterns = db.Column(db.JSON, nullable=True)
    evidence_items = db.Column(db.JSON, nullable=True)
    interpretations = db.Column(db.JSON, nullable=True)
    limitations = db.Column(db.JSON, nullable=True)
    next_steps = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    investigation = db.relationship("Investigation", back_populates="messages")
    tool_calls = db.relationship("InvestigationToolCall", back_populates="message", cascade="all, delete-orphan")
    feedback = db.relationship("InvestigatorFeedback", back_populates="message", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "investigation_id": self.investigation_id,
            "sender": self.sender,
            "user_question": self.user_question,
            "response_text": self.response_text,
            "facts": self.facts or [],
            "detected_patterns": self.detected_patterns or [],
            "evidence_items": self.evidence_items or [],
            "interpretations": self.interpretations or [],
            "limitations": self.limitations or [],
            "next_steps": self.next_steps or [],
            "tool_calls": [t.to_dict() for t in self.tool_calls],
            "feedback": [f.to_dict() for f in self.feedback],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InvestigationToolCall(db.Model):
    __tablename__ = "investigation_tool_calls"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = db.Column(db.String(36), db.ForeignKey("investigations.investigation_id"), nullable=False, index=True)
    message_id = db.Column(db.String(36), db.ForeignKey("investigation_messages.message_id"), nullable=False, index=True)
    tool_name = db.Column(db.String(100), nullable=False, index=True)
    tool_arguments = db.Column(db.JSON, nullable=True)
    tool_results = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(30), default="SUCCESS", nullable=False)  # SUCCESS, ERROR
    duration_ms = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    message = db.relationship("InvestigationMessage", back_populates="tool_calls")

    def to_dict(self):
        return {
            "id": self.id,
            "investigation_id": self.investigation_id,
            "message_id": self.message_id,
            "tool_name": self.tool_name,
            "tool_arguments": self.tool_arguments or {},
            "tool_results": self.tool_results,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InvestigatorFeedback(db.Model):
    __tablename__ = "investigator_feedback"

    feedback_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    investigation_id = db.Column(db.String(36), db.ForeignKey("investigations.investigation_id"), nullable=False, index=True)
    message_id = db.Column(db.String(36), db.ForeignKey("investigation_messages.message_id"), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    feedback_type = db.Column(db.String(50), nullable=False)  # Correct, Incorrect, False Positive, Needs Review
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    message = db.relationship("InvestigationMessage", back_populates="feedback")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "feedback_id": self.feedback_id,
            "case_id": self.case_id,
            "investigation_id": self.investigation_id,
            "message_id": self.message_id,
            "user_id": self.user_id,
            "feedback_type": self.feedback_type,
            "comment": self.comment,
            "user_name": self.user.full_name if self.user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
