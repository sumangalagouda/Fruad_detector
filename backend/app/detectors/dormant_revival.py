from collections import defaultdict
from typing import List, Dict, Any
from app.detectors.base import BaseDetector, DetectorOutput
from app.models.transaction import Transaction


class DormantRevivalDetector(BaseDetector):
    DEFAULT_DORMANT_DAYS = 90
    DEFAULT_REVIVAL_MIN_AMOUNT = 20000.0

    def run(self, transactions: List[Transaction], case_context: Dict[str, Any] = None) -> DetectorOutput:
        dormant_days_thresh = int(self.config.get("dormant_days", self.DEFAULT_DORMANT_DAYS))
        revival_min_amount = float(self.config.get("revival_min_amount", self.DEFAULT_REVIVAL_MIN_AMOUNT))

        active_txs = [t for t in self.filter_successful_transactions(transactions) if t.transaction_date]
        active_txs.sort(key=lambda x: x.transaction_date)

        # Group by account
        by_account = defaultdict(list)
        for t in active_txs:
            by_account[t.account_id].append(t)

        flagged_revivals = []
        flagged_ids = []
        evidence = []

        for acc_id, tx_list in by_account.items():
            if len(tx_list) < 2:
                continue

            for i in range(1, len(tx_list)):
                prev_tx = tx_list[i - 1]
                curr_tx = tx_list[i]
                gap_days = (curr_tx.transaction_date - prev_tx.transaction_date).total_seconds() / 86400.0

                if gap_days >= dormant_days_thresh and curr_tx.amount >= revival_min_amount:
                    flagged_ids.append(curr_tx.transaction_id)
                    flagged_revivals.append((prev_tx, curr_tx, gap_days))

                    evidence.append({
                        "revival_transaction_id": curr_tx.transaction_id,
                        "account_number": curr_tx.account_number,
                        "dormant_period_days": round(gap_days, 1),
                        "previous_activity_date": prev_tx.transaction_date.isoformat(),
                        "revival_date": curr_tx.transaction_date.isoformat(),
                        "revival_amount": curr_tx.amount,
                        "source_statement": curr_tx.source_file,
                        "reason": f"Account {curr_tx.account_number} had {int(gap_days)} days of inactivity before a sudden revival transaction of ₹{curr_tx.amount:,.2f}.",
                    })

        triggered = len(flagged_ids) > 0
        severity = "HIGH" if any(r[1].amount >= 100000 for r in flagged_revivals) else ("MEDIUM" if triggered else "LOW")
        reason = (
            f"Detected {len(flagged_ids)} dormant account revival transaction(s) after >= {dormant_days_thresh} days of inactivity."
            if triggered
            else f"No account dormancy revival events exceeding {dormant_days_thresh} days were detected."
        )

        return DetectorOutput(
            detector_name="DORMANT_ACCOUNT_REVIVAL",
            triggered=triggered,
            severity=severity,
            suspicious_transaction_ids=flagged_ids,
            metrics={
                "dormant_threshold_days": dormant_days_thresh,
                "revival_min_amount": revival_min_amount,
                "revivals_count": len(flagged_revivals),
            },
            reason=reason,
            evidence=evidence,
            configuration_used={
                "dormant_days": dormant_days_thresh,
                "revival_min_amount": revival_min_amount,
            },
        )
