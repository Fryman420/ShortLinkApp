from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime

class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: str | None = Field(None, description="Опциональный alias для короткой ссылки")
    expires_at: datetime | None = Field(None, description="Время истечения ссылки (с точностью до минуты)")

class LinkUpdate(BaseModel):
    original_url: HttpUrl

class LinkStats(BaseModel):
    original_url: HttpUrl
    created_at: datetime
    expires_at: datetime | None
    clicks: int
    last_accessed_at: datetime | None


class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str