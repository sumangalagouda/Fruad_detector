from datetime import datetime, timezone
import uuid
from app.extensions import db


class DetectorResult(db.Model):
    __tablename__ = "detector_results"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    detector_name = db.Column(db.String(100), nullable=False, index=True)
    triggered = db.Column(db.Boolean, default=False, nullable=False, index=True)
    severity = db.Column(db.String(30), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    transactions = db.Column(db.JSON, nullable=True)  # List of transaction_ids flagged
    metrics = db.Column(db.JSON, nullable=True)  # e.g., {"window_days": 7, "total_amount": 145000}
    reason = db.Column(db.Text, nullable=False)
    evidence = db.Column(db.JSON, nullable=True)  # Detailed evidence entries
    configuration_used = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    case = db.relationship("Case", back_populates="detector_results")

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "detector": self.detector_name,
            "triggered": self.triggered,
            "severity": self.severity,
            "transactions": self.transactions or [],
            "metrics": self.metrics or {},
            "reason": self.reason,
            "evidence": self.evidence or [],
            "configuration_used": self.configuration_used or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SuspiciousTransaction(db.Model):
    __tablename__ = "suspicious_transactions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    transaction_id = db.Column(db.String(36), db.ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    detector_name = db.Column(db.String(100), nullable=False, index=True)
    severity = db.Column(db.String(30), default="MEDIUM", nullable=False)
    score_contribution = db.Column(db.Float, default=0.0, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    evidence_data = db.Column(db.JSON, nullable=True)
    flagged_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    case = db.relationship("Case", back_populates="suspicious_transactions")
    transaction = db.relationship("Transaction", back_populates="suspicious_flags")

    def to_dict(self):
        tx_dict = self.transaction.to_dict() if self.transaction else None
        return {
            "id": self.id,
            "case_id": self.case_id,
            "transaction_id": self.transaction_id,
            "detector_name": self.detector_name,
            "severity": self.severity,
            "score_contribution": self.score_contribution,
            "reason": self.reason,
            "evidence_data": self.evidence_data or {},
            "transaction": tx_dict,
            "flagged_at": self.flagged_at.isoformat() if self.flagged_at else None,
        }
