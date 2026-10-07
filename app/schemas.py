from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    admin_code: Optional[str] = None  # matches ADMIN_SIGNUP_CODE to register as admin


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class NewsSubmit(BaseModel):
    text: str = Field(..., min_length=10, description="Raw news/article text to check")


class NewsResult(BaseModel):
    id: int
    prediction: str
    confidence: float
    category: str
    is_repeated: bool
    matched_fake_news_id: Optional[int] = None
    similarity_score: Optional[float] = None
    alert_raised: bool


class HistoryItem(BaseModel):
    id: int
    original_text: str
    prediction: str
    confidence: float
    category: Optional[str]
    is_repeated: bool
    checked_at: str


class ReportSubmit(BaseModel):
    text: str = Field(..., min_length=10)
    reason: Optional[str] = None


class ReportItem(BaseModel):
    id: int
    reported_text: str
    reason: Optional[str]
    status: str
    created_at: str


class AlertItem(BaseModel):
    id: int
    fake_news_id: int
    alert_type: str
    message: str
    severity: str
    status: str
    created_at: str


class AdminStats(BaseModel):
    total_checked: int
    fake_count: int
    genuine_count: int
    repeated_count: int
    alerts_count: int
    category_breakdown: dict