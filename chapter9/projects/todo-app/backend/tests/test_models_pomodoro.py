from datetime import datetime, timezone
from sqlalchemy import select
from app.models import Task, PomodoroSession


def _make_task(db_session, title="Test Task") -> Task:
    task = Task(title=title)
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


def test_pomodoro_session_created_with_id_and_started_at(db_session):
    task = _make_task(db_session)
    session = PomodoroSession(task_id=task.id, phase="focus", planned_duration_sec=1500)
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    assert session.id is not None
    assert session.started_at is not None


def test_pomodoro_session_active_fields_null_by_default(db_session):
    task = _make_task(db_session)
    session = PomodoroSession(task_id=task.id, phase="focus", planned_duration_sec=1500)
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    assert session.ended_at is None
    assert session.end_reason is None


def test_task_pomodoro_session_bidirectional_relationship(db_session):
    task = _make_task(db_session)
    s1 = PomodoroSession(task_id=task.id, phase="focus", planned_duration_sec=1500)
    s2 = PomodoroSession(task_id=task.id, phase="short_break", planned_duration_sec=300)
    db_session.add_all([s1, s2])
    db_session.commit()
    db_session.refresh(task)

    assert len(task.pomodoro_sessions) == 2
    for s in task.pomodoro_sessions:
        assert s.task.id == task.id


def test_sessions_survive_task_soft_delete(db_session):
    task = _make_task(db_session)
    s1 = PomodoroSession(task_id=task.id, phase="focus", planned_duration_sec=1500)
    s2 = PomodoroSession(task_id=task.id, phase="focus", planned_duration_sec=1500)
    db_session.add_all([s1, s2])
    db_session.commit()

    task.deleted_at = datetime.now(timezone.utc)
    db_session.commit()

    sessions = db_session.execute(
        select(PomodoroSession).where(PomodoroSession.task_id == task.id)
    ).scalars().all()
    assert len(sessions) == 2
