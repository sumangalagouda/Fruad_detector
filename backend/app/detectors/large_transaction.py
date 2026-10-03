from typing import List, Dict, Any
from app.detectors.base import BaseDetector, DetectorOutput
from app.models.transaction import Transaction


class LargeTransactionDetector(BaseDetector):
    DEFAULT_THRESHOLD = 50000.0

    def run(self, transactions: List[Transaction], case_context: Dict[str, Any] = None) -> DetectorOutput:
        threshold = float(self.config.get("threshold", self.DEFAULT_THRESHOLD))
        active_txs = self.filter_successful_transactions(transactions)

        flagged_ids = []
        evidence = []
        max_amount = 0.0

        for tx in active_txs:
            if tx.amount >= threshold:
                flagged_ids.append(tx.transaction_id)
                diff = tx.amount - threshold
                if tx.amount > max_amount:
                    max_amount = tx.amount

                evidence.append({
                    "transaction_id": tx.transaction_id,
                    "amount": tx.amount,
                    "threshold": threshold,
                    "difference": diff,
                    "transaction_date": tx.transaction_date.isoformat() if tx.transaction_date else None,
                    "source_statement": tx.source_file,
                    "source_page": tx.source_page,
                    "reason": f"Transaction amount of ₹{tx.amount:,.2f} exceeds configured threshold of ₹{threshold:,.2f} by ₹{diff:,.2f}.",
                })

        triggered = len(flagged_ids) > 0
        severity = "HIGH" if max_amount >= threshold * 2 else ("MEDIUM" if triggered else "LOW")
        reason = (
            f"Detected {len(flagged_ids)} transaction(s) exceeding threshold of ₹{threshold:,.2f}."
            if triggered
            else f"No transactions observed exceeding the threshold of ₹{threshold:,.2f}."
        )

        return DetectorOutput(
            detector_name="LARGE_TRANSACTION",
            triggered=triggered,
            severity=severity,
            suspicious_transaction_ids=flagged_ids,
            metrics={
                "threshold": threshold,
                "flagged_count": len(flagged_ids),
                "max_amount": max_amount,
            },
            reason=reason,
            evidence=evidence,
            configuration_used={"threshold": threshold},
        )
