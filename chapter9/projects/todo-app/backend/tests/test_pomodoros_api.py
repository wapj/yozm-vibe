from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_session
from app.models.task import Task
from app.models.pomodoro import PomodoroSession


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _make_task(db_session, title="Test Task") -> Task:
    task = Task(title=title)
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


# 1. POST /pomodoros with valid task + focus + 1500 → 201
def test_create_pomodoro_valid(client, db_session):
    task = _make_task(db_session)
    resp = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["task_id"] == task.id
    assert data["phase"] == "focus"
    assert data["started_at"] is not None
    assert data["ended_at"] is None
    assert data["end_reason"] is None


# 2. POST with non-existent task_id → 404
def test_create_pomodoro_task_not_found(client):
    resp = client.post("/pomodoros", json={"task_id": 9999, "phase": "focus", "planned_duration_sec": 1500})
    assert resp.status_code == 404


# 3. POST with soft-deleted task → 404
def test_create_pomodoro_deleted_task(client, db_session):
    task = _make_task(db_session)
    task.deleted_at = datetime.now(timezone.utc)
    db_session.commit()

    resp = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
    assert resp.status_code == 404


# 4. POST with invalid phase → 422
def test_create_pomodoro_invalid_phase(client, db_session):
    task = _make_task(db_session)
    resp = client.post("/pomodoros", json={"task_id": task.id, "phase": "invalid", "planned_duration_sec": 1500})
    assert resp.status_code == 422


# 5. POST with planned_duration_sec=0 → 422
def test_create_pomodoro_zero_duration(client, db_session):
    task = _make_task(db_session)
    resp = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 0})
    assert resp.status_code == 422


# 6. POST twice without ending first → second is 409
def test_create_pomodoro_duplicate_active(client, db_session):
    task = _make_task(db_session)
    r1 = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
    assert r1.status_code == 201

    r2 = client.post("/pomodoros", json={"task_id": task.id, "phase": "short_break", "planned_duration_sec": 300})
    assert r2.status_code == 409


# 7. GET /pomodoros/active with active session → 200 + session body
def test_get_active_pomodoro_exists(client, db_session):
    task = _make_task(db_session)
    r = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
    assert r.status_code == 201
    created_id = r.json()["id"]

    resp = client.get("/pomodoros/active")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == created_id
    assert data["ended_at"] is None


# 8. GET /pomodoros/active with no active session → 404
def test_get_active_pomodoro_none(client):
    resp = client.get("/pomodoros/active")
    assert resp.status_code == 404


# 9. GET /pomodoros/active with only ended sessions → 404
def test_get_active_pomodoro_only_ended(client, db_session):
    task = _make_task(db_session)
    ps = PomodoroSession(
        task_id=task.id,
        phase="focus",
        planned_duration_sec=1500,
        ended_at=datetime.now(timezone.utc),
        end_reason="completed",
    )
    db_session.add(ps)
    db_session.commit()

    resp = client.get("/pomodoros/active")
    assert resp.status_code == 404


# M4-2b tests


def _make_active_session(client, db_session, title="Task for End Test"):
    task = _make_task(db_session, title=title)
    r = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
    assert r.status_code == 201
    return task, r.json()


# 10. POST /pomodoros/{id}/end on active session → 200, ended_at not None, end_reason == "completed"
def test_end_active_session(client, db_session):
    task, ps_data = _make_active_session(client, db_session)
    pid = ps_data["id"]

    resp = client.post(f"/pomodoros/{pid}/end")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == pid
    assert data["task_id"] == task.id
    assert data["ended_at"] is not None
    assert data["end_reason"] == "completed"


# 11. POST /pomodoros/{id}/end non-existent id → 404
def test_end_session_not_found(client):
    resp = client.post("/pomodoros/99999/end")
    assert resp.status_code == 404


# 12. POST /pomodoros/{id}/end already ended session → 409
def test_end_already_ended_session(client, db_session):
    task, ps_data = _make_active_session(client, db_session, title="Task End 409")
    pid = ps_data["id"]

    client.post(f"/pomodoros/{pid}/end")
    resp = client.post(f"/pomodoros/{pid}/end")
    assert resp.status_code == 409
    assert f"id={pid}" in resp.json()["detail"]


