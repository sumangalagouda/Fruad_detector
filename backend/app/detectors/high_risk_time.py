from typing import List, Dict, Any
from app.detectors.base import BaseDetector, DetectorOutput
from app.models.transaction import Transaction


class HighRiskTimeDetector(BaseDetector):
    DEFAULT_START_HOUR = 0  # Midnight (00:00)
    DEFAULT_END_HOUR = 5    # 05:00 AM

    def run(self, transactions: List[Transaction], case_context: Dict[str, Any] = None) -> DetectorOutput:
        start_hour = int(self.config.get("start_hour", self.DEFAULT_START_HOUR))
        end_hour = int(self.config.get("end_hour", self.DEFAULT_END_HOUR))

        active_txs = [t for t in self.filter_successful_transactions(transactions) if t.transaction_date]

        flagged_ids = []
        evidence = []

        for tx in active_txs:
            hour = tx.transaction_date.hour
            # Check whether hour falls in [start_hour, end_hour)
            is_in_range = False
            if start_hour <= end_hour:
                is_in_range = start_hour <= hour <= end_hour
            else:
                # overnight wrap-around (e.g. 23:00 to 04:00)
                is_in_range = hour >= start_hour or hour <= end_hour

            if is_in_range and tx.amount >= 10000:  # significant transactions at unusual hours
                flagged_ids.append(tx.transaction_id)
                evidence.append({
                    "transaction_id": tx.transaction_id,
                    "amount": tx.amount,
                    "transaction_time": tx.transaction_date.strftime("%H:%M:%S"),
                    "transaction_date": tx.transaction_date.isoformat(),
                    "configured_time_range": f"{start_hour:02d}:00 to {end_hour:02d}:00",
                    "source_statement": tx.source_file,
                    "reason": f"Transaction of ₹{tx.amount:,.2f} recorded at {tx.transaction_date.strftime('%H:%M:%S')}, falling within configured unusual-hours window ({start_hour:02d}:00 - {end_hour:02d}:00).",
                })

        triggered = len(flagged_ids) > 0
        severity = "MEDIUM" if any(t.amount >= 50000 for t in active_txs if t.transaction_id in flagged_ids) else ("LOW" if triggered else "LOW")
        reason = (
            f"Detected {len(flagged_ids)} transaction(s) recorded within configured unusual-hours monitoring window ({start_hour:02d}:00 - {end_hour:02d}:00)."
            if triggered
            else f"No transactions above threshold observed in the configured time range ({start_hour:02d}:00 - {end_hour:02d}:00)."
        )

        return DetectorOutput(
            detector_name="HIGH_RISK_TIME",
            triggered=triggered,
            severity=severity,
            suspicious_transaction_ids=flagged_ids,
            metrics={
                "start_hour": start_hour,
                "end_hour": end_hour,
                "flagged_count": len(flagged_ids),
            },
            reason=reason,
            evidence=evidence,
            configuration_used={
                "start_hour": start_hour,
                "end_hour": end_hour,
            },
        )
