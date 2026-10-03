from typing import List, Dict, Any
from app.detectors.base import BaseDetector, DetectorOutput
from app.models.transaction import Transaction


class PassThroughDetector(BaseDetector):
    DEFAULT_RATIO = 0.90
    DEFAULT_MAX_HOURS = 48.0

    def run(self, transactions: List[Transaction], case_context: Dict[str, Any] = None) -> DetectorOutput:
        min_ratio = float(self.config.get("min_ratio", self.DEFAULT_RATIO))
        max_hours = float(self.config.get("max_hours", self.DEFAULT_MAX_HOURS))

        active_txs = [t for t in self.filter_successful_transactions(transactions) if t.transaction_date]
        active_txs.sort(key=lambda x: x.transaction_date)

        credits = [t for t in active_txs if t.transaction_type == "CREDIT" or t.credit > 0]
        debits = [t for t in active_txs if t.transaction_type == "DEBIT" or t.debit > 0]

        flagged_pairs = []
        flagged_ids = set()
        evidence = []

        for cr in credits:
            if cr.amount < 10000:  # ignore trivial sums
                continue
            for dr in debits:
                if dr.account_id == cr.account_id and dr.transaction_date >= cr.transaction_date:
                    delta_hours = (dr.transaction_date - cr.transaction_date).total_seconds() / 3600.0
                    if delta_hours <= max_hours:
                        ratio = round(dr.amount / cr.amount, 4)
                        if min_ratio <= ratio <= 1.05:  # within 90% to 105% of inflow
                            flagged_pairs.append((cr, dr, ratio, delta_hours))
                            flagged_ids.add(cr.transaction_id)
                            flagged_ids.add(dr.transaction_id)

                            evidence.append({
                                "source_transaction_id": cr.transaction_id,
                                "destination_transaction_id": dr.transaction_id,
                                "incoming_amount": cr.amount,
                                "outgoing_amount": dr.amount,
                                "ratio": ratio,
                                "time_difference_hours": round(delta_hours, 2),
                                "account_number": cr.account_number,
                                "source_statement": cr.source_file,
                                "reason": f"Inflow of ₹{cr.amount:,.2f} followed by outflow of ₹{dr.amount:,.2f} ({ratio*100:.1f}%) within {delta_hours:.1f} hours.",
                            })

        triggered = len(flagged_ids) > 0
        severity = "HIGH" if any(p[2] >= 0.95 for p in flagged_pairs) else ("MEDIUM" if triggered else "LOW")
        reason = (
            f"Identified {len(flagged_pairs)} pass-through pattern(s) where outgoing funds exceeded {int(min_ratio*100)}% of incoming funds within {int(max_hours)}h."
            if triggered
            else f"No pass-through fund movement exceeding {int(min_ratio*100)}% threshold was detected."
        )

        return DetectorOutput(
            detector_name="PASS_THROUGH",
            triggered=triggered,
            severity=severity,
            suspicious_transaction_ids=sorted(list(flagged_ids)),
            metrics={
                "min_ratio": min_ratio,
                "max_hours": max_hours,
                "pairs_count": len(flagged_pairs),
                "total_flagged": len(flagged_ids),
            },
            reason=reason,
            evidence=evidence,
            configuration_used={"min_ratio": min_ratio, "max_hours": max_hours},
        )
