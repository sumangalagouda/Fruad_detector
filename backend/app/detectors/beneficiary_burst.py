from typing import List, Dict, Any
from app.detectors.base import BaseDetector, DetectorOutput
from app.models.transaction import Transaction


class BeneficiaryBurstDetector(BaseDetector):
    MIN_BENEFICIARIES = 4
    MIN_DISPERSED_AMOUNT = 5000.0
    WINDOW_HOURS = 24.0

    def run(self, transactions: List[Transaction], case_context: Dict[str, Any] = None) -> DetectorOutput:
        min_beneficiaries = int(self.config.get("min_beneficiaries", self.MIN_BENEFICIARIES))
        min_amount = float(self.config.get("min_dispersed_amount", self.MIN_DISPERSED_AMOUNT))
        window_hours = float(self.config.get("window_hours", self.WINDOW_HOURS))

        # Look at debits (outflows to beneficiaries)
        active_txs = [
            t for t in self.filter_successful_transactions(transactions)
            if t.transaction_date and (t.transaction_type == "DEBIT" or t.debit > 0) and t.amount >= min_amount
        ]
        active_txs.sort(key=lambda x: x.transaction_date)

        flagged_bursts = []
        flagged_ids = set()
        evidence = []
        max_beneficiaries_seen = 0

        for i, tx_start in enumerate(active_txs):
            window_txs = [tx_start]
            beneficiaries = set()
            b_name = tx_start.counterparty_name or tx_start.counterparty_account or tx_start.description
            beneficiaries.add(b_name)

            for j in range(i + 1, len(active_txs)):
                tx_next = active_txs[j]
                delta_hours = (tx_next.transaction_date - tx_start.transaction_date).total_seconds() / 3600.0
                if delta_hours <= window_hours:
                    window_txs.append(tx_next)
                    next_b = tx_next.counterparty_name or tx_next.counterparty_account or tx_next.description
                    beneficiaries.add(next_b)
                else:
                    break

            if len(beneficiaries) >= min_beneficiaries:
                if len(beneficiaries) > max_beneficiaries_seen:
                    max_beneficiaries_seen = len(beneficiaries)
                burst_tuple = tuple(sorted([t.transaction_id for t in window_txs]))
                if burst_tuple not in flagged_bursts:
                    flagged_bursts.append(burst_tuple)
                    total_disp = sum(t.amount for t in window_txs)
                    for t in window_txs:
                        flagged_ids.add(t.transaction_id)
                        evidence.append({
                            "transaction_id": t.transaction_id,
                            "amount": t.amount,
                            "beneficiary": t.counterparty_name or t.description,
                            "transaction_date": t.transaction_date.isoformat(),
                            "source_statement": t.source_file,
                            "reason": f"Dispersal transaction of ₹{t.amount:,.2f} part of a {len(beneficiaries)}-beneficiary burst totalling ₹{total_disp:,.2f} within {int(window_hours)}h.",
                        })

        triggered = len(flagged_ids) > 0
        severity = "HIGH" if max_beneficiaries_seen >= 6 else ("MEDIUM" if triggered else "LOW")
        reason = (
            f"Detected rapid dispersal burst to {max_beneficiaries_seen} distinct beneficiaries within {int(window_hours)} hours (threshold: {min_beneficiaries})."
            if triggered
            else f"No beneficiary dispersal bursts exceeding {min_beneficiaries} distinct parties detected in {int(window_hours)}h."
        )

        return DetectorOutput(
            detector_name="BENEFICIARY_BURST",
            triggered=triggered,
            severity=severity,
            suspicious_transaction_ids=sorted(list(flagged_ids)),
            metrics={
                "min_beneficiaries": min_beneficiaries,
                "window_hours": window_hours,
                "max_beneficiaries_observed": max_beneficiaries_seen,
                "bursts_count": len(flagged_bursts),
                "total_flagged": len(flagged_ids),
            },
            reason=reason,
            evidence=evidence,
            configuration_used={
                "min_beneficiaries": min_beneficiaries,
                "min_dispersed_amount": min_amount,
                "window_hours": window_hours,
            },
        )
