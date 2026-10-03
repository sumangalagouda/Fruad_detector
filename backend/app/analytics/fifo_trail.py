from collections import defaultdict
from typing import List, Dict, Any
from app.extensions import db
from app.models.transaction import Transaction
from app.models.graph import MoneyTrail, MoneyTrailLink
from app.utils.logger import logger


class FifoMoneyTrailTracer:
    @staticmethod
    def compute_fifo_trails(case_id: str) -> List[Dict[str, Any]]:
        """
        Compute First-In-First-Out (FIFO) fund allocation trails for all accounts in the case.
        When credits enter an account, they are depleted sequentially against subsequent debits.
        """
        MoneyTrail.query.filter_by(case_id=case_id).delete()

        # Fetch active chronological transactions
        transactions = Transaction.query.filter(
            Transaction.case_id == case_id,
            ~Transaction.status.in_(["FAILED", "REVERSED", "RETURNED"]),
            Transaction.transaction_date.isnot(None),
        ).order_by(Transaction.transaction_date.asc()).all()

        # Group by account
        account_groups = defaultdict(list)
        for tx in transactions:
            account_groups[tx.account_id].append(tx)

        persisted_trails = []

        for acc_id, tx_list in account_groups.items():
            inflows = [
                {"tx": t, "remaining": t.amount}
                for t in tx_list
                if t.transaction_type == "CREDIT" or t.credit > 0
            ]
            outflows = [
                {"tx": t, "remaining": t.amount}
                for t in tx_list
                if t.transaction_type == "DEBIT" or t.debit > 0
            ]

            in_idx = 0
            out_idx = 0

            while in_idx < len(inflows) and out_idx < len(outflows):
                current_in = inflows[in_idx]
                current_out = outflows[out_idx]

                # Outflow must occur on or after inflow
                if current_out["tx"].transaction_date < current_in["tx"].transaction_date:
                    out_idx += 1
                    continue

                allocation = min(current_in["remaining"], current_out["remaining"])

                if allocation > 0:
                    current_in["remaining"] -= allocation
                    current_out["remaining"] -= allocation

                    trail = MoneyTrail(
                        case_id=case_id,
                        source_transaction_id=current_in["tx"].transaction_id,
                        destination_transaction_id=current_out["tx"].transaction_id,
                        allocated_amount=round(allocation, 2),
                        trail_status="ALLOCATED",
                    )
                    db.session.add(trail)
                    db.session.flush()

                    # Source link
                    link_1 = MoneyTrailLink(
                        money_trail_id=trail.id,
                        step_order=1,
                        from_account=current_in["tx"].counterparty_account or current_in["tx"].counterparty_name or "External Source",
                        to_account=current_in["tx"].account_number,
                        transaction_id=current_in["tx"].transaction_id,
                        amount=round(allocation, 2),
                        date=current_in["tx"].transaction_date,
                    )
                    # Destination link
                    link_2 = MoneyTrailLink(
                        money_trail_id=trail.id,
                        step_order=2,
                        from_account=current_out["tx"].account_number,
                        to_account=current_out["tx"].counterparty_account or current_out["tx"].counterparty_name or "External Beneficiary",
                        transaction_id=current_out["tx"].transaction_id,
                        amount=round(allocation, 2),
                        date=current_out["tx"].transaction_date,
                    )
                    db.session.add_all([link_1, link_2])
                    persisted_trails.append(trail)

                if current_in["remaining"] <= 0.01:
                    in_idx += 1
                if current_out["remaining"] <= 0.01:
                    out_idx += 1

        db.session.commit()
        logger.info(f"Computed {len(persisted_trails)} FIFO money trail allocations for case {case_id}.")
        return [t.to_dict() for t in persisted_trails]

    @staticmethod
    def get_trail_for_transaction(case_id: str, transaction_id: str) -> Dict[str, Any]:
        """Retrieve FIFO allocations associated with a specific transaction."""
        as_source = MoneyTrail.query.filter_by(case_id=case_id, source_transaction_id=transaction_id).all()
        as_dest = MoneyTrail.query.filter_by(case_id=case_id, destination_transaction_id=transaction_id).all()

        return {
            "transaction_id": transaction_id,
            "outgoing_allocations_from_this_deposit": [t.to_dict() for t in as_source],
            "incoming_sources_funding_this_withdrawal": [t.to_dict() for t in as_dest],
            "disclaimer": "FIFO allocation indicates the temporal sequencing of fund availability and dispersal. It does not definitively prove mathematical provenance of fungible currency.",
        }
