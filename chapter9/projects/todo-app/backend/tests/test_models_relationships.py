from sqlalchemy import select
from app.models.task import Task, TaskTag
from app.models.tag import Tag


def test_task_with_two_tags(db_session):
    task = Task(title="Test Task")
    tag1 = Tag(name="tag1")
    tag2 = Tag(name="tag2")
    db_session.add_all([task, tag1, tag2])
    db_session.flush()

    db_session.add(TaskTag(task_id=task.id, tag_id=tag1.id))
    db_session.add(TaskTag(task_id=task.id, tag_id=tag2.id))
    db_session.commit()

    db_session.refresh(task)
    assert len(task.task_tags) == 2


def test_task_delete_cascades_to_task_tags(db_session):
    task = Task(title="Test Task")
    tag = Tag(name="tag1")
    db_session.add_all([task, tag])
    db_session.flush()

    db_session.add(TaskTag(task_id=task.id, tag_id=tag.id))
    db_session.commit()

    task_id = task.id
    tag_id = tag.id

    db_session.delete(task)
    db_session.commit()

    task_tag = db_session.execute(
        select(TaskTag).where(TaskTag.task_id == task_id)
    ).scalar_one_or_none()
    assert task_tag is None

    surviving_tag = db_session.get(Tag, tag_id)
    assert surviving_tag is not None
