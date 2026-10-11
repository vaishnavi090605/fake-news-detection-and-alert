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
    text: str = Field(..., min_length=3, description="Raw news/article text to check")
    category: Optional[str] = "General News"
    source_url: Optional[str] = None
    submission_category: Optional[str] = "news_article"  # news_article, social_media_post, forwarded_message
    evidence_link: Optional[str] = None
    user_location: Optional[str] = None


class NewsResult(BaseModel):
    id: int
    prediction: str
    confidence: float
    category: str
    is_repeated: bool
    matched_fake_news_id: Optional[int] = None
    similarity_score: Optional[float] = None
    detection_count: int
    severity: str
    alert_raised: bool
    is_inconclusive: bool = False
    reasons: Optional[list[str]] = None
    user_fake_count: int = 1
    police_escalation: bool = False
    nearest_police_station: Optional[dict] = None
    person_location: Optional[str] = None


class ProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    full_name: Optional[str] = None

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    role: str
    location: Optional[str] = None
    created_at: str

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


class PoliceAlertRequest(BaseModel):
    text: str
    location: Optional[str] = None