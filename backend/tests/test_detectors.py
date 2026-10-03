from datetime import datetime, timedelta
from app.models.transaction import Transaction
from app.detectors import (
    LargeTransactionDetector,
    StructuringDetector,
    TransactionVelocityDetector,
    PassThroughDetector,
    DormantRevivalDetector,
    CashCyclingDetector,
    HighRiskTimeDetector,
    BeneficiaryBurstDetector,
    SuspicionScoringEngine,
)


def make_tx(tx_id, amount, date, tx_type="DEBIT", status="SUCCESS", acc_id="acc-1", acc_num="112233", cp_name="Vendor"):
    return Transaction(
        transaction_id=tx_id,
        statement_id="stmt-1",
        case_id="case-1",
        account_id=acc_id,
        account_number=acc_num,
        bank_name="Test Bank",
        transaction_date=date,
        description=f"Transaction {tx_id}",
        debit=amount if tx_type == "DEBIT" else 0,
        credit=amount if tx_type == "CREDIT" else 0,
        amount=amount,
        balance=100000.0,
        transaction_type=tx_type,
        status=status,
        counterparty_name=cp_name,
        source_file="stmt.csv",
        source_page=1,
    )


def test_large_transaction_detector():
    txs = [
        make_tx("T1", 25000, datetime(2026, 1, 1)),
        make_tx("T2", 75000, datetime(2026, 1, 2)),  # > 50000
    ]
    det = LargeTransactionDetector({"threshold": 50000})
    out = det.run(txs)
    assert out.triggered is True
    assert "T2" in out.suspicious_transaction_ids
    assert "T1" not in out.suspicious_transaction_ids


def test_structuring_detector():
    now = datetime(2026, 1, 10, 10, 0)
    txs = [
        make_tx("S1", 47000, now),
        make_tx("S2", 48000, now + timedelta(days=2)),
        make_tx("S3", 46500, now + timedelta(days=4)),
    ]
    det = StructuringDetector({"structuring_min": 40000, "regulatory_threshold": 50000, "window_days": 7})
    out = det.run(txs)
    assert out.triggered is True
    assert len(out.suspicious_transaction_ids) == 3
    assert "consistent with the configured structuring rule" in out.reason


def test_velocity_detector():
    now = datetime(2026, 1, 10, 10, 0)
    txs = [
        make_tx("V1", 50000, now, tx_type="CREDIT"),
        make_tx("V2", 48000, now + timedelta(minutes=10), tx_type="DEBIT"),  # within 3600s
    ]
    det = TransactionVelocityDetector({"velocity_seconds": 3600})
    out = det.run(txs)
    assert out.triggered is True
    assert "V1" in out.suspicious_transaction_ids
    assert "V2" in out.suspicious_transaction_ids


def test_pass_through_detector():
    now = datetime(2026, 1, 10, 10, 0)
    txs = [
        make_tx("P1", 100000, now, tx_type="CREDIT"),
        make_tx("P2", 95000, now + timedelta(hours=3), tx_type="DEBIT"),  # 95% pass-through
    ]
    det = PassThroughDetector({"min_ratio": 0.90, "max_hours": 48})
    out = det.run(txs)
    assert out.triggered is True


def test_dormant_revival_detector():
    t1 = datetime(2025, 8, 1, 10, 0)
    t2 = datetime(2025, 12, 1, 10, 0)  # > 90 days gap
    txs = [
        make_tx("D1", 10000, t1),
        make_tx("D2", 50000, t2),
    ]
    det = DormantRevivalDetector({"dormant_days": 90, "revival_min_amount": 20000})
    out = det.run(txs)
    assert out.triggered is True
    assert "D2" in out.suspicious_transaction_ids


def test_cash_cycling_detector():
    now = datetime(2026, 1, 10, 10, 0)
    txs = [
        make_tx("C1", 50000, now, tx_type="DEBIT"),
        make_tx("C2", 49000, now + timedelta(hours=6), tx_type="CREDIT"),  # 98% match
    ]
    det = CashCyclingDetector({"window_hours": 24, "match_threshold": 0.80})
    out = det.run(txs)
    assert out.triggered is True


def test_high_risk_time_detector():
    t_unusual = datetime(2026, 1, 10, 2, 30)  # 02:30 AM
    t_normal = datetime(2026, 1, 10, 14, 30)  # 02:30 PM
    txs = [
        make_tx("H1", 25000, t_unusual),
        make_tx("H2", 25000, t_normal),
    ]
    det = HighRiskTimeDetector({"start_hour": 0, "end_hour": 5})
    out = det.run(txs)
    assert out.triggered is True
    assert "H1" in out.suspicious_transaction_ids
    assert "H2" not in out.suspicious_transaction_ids


def test_beneficiary_burst_detector():
    now = datetime(2026, 1, 10, 9, 0)
    txs = [
        make_tx("B1", 10000, now, tx_type="DEBIT", cp_name="Alice"),
        make_tx("B2", 10000, now + timedelta(hours=1), tx_type="DEBIT", cp_name="Bob"),
        make_tx("B3", 10000, now + timedelta(hours=2), tx_type="DEBIT", cp_name="Charlie"),
        make_tx("B4", 10000, now + timedelta(hours=3), tx_type="DEBIT", cp_name="David"),
    ]
    det = BeneficiaryBurstDetector({"min_beneficiaries": 4, "window_hours": 24})
    out = det.run(txs)
    assert out.triggered is True
    assert len(out.suspicious_transaction_ids) == 4
