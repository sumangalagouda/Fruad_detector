from datetime import datetime, timezone
import uuid
from app.extensions import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    transaction_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    statement_id = db.Column(db.String(36), db.ForeignKey("bank_statements.statement_id"), nullable=False, index=True)
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    account_id = db.Column(db.String(36), db.ForeignKey("accounts.account_id"), nullable=False, index=True)

    # Denormalized canonical identity for fast queries and integrity
    account_number = db.Column(db.String(100), nullable=False, index=True)
    account_holder = db.Column(db.String(200), nullable=True)
    bank_name = db.Column(db.String(150), nullable=False, index=True)

    # Dates
    transaction_date = db.Column(db.DateTime, nullable=False, index=True)
    value_date = db.Column(db.DateTime, nullable=True)

    description = db.Column(db.Text, nullable=False)
    reference_number = db.Column(db.String(150), nullable=True, index=True)

    # Amounts
    debit = db.Column(db.Float, default=0.0, nullable=False)
    credit = db.Column(db.Float, default=0.0, nullable=False)
    amount = db.Column(db.Float, nullable=False, index=True)  # absolute transaction amount
    balance = db.Column(db.Float, nullable=True)

    transaction_type = db.Column(db.String(20), nullable=False)  # DEBIT, CREDIT

    # Status classification: SUCCESS, FAILED, REVERSED, RETURNED, REFUNDED, PENDING, UNKNOWN
    status = db.Column(db.String(30), default="SUCCESS", nullable=False, index=True)

    # Counterparty details
    counterparty_name = db.Column(db.String(200), nullable=True, index=True)
    counterparty_account = db.Column(db.String(100), nullable=True, index=True)
    counterparty_bank = db.Column(db.String(150), nullable=True)

    # Provenance
    source_file = db.Column(db.String(255), nullable=False)
    source_page = db.Column(db.Integer, default=1, nullable=False)
    raw_text = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = db.relationship("Case", back_populates="transactions")
    statement = db.relationship("BankStatement", back_populates="transactions")
    account = db.relationship("Account", back_populates="transactions")
    validation = db.relationship("TransactionValidation", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    suspicious_flags = db.relationship("SuspiciousTransaction", back_populates="transaction", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "statement_id": self.statement_id,
            "case_id": self.case_id,
            "account_id": self.account_id,
            "account_number": self.account_number,
            "account_holder": self.account_holder,
            "bank_name": self.bank_name,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "value_date": self.value_date.isoformat() if self.value_date else None,
            "description": self.description,
            "reference_number": self.reference_number,
            "debit": self.debit,
            "credit": self.credit,
            "amount": self.amount,
            "balance": self.balance,
            "transaction_type": self.transaction_type,
            "status": self.status,
            "counterparty_name": self.counterparty_name,
            "counterparty_account": self.counterparty_account,
            "counterparty_bank": self.counterparty_bank,
            "source_file": self.source_file,
            "source_page": self.source_page,
            "raw_text": self.raw_text,
            "validation": self.validation.to_dict() if self.validation else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TransactionValidation(db.Model):
    __tablename__ = "transaction_validation"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = db.Column(db.String(36), db.ForeignKey("transactions.transaction_id"), nullable=False, unique=True, index=True)
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    validation_status = db.Column(db.String(30), default="VALID", nullable=False)  # VALID, WARNING, INVALID
    issues = db.Column(db.JSON, nullable=True)  # List of strings describing warnings or errors
    checked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    transaction = db.relationship("Transaction", back_populates="validation")

    def to_dict(self):
        return {
            "validation_id": self.id,
            "transaction_id": self.transaction_id,
            "case_id": self.case_id,
            "validation_status": self.validation_status,
            "issues": self.issues or [],
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
        }
