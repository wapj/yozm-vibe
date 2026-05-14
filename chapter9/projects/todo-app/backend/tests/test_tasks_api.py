import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db import get_session
from app.models.tag import Tag
from app.models.task import Task
from app.models.pomodoro import PomodoroSession


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_task_with_two_new_tags(client, db_session):
    response = client.post("/tasks", json={"title": "Test Task", "tags": ["python", "backend"]})
    assert response.status_code == 201
    data = response.json()
    assert "python" in data["tags"]
    assert "backend" in data["tags"]

    tags = db_session.execute(select(Tag)).scalars().all()
    assert len(tags) == 2


def test_create_task_reuses_existing_tag(client, db_session):
    r1 = client.post("/tasks", json={"title": "Task 1", "tags": ["python", "backend"]})
    assert r1.status_code == 201

    tags_after_first = db_session.execute(select(Tag)).scalars().all()
    assert len(tags_after_first) == 2

    r2 = client.post("/tasks", json={"title": "Task 2", "tags": ["python", "newone"]})
    assert r2.status_code == 201

    tags = db_session.execute(select(Tag)).scalars().all()
    assert len(tags) == 3  # python reused, newone added (+1 only)


def test_create_task_empty_title(client):
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 422


def test_create_task_whitespace_title(client):
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 422


def test_create_task_missing_title(client):
    response = client.post("/tasks", json={"note": "no title here"})
    assert response.status_code == 422


def test_list_tasks_empty(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_all_sorted_by_updated_at_desc(client):
    import time
    r1 = client.post("/tasks", json={"title": "First"})
    assert r1.status_code == 201
    time.sleep(0.01)
    r2 = client.post("/tasks", json={"title": "Second"})
    assert r2.status_code == 201

    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == r2.json()["id"]
    assert data[1]["id"] == r1.json()["id"]


def test_list_tasks_excludes_soft_deleted(client):
    r1 = client.post("/tasks", json={"title": "Keep"})
    r2 = client.post("/tasks", json={"title": "Delete"})
    del_id = r2.json()["id"]

    client.delete(f"/tasks/{del_id}")

    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == r1.json()["id"]


def test_delete_task_sets_deleted_at(client, db_session):
    r = client.post("/tasks", json={"title": "To Delete"})
    task_id = r.json()["id"]

    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204

    task = db_session.get(Task, task_id)
    db_session.refresh(task)
    assert task.deleted_at is not None


def test_delete_task_nonexistent_returns_404(client):
    response = client.delete("/tasks/99999")
    assert response.status_code == 404


def test_delete_task_already_deleted_returns_404(client):
    r = client.post("/tasks", json={"title": "Delete Twice"})
    task_id = r.json()["id"]

    client.delete(f"/tasks/{task_id}")
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 404


# --- PATCH /tasks/{id} ---

def test_patch_title_only(client):
    r = client.post("/tasks", json={"title": "Original", "tags": ["a"], "priority": "low"})
    task_id = r.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"title": "Updated"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated"
    assert data["tags"] == ["a"]
    assert data["priority"] == "low"
    assert data["status"] == "active"


def test_patch_priority_and_note(client):
    import time
    r = client.post("/tasks", json={"title": "Task"})
    task_id = r.json()["id"]
    created_at = r.json()["updated_at"]
    time.sleep(0.05)

    resp = client.patch(f"/tasks/{task_id}", json={"priority": "high", "note": "hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["priority"] == "high"
    assert data["note"] == "hello"
    assert data["updated_at"] > created_at


def test_patch_tags_replace(client, db_session):
    from app.models.task import TaskTag
    r = client.post("/tasks", json={"title": "Taggy", "tags": ["a", "b"]})
    task_id = r.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"tags": ["x", "y"]})
    assert resp.status_code == 200
    assert resp.json()["tags"] == ["x", "y"]

    db_session.expire_all()
    links = db_session.execute(
        select(TaskTag).where(TaskTag.task_id == task_id)
    ).scalars().all()
    from app.models.tag import Tag
    linked_names = {db_session.get(Tag, lnk.tag_id).name for lnk in links}
    assert linked_names == {"x", "y"}


def test_patch_tags_empty_removes_all(client):
    r = client.post("/tasks", json={"title": "Tag Task", "tags": ["a", "b"]})
    task_id = r.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"tags": []})
    assert resp.status_code == 200
    assert resp.json()["tags"] == []


