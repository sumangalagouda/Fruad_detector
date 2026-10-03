from datetime import datetime, timezone
import uuid
from app.extensions import db


class FundFlowEdge(db.Model):
    __tablename__ = "fund_flow_edges"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    source_account = db.Column(db.String(100), nullable=False, index=True)
    destination_account = db.Column(db.String(100), nullable=False, index=True)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    transaction_count = db.Column(db.Integer, nullable=False, default=1)
    transaction_ids = db.Column(db.JSON, nullable=True)
    first_date = db.Column(db.DateTime, nullable=True)
    last_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "source_account": self.source_account,
            "destination_account": self.destination_account,
            "total_amount": self.total_amount,
            "transaction_count": self.transaction_count,
            "transaction_ids": self.transaction_ids or [],
            "first_date": self.first_date.isoformat() if self.first_date else None,
            "last_date": self.last_date.isoformat() if self.last_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CircularFlow(db.Model):
    __tablename__ = "circular_flows"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    cycle_path = db.Column(db.JSON, nullable=False)  # e.g., ["ACC-001", "ACC-002", "ACC-003", "ACC-001"]
    length = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    duration_days = db.Column(db.Float, nullable=True)
    risk_level = db.Column(db.String(20), default="HIGH", nullable=False)
    evidence_summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    transactions = db.relationship("CircularFlowTransaction", back_populates="circular_flow", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "cycle_path": self.cycle_path,
            "length": self.length,
            "total_amount": self.total_amount,
            "duration_days": self.duration_days,
            "risk_level": self.risk_level,
            "evidence_summary": self.evidence_summary,
            "transactions": [t.to_dict() for t in self.transactions],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CircularFlowTransaction(db.Model):
    __tablename__ = "circular_flow_transactions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    circular_flow_id = db.Column(db.String(36), db.ForeignKey("circular_flows.id"), nullable=False, index=True)
    transaction_id = db.Column(db.String(36), db.ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    sequence_order = db.Column(db.Integer, nullable=False)

    circular_flow = db.relationship("CircularFlow", back_populates="transactions")
    transaction = db.relationship("Transaction")

    def to_dict(self):
        return {
            "id": self.id,
            "circular_flow_id": self.circular_flow_id,
            "transaction_id": self.transaction_id,
            "sequence_order": self.sequence_order,
            "transaction": self.transaction.to_dict() if self.transaction else None,
        }


class LayeringChain(db.Model):
    __tablename__ = "layering_chains"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    chain_path = db.Column(db.JSON, nullable=False)  # e.g., ["ACC-A", "ACC-B", "ACC-C", "ACC-D"]
    hops_count = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    duration_hours = db.Column(db.Float, nullable=True)
    risk_level = db.Column(db.String(20), default="HIGH", nullable=False)
    evidence_summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    transactions = db.relationship("LayeringChainTransaction", back_populates="layering_chain", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "chain_path": self.chain_path,
            "hops_count": self.hops_count,
            "total_amount": self.total_amount,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "duration_hours": self.duration_hours,
            "risk_level": self.risk_level,
            "evidence_summary": self.evidence_summary,
            "transactions": [t.to_dict() for t in self.transactions],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LayeringChainTransaction(db.Model):
    __tablename__ = "layering_chain_transactions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    layering_chain_id = db.Column(db.String(36), db.ForeignKey("layering_chains.id"), nullable=False, index=True)
    transaction_id = db.Column(db.String(36), db.ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    sequence_order = db.Column(db.Integer, nullable=False)

    layering_chain = db.relationship("LayeringChain", back_populates="transactions")
    transaction = db.relationship("Transaction")

    def to_dict(self):
        return {
            "id": self.id,
            "layering_chain_id": self.layering_chain_id,
            "transaction_id": self.transaction_id,
            "sequence_order": self.sequence_order,
            "transaction": self.transaction.to_dict() if self.transaction else None,
        }


class MoneyTrail(db.Model):
    __tablename__ = "money_trails"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey("cases.case_id"), nullable=False, index=True)
    source_transaction_id = db.Column(db.String(36), db.ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    destination_transaction_id = db.Column(db.String(36), db.ForeignKey("transactions.transaction_id"), nullable=True, index=True)
    allocated_amount = db.Column(db.Float, nullable=False)
    trail_status = db.Column(db.String(50), default="ALLOCATED", nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    source_transaction = db.relationship("Transaction", foreign_keys=[source_transaction_id])
    destination_transaction = db.relationship("Transaction", foreign_keys=[destination_transaction_id])
    links = db.relationship("MoneyTrailLink", back_populates="money_trail", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "source_transaction_id": self.source_transaction_id,
            "destination_transaction_id": self.destination_transaction_id,
            "allocated_amount": self.allocated_amount,
            "trail_status": self.trail_status,
            "links": [l.to_dict() for l in self.links],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MoneyTrailLink(db.Model):
    __tablename__ = "money_trail_links"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    money_trail_id = db.Column(db.String(36), db.ForeignKey("money_trails.id"), nullable=False, index=True)
    step_order = db.Column(db.Integer, nullable=False)
    from_account = db.Column(db.String(100), nullable=False)
    to_account = db.Column(db.String(100), nullable=False)
    transaction_id = db.Column(db.String(36), db.ForeignKey("transactions.transaction_id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=True)

    money_trail = db.relationship("MoneyTrail", back_populates="links")
    transaction = db.relationship("Transaction")

    def to_dict(self):
        return {
            "id": self.id,
            "money_trail_id": self.money_trail_id,
            "step_order": self.step_order,
            "from_account": self.from_account,
            "to_account": self.to_account,
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "date": self.date.isoformat() if self.date else None,
            "transaction": self.transaction.to_dict() if self.transaction else None,
        }
