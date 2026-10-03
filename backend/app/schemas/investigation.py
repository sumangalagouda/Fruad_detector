from pydantic import BaseModel, Field
from typing import Optional


class InvestigateQuestionRequest(BaseModel):
    question: str = Field(..., min_length=2)
    investigation_id: Optional[str] = None


class InvestigatorFeedbackRequest(BaseModel):
    message_id: str
    feedback_type: str = Field(..., pattern="^(Correct|Incorrect|False Positive|Needs Review)$")
    comment: Optional[str] = None
