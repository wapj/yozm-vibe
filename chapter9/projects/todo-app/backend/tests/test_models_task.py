from app.models import Task


def test_task_defaults(db_session):
    task = Task(title="Buy groceries")
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.id is not None
    assert task.title == "Buy groceries"
    assert task.priority == "normal"
    assert task.status == "active"
    assert task.deleted_at is None
    assert task.note is None
    assert task.completed_at is None
    assert task.created_at is not None
    assert task.updated_at is not None
