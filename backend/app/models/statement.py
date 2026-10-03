from datetime import datetime, timezone
import uuid
from app.extensions import db


class BankStatement(db.Model):
    __tablename__ = "bank_statements"

    statement_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    account_id = db.Column(db.String(36), db.ForeignKey("accounts.account_id"), nullable=True, index=True)

    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # PDF, CSV, XLSX, XLS, IMAGE
    file_size = db.Column(db.Integer, nullable=False, default=0)

    upload_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    processing_status = db.Column(
        db.String(50),
        default="UPLOADED",
        nullable=False,
        index=True
    )  # UPLOADED, PROCESSING, NORMALIZED, ANALYZING, COMPLETED, FAILED
    page_count = db.Column(db.Integer, default=1, nullable=False)

    # Document Header metadata
    bank_name = db.Column(db.String(150), nullable=True)
    account_holder = db.Column(db.String(200), nullable=True)
    account_number = db.Column(db.String(100), nullable=True)

    source_path = db.Column(db.String(500), nullable=False)  # Internal file path, never exposed to frontend
    extraction_method = db.Column(db.String(100), default="STRUCTURED", nullable=False)  # STRUCTURED, OCR, HYBRID
    processing_error = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = db.relationship("Case", back_populates="statements")
    account = db.relationship("Account", back_populates="statements")
    transactions = db.relationship("Transaction", back_populates="statement", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        # NOTE: source_path is NEVER exposed to the frontend as required by Section 6
        return {
            "statement_id": self.statement_id,
            "case_id": self.case_id,
            "account_id": self.account_id,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "upload_timestamp": self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            "processing_status": self.processing_status,
            "page_count": self.page_count,
            "bank_name": self.bank_name,
            "account_holder": self.account_holder,
            "account_number": self.account_number,
            "extraction_method": self.extraction_method,
            "processing_error": self.processing_error,
            "transactions_count": self.transactions.count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
