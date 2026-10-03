import cv2
import numpy as np
import os
import re
from typing import List, Tuple, Optional
from PIL import Image
from app.utils.logger import logger

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


class OcrEngine:
    @staticmethod
    def preprocess_image(pil_img: Image.Image) -> Image.Image:
        """
        Preprocess image with OpenCV:
        1. Convert PIL to CV2 BGR
        2. Convert to Grayscale
        3. Denoise and adaptive Otsu thresholding
        4. Return clean PIL Image for OCR
        """
        try:
            cv_img = np.array(pil_img.convert("RGB"))
            cv_img = cv_img[:, :, ::-1].copy()  # RGB to BGR

            # Grayscale
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

            # Denoise
            denoised = cv2.fastNlMeansDenoising(gray, h=10)

            # Otsu thresholding
            _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Convert back to PIL
            return Image.fromarray(thresh)
        except Exception as e:
            logger.warning(f"OpenCV image preprocessing fallback: {e}")
            return pil_img

    @staticmethod
    def extract_text_from_image(pil_img: Image.Image) -> str:
        """Run Tesseract OCR on preprocessed image."""
        if not PYTESSERACT_AVAILABLE:
            return ""

        try:
            processed = OcrEngine.preprocess_image(pil_img)
            text = pytesseract.image_to_string(processed, config="--psm 6")
            return text
        except Exception as e:
            logger.warning(f"Tesseract OCR execution error: {e}")
            return ""

    @staticmethod
    def parse_tabular_lines_from_ocr(raw_text: str, page_num: int = 1) -> List[dict]:
        """
        Extract tabular transaction lines from raw OCR text using regex patterns.
        Handles date, description, amounts, balance.
        """
        rows = []
        date_pattern = re.compile(
            r"(\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b|\b\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4}\b)"
        )
        amount_pattern = re.compile(r"([0-9,]+\.\d{2})")

        for line in raw_text.splitlines():
            line_str = line.strip()
            if not line_str or len(line_str) < 10:
                continue

            date_match = date_pattern.search(line_str)
            if not date_match:
                continue

            raw_date = date_match.group(1)
            remainder = line_str[date_match.end():].strip()

            amounts = amount_pattern.findall(remainder)
            if not amounts:
                continue

            # In typical bank statements: [debit/credit, balance] or [debit, credit, balance]
            debit_val = None
            credit_val = None
            bal_val = None

            cleaned_amounts = [a.replace(",", "") for a in amounts]
            if len(cleaned_amounts) >= 2:
                # determine if dr or cr is mentioned
                if re.search(r"\b(dr|debit|withd)\b", remainder, re.I):
                    debit_val = cleaned_amounts[0]
                    bal_val = cleaned_amounts[-1]
                elif re.search(r"\b(cr|credit|dep)\b", remainder, re.I):
                    credit_val = cleaned_amounts[0]
                    bal_val = cleaned_amounts[-1]
                else:
                    debit_val = cleaned_amounts[0]
                    bal_val = cleaned_amounts[1]
            elif len(cleaned_amounts) == 1:
                debit_val = cleaned_amounts[0]

            desc_part = amount_pattern.sub("", remainder).strip()
            desc_part = re.sub(r"\b(dr|cr)\b", "", desc_part, flags=re.I).strip()

            rows.append({
                "date": raw_date,
                "description": desc_part,
                "debit": debit_val,
                "credit": credit_val,
                "balance": bal_val,
                "page": page_num,
                "raw_text": line_str,
            })

        return rows
