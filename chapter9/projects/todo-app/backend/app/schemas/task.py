from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, field_validator


class TaskCreate(BaseModel):
    title: str
    note: Optional[str] = None
    priority: Literal["high", "normal", "low"] = "normal"
    tags: list[str] = []

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title must not be blank")
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    note: Optional[str] = None
    priority: Optional[Literal["high", "normal", "low"]] = None
    status: Optional[Literal["active", "done"]] = None
    tags: Optional[list[str]] = None

    @field_validator("title", mode="before")
    @classmethod
    def title_not_blank(cls, v):
        if v is None:
            return v
        if not str(v).strip():
            raise ValueError("title must not be blank")
        return v


class TaskRead(BaseModel):
    id: int
    title: str
    note: Optional[str]
    priority: str
    status: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}
