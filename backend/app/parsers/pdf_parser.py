import fitz  # PyMuPDF
import pdfplumber
import re
import io
from PIL import Image
from typing import List, Dict, Any, Optional
from app.parsers.base import BaseStatementParser, ParseResult, RawTransactionRow
from app.parsers.csv_parser import CsvStatementParser
from app.parsers.ocr_engine import OcrEngine
from app.utils.logger import logger


class PdfStatementParser(BaseStatementParser):
    def parse(self, file_path: str, original_filename: str) -> ParseResult:
        transactions: List[RawTransactionRow] = []
        errors = []
        bank_name = None
        account_number = None
        account_holder = None
        full_doc_text = []
        extraction_methods_used = set()

        csv_helper = CsvStatementParser()

        # Step 1: Open with PyMuPDF to inspect text layer and metadata
        doc = fitz.open(file_path)
        page_count = len(doc)

        for page_idx in range(page_count):
            page_num = page_idx + 1
            page = doc[page_idx]
            page_text = page.get_text()
            full_doc_text.append(f"--- Page {page_num} ---\n{page_text}")

            # Extract header metadata from early text
            if not account_number:
                m_acc = re.search(r"account\s*(?:no|number|#)?[:\s]+([0-9xX]+)", page_text, re.I)
                if m_acc:
                    account_number = m_acc.group(1).strip()
            if not bank_name:
                for b in ["HDFC", "SBI", "ICICI", "Axis", "Citibank", "Chase", "HSBC", "Bank of America", "Barclays", "Standard Chartered", "Kotak", "Punjab National Bank"]:
                    if b.lower() in page_text.lower():
                        bank_name = b
                        break
            if not account_holder:
                m_name = re.search(r"(?:account\s*name|name\s*of\s*holder|account\s*holder)[:\s]+([A-Za-z\s.]+)", page_text, re.I)
                if m_name and len(m_name.group(1).strip()) > 2:
                    account_holder = m_name.group(1).strip()

        doc.close()

        # Step 2: Try structured extraction using pdfplumber
        structured_success = False
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    page_num = page_idx + 1
                    tables = page.extract_tables()

                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        # Find header row
                        header_row_idx = -1
                        col_indices = {}

                        for r_idx, row in enumerate(table[:5]):
                            row_clean = [str(c).strip().lower() if c else "" for c in row]
                            matched = csv_helper._map_header_indices(row_clean)
                            if ("date" in matched or "description" in matched) and ("debit" in matched or "credit" in matched or "amount" in matched):
                                header_row_idx = r_idx
                                col_indices = matched
                                break

                        if header_row_idx != -1:
                            structured_success = True
                            extraction_methods_used.add("STRUCTURED_PDF")

                            for row in table[header_row_idx + 1:]:
                                if not row or not any(row):
                                    continue

                                desc_val = str(row[col_indices["description"]]).strip() if "description" in col_indices and col_indices["description"] < len(row) and row[col_indices["description"]] else ""
                                if any(k in desc_val.lower() for k in ["total", "opening balance", "closing balance"]):
                                    continue

                                raw_date = str(row[col_indices["date"]]).strip() if "date" in col_indices and col_indices["date"] < len(row) and row[col_indices["date"]] else None
                                ref_val = str(row[col_indices["reference"]]).strip() if "reference" in col_indices and col_indices["reference"] < len(row) and row[col_indices["reference"]] else None
                                debit_val = str(row[col_indices["debit"]]).strip() if "debit" in col_indices and col_indices["debit"] < len(row) and row[col_indices["debit"]] else None
                                credit_val = str(row[col_indices["credit"]]).strip() if "credit" in col_indices and col_indices["credit"] < len(row) and row[col_indices["credit"]] else None
                                amount_val = str(row[col_indices["amount"]]).strip() if "amount" in col_indices and col_indices["amount"] < len(row) and row[col_indices["amount"]] else None
                                bal_val = str(row[col_indices["balance"]]).strip() if "balance" in col_indices and col_indices["balance"] < len(row) and row[col_indices["balance"]] else None

                                if raw_date or desc_val or debit_val or credit_val:
                                    transactions.append(RawTransactionRow(
                                        raw_date=raw_date,
                                        description=desc_val,
                                        reference_number=ref_val,
                                        debit_str=debit_val,
                                        credit_str=credit_val,
                                        amount_str=amount_val,
                                        balance_str=bal_val,
                                        source_page=page_num,
                                        raw_text=" | ".join([str(c) for c in row if c]),
                                    ))
        except Exception as pdfplumber_err:
            errors.append(f"pdfplumber structured extraction notice: {str(pdfplumber_err)}")

        # Step 3: If structured table extraction yielded nothing or PDF is scanned/image-based
        if not transactions:
            logger.info(f"Structured table extraction found 0 rows. Attempting line parsing and OCR fallback on {file_path}")
            # Try line-based parsing on digital text first
            doc = fitz.open(file_path)
            for page_idx in range(page_count):
                page_num = page_idx + 1
                page = doc[page_idx]
                page_text = page.get_text()

                if len(page_text.strip()) > 50:
                    # Digital text lines
                    parsed_lines = OcrEngine.parse_tabular_lines_from_ocr(page_text, page_num=page_num)
                    if parsed_lines:
                        extraction_methods_used.add("PYMUPDF_TEXT")
                        for pl in parsed_lines:
                            transactions.append(RawTransactionRow(
                                raw_date=pl.get("date"),
                                description=pl.get("description", ""),
                                debit_str=pl.get("debit"),
                                credit_str=pl.get("credit"),
                                balance_str=pl.get("balance"),
                                source_page=page_num,
                                raw_text=pl.get("raw_text", ""),
                            ))
                else:
                    # Scanned PDF: Render page pixmap and run OCR
                    extraction_methods_used.add("OCR_SCANNED")
                    try:
                        pix = page.get_pixmap(dpi=200)
                        img_bytes = pix.tobytes("png")
                        pil_img = Image.open(io.BytesIO(img_bytes))
                        ocr_text = OcrEngine.extract_text_from_image(pil_img)
                        parsed_ocr_lines = OcrEngine.parse_tabular_lines_from_ocr(ocr_text, page_num=page_num)
                        for pl in parsed_ocr_lines:
                            transactions.append(RawTransactionRow(
                                raw_date=pl.get("date"),
                                description=pl.get("description", ""),
                                debit_str=pl.get("debit"),
                                credit_str=pl.get("credit"),
                                balance_str=pl.get("balance"),
                                source_page=page_num,
                                raw_text=pl.get("raw_text", ""),
                            ))
                    except Exception as ocr_err:
                        errors.append(f"Page {page_num} OCR error: {str(ocr_err)}")

            doc.close()

        final_method = "+".join(sorted(list(extraction_methods_used))) if extraction_methods_used else "STRUCTURED_PDF"

        return ParseResult(
            transactions=transactions,
            bank_name=bank_name or "Unknown Bank",
            account_number=account_number or "UNKNOWN-ACC",
            account_holder=account_holder,
            page_count=page_count,
            extraction_method=final_method,
            raw_document_text="\n".join(full_doc_text[:10]),
            errors=errors,
        )
