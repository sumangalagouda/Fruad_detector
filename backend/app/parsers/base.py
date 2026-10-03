from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawTransactionRow:
    raw_date: Optional[str] = None
    value_date: Optional[str] = None
    description: str = ""
    reference_number: Optional[str] = None
    debit_str: Optional[str] = None
    credit_str: Optional[str] = None
    amount_str: Optional[str] = None
    balance_str: Optional[str] = None
    transaction_type_hint: Optional[str] = None
    status_hint: Optional[str] = None
    source_page: int = 1
    raw_text: str = ""
    extra_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    transactions: List[RawTransactionRow]
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    page_count: int = 1
    extraction_method: str = "STRUCTURED"
    raw_document_text: str = ""
    errors: List[str] = field(default_factory=list)


class BaseStatementParser(ABC):
    @abstractmethod
    def parse(self, file_path: str, original_filename: str) -> ParseResult:
        """Parse the bank statement and return raw rows and metadata."""
        pass