def test_patch_status_done_and_revert(client):
    r = client.post("/tasks", json={"title": "Toggle"})
    task_id = r.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["completed_at"] is not None

    resp2 = client.patch(f"/tasks/{task_id}", json={"status": "active"})
    assert resp2.status_code == 200
    assert resp2.json()["completed_at"] is None


def test_patch_blank_title_422(client):
    r = client.post("/tasks", json={"title": "Valid"})
    task_id = r.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"title": "   "})
    assert resp.status_code == 422


def test_patch_nonexistent_404(client):
    resp = client.patch("/tasks/99999", json={"title": "Ghost"})
    assert resp.status_code == 404


def test_patch_soft_deleted_404(client):
    r = client.post("/tasks", json={"title": "Soon Deleted"})
    task_id = r.json()["id"]
    client.delete(f"/tasks/{task_id}")

    resp = client.patch(f"/tasks/{task_id}", json={"title": "Updated"})
    assert resp.status_code == 404


# --- M2-2b2 후속 A: done→done completed_at 불변 ---

def test_patch_done_to_done_completed_at_unchanged(client):
    import time
    r = client.post("/tasks", json={"title": "Done Twice"})
    task_id = r.json()["id"]

    resp1 = client.patch(f"/tasks/{task_id}", json={"status": "done"})
    assert resp1.status_code == 200
    completed_at_first = resp1.json()["completed_at"]
    assert completed_at_first is not None

    time.sleep(0.01)

    resp2 = client.patch(f"/tasks/{task_id}", json={"status": "done"})
    assert resp2.status_code == 200
    assert resp2.json()["completed_at"] == completed_at_first


# --- M3-1: GET /tasks 검색·필터 ---

