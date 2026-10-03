from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass, field
from app.models.transaction import Transaction


@dataclass
class DetectorOutput:
    detector_name: str
    triggered: bool
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    suspicious_transaction_ids: List[str]
    metrics: Dict[str, Any]
    reason: str
    evidence: List[Dict[str, Any]]
    configuration_used: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detector": self.detector_name,
            "triggered": self.triggered,
            "severity": self.severity,
            "transactions": self.suspicious_transaction_ids,
            "metrics": self.metrics,
            "reason": self.reason,
            "evidence": self.evidence,
            "configuration_used": self.configuration_used,
        }


class BaseDetector(ABC):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    def run(self, transactions: List[Transaction], case_context: Dict[str, Any] = None) -> DetectorOutput:
        """Execute detection algorithm on transactions and return structured output."""
        pass

    def filter_successful_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Exclude confirmed FAILED, REVERSED, and RETURNED transactions from money-flow detectors.
        PENDING transactions may be evaluated or flagged separately.
        """
        excluded_statuses = {"FAILED", "REVERSED", "RETURNED"}
        return [t for t in transactions if t.status not in excluded_statuses]
