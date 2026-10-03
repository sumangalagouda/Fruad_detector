from pydantic import BaseModel, Field
from typing import Optional


class PersonCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    identifier_type: Optional[str] = None
    identifier_value: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class CaseCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    priority: str = Field("MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    person: PersonCreateRequest


class AccountCreateRequest(BaseModel):
    bank_name: str = Field(..., min_length=2, max_length=150)
    account_number: str = Field(..., min_length=3, max_length=100)
    account_holder: Optional[str] = None
    account_type: str = Field("SAVINGS", pattern="^(SAVINGS|CURRENT|CHECKING|CREDIT)$")
    currency: str = Field("INR", max_length=10)
    branch: Optional[str] = None
