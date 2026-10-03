import os
import pytest
from app.parsers.csv_parser import CsvStatementParser
from app.parsers.normalizer import TransactionNormalizer
from app.parsers.base import RawTransactionRow


def test_transaction_normalizer_status_classification():
    # Failed
    status = TransactionNormalizer.classify_status("UPI transfer timed out failed to reach beneficiary")
    assert status == "FAILED"

    # Reversed
    status = TransactionNormalizer.classify_status("Auto-reversal of ATM withdrawal")
    assert status == "REVERSED"

    # Returned
    status = TransactionNormalizer.classify_status("Cheque return clearing bounced")
    assert status == "RETURNED"

    # Refunded
    status = TransactionNormalizer.classify_status("Merchant refund credited")
    assert status == "REFUNDED"

    # Normal success
    status = TransactionNormalizer.classify_status("Salary credit for November")
    assert status == "SUCCESS"


def test_transaction_normalizer_row():
    raw_row = RawTransactionRow(
        raw_date="2026-01-15 11:30:00",
        description="Transfer to Vendor Corp a/c 9988776655 via NEFT",
        reference_number="REF-00129",
        debit_str="52000.00",
        credit_str="",
        amount_str="52000.00",
        balance_str="150000.00",
        source_page=1,
    )
    canon, val = TransactionNormalizer.normalize_row(
        row=raw_row,
        case_id="case-1",
        statement_id="stmt-1",
        account_id="acc-1",
        account_number="12345678",
        account_holder="Test Holder",
        bank_name="Test Bank",
        source_file="test.csv",
    )
    assert canon["amount"] == 52000.0
    assert canon["transaction_type"] == "DEBIT"
    assert canon["counterparty_account"] == "9988776655"
    assert val["validation_status"] == "VALID"
