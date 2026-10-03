from datetime import datetime, timezone
import uuid
from app.extensions import db


class Person(db.Model):
    __tablename__ = "persons"

    person_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = db.Column(db.String(200), nullable=False, index=True)
    identifier_type = db.Column(db.String(50), nullable=True)  # PAN, SSN, Passport, National ID
    identifier_value = db.Column(db.String(100), nullable=True, index=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    cases = db.relationship("Case", back_populates="person", lazy="dynamic")
    accounts = db.relationship("Account", back_populates="person", lazy="dynamic")

    def to_dict(self):
        return {
            "person_id": self.person_id,
            "full_name": self.full_name,
            "identifier_type": self.identifier_type,
            "identifier_value": self.identifier_value,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Case(db.Model):
    __tablename__ = "cases"

    case_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="ACTIVE", nullable=False)  # ACTIVE, PENDING_REVIEW, CLOSED, ARCHIVED
    priority = db.Column(db.String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    person_id = db.Column(db.String(36), db.ForeignKey("persons.person_id"), nullable=False, index=True)
    created_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)

    # Explainable Suspicion Score
    suspicion_score = db.Column(db.Float, default=0.0, nullable=False)
    score_version = db.Column(db.String(50), default="v1.0", nullable=False)
    score_breakdown = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    person = db.relationship("Person", back_populates="cases")
    creator = db.relationship("User", foreign_keys=[created_by])
    accounts = db.relationship("Account", back_populates="case", lazy="dynamic", cascade="all, delete-orphan")
    statements = db.relationship("BankStatement", back_populates="case", lazy="dynamic", cascade="all, delete-orphan")
    transactions = db.relationship("Transaction", back_populates="case", lazy="dynamic", cascade="all, delete-orphan")
    detector_results = db.relationship("DetectorResult", back_populates="case", lazy="dynamic", cascade="all, delete-orphan")
    suspicious_transactions = db.relationship("SuspiciousTransaction", back_populates="case", lazy="dynamic", cascade="all, delete-orphan")
    reports = db.relationship("InvestigationReport", back_populates="case", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "case_id": self.case_id,
            "case_number": self.case_number,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "person_id": self.person_id,
            "person": self.person.to_dict() if self.person else None,
            "created_by": self.created_by,
            "suspicion_score": self.suspicion_score,
            "score_version": self.score_version,
            "score_breakdown": self.score_breakdown or {},
            "accounts_count": self.accounts.count(),
            "statements_count": self.statements.count(),
            "transactions_count": self.transactions.count(),
            "suspicious_count": self.suspicious_transactions.count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Account(db.Model):
    __tablename__ = "accounts"

    account_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    person_id = db.Column(db.String(36), db.ForeignKey("persons.person_id"), nullable=False, index=True)
    bank_name = db.Column(db.String(150), nullable=False, index=True)
    account_number = db.Column(db.String(100), nullable=False, index=True)
    account_holder = db.Column(db.String(200), nullable=True)
    account_type = db.Column(db.String(50), default="SAVINGS", nullable=False)  # SAVINGS, CURRENT, CHECKING, CREDIT
    currency = db.Column(db.String(10), default="INR", nullable=False)
    branch = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(50), default="ACTIVE", nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = db.relationship("Case", back_populates="accounts")
    person = db.relationship("Person", back_populates="accounts")
    statements = db.relationship("BankStatement", back_populates="account", lazy="dynamic")
    transactions = db.relationship("Transaction", back_populates="account", lazy="dynamic")

    def to_dict(self):
        return {
            "account_id": self.account_id,
            "case_id": self.case_id,
            "person_id": self.person_id,
            "bank_name": self.bank_name,
            "account_number": self.account_number,
            "account_holder": self.account_holder,
            "account_type": self.account_type,
            "currency": self.currency,
            "branch": self.branch,
            "status": self.status,
            "transactions_count": self.transactions.count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
