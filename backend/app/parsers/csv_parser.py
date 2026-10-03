import csv
import io
import re
from typing import List, Dict, Optional
from app.parsers.base import BaseStatementParser, ParseResult, RawTransactionRow
from app.utils.logger import logger


class CsvStatementParser(BaseStatementParser):
    HEADER_MAPPINGS = {
        "date": ["date", "txn date", "transaction date", "trans date", "value date", "posting date"],
        "value_date": ["value date", "val date", "effective date"],
        "description": ["description", "narration", "particulars", "transaction remarks", "details", "memo"],
        "reference": ["ref no", "reference", "ref", "chq no", "cheque no", "utr", "transaction id", "journal no"],
        "debit": ["debit", "dr", "withdrawal", "withdrawals", "amount debited", "dr amount", "debit amount"],
        "credit": ["credit", "cr", "deposit", "deposits", "amount credited", "cr amount", "credit amount"],
        "amount": ["amount", "txn amount", "transaction amount"],
        "type": ["type", "dr/cr", "cr/dr", "d/c"],
        "balance": ["balance", "closing balance", "running balance", "bal", "avail balance"],
        "status": ["status", "txn status", "state"],
    }

    def parse(self, file_path: str, original_filename: str) -> ParseResult:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        bank_name = None
        account_number = None
        account_holder = None
        header_idx = -1
        col_map = {}

        # Look for headers and metadata in the first 25 lines
        for idx, line in enumerate(lines[:25]):
            lower = line.lower()
            # Extract metadata hints if present
            if not account_number:
                m_acc = re.search(r"account\s*(?:no|number|#)?[:\s]+([0-9xX]+)", line, re.I)
                if m_acc:
                    account_number = m_acc.group(1).strip()
            if not bank_name:
                for b in ["HDFC", "SBI", "ICICI", "Axis", "Citibank", "Chase", "HSBC", "Bank of America", "Barclays", "Standard Chartered", "Punjab National Bank", "Kotak"]:
                    if b.lower() in lower:
                        bank_name = b
                        break
            if not account_holder:
                m_name = re.search(r"(?:name|account holder|holder)[:\s]+([A-Za-z\s.]+)", line, re.I)
                if m_name and len(m_name.group(1).strip()) > 2:
                    account_holder = m_name.group(1).strip()

            # Check if this line looks like a column header
            matched_cols = self._detect_columns(line)
            if ("date" in matched_cols or "description" in matched_cols) and ("debit" in matched_cols or "credit" in matched_cols or "amount" in matched_cols):
                header_idx = idx
                col_map = matched_cols
                break

        if header_idx == -1:
            # Fallback: check line 0
            if lines:
                col_map = self._detect_columns(lines[0])
                header_idx = 0

        transactions: List[RawTransactionRow] = []
        errors = []

        if header_idx != -1 and header_idx < len(lines):
            # Read CSV from header line onwards
            csv_content = "".join(lines[header_idx:])
            # Determine dialect/delimiter
            try:
                sample = "".join(lines[header_idx:min(header_idx + 10, len(lines))])
                delimiter = "," if sample.count(",") >= sample.count(";") else ";"
                reader = csv.reader(io.StringIO(csv_content), delimiter=delimiter)
                headers = [h.strip().lower() for h in next(reader, [])]
                
                # Re-map columns from actual header list
                field_indices = self._map_header_indices(headers)

                for row_idx, row in enumerate(reader, start=header_idx + 2):
                    if not row or not any(row):
                        continue
                    try:
                        raw_date = row[field_indices["date"]] if "date" in field_indices and field_indices["date"] < len(row) else None
                        desc = row[field_indices["description"]] if "description" in field_indices and field_indices["description"] < len(row) else ""
                        ref = row[field_indices["reference"]] if "reference" in field_indices and field_indices["reference"] < len(row) else None
                        debit = row[field_indices["debit"]] if "debit" in field_indices and field_indices["debit"] < len(row) else None
                        credit = row[field_indices["credit"]] if "credit" in field_indices and field_indices["credit"] < len(row) else None
                        amount = row[field_indices["amount"]] if "amount" in field_indices and field_indices["amount"] < len(row) else None
                        bal = row[field_indices["balance"]] if "balance" in field_indices and field_indices["balance"] < len(row) else None
                        status = row[field_indices["status"]] if "status" in field_indices and field_indices["status"] < len(row) else None
                        tx_type = row[field_indices["type"]] if "type" in field_indices and field_indices["type"] < len(row) else None

                        # Skip summary rows (e.g. Total, Opening Balance, etc.)
                        if desc and any(k in desc.lower() for k in ["opening balance", "total debits", "total credits", "closing balance"]):
                            continue

                        if raw_date or desc or debit or credit or amount:
                            transactions.append(RawTransactionRow(
                                raw_date=raw_date,
                                description=desc,
                                reference_number=ref,
                                debit_str=debit,
                                credit_str=credit,
                                amount_str=amount,
                                balance_str=bal,
                                transaction_type_hint=tx_type,
                                status_hint=status,
                                source_page=1,
                                raw_text=",".join(row),
                            ))
                    except Exception as row_err:
                        errors.append(f"Row {row_idx} parse warning: {str(row_err)}")
            except Exception as e:
                errors.append(f"CSV read error: {str(e)}")

        return ParseResult(
            transactions=transactions,
            bank_name=bank_name or "Unknown Bank",
            account_number=account_number or "UNKNOWN-ACC",
            account_holder=account_holder,
            page_count=1,
            extraction_method="CSV_STRUCTURED",
            raw_document_text="".join(lines[:100]),
            errors=errors,
        )

    def _detect_columns(self, line: str) -> Dict[str, str]:
        cols = {}
        for canonical, aliases in self.HEADER_MAPPINGS.items():
            for alias in aliases:
                # check if alias is a distinct word in line
                if re.search(r"(?:^|[,;\"\s])" + re.escape(alias) + r"(?:$|[,;\"\s])", line, re.I):
                    cols[canonical] = alias
                    break
        return cols

    def _map_header_indices(self, headers: List[str]) -> Dict[str, int]:
        mapping = {}
        for idx, h in enumerate(headers):
            clean_h = h.strip().lower()
            for canonical, aliases in self.HEADER_MAPPINGS.items():
                if canonical not in mapping:
                    if any(alias == clean_h or alias in clean_h for alias in aliases):
                        mapping[canonical] = idx
        return mapping
