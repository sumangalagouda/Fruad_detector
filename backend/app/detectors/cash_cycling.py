from typing import List, Dict, Any
from app.detectors.base import BaseDetector, DetectorOutput
from app.models.transaction import Transaction


class CashCyclingDetector(BaseDetector):
    WINDOW_HOURS = 24.0
    MATCH_THRESHOLD = 0.80
    CRITICAL_THRESHOLD = 0.95

    def run(self, transactions: List[Transaction], case_context: Dict[str, Any] = None) -> DetectorOutput:
        window_hours = float(self.config.get("window_hours", self.WINDOW_HOURS))
        match_thresh = float(self.config.get("match_threshold", self.MATCH_THRESHOLD))
        critical_thresh = float(self.config.get("critical_threshold", self.CRITICAL_THRESHOLD))

        active_txs = [t for t in self.filter_successful_transactions(transactions) if t.transaction_date]
        active_txs.sort(key=lambda x: x.transaction_date)

        flagged_pairs = []
        flagged_ids = set()
        evidence = []
        max_ratio = 0.0

        for i, tx1 in enumerate(active_txs):
            # Cash or rapid reciprocal matching
            for j in range(i + 1, len(active_txs)):
                tx2 = active_txs[j]
                delta_hours = (tx2.transaction_date - tx1.transaction_date).total_seconds() / 3600.0
                if delta_hours > window_hours:
                    break

                # Check if one is debit and other is credit (cycling funds)
                if tx1.transaction_type != tx2.transaction_type and tx1.amount > 5000 and tx2.amount > 5000:
                    smaller = min(tx1.amount, tx2.amount)
                    larger = max(tx1.amount, tx2.amount)
                    ratio = smaller / larger

                    if ratio >= match_thresh:
                        if ratio > max_ratio:
                            max_ratio = ratio
                        flagged_pairs.append((tx1, tx2, ratio, delta_hours))
                        flagged_ids.add(tx1.transaction_id)
                        flagged_ids.add(tx2.transaction_id)

                        evidence.append({
                            "first_transaction_id": tx1.transaction_id,
                            "second_transaction_id": tx2.transaction_id,
                            "amount_1": tx1.amount,
                            "amount_2": tx2.amount,
                            "match_ratio": round(ratio, 4),
                            "duration_hours": round(delta_hours, 2),
                            "source_statement": tx1.source_file,
                            "reason": f"Reciprocal {tx1.transaction_type} (₹{tx1.amount:,.2f}) and {tx2.transaction_type} (₹{tx2.amount:,.2f}) with {ratio*100:.1f}% match within {delta_hours:.1f} hours.",
                        })

        triggered = len(flagged_ids) > 0
        severity = "CRITICAL" if max_ratio >= critical_thresh else ("HIGH" if triggered else "LOW")
        reason = (
            f"Detected {len(flagged_pairs)} fund cycling pair(s) matching >= {int(match_thresh*100)}% within {int(window_hours)}h."
            if triggered
            else f"No fund cycling detected within the configured {int(window_hours)}-hour window."
        )

        return DetectorOutput(
            detector_name="CASH_CYCLING",
            triggered=triggered,
            severity=severity,
            suspicious_transaction_ids=sorted(list(flagged_ids)),
            metrics={
                "window_hours": window_hours,
                "match_threshold": match_thresh,
                "critical_threshold": critical_thresh,
                "pairs_count": len(flagged_pairs),
                "max_match_ratio": round(max_ratio, 4),
            },
            reason=reason,
            evidence=evidence,
            configuration_used={
                "window_hours": window_hours,
                "match_threshold": match_thresh,
                "critical_threshold": critical_thresh,
            },
        )
