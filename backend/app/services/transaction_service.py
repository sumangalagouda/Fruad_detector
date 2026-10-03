from app.extensions import db
from app.models.transaction import Transaction, TransactionValidation
from sqlalchemy import or_, and_
from typing import Optional, Dict, Any


class TransactionService:
    @staticmethod
    def get_transaction(transaction_id: str) -> Optional[Transaction]:
        return db.session.get(Transaction, transaction_id)

    @staticmethod
    def search_transactions(
        case_id: str,
        query: Optional[str] = None,
        account_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        transaction_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        q = Transaction.query.filter_by(case_id=case_id)

        if account_id:
            q = q.filter(Transaction.account_id == account_id)
        if transaction_type:
            q = q.filter(Transaction.transaction_type == transaction_type.upper())
        if status:
            q = q.filter(Transaction.status == status.upper())
        if min_amount is not None:
            q = q.filter(Transaction.amount >= min_amount)
        if max_amount is not None:
            q = q.filter(Transaction.amount <= max_amount)
        if start_date:
            q = q.filter(Transaction.transaction_date >= start_date)
        if end_date:
            q = q.filter(Transaction.transaction_date <= end_date)

        if query:
            term = f"%{query}%"
            q = q.filter(
                or_(
                    Transaction.description.ilike(term),
                    Transaction.reference_number.ilike(term),
                    Transaction.counterparty_name.ilike(term),
                    Transaction.counterparty_account.ilike(term),
                    Transaction.account_number.ilike(term),
                )
            )

        total_count = q.count()
        transactions = q.order_by(Transaction.transaction_date.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        ).items

        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "transactions": [t.to_dict() for t in transactions],
        }
