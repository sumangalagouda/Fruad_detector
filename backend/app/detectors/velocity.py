from typing import List, Dict, Any
from app.detectors.base import BaseDetector, DetectorOutput
from app.models.transaction import Transaction


class TransactionVelocityDetector(BaseDetector):
    DEFAULT_VELOCITY_SECONDS = 3600.0  # 1 hour

    def run(self, transactions: List[Transaction], case_context: Dict[str, Any] = None) -> DetectorOutput:
        max_sec = float(self.config.get("velocity_seconds", self.DEFAULT_VELOCITY_SECONDS))

        active_txs = [t for t in self.filter_successful_transactions(transactions) if t.transaction_date]
        active_txs.sort(key=lambda x: x.transaction_date)

        credits = [t for t in active_txs if t.transaction_type == "CREDIT" or t.credit > 0]
        debits = [t for t in active_txs if t.transaction_type == "DEBIT" or t.debit > 0]

        flagged_pairs = []
        flagged_ids = set()
        evidence = []

        for cr in credits:
            for dr in debits:
                if dr.account_id == cr.account_id and dr.transaction_date >= cr.transaction_date:
                    delta_sec = (dr.transaction_date - cr.transaction_date).total_seconds()
                    if 0 <= delta_sec <= max_sec:
                        ratio = round(dr.amount / cr.amount, 2) if cr.amount > 0 else 1.0
                        flagged_pairs.append((cr, dr, delta_sec, ratio))
                        flagged_ids.add(cr.transaction_id)
                        flagged_ids.add(dr.transaction_id)

                        evidence.append({
                            "incoming_transaction_id": cr.transaction_id,
                            "outgoing_transaction_id": dr.transaction_id,
                            "incoming_amount": cr.amount,
                            "outgoing_amount": dr.amount,
                            "ratio": ratio,
                            "time_difference_seconds": delta_sec,
                            "account_number": cr.account_number,
                            "source_statement": cr.source_file,
                            "reason": f"Incoming credit of ₹{cr.amount:,.2f} followed by outgoing debit of ₹{dr.amount:,.2f} in {int(delta_sec)} seconds (limit: {int(max_sec)}s).",
                        })

        triggered = len(flagged_ids) > 0
        severity = "HIGH" if any(p[2] <= 600 or p[1].amount >= 50000 for p in flagged_pairs) else ("MEDIUM" if triggered else "LOW")
        reason = (
            f"Detected {len(flagged_pairs)} rapid fund movement pair(s) within configured velocity window of {int(max_sec)}s."
            if triggered
            else f"No rapid incoming-to-outgoing transaction velocity observed within {int(max_sec)} seconds."
        )

        return DetectorOutput(
            detector_name="TRANSACTION_VELOCITY",
            triggered=triggered,
            severity=severity,
            suspicious_transaction_ids=sorted(list(flagged_ids)),
            metrics={
                "velocity_seconds": max_sec,
                "pairs_count": len(flagged_pairs),
                "total_flagged": len(flagged_ids),
            },
            reason=reason,
            evidence=evidence,
            configuration_used={"velocity_seconds": max_sec},
        )
