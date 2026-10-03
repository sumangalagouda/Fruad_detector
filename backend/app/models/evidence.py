from datetime import datetime, timezone
import uuid
from app.extensions import db


class EvidenceRecord(db.Model):
    __tablename__ = "evidence_records"

    evidence_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)  # TRANSACTION, ACCOUNT, STATEMENT, PATTERN
    entity_id = db.Column(db.String(100), nullable=False, index=True)
    source = db.Column(db.String(150), nullable=False)  # Bank Name / Parser / Detector
    source_statement = db.Column(db.String(255), nullable=True)
    source_page = db.Column(db.Integer, nullable=True)
    transaction_id = db.Column(db.String(36), db.ForeignKey("transactions.transaction_id"), nullable=True, index=True)
    evidence_type = db.Column(db.String(100), nullable=False, index=True)  # STRUCTURING_BURST, HIGH_VELOCITY, etc.
    evidence_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    transaction = db.relationship("Transaction", foreign_keys=[transaction_id])

    def to_dict(self):
        return {
            "evidence_id": self.evidence_id,
            "case_id": self.case_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "source": self.source,
            "source_statement": self.source_statement,
            "source_page": self.source_page,
            "transaction_id": self.transaction_id,
            "evidence_type": self.evidence_type,
            "evidence_data": self.evidence_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
