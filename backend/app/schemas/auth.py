from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2, max_length=150)
    role: str = Field("investigator", pattern="^(admin|investigator|viewer)$")


class LoginRequest(BaseModel):
    username: str
    password: str
