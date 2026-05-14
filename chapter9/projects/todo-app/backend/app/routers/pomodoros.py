from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.db import get_session
from app.models.task import Task
from app.models.pomodoro import PomodoroSession
from app.schemas.pomodoro import PomodoroSessionCreate, PomodoroSessionDiscard, PomodoroSessionRead, PomodoroNextPhase

router = APIRouter(prefix="/pomodoros", tags=["pomodoros"])

_FOCUS_SEC = 1500
_SHORT_BREAK_SEC = 300
_LONG_BREAK_SEC = 900


@router.post("", status_code=201, response_model=PomodoroSessionRead)
def start_pomodoro(body: PomodoroSessionCreate, session: Session = Depends(get_session)):
    task = session.execute(select(Task).where(Task.id == body.task_id)).scalar_one_or_none()
    if task is None or task.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Task not found")

    active = session.execute(
        select(PomodoroSession).where(PomodoroSession.ended_at.is_(None))
    ).scalar_one_or_none()
    if active is not None:
        raise HTTPException(status_code=409, detail=f"Active session already exists: id={active.id}")

    ps = PomodoroSession(
        task_id=body.task_id,
        phase=body.phase,
        planned_duration_sec=body.planned_duration_sec,
    )
    session.add(ps)
    session.commit()
    session.refresh(ps)
    return ps


@router.get("/active", response_model=PomodoroSessionRead)
def get_active_pomodoro(session: Session = Depends(get_session)):
    active = session.execute(
        select(PomodoroSession).where(PomodoroSession.ended_at.is_(None))
    ).scalar_one_or_none()
    if active is None:
        raise HTTPException(status_code=404, detail="No active session")
    return active


@router.get("/next-phase", response_model=PomodoroNextPhase)
def get_next_phase(session: Session = Depends(get_session)) -> PomodoroNextPhase:
    recent = session.execute(
        select(PomodoroSession)
        .where(PomodoroSession.ended_at.is_not(None))
        .order_by(PomodoroSession.ended_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if recent is None:
        return PomodoroNextPhase(phase="focus", planned_duration_sec=_FOCUS_SEC)
    if recent.phase == "focus" and recent.end_reason == "completed":
        last_long_id = session.execute(
            select(PomodoroSession.id)
            .where(PomodoroSession.phase == "long_break", PomodoroSession.ended_at.is_not(None))
            .order_by(PomodoroSession.id.desc())
            .limit(1)
        ).scalar_one_or_none() or 0
        completed_focus = session.execute(
            select(func.count(PomodoroSession.id))
            .where(
                PomodoroSession.phase == "focus",
                PomodoroSession.end_reason == "completed",
                PomodoroSession.id > last_long_id,
            )
        ).scalar_one()
        if completed_focus > 0 and completed_focus % 4 == 0:
            return PomodoroNextPhase(phase="long_break", planned_duration_sec=_LONG_BREAK_SEC)
        return PomodoroNextPhase(phase="short_break", planned_duration_sec=_SHORT_BREAK_SEC)
    return PomodoroNextPhase(phase="focus", planned_duration_sec=_FOCUS_SEC)


@router.post("/{pomodoro_id}/end", response_model=PomodoroSessionRead)
def end_pomodoro(pomodoro_id: int, session: Session = Depends(get_session)):
    ps = session.get(PomodoroSession, pomodoro_id)
    if ps is None:
        raise HTTPException(status_code=404, detail="Pomodoro session not found")
    if ps.ended_at is not None:
        raise HTTPException(status_code=409, detail=f"Pomodoro session already ended: id={ps.id}")
    ps.ended_at = datetime.now(timezone.utc)
    ps.end_reason = "completed"
    session.commit()
    session.refresh(ps)
    return ps


@router.post("/{pomodoro_id}/discard", response_model=PomodoroSessionRead)
def discard_pomodoro(pomodoro_id: int, body: PomodoroSessionDiscard, session: Session = Depends(get_session)):
    ps = session.get(PomodoroSession, pomodoro_id)
    if ps is None:
        raise HTTPException(status_code=404, detail="Pomodoro session not found")
    if ps.ended_at is not None:
        raise HTTPException(status_code=409, detail=f"Pomodoro session already ended: id={ps.id}")
    ps.ended_at = datetime.now(timezone.utc)
    ps.end_reason = body.end_reason
    session.commit()
    session.refresh(ps)
    return ps
