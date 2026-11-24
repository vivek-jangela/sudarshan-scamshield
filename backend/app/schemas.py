from typing import Optional
from pydantic import BaseModel


class MessageIn(BaseModel):
    text: str
    reporter: str = "citizen"
    channel: str = "sms"


class UrlIn(BaseModel):
    url: str
    reporter: str = "citizen"


class WebsiteIn(BaseModel):
    html: Optional[str] = None
    url: Optional[str] = None
    reporter: str = "citizen"


class AssistantIn(BaseModel):
    question: str
    case_id: Optional[int] = None


class StatusIn(BaseModel):
    status: str
