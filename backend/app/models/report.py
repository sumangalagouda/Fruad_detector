from datetime import datetime, timezone
import uuid
from app.extensions import db


class InvestigationReport(db.Model):
    __tablename__ = "investigation_reports"

    report_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="GENERATED", nullable=False)  # DRAFT, GENERATED, FINALIZED

    # Structured 17 sections stored as JSON and compiled Markdown/HTML
    sections_data = db.Column(db.JSON, nullable=False)
    content_markdown = db.Column(db.Text, nullable=False)

    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = db.relationship("Case", back_populates="reports")
    creator = db.relationship("User")

    def to_dict(self):
        return {
            "report_id": self.report_id,
            "case_id": self.case_id,
            "user_id": self.user_id,
            "title": self.title,
            "status": self.status,
            "sections_data": self.sections_data,
            "content_markdown": self.content_markdown,
            "creator_name": self.creator.full_name if self.creator else None,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
