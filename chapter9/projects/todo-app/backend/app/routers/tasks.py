from datetime import datetime, timedelta, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, or_, func
from app.db import get_session
from app.models.task import Task, TaskTag
from app.models.tag import Tag
from app.models.pomodoro import PomodoroSession
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.tag_sync import sync_tags

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _date_preset_floor(preset: str) -> datetime | None:
    now = datetime.now(timezone.utc)
    if preset == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if preset == "this_week":
        monday = now - timedelta(days=now.weekday())
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return None


def _task_to_read(task: Task) -> TaskRead:
    tag_names = sorted(tt.tag.name for tt in task.task_tags)
    return TaskRead(
        id=task.id,
        title=task.title,
        note=task.note,
        priority=task.priority,
        status=task.status,
        tags=tag_names,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
    )


@router.get("", status_code=200, response_model=list[TaskRead])
def list_tasks(
    q: str | None = None,
    tags: list[str] | None = Query(default=None),
    date_preset: Literal["today", "this_week", "all"] | None = None,
    status: Literal["active", "done"] | None = None,
    session: Session = Depends(get_session),
):
    stmt = select(Task).where(Task.deleted_at.is_(None))

    if q is not None and q.strip() != "":
        q_lower = q.lower()
        stmt = stmt.where(
            or_(
                func.lower(Task.title).contains(q_lower),
                func.lower(Task.note).contains(q_lower),
            )
        )

    if tags is not None:
        non_empty_tags = [t for t in tags if t]
        if non_empty_tags:
            subq = (
                select(TaskTag.task_id)
                .join(Tag)
                .where(Tag.name.in_(non_empty_tags))
                .group_by(TaskTag.task_id)
                .having(func.count(func.distinct(Tag.id)) == len(non_empty_tags))
            )
            stmt = stmt.where(Task.id.in_(subq))

    if date_preset and date_preset != "all":
        floor_dt = _date_preset_floor(date_preset)
        if floor_dt is not None:
            last_activity_subq = (
                select(func.max(PomodoroSession.started_at))
                .where(PomodoroSession.task_id == Task.id)
                .correlate(Task.__table__)
                .scalar_subquery()
            )
            stmt = stmt.where(func.coalesce(last_activity_subq, Task.created_at) >= floor_dt)

    if status is not None:
        stmt = stmt.where(Task.status == status)

    stmt = stmt.options(
        selectinload(Task.task_tags).selectinload(TaskTag.tag)
    ).order_by(Task.updated_at.desc())

    tasks = session.execute(stmt).scalars().all()
    return [_task_to_read(t) for t in tasks]


@router.post("", status_code=201, response_model=TaskRead)
def create_task(body: TaskCreate, session: Session = Depends(get_session)):
    task = Task(
        title=body.title,
        note=body.note,
        priority=body.priority,
    )
    session.add(task)
    sync_tags(session, task, body.tags)
    session.commit()
    session.refresh(task)
    return _task_to_read(task)


@router.patch("/{task_id}", status_code=200, response_model=TaskRead)
def update_task(task_id: int, body: TaskUpdate, session: Session = Depends(get_session)):
    task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
    if task is None or task.deleted_at is not None:
        raise HTTPException(status_code=404)

    data = body.model_dump(exclude_unset=True)

    if "title" in data:
        task.title = data["title"]
    if "note" in data:
        task.note = data["note"]
    if "priority" in data:
        task.priority = data["priority"]
    if "status" in data:
        new_status = data["status"]
        if task.status != new_status:
            if new_status == "done":
                task.completed_at = datetime.now(timezone.utc)
            else:
                task.completed_at = None
        task.status = new_status
    if "tags" in data:
        sync_tags(session, task, data["tags"])

    session.commit()
    session.refresh(task)
    return _task_to_read(task)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
    if task is None or task.deleted_at is not None:
        raise HTTPException(status_code=404)
    task.deleted_at = datetime.now(timezone.utc)
    session.commit()
