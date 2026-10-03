import re
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional
from app.parsers.base import RawTransactionRow
from app.utils.logger import logger


class TransactionNormalizer:
    COMMON_DATE_FORMATS = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%d-%b-%Y",
        "%d-%b-%y",
        "%d %b %Y",
        "%d %B %Y",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]

    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        clean_date = str(date_str).strip()
        # Remove trailing tz or excess spaces
        clean_date = re.sub(r"\s+[A-Z]{3,4}$", "", clean_date)
        clean_date = re.sub(r"\.000000$", "", clean_date)

        for fmt in TransactionNormalizer.COMMON_DATE_FORMATS:
            try:
                return datetime.strptime(clean_date, fmt)
            except ValueError:
                continue

        # Try heuristic match for standard ISO prefix
        try:
            return datetime.fromisoformat(clean_date)
        except Exception:
            return None

    @staticmethod
    def clean_amount(val: Any) -> float:
        if val is None:
            return 0.0
        val_str = str(val).strip()
        if not val_str or val_str.lower() in ["nan", "none", "-", "", "nil"]:
            return 0.0
        # Remove currency symbols and commas
        cleaned = re.sub(r"[₹$,\sA-Za-z]", "", val_str)
        try:
            return abs(float(cleaned))
        except ValueError:
            return 0.0

    @staticmethod
    def classify_status(description: str, status_hint: Optional[str] = None) -> str:
        text = f"{status_hint or ''} {description}".lower()

        if any(w in text for w in ["failed", "declined", "unsuccessful", "timed out", "reject"]):
            return "FAILED"
        if any(w in text for w in ["reversed", "reversal", "chargeback", "rev txn"]):
            return "REVERSED"
        if any(w in text for w in ["returned", "bounced", "dishonor", "dishonoured", "return chq"]):
            return "RETURNED"
        if any(w in text for w in ["refund", "refunded"]):
            return "REFUNDED"
        if any(w in text for w in ["pending", "in progress", "unposted", "hold", "processing"]):
            return "PENDING"
        if status_hint and status_hint.upper() in ["SUCCESS", "FAILED", "REVERSED", "RETURNED", "REFUNDED", "PENDING", "UNKNOWN"]:
            return status_hint.upper()

        return "SUCCESS"

    @staticmethod
    def extract_counterparty(description: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract (counterparty_name, counterparty_account, counterparty_bank)
        from transaction descriptions (UPI, NEFT, IMPS, RTGS, Transfers).
        """
        name = None
        account = None
        bank = None

        desc = description.strip()

        # Check for UPI: UPI/123456789/PayeeName/Bank or UPI-PayeeName@bank
        m_upi = re.search(r"UPI[-/](?:[0-9]+[-/])?([A-Za-z0-9._\s]+?)(?:/|@|$)", desc, re.I)
        if m_upi:
            candidate = m_upi.group(1).strip()
            if candidate and not candidate.isdigit() and len(candidate) > 2:
                name = candidate

        # Check for NEFT/RTGS/IMPS patterns: NEFT/RTGS/IMPS-UTRN-Name-Account
        m_neft = re.search(r"(?:NEFT|RTGS|IMPS)[-/:\s]+(?:[A-Za-z0-9]+[-/:\s]+)?([A-Za-z\s.]+?)(?:[-/:\s]+|$)", desc, re.I)
        if not name and m_neft:
            candidate = m_neft.group(1).strip()
            if candidate and not candidate.isdigit() and len(candidate) > 2:
                name = candidate

        # Check for "Transfer to / Transfer from"
        m_transfer = re.search(r"transfer\s+(?:to|from)\s+([A-Za-z0-9\s._]+?)(?:\s+a/c|\s+acc|\s+ref|\s*$)", desc, re.I)
        if not name and m_transfer:
            candidate = m_transfer.group(1).strip()
            if candidate and len(candidate) > 2:
                name = candidate

        # Extract account number if present in text
        m_acc = re.search(r"(?:a/c|ac|acc|account)?\s*#?[:\s]*([0-9]{4,18})\b", desc, re.I)
        if m_acc:
            account = m_acc.group(1).strip()

        # Extract known bank mentions
        for b in ["HDFC", "SBI", "ICICI", "Axis", "Citibank", "Chase", "HSBC", "Bank of America", "Barclays", "Standard Chartered", "Kotak", "PNB"]:
            if re.search(rf"\b{b}\b", desc, re.I):
                bank = b
                break

        return name, account, bank

    @staticmethod
    def normalize_row(
        row: RawTransactionRow,
        case_id: str,
        statement_id: str,
        account_id: str,
        account_number: str,
        account_holder: Optional[str],
        bank_name: str,
        source_file: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Normalize a RawTransactionRow to canonical dictionary and validate it.
        Returns: (canonical_dict, validation_dict)
        """
        issues: List[str] = []

        # 1. Parse Date
        tx_date = TransactionNormalizer.parse_date(row.raw_date)
        if not tx_date:
            tx_date = datetime.now()
            issues.append(f"Could not parse valid transaction date from '{row.raw_date}'; defaulted to current timestamp.")

        value_date = TransactionNormalizer.parse_date(row.value_date)

        # 2. Amounts and Dr/Cr
        debit = TransactionNormalizer.clean_amount(row.debit_str)
        credit = TransactionNormalizer.clean_amount(row.credit_str)
        amount = TransactionNormalizer.clean_amount(row.amount_str)
        balance = TransactionNormalizer.clean_amount(row.balance_str) if row.balance_str else None

        # Determine direction

        if debit > 0 and credit == 0:
            tx_type = "DEBIT"
            amount = debit

        elif credit > 0 and debit == 0:
            tx_type = "CREDIT"
            amount = credit

        elif debit == 0 and credit == 0 and amount > 0:
            # Amount exists, but there is no reliable debit/credit direction.
            # Do not guess the direction from the description.
            tx_type = "UNKNOWN"
            issues.append(
                "Transaction direction could not be determined from debit/credit values."
            )

        else:
            # Both debit and credit are zero and no amount is available.
            tx_type = "UNKNOWN"
            amount = 0.0
            issues.append(
                "Transaction has zero or indeterminable amount."
            )

        # Check debit/credit consistency
        if debit > 0 and credit > 0:
            issues.append("Both debit and credit amounts populated; selected higher value.")
            if debit >= credit:
                tx_type = "DEBIT"
                amount = debit
                credit = 0.0
            else:
                tx_type = "CREDIT"
                amount = credit
                debit = 0.0

        # Description and Reference
        description = row.description.strip() if row.description else "Unlabeled Transaction"
        if not row.description:
            issues.append("Missing transaction description.")

        reference_number = row.reference_number
        if not reference_number:
            # Check description for ref/utr/chq
            m_ref = re.search(r"(?:ref|utr|chq|txn)[:\s]+([A-Za-z0-9]{6,25})", description, re.I)
            if m_ref:
                reference_number = m_ref.group(1).strip()
            else:
                issues.append("Missing transaction reference number.")

        # Status
        status = TransactionNormalizer.classify_status(description, row.status_hint)

        # Counterparty
        cp_name, cp_acc, cp_bank = TransactionNormalizer.extract_counterparty(description)

        # Validation status
        val_status = "VALID"
        if any("zero" in i or "Missing transaction description" in i for i in issues):
            val_status = "INVALID"
        elif issues:
            val_status = "WARNING"

        canonical = {
            "case_id": case_id,
            "statement_id": statement_id,
            "account_id": account_id,
            "account_number": account_number,
            "account_holder": account_holder,
            "bank_name": bank_name,
            "transaction_date": tx_date,
            "value_date": value_date,
            "description": description,
            "reference_number": reference_number,
            "debit": debit,
            "credit": credit,
            "amount": amount,
            "balance": balance,
            "transaction_type": tx_type,
            "status": status,
            "counterparty_name": cp_name,
            "counterparty_account": cp_acc,
            "counterparty_bank": cp_bank,
            "source_file": source_file,
            "source_page": row.source_page,
            "raw_text": row.raw_text,
        }

        validation = {
            "validation_status": val_status,
            "issues": issues,
        }

        return canonical, validation
