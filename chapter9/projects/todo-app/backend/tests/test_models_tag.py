import pytest
from sqlalchemy.exc import IntegrityError
from app.models.tag import Tag


def test_tag_insert_select(db_session):
    tag = Tag(name="work")
    db_session.add(tag)
    db_session.commit()

    result = db_session.get(Tag, tag.id)
    assert result is not None
    assert result.name == "work"


def test_tag_unique_constraint(db_session):
    db_session.add(Tag(name="work"))
    db_session.commit()

    db_session.add(Tag(name="work"))
    with pytest.raises(IntegrityError):
        db_session.commit()
