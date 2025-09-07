from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
import uuid

# Analytics Models
class AnalyticsTrack(BaseModel):
    page: str
    sessionId: str
    userAgent: Optional[str] = None
    referrer: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AnalyticsRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sessionId: str
    page: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    userAgent: Optional[str] = None
    ip: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    referrer: Optional[str] = None

class AnalyticsStats(BaseModel):
    totalViews: int
    uniqueVisitors: int
    popularPages: list
    recentVisitors: list
    countryStats: dict

# Contact Models
class ContactMessage(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    subject: str
    message: str

class ContactRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    firstName: str
    lastName: str
    email: EmailStr
    subject: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "new"  # new, read, replied
    ip: Optional[str] = None

# Newsletter Models
class NewsletterSubscribe(BaseModel):
    email: EmailStr
    name: str

class NewsletterRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    subscribedAt: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"  # active, unsubscribed

# Response Models
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str