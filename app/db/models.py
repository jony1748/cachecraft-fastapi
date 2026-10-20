from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TransformCache(Base):
    __tablename__ = "transform_cache"
    __table_args__ = (UniqueConstraint("source_hash", "transform_version", name="uq_transform_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    transform_version: Mapped[str] = mapped_column(String(32), default="uppercase-v1")
    transformed_value: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)


class Payload(Base):
    __tablename__ = "payloads"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    input_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    output: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
