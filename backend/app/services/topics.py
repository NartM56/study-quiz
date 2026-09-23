from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.study_models import Topic


def get_or_create_topic(db: Session, name: str) -> Topic:
    """Find a Topic by exact (normalized) name, or create one if it doesn't exist yet."""
    normalized = name.strip()

    existing = db.scalar(select(Topic).where(Topic.name == normalized))
    if existing is not None:
        return existing

    topic = Topic(name=normalized)
    db.add(topic)
    db.flush()  # assigns topic.id without committing — caller commits alongside the rest
    return topic
