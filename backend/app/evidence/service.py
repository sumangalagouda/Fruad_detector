from typing import List, Dict, Any, Optional
from app.extensions import db
from app.models.case import Case, Person, Account
from app.models.statement import BankStatement
from app.models.transaction import Transaction
from app.models.detector import DetectorResult, SuspiciousTransaction
from app.models.graph import FundFlowEdge, CircularFlow, LayeringChain, MoneyTrail
from app.models.evidence import EvidenceRecord
from app.models.investigation import Investigation
from app.utils.logger import logger


class EvidenceService:
    """
    Authorized Evidence Abstraction Layer.
    Guarantees strict case-level isolation: prevents any cross-case data leakage.
    Serves structured facts, deterministic detector outputs, and graph evidence.
    """

    @staticmethod
    def get_case_evidence(case_id: str) -> Optional[Dict[str, Any]]:
        case = db.session.get(Case, case_id)
        if not case:
            return None
        return case.to_dict()

    @staticmethod
    def get_person_evidence(case_id: str) -> Optional[Dict[str, Any]]:
        case = db.session.get(Case, case_id)
        if not case or not case.person:
            return None
        return case.person.to_dict()

    @staticmethod
    def get_accounts_evidence(case_id: str) -> List[Dict[str, Any]]:
        accounts = Account.query.filter_by(case_id=case_id).all()
        return [a.to_dict() for a in accounts]

    @staticmethod
    def get_statements_evidence(case_id: str) -> List[Dict[str, Any]]:
        statements = BankStatement.query.filter_by(case_id=case_id).all()
        return [s.to_dict() for s in statements]

    @staticmethod
    def get_statement_evidence(case_id: str, statement_id: str) -> Optional[Dict[str, Any]]:
        statement = BankStatement.query.filter_by(case_id=case_id, statement_id=statement_id).first()
        return statement.to_dict() if statement else None

    @staticmethod
    def get_transactions_evidence(
        case_id: str,
        account_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        q = Transaction.query.filter_by(case_id=case_id)
        if account_id:
            q = q.filter_by(account_id=account_id)
        txs = q.order_by(Transaction.transaction_date.desc()).offset(offset).limit(limit).all()
        return [t.to_dict() for t in txs]

    @staticmethod
    def get_transaction_evidence(case_id: str, transaction_id: str) -> Optional[Dict[str, Any]]:
        tx = Transaction.query.filter_by(case_id=case_id, transaction_id=transaction_id).first()
        return tx.to_dict() if tx else None

    @staticmethod
    def search_transactions_evidence(
        case_id: str,
        query: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        status: Optional[str] = None,
        transaction_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        q = Transaction.query.filter_by(case_id=case_id)
        if min_amount is not None:
            q = q.filter(Transaction.amount >= min_amount)
        if max_amount is not None:
            q = q.filter(Transaction.amount <= max_amount)
        if status:
            q = q.filter(Transaction.status == status.upper())
        if transaction_type:
            q = q.filter(Transaction.transaction_type == transaction_type.upper())
        if query:
            term = f"%{query}%"
            q = q.filter(
                db.or_(
                    Transaction.description.ilike(term),
                    Transaction.reference_number.ilike(term),
                    Transaction.counterparty_name.ilike(term),
                    Transaction.account_number.ilike(term),
                )
            )
        txs = q.order_by(Transaction.transaction_date.desc()).limit(limit).all()
        return [t.to_dict() for t in txs]

    @staticmethod
    def get_suspicious_transactions_evidence(case_id: str, detector: Optional[str] = None) -> List[Dict[str, Any]]:
        q = SuspiciousTransaction.query.filter_by(case_id=case_id)
        if detector:
            q = q.filter_by(detector_name=detector.upper())
        items = q.all()
        return [item.to_dict() for item in items]

    @staticmethod
    def get_detector_results_evidence(case_id: str, detector_name: Optional[str] = None) -> List[Dict[str, Any]]:
        q = DetectorResult.query.filter_by(case_id=case_id)
        if detector_name:
            q = q.filter_by(detector_name=detector_name.upper())
        return [r.to_dict() for r in q.all()]

    @staticmethod
    def get_fund_flow_evidence(case_id: str) -> Dict[str, Any]:
        edges = FundFlowEdge.query.filter_by(case_id=case_id).all()
        nodes = set()
        edge_dicts = []
        for e in edges:
            nodes.add(e.source_account)
            nodes.add(e.destination_account)
            edge_dicts.append(e.to_dict())
        return {
            "case_id": case_id,
            "nodes": [{"id": n, "label": n} for n in sorted(list(nodes))],
            "edges": edge_dicts,
        }

    @staticmethod
    def get_circular_flows_evidence(case_id: str) -> List[Dict[str, Any]]:
        flows = CircularFlow.query.filter_by(case_id=case_id).all()
        return [f.to_dict() for f in flows]

    @staticmethod
    def get_layering_chains_evidence(case_id: str) -> List[Dict[str, Any]]:
        chains = LayeringChain.query.filter_by(case_id=case_id).all()
        return [c.to_dict() for c in chains]

    @staticmethod
    def get_money_trail_evidence(case_id: str, transaction_id: Optional[str] = None) -> Dict[str, Any]:
        q = MoneyTrail.query.filter_by(case_id=case_id)
        if transaction_id:
            q = q.filter(
                db.or_(
                    MoneyTrail.source_transaction_id == transaction_id,
                    MoneyTrail.destination_transaction_id == transaction_id,
                )
            )
        trails = q.all()
        return {
            "case_id": case_id,
            "trails": [t.to_dict() for t in trails],
            "disclaimer": "FIFO allocation indicates temporal order of credit utilization, not proven physical currency identity.",
        }

    @staticmethod
    def get_investigation_history_evidence(case_id: str) -> List[Dict[str, Any]]:
        invs = Investigation.query.filter_by(case_id=case_id).order_by(Investigation.created_at.desc()).all()
        return [i.to_dict() for i in invs]
