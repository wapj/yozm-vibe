from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.task import Task, TaskTag
from app.models.tag import Tag


def sync_tags(session: Session, task: Task, tag_names: list[str]) -> list[Tag]:
    seen: set[str] = set()
    clean_names: list[str] = []
    for name in tag_names:
        if name and name not in seen:
            seen.add(name)
            clean_names.append(name)

    # Ensure task has an ID before creating TaskTag rows
    session.flush()

    result_tags: list[Tag] = []
    for name in clean_names:
        tag = session.execute(select(Tag).where(Tag.name == name)).scalar_one_or_none()
        if tag is None:
            tag = Tag(name=name)
            session.add(tag)
            session.flush()
        result_tags.append(tag)

    result_tag_ids = {tag.id for tag in result_tags}

    # Remove stale links (entries not in the new list)
    for tt in list(task.task_tags):
        if tt.tag_id not in result_tag_ids:
            session.delete(tt)
    session.flush()

    # Add missing links
    linked_ids = {tt.tag_id for tt in task.task_tags}
    for tag in result_tags:
        if tag.id not in linked_ids:
            session.add(TaskTag(task_id=task.id, tag_id=tag.id))
    session.flush()

    return result_tags
