"""
SQLAlchemy models for the AI journaling app.
"""

from __future__ import annotations

from datetime import datetime, timezone  # ADD timezone here
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class JournalEntry(Base):
    """
    Represents a single journal entry written by the user.
    """

    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # FIXED: Use timezone-aware UTC
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    mood_analyses: Mapped[List["MoodAnalysis"]] = relationship(
        back_populates="entry",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<JournalEntry id={self.id!r} date={self.date!r} title={self.title!r}>"


class MoodAnalysis(Base):
    """
    Stores the AI-generated mood and sentiment analysis for a journal entry.
    """

    __tablename__ = "mood_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    entry_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False,
    )

    mood_score: Mapped[float] = mapped_column(Float, nullable=False)
    dominant_emotion: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # FIXED: Use timezone-aware UTC
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    entry: Mapped["JournalEntry"] = relationship(back_populates="mood_analyses")

    __table_args__ = (
        CheckConstraint("mood_score >= -1.0 AND mood_score <= 1.0", name="ck_mood_score_range"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_confidence_range"),
        CheckConstraint(
            "dominant_emotion IN ('happy', 'sad', 'anxious', 'calm', 'angry', 'neutral')",
            name="ck_dominant_emotion_values",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<MoodAnalysis id={self.id!r} entry_id={self.entry_id!r} "
            f"mood_score={self.mood_score!r}>"
        )


class ReflectionPrompt(Base):
    """
    Stores reusable reflection prompts.
    """

    __tablename__ = "reflection_prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "category IN ('gratitude', 'growth', 'challenge', 'creativity')",
            name="ck_reflection_prompt_category",
        ),
    )

    def __repr__(self) -> str:
        return f"<ReflectionPrompt id={self.id!r} category={self.category!r}>"