def test_filter_q_title_match(client):
    client.post("/tasks", json={"title": "Buy groceries"})
    client.post("/tasks", json={"title": "Read a book"})

    resp = client.get("/tasks", params={"q": "groceries"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "groceries" in data[0]["title"]


def test_filter_q_note_match_and_case_insensitive(client):
    client.post("/tasks", json={"title": "Task A", "note": "Important meeting notes"})
    client.post("/tasks", json={"title": "Task B", "note": "nothing special"})

    resp = client.get("/tasks", params={"q": "MEETING"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task A"


def test_filter_tags_and(client):
    client.post("/tasks", json={"title": "Both tags", "tags": ["work", "urgent"]})
    client.post("/tasks", json={"title": "Only work", "tags": ["work"]})
    client.post("/tasks", json={"title": "Only urgent", "tags": ["urgent"]})

    resp = client.get("/tasks", params=[("tags", "work"), ("tags", "urgent")])
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Both tags"


def test_filter_date_preset_today(client, db_session):
    from datetime import datetime, timedelta, timezone

    r_today = client.post("/tasks", json={"title": "Today task"})
    today_id = r_today.json()["id"]

    r_old = client.post("/tasks", json={"title": "Old task"})
    old_id = r_old.json()["id"]

    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    old_task = db_session.get(Task, old_id)
    old_task.created_at = yesterday
    db_session.commit()

    resp = client.get("/tasks", params={"date_preset": "today"})
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()]
    assert today_id in ids
    assert old_id not in ids


def test_filter_date_preset_this_week(client, db_session):
    from datetime import datetime, timedelta, timezone

    r_week = client.post("/tasks", json={"title": "This week task"})
    week_id = r_week.json()["id"]

    r_old = client.post("/tasks", json={"title": "Last week task"})
    old_id = r_old.json()["id"]

    last_week = datetime.now(timezone.utc) - timedelta(days=8)
    old_task = db_session.get(Task, old_id)
    old_task.created_at = last_week
    db_session.commit()

    resp = client.get("/tasks", params={"date_preset": "this_week"})
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()]
    assert week_id in ids
    assert old_id not in ids


def test_filter_status_active(client):
    client.post("/tasks", json={"title": "Active task"})
    r_done = client.post("/tasks", json={"title": "Done task"})
    done_id = r_done.json()["id"]
    client.patch(f"/tasks/{done_id}", json={"status": "done"})

    resp = client.get("/tasks", params={"status": "active"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(t["status"] == "active" for t in data)
    assert any(t["title"] == "Active task" for t in data)
    assert not any(t["id"] == done_id for t in data)


def test_filter_status_done(client):
    client.post("/tasks", json={"title": "Active task"})
    r_done = client.post("/tasks", json={"title": "Done task"})
    done_id = r_done.json()["id"]
    client.patch(f"/tasks/{done_id}", json={"status": "done"})

    resp = client.get("/tasks", params={"status": "done"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(t["status"] == "done" for t in data)
    assert len(data) == 1
    assert data[0]["id"] == done_id


def test_filter_combined_q_and_status(client):
    client.post("/tasks", json={"title": "Fix bug active"})
    r2 = client.post("/tasks", json={"title": "Fix bug done"})
    done_id = r2.json()["id"]
    client.patch(f"/tasks/{done_id}", json={"status": "done"})
    client.post("/tasks", json={"title": "Unrelated active"})

    resp = client.get("/tasks", params={"q": "fix bug", "status": "active"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Fix bug active"


def test_filter_empty_q_ignored(client):
    client.post("/tasks", json={"title": "Task 1"})
    client.post("/tasks", json={"title": "Task 2"})

    resp = client.get("/tasks", params={"q": ""})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# --- M4-2c: date_preset 기준일을 last pomodoro started_at으로 전환 ---

def test_date_preset_today_includes_old_task_with_today_session(client, db_session):
    from datetime import datetime, timedelta, timezone

    # Task A: created_at = 8일 전 → created_at 기준이었다면 제외됐어야 함
    r_a = client.post("/tasks", json={"title": "Old task with today session"})
    task_a_id = r_a.json()["id"]
    task_a = db_session.get(Task, task_a_id)
    task_a.created_at = datetime.now(timezone.utc) - timedelta(days=8)
    db_session.commit()

    # 오늘 시작된 PomodoroSession INSERT
    session_a = PomodoroSession(
        task_id=task_a_id,
        phase="focus",
        started_at=datetime.now(timezone.utc),
        planned_duration_sec=1500,
    )
    db_session.add(session_a)
    db_session.commit()

    resp = client.get("/tasks", params={"date_preset": "today"})
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()]
    assert task_a_id in ids


def test_date_preset_today_falls_back_to_created_at_when_no_sessions(client, db_session):
    from datetime import datetime, timedelta, timezone

    # Task B: created_at = 오늘, 세션 없음 → 포함
    r_b = client.post("/tasks", json={"title": "New task no sessions"})
    task_b_id = r_b.json()["id"]

    # Task C: created_at = 8일 전, 세션 없음 → 미포함
    r_c = client.post("/tasks", json={"title": "Old task no sessions"})
    task_c_id = r_c.json()["id"]
    task_c = db_session.get(Task, task_c_id)
    task_c.created_at = datetime.now(timezone.utc) - timedelta(days=8)
    db_session.commit()

    resp = client.get("/tasks", params={"date_preset": "today"})
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()]
    assert task_b_id in ids
    assert task_c_id not in ids


def test_date_preset_today_excludes_task_with_only_old_sessions(client, db_session):
    from datetime import datetime, timedelta, timezone

    # Task D: created_at = 오늘 + 8일 전 세션만 → COALESCE 결과 = 8일 전 → 미포함
    r_d = client.post("/tasks", json={"title": "Today task but only old sessions"})
    task_d_id = r_d.json()["id"]

    session_d = PomodoroSession(
        task_id=task_d_id,
        phase="focus",
        started_at=datetime.now(timezone.utc) - timedelta(days=8),
        planned_duration_sec=1500,
    )
    db_session.add(session_d)
    db_session.commit()

    resp = client.get("/tasks", params={"date_preset": "today"})
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()]
    assert task_d_id not in ids


def test_date_preset_this_week_uses_last_pomodoro_started_at(client, db_session):
    from datetime import datetime, timedelta, timezone

    # Task E: created_at = 2주 전 + 어제(이번 주) 세션 → 포함
    r_e = client.post("/tasks", json={"title": "Old task with this week session"})
    task_e_id = r_e.json()["id"]
    task_e = db_session.get(Task, task_e_id)
    task_e.created_at = datetime.now(timezone.utc) - timedelta(days=14)
    db_session.commit()

    session_e = PomodoroSession(
        task_id=task_e_id,
        phase="focus",
        started_at=datetime.now(timezone.utc) - timedelta(days=1),
        planned_duration_sec=1500,
    )
    db_session.add(session_e)
    db_session.commit()

    # Task F: created_at = 2주 전, 세션 없음 → 미포함
    r_f = client.post("/tasks", json={"title": "Old task no sessions this week"})
    task_f_id = r_f.json()["id"]
    task_f = db_session.get(Task, task_f_id)
    task_f.created_at = datetime.now(timezone.utc) - timedelta(days=14)
    db_session.commit()

    resp = client.get("/tasks", params={"date_preset": "this_week"})
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()]
    assert task_e_id in ids
    assert task_f_id not in ids
