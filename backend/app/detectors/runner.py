from typing import List, Dict, Any
from app.extensions import db
from app.models.case import Case
from app.models.transaction import Transaction
from app.models.detector import DetectorResult, SuspiciousTransaction
from app.models.evidence import EvidenceRecord
from app.detectors.large_transaction import LargeTransactionDetector
from app.detectors.structuring import StructuringDetector
from app.detectors.velocity import TransactionVelocityDetector
from app.detectors.pass_through import PassThroughDetector
from app.detectors.dormant_revival import DormantRevivalDetector
from app.detectors.cash_cycling import CashCyclingDetector
from app.detectors.high_risk_time import HighRiskTimeDetector
from app.detectors.beneficiary_burst import BeneficiaryBurstDetector
from app.detectors.scoring import SuspicionScoringEngine
from app.utils.logger import logger


class DetectorRunner:
    @staticmethod
    def run_all_detectors(case_id: str, custom_configs: Dict[str, Any] = None) -> Dict[str, Any]:
        case = db.session.get(Case, case_id)
        if not case:
            raise ValueError("Case not found.")

        custom_configs = custom_configs or {}
        transactions = Transaction.query.filter_by(case_id=case_id).all()

        detectors = [
            LargeTransactionDetector(custom_configs.get("LARGE_TRANSACTION")),
            StructuringDetector(custom_configs.get("STRUCTURING")),
            TransactionVelocityDetector(custom_configs.get("TRANSACTION_VELOCITY")),
            PassThroughDetector(custom_configs.get("PASS_THROUGH")),
            DormantRevivalDetector(custom_configs.get("DORMANT_ACCOUNT_REVIVAL")),
            CashCyclingDetector(custom_configs.get("CASH_CYCLING")),
            HighRiskTimeDetector(custom_configs.get("HIGH_RISK_TIME")),
            BeneficiaryBurstDetector(custom_configs.get("BENEFICIARY_BURST")),
        ]

        # Clear existing detector results and suspicious transactions for re-analysis
        DetectorResult.query.filter_by(case_id=case_id).delete()
        SuspiciousTransaction.query.filter_by(case_id=case_id).delete()
        EvidenceRecord.query.filter_by(case_id=case_id, entity_type="DETECTOR").delete()

        detector_outputs = []

        for detector in detectors:
            try:
                print("\n🔥 RUNNING DETECTOR:", detector.__class__.__name__)

                output = detector.run(
                    transactions,
                    case_context={"case_number": case.case_number}
                )

                print("✅ FINISHED DETECTOR:", detector.__class__.__name__)
                detector_outputs.append(output)

                # Persist DetectorResult
                res_record = DetectorResult(
                    case_id=case_id,
                    detector_name=output.detector_name,
                    triggered=output.triggered,
                    severity=output.severity,
                    transactions=output.suspicious_transaction_ids,
                    metrics=output.metrics,
                    reason=output.reason,
                    evidence=output.evidence,
                    configuration_used=output.configuration_used,
                )
                db.session.add(res_record)

                # Persist SuspiciousTransaction entries
                for tx_id in output.suspicious_transaction_ids:
                    # Find specific evidence item if available
                    ev_item = next((e for e in output.evidence if e.get("transaction_id") == tx_id), {})
                    susp_tx = SuspiciousTransaction(
                        case_id=case_id,
                        transaction_id=tx_id,
                        detector_name=output.detector_name,
                        severity=output.severity,
                        score_contribution=0.0,
                        reason=ev_item.get("reason", output.reason),
                        evidence_data=ev_item,
                    )
                    db.session.add(susp_tx)

                # Persist into EvidenceRecord for evidence layer
                if output.triggered:
                    ev_rec = EvidenceRecord(
                        case_id=case_id,
                        entity_type="DETECTOR",
                        entity_id=output.detector_name,
                        source=f"Detector:{output.detector_name}",
                        evidence_type=f"PATTERN_{output.detector_name}",
                        evidence_data=output.to_dict(),
                    )
                    db.session.add(ev_rec)

            except Exception as e:
                logger.error(f"Error running detector {detector.__class__.__name__} on case {case_id}: {e}", exc_info=True)

        # Calculate Suspicion Score
        score_data = SuspicionScoringEngine.calculate_score(detector_outputs)

        # Update case
        case.suspicion_score = score_data["suspicion_score"]
        case.score_version = score_data["score_version"]
        case.score_breakdown = score_data

        # Update individual score contributions on SuspiciousTransactions
        for susp in SuspiciousTransaction.query.filter_by(case_id=case_id).all():
            susp.score_contribution = score_data["detector_contributions"].get(susp.detector_name, 0.0)

        db.session.commit()

        logger.info(f"Analysis completed for case {case_id}: Suspicion Score = {score_data['suspicion_score']}")
        return {
            "case_id": case_id,
            "suspicion_score": score_data["suspicion_score"],
            "score_breakdown": score_data,
            "detector_results": [o.to_dict() for o in detector_outputs],
        }
