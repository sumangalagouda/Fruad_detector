import pandas as pd
import re
from typing import List
from app.parsers.base import BaseStatementParser, ParseResult, RawTransactionRow
from app.parsers.csv_parser import CsvStatementParser
from app.utils.logger import logger


class ExcelStatementParser(BaseStatementParser):
    def parse(self, file_path: str, original_filename: str) -> ParseResult:
        errors = []
        transactions: List[RawTransactionRow] = []
        bank_name = None
        account_number = None
        account_holder = None

        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_name = excel_file.sheet_names[0]
            df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

            # Look through first 25 rows for headers and metadata
            header_row_idx = -1
            csv_helper = CsvStatementParser()

            for idx in range(min(25, len(df_raw))):
                row_str = " ".join([str(val) for val in df_raw.iloc[idx].dropna()])
                lower = row_str.lower()

                if not account_number:
                    m_acc = re.search(r"account\s*(?:no|number|#)?[:\s]+([0-9xX]+)", row_str, re.I)
                    if m_acc:
                        account_number = m_acc.group(1).strip()
                if not bank_name:
                    for b in ["HDFC", "SBI", "ICICI", "Axis", "Citibank", "Chase", "HSBC", "Bank of America", "Barclays", "Standard Chartered", "Kotak"]:
                        if b.lower() in lower:
                            bank_name = b
                            break
                if not account_holder:
                    m_name = re.search(r"(?:name|account holder|holder)[:\s]+([A-Za-z\s.]+)", row_str, re.I)
                    if m_name and len(m_name.group(1).strip()) > 2:
                        account_holder = m_name.group(1).strip()

                cols = csv_helper._detect_columns(row_str)
                if ("date" in cols or "description" in cols) and ("debit" in cols or "credit" in cols or "amount" in cols):
                    header_row_idx = idx
                    break

            if header_row_idx == -1:
                header_row_idx = 0

            df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=header_row_idx)
            headers = [str(c).strip().lower() for c in df.columns]
            col_indices = csv_helper._map_header_indices(headers)

            for row_idx, row in df.iterrows():
                try:
                    desc_val = str(row.iloc[col_indices["description"]]) if "description" in col_indices and pd.notna(row.iloc[col_indices["description"]]) else ""
                    if any(k in desc_val.lower() for k in ["total", "opening balance", "closing balance"]):
                        continue

                    raw_date = str(row.iloc[col_indices["date"]]) if "date" in col_indices and pd.notna(row.iloc[col_indices["date"]]) else None
                    ref_val = str(row.iloc[col_indices["reference"]]) if "reference" in col_indices and pd.notna(row.iloc[col_indices["reference"]]) else None
                    debit_val = str(row.iloc[col_indices["debit"]]) if "debit" in col_indices and pd.notna(row.iloc[col_indices["debit"]]) else None
                    credit_val = str(row.iloc[col_indices["credit"]]) if "credit" in col_indices and pd.notna(row.iloc[col_indices["credit"]]) else None
                    amount_val = str(row.iloc[col_indices["amount"]]) if "amount" in col_indices and pd.notna(row.iloc[col_indices["amount"]]) else None
                    bal_val = str(row.iloc[col_indices["balance"]]) if "balance" in col_indices and pd.notna(row.iloc[col_indices["balance"]]) else None
                    status_val = str(row.iloc[col_indices["status"]]) if "status" in col_indices and pd.notna(row.iloc[col_indices["status"]]) else None

                    if raw_date or desc_val or debit_val or credit_val or amount_val:
                        transactions.append(RawTransactionRow(
                            raw_date=raw_date,
                            description=desc_val,
                            reference_number=ref_val,
                            debit_str=debit_val,
                            credit_str=credit_val,
                            amount_str=amount_val,
                            balance_str=bal_val,
                            status_hint=status_val,
                            source_page=1,
                            raw_text=" | ".join([f"{k}:{v}" for k, v in row.dropna().items()]),
                        ))
                except Exception as r_err:
                    errors.append(f"Row {row_idx} parse warning: {str(r_err)}")

        except Exception as e:
            errors.append(f"Excel read failure: {str(e)}")

        return ParseResult(
            transactions=transactions,
            bank_name=bank_name or "Unknown Bank",
            account_number=account_number or "UNKNOWN-ACC",
            account_holder=account_holder,
            page_count=1,
            extraction_method="EXCEL_STRUCTURED",
            raw_document_text="",
            errors=errors,
        )
