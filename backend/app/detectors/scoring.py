from typing import Dict, List, Any
from app.detectors.base import DetectorOutput


class SuspicionScoringEngine:
    DEFAULT_WEIGHTS = {
        "LARGE_TRANSACTION": 10.0,
        "STRUCTURING": 20.0,
        "TRANSACTION_VELOCITY": 15.0,
        "PASS_THROUGH": 15.0,
        "DORMANT_ACCOUNT_REVIVAL": 10.0,
        "CASH_CYCLING": 15.0,
        "HIGH_RISK_TIME": 5.0,
        "BENEFICIARY_BURST": 10.0,
    }
    SCORING_VERSION = "v1.0-explainable"

    @classmethod
    def calculate_score(
        cls,
        detector_outputs: List[DetectorOutput],
        custom_weights: Dict[str, float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate an explainable Suspicion Score (0 to 100).
        NOTE: This is strictly an Investigation Risk Indicator, NOT a probability of fraud.
        """
        weights = dict(cls.DEFAULT_WEIGHTS)
        if custom_weights:
            weights.update(custom_weights)

        total_score = 0.0
        contributions = {}
        triggered_detectors = []

        for out in detector_outputs:
            weight = weights.get(out.detector_name, 0.0)
            if out.triggered:
                # Scale by severity
                severity_mult = {
                    "LOW": 0.5,
                    "MEDIUM": 0.75,
                    "HIGH": 1.0,
                    "CRITICAL": 1.25,
                }.get(out.severity, 1.0)

                awarded = min(weight, weight * severity_mult)
                total_score += awarded
                contributions[out.detector_name] = round(awarded, 2)
                triggered_detectors.append({
                    "detector": out.detector_name,
                    "severity": out.severity,
                    "contribution": round(awarded, 2),
                    "max_weight": weight,
                    "flagged_transactions_count": len(out.suspicious_transaction_ids),
                })
            else:
                contributions[out.detector_name] = 0.0

        # Cap total at 100.0
        final_score = min(100.0, round(total_score, 1))

        risk_category = "LOW"
        if final_score >= 70:
            risk_category = "CRITICAL"
        elif final_score >= 50:
            risk_category = "HIGH"
        elif final_score >= 25:
            risk_category = "MEDIUM"

        return {
            "suspicion_score": final_score,
            "max_score": 100.0,
            "risk_category": risk_category,
            "score_version": cls.SCORING_VERSION,
            "metric_name": "Suspicion Score (Investigation Risk Indicator)",
            "detector_contributions": contributions,
            "triggered_detectors": triggered_detectors,
            "total_triggered": len(triggered_detectors),
        }
