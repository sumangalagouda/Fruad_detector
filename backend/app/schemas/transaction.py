from pydantic import BaseModel
from typing import Optional, List


class TransactionSearchRequest(BaseModel):
    query: Optional[str] = None
    account_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    transaction_type: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 50
