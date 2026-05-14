from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class PomodoroNextPhase(BaseModel):
    phase: Literal["focus", "short_break", "long_break"]
    planned_duration_sec: int


class PomodoroSessionCreate(BaseModel):
    task_id: int
    phase: Literal["focus", "short_break", "long_break"]
    planned_duration_sec: int = Field(gt=0)


class PomodoroSessionDiscard(BaseModel):
    end_reason: Literal["abandoned", "discarded"]


class PomodoroSessionRead(BaseModel):
    id: int
    task_id: int
    phase: str
    started_at: datetime
    planned_duration_sec: int
    ended_at: Optional[datetime]
    end_reason: Optional[str]

    model_config = {"from_attributes": True}
