from sqlalchemy import select
from app.models.task import Task
from app.models.tag import Tag
from app.services.tag_sync import sync_tags


def test_sync_tags_filters_empty_string(db_session):
    task = Task(title="Test")
    db_session.add(task)
    result = sync_tags(db_session, task, ["", "a"])
    db_session.commit()

    assert len(result) == 1
    assert result[0].name == "a"
    tags = db_session.execute(select(Tag)).scalars().all()
    assert len(tags) == 1


def test_sync_tags_deduplicates(db_session):
    task = Task(title="Test")
    db_session.add(task)
    result = sync_tags(db_session, task, ["a", "a"])
    db_session.commit()

    assert len(result) == 1
    tags = db_session.execute(select(Tag)).scalars().all()
    assert len(tags) == 1


def test_sync_tags_removes_stale_links_preserves_tag_row(db_session):
    task = Task(title="Test")
    db_session.add(task)

    sync_tags(db_session, task, ["a", "b"])
    db_session.commit()

    sync_tags(db_session, task, ["b", "c"])
    db_session.commit()

    linked_names = {tt.tag.name for tt in task.task_tags}
    assert linked_names == {"b", "c"}

    all_tag_names = {t.name for t in db_session.execute(select(Tag)).scalars().all()}
    assert "a" in all_tag_names
    assert all_tag_names == {"a", "b", "c"}
