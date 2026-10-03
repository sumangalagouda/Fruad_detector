from PIL import Image
from app.parsers.base import BaseStatementParser, ParseResult, RawTransactionRow
from app.parsers.ocr_engine import OcrEngine
from app.utils.logger import logger


class ImageStatementParser(BaseStatementParser):
    def parse(self, file_path: str, original_filename: str) -> ParseResult:
        errors = []
        transactions = []
        raw_text = ""

        try:
            pil_img = Image.open(file_path)
            raw_text = OcrEngine.extract_text_from_image(pil_img)
            rows = OcrEngine.parse_tabular_lines_from_ocr(raw_text, page_num=1)
            for r in rows:
                transactions.append(RawTransactionRow(
                    raw_date=r.get("date"),
                    description=r.get("description", ""),
                    debit_str=r.get("debit"),
                    credit_str=r.get("credit"),
                    balance_str=r.get("balance"),
                    source_page=1,
                    raw_text=r.get("raw_text", ""),
                ))
        except Exception as e:
            errors.append(f"Image OCR failure: {str(e)}")

        return ParseResult(
            transactions=transactions,
            bank_name="Image Statement",
            account_number="IMG-ACC-01",
            page_count=1,
            extraction_method="IMAGE_OCR",
            raw_document_text=raw_text,
            errors=errors,
        )
