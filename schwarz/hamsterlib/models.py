from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


# Association table for many-to-many relationship between facts and tags
fact_tags = Table(
    "fact_tags",
    Base.metadata,
    Column("fact_id", Integer, ForeignKey("facts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Version(Base):
    __tablename__ = "version"

    version: Mapped[int] = mapped_column(Integer, primary_key=True)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    color_code: Mapped[str | None] = mapped_column(String(50))
    category_order: Mapped[int | None] = mapped_column(Integer)
    search_name: Mapped[str | None] = mapped_column(String(500))

    activities: Mapped[list[Activity]] = relationship(
        "Activity", back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"


class Activity(Base):
    """Specific activities/tasks within categories."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    work: Mapped[int | None] = mapped_column(Integer)
    activity_order: Mapped[int | None] = mapped_column(Integer)
    deleted: Mapped[int | None] = mapped_column(Integer, default=0)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categories.id"))
    search_name: Mapped[str | None] = mapped_column(String(500))

    category: Mapped[Category | None] = relationship("Category", back_populates="activities")
    facts: Mapped[list[Fact]] = relationship(
        "Fact", back_populates="activity", cascade="all, delete-orphan"
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the activity is marked as deleted."""
        return bool(self.deleted)

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, name='{self.name}', category_id={self.category_id})>"


class Tag(Base):
    """Tags that can be applied to time tracking facts."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    autocomplete: Mapped[bool] = mapped_column(Boolean, default=True)

    facts: Mapped[list[Fact]] = relationship("Fact", secondary=fact_tags, back_populates="tags")

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}')>"


class Fact(Base):
    """Time tracking entries (facts) representing work periods."""

    __tablename__ = "facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("activities.id"))
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    description: Mapped[str | None] = mapped_column(String(500))

    activity: Mapped[Activity | None] = relationship("Activity", back_populates="facts")
    tags: Mapped[list[Tag]] = relationship("Tag", secondary=fact_tags, back_populates="facts")

    @property
    def duration(self) -> timedelta | None:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def is_ongoing(self) -> bool:
        return (self.start_time is not None) and (self.end_time is None)

    def __repr__(self) -> str:
        duration = f" ({self.duration})" if self.duration else ""
        return f"<Fact(id={self.id}, activity_id={self.activity_id}, start={self.start_time}{duration})>"
