from typing import List, Dict, Any
from app.detectors.base import BaseDetector, DetectorOutput
from app.models.transaction import Transaction


class StructuringDetector(BaseDetector):
    """
    Detects repeated transactions that individually remain below
    the configured regulatory threshold but collectively form
    a suspicious pattern within a short time window.
    """

    

    STRUCTURING_MIN = 40000.0
    NEAR_THRESHOLD_MIN = 45000.0
    REGULATORY_THRESHOLD = 50000.0
    WINDOW_DAYS = 7
    MIN_CLUSTER_SIZE = 2

    def run(
        self,
        transactions: List[Transaction],
        case_context: Dict[str, Any] = None
    ) -> DetectorOutput:

        print("\n========== STRUCTURING DEBUG ==========")
        print("TOTAL TRANSACTIONS:", len(transactions))

        for tx in transactions:
            print(
                "DATE:", tx.transaction_date,
                "| AMOUNT:", tx.amount,
                "| DEBIT:", tx.debit,
                "| CREDIT:", tx.credit,
                "| TYPE:", tx.transaction_type,
                "| STATUS:", tx.status,
                "| ACCOUNT:", tx.account_id
            )

        print("========================================\n")

        # ---------------------------------------------------------
        # 1. Load configuration
        # ---------------------------------------------------------
        min_struct = float(
            self.config.get(
                "structuring_min",
                self.STRUCTURING_MIN
            )
        )

        near_threshold_min = float(
            self.config.get(
                "near_threshold_min",
                self.NEAR_THRESHOLD_MIN
            )
        )

        reg_threshold = float(
            self.config.get(
                "regulatory_threshold",
                self.REGULATORY_THRESHOLD
            )
        )

        window_days = int(
            self.config.get(
                "window_days",
                self.WINDOW_DAYS
            )
        )

        min_cluster_size = int(
            self.config.get(
                "min_cluster_size",
                self.MIN_CLUSTER_SIZE
            )
        )

        # ---------------------------------------------------------
        # 2. Keep only successful transactions with valid dates
        # ---------------------------------------------------------
        active_txs = [
            tx
            for tx in self.filter_successful_transactions(transactions)
            if tx.transaction_date
            and tx.amount is not None
            and float(tx.amount) > 0
        ]

        # Sort chronologically
        active_txs.sort(key=lambda tx: tx.transaction_date)

        # ---------------------------------------------------------
        # 3. Select structuring candidates
        #
        # Example:
        # 40,000 <= amount < 50,000
        #
        # Therefore:
        # 42,000 -> candidate
        # 43,000 -> candidate
        # 44,000 -> candidate
        # 50,000 -> NOT candidate
        # 30,000 -> NOT candidate
        # ---------------------------------------------------------
        candidates = [
            tx
            for tx in active_txs
            if min_struct <= float(tx.amount) < reg_threshold
        ]

        # ---------------------------------------------------------
        # 4. Group candidates by account and transaction direction
        #
        # This prevents unrelated accounts/directions from being
        # combined into one structuring cluster.
        # ---------------------------------------------------------
        grouped_candidates = {}

        for tx in candidates:

            account_key = (
                getattr(tx, "account_id", None)
                or getattr(tx, "account_number", None)
                or "UNKNOWN_ACCOUNT"
            )

            transaction_type = (
                getattr(tx, "transaction_type", None)
                or "UNKNOWN"
            ).upper()

            group_key = (
                str(account_key),
                transaction_type
            )

            grouped_candidates.setdefault(group_key, []).append(tx)

        # ---------------------------------------------------------
        # 5. Detect clusters
        # ---------------------------------------------------------
        flagged_clusters = []
        flagged_transaction_ids = set()
        evidence = []

        window_seconds = window_days * 24 * 60 * 60

        for (account_key, transaction_type), account_transactions in grouped_candidates.items():

            account_transactions.sort(
                key=lambda tx: tx.transaction_date
            )

            left = 0

            for right in range(len(account_transactions)):

                current_tx = account_transactions[right]

                # Move left side of sliding window forward
                while (
                    left < right
                    and (
                        current_tx.transaction_date
                        - account_transactions[left].transaction_date
                    ).total_seconds() > window_seconds
                ):
                    left += 1

                cluster = account_transactions[left:right + 1]

                # Need at least 2 transactions
                if len(cluster) < min_cluster_size:
                    continue

                cluster_ids = tuple(
                    sorted(
                        tx.transaction_id
                        for tx in cluster
                    )
                )

                # Avoid duplicate clusters
                if cluster_ids in flagged_clusters:
                    continue

                flagged_clusters.append(cluster_ids)

                total_amount = sum(
                    float(tx.amount)
                    for tx in cluster
                )

                first_date = cluster[0].transaction_date
                last_date = cluster[-1].transaction_date

                # -------------------------------------------------
                # 6. Record evidence
                # -------------------------------------------------
                for tx in cluster:

                    flagged_transaction_ids.add(
                        tx.transaction_id
                    )

                    amount = float(tx.amount)

                    if amount >= near_threshold_min:
                        proximity = "near regulatory threshold"
                    else:
                        proximity = "below regulatory threshold"

                    evidence.append({
                        "transaction_id": tx.transaction_id,
                        "amount": amount,
                        "transaction_date": tx.transaction_date.isoformat(),
                        "transaction_type": transaction_type,
                        "account_id": getattr(
                            tx,
                            "account_id",
                            None
                        ),
                        "account_number": getattr(
                            tx,
                            "account_number",
                            None
                        ),
                        "source_statement": getattr(
                            tx,
                            "source_file",
                            None
                        ),
                        "source_page": getattr(
                            tx,
                            "source_page",
                            None
                        ),
                        "cluster_size": len(cluster),
                        "cluster_total_amount": total_amount,
                        "cluster_start": first_date.isoformat(),
                        "cluster_end": last_date.isoformat(),
                        "reason": (
                            f"₹{amount:,.2f} transaction is part of a "
                            f"{len(cluster)}-transaction {transaction_type} "
                            f"cluster totaling ₹{total_amount:,.2f} "
                            f"within {window_days} days; "
                            f"individual transaction is {proximity} "
                            f"to the ₹{reg_threshold:,.2f} threshold."
                        )
                    })

        # ---------------------------------------------------------
        # 7. Final detector result
        # ---------------------------------------------------------
        triggered = len(flagged_transaction_ids) > 0

        if len(flagged_transaction_ids) >= 3:
            severity = "HIGH"
        elif triggered:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        if triggered:
            reason = (
                f"Detected {len(flagged_transaction_ids)} transaction(s) "
                f"in {len(flagged_clusters)} structuring cluster(s). "
                f"Transactions were between ₹{min_struct:,.2f} and "
                f"below the ₹{reg_threshold:,.2f} regulatory threshold "
                f"within a {window_days}-day window."
            )
        else:
            reason = (
                "No transaction clustering consistent with the "
                "configured structuring rule was identified."
            )

        # ---------------------------------------------------------
        # 8. Return standardized detector output
        # ---------------------------------------------------------
        return DetectorOutput(
            detector_name="STRUCTURING",
            triggered=triggered,
            severity=severity,
            suspicious_transaction_ids=sorted(
                list(flagged_transaction_ids)
            ),
            metrics={
                "window_days": window_days,
                "structuring_min": min_struct,
                "near_threshold_min": near_threshold_min,
                "regulatory_threshold": reg_threshold,
                "min_cluster_size": min_cluster_size,
                "candidates_count": len(candidates),
                "clusters_count": len(flagged_clusters),
                "total_flagged_transactions": len(
                    flagged_transaction_ids
                ),
            },
            reason=reason,
            evidence=evidence,
            configuration_used={
                "structuring_min": min_struct,
                "near_threshold_min": near_threshold_min,
                "regulatory_threshold": reg_threshold,
                "window_days": window_days,
                "min_cluster_size": min_cluster_size,
            },
        )