# 13. POST /pomodoros/{id}/discard with end_reason="abandoned" → 200
def test_discard_session_abandoned(client, db_session):
    _, ps_data = _make_active_session(client, db_session, title="Task Abandon")
    pid = ps_data["id"]

    resp = client.post(f"/pomodoros/{pid}/discard", json={"end_reason": "abandoned"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["end_reason"] == "abandoned"
    assert data["ended_at"] is not None


# 14. POST /pomodoros/{id}/discard with end_reason="discarded" → 200
def test_discard_session_discarded(client, db_session):
    _, ps_data = _make_active_session(client, db_session, title="Task Discard")
    pid = ps_data["id"]

    resp = client.post(f"/pomodoros/{pid}/discard", json={"end_reason": "discarded"})
    assert resp.status_code == 200
    assert resp.json()["end_reason"] == "discarded"


# 15. POST /pomodoros/{id}/discard with invalid end_reason → 422
def test_discard_session_invalid_reason(client, db_session):
    _, ps_data = _make_active_session(client, db_session, title="Task Invalid Reason")
    pid = ps_data["id"]

    resp = client.post(f"/pomodoros/{pid}/discard", json={"end_reason": "invalid"})
    assert resp.status_code == 422


# 16. POST /pomodoros/{id}/discard with empty body → 422
def test_discard_session_missing_body(client, db_session):
    _, ps_data = _make_active_session(client, db_session, title="Task Missing Body")
    pid = ps_data["id"]

    resp = client.post(f"/pomodoros/{pid}/discard", json={})
    assert resp.status_code == 422


# 17. POST /pomodoros/{id}/discard non-existent id → 404
def test_discard_session_not_found(client):
    resp = client.post("/pomodoros/99999/discard", json={"end_reason": "abandoned"})
    assert resp.status_code == 404


# 18. POST /pomodoros/{id}/discard already ended session → 409
def test_discard_already_ended_session(client, db_session):
    _, ps_data = _make_active_session(client, db_session, title="Task Discard 409")
    pid = ps_data["id"]

    client.post(f"/pomodoros/{pid}/discard", json={"end_reason": "abandoned"})
    resp = client.post(f"/pomodoros/{pid}/discard", json={"end_reason": "discarded"})
    assert resp.status_code == 409


# 19. After /end, GET /active → 404, then POST /pomodoros → 201 (active lock released)
def test_end_releases_active_lock(client, db_session):
    task, ps_data = _make_active_session(client, db_session, title="Task Lock Release")
    pid = ps_data["id"]

    client.post(f"/pomodoros/{pid}/end")

    active_resp = client.get("/pomodoros/active")
    assert active_resp.status_code == 404

    new_resp = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
    assert new_resp.status_code == 201


# M4-4a tests — GET /pomodoros/next-phase


# 20. Empty DB → focus (1500)
def test_next_phase_empty_db(client):
    resp = client.get("/pomodoros/next-phase")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"phase": "focus", "planned_duration_sec": 1500}


# 21. focus completed 1 time → short_break (300)
def test_next_phase_after_one_focus_completed(client, db_session):
    task = _make_task(db_session)
    r = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
    pid = r.json()["id"]
    client.post(f"/pomodoros/{pid}/end")

    resp = client.get("/pomodoros/next-phase")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"phase": "short_break", "planned_duration_sec": 300}


# 22. focus completed 4 times → long_break (900)
def test_next_phase_after_four_focus_completed(client, db_session):
    task = _make_task(db_session)
    for _ in range(4):
        r = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
        pid = r.json()["id"]
        client.post(f"/pomodoros/{pid}/end")

    resp = client.get("/pomodoros/next-phase")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"phase": "long_break", "planned_duration_sec": 900}


# 23. focus completed + short_break completed → focus (1500)
def test_next_phase_after_break_completed(client, db_session):
    task = _make_task(db_session)
    r1 = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
    client.post(f"/pomodoros/{r1.json()['id']}/end")

    r2 = client.post("/pomodoros", json={"task_id": task.id, "phase": "short_break", "planned_duration_sec": 300})
    client.post(f"/pomodoros/{r2.json()['id']}/end")

    resp = client.get("/pomodoros/next-phase")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"phase": "focus", "planned_duration_sec": 1500}


# 24. focus discarded (abandoned) → focus (1500)
def test_next_phase_after_focus_abandoned(client, db_session):
    task = _make_task(db_session)
    r = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
    pid = r.json()["id"]
    client.post(f"/pomodoros/{pid}/discard", json={"end_reason": "abandoned"})

    resp = client.get("/pomodoros/next-phase")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"phase": "focus", "planned_duration_sec": 1500}


# 25. long_break 종료 후 focus 4회 완주 → 다시 long_break (카운트 리셋 검증)
def test_next_phase_after_long_break_resets_count(client, db_session):
    task = _make_task(db_session)

    # focus 4회 완주
    for _ in range(4):
        r = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
        client.post(f"/pomodoros/{r.json()['id']}/end")

    # long_break 1회 완주
    r = client.post("/pomodoros", json={"task_id": task.id, "phase": "long_break", "planned_duration_sec": 900})
    client.post(f"/pomodoros/{r.json()['id']}/end")

    # 다시 focus 4회 완주
    for _ in range(4):
        r = client.post("/pomodoros", json={"task_id": task.id, "phase": "focus", "planned_duration_sec": 1500})
        client.post(f"/pomodoros/{r.json()['id']}/end")

    resp = client.get("/pomodoros/next-phase")
    assert resp.status_code == 200
    assert resp.json() == {"phase": "long_break", "planned_duration_sec": 900}
