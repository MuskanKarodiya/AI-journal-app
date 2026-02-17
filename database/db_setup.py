"""
Database setup utilities for the AI journaling app.

This module provides:
    - init_database(): create the SQLite database, tables, and seed data.
    - get_session(): obtain a SQLAlchemy session for running queries.
"""

from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from config import DATABASE_PATH
from .models import Base, ReflectionPrompt


_engine = None
_SessionLocal: Optional[sessionmaker[Session]] = None


def _get_engine():
    """Create (or return) a singleton SQLAlchemy engine for the SQLite database."""
    global _engine

    if _engine is None:
        # Ensure the database directory exists
        db_dir = os.path.dirname(DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        database_url = f"sqlite:///{DATABASE_PATH}"
        print(f"[DB] Using SQLite database at: {DATABASE_PATH}")

        _engine = create_engine(
            database_url,
            echo=False,
            future=True,
        )

    return _engine


def init_database() -> str:
    """
    Initialize the SQLite database and seed it with reflection prompts.

    - Ensures the database file and directory exist.
    - Creates all tables defined in the SQLAlchemy models if they don't exist.
    - Inserts a default set of reflection prompts if none are present.

    Returns:
        A success message describing what was done.
    """
    global _SessionLocal

    engine = _get_engine()

    try:
        print("[DB] Creating tables (if they do not already exist)...")
        Base.metadata.create_all(bind=engine)

        if _SessionLocal is None:
            _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

        with _SessionLocal() as session:
            # Check if prompts already exist
            existing_count = session.query(ReflectionPrompt).count()
            print(f"[DB] Existing reflection prompts: {existing_count}")

            if existing_count == 0:
                print("[DB] Seeding default reflection prompts...")
                sample_prompts = [
                    ReflectionPrompt(
                        prompt_text="List three things you are grateful for today and why.",
                        category="gratitude",
                    ),
                    ReflectionPrompt(
                        prompt_text="Describe a small win you had recently. How did it make you feel?",
                        category="gratitude",
                    ),
                    ReflectionPrompt(
                        prompt_text="What is one area of your life where you’ve grown in the last year?",
                        category="growth",
                    ),
                    ReflectionPrompt(
                        prompt_text="What is a skill you would like to develop and why?",
                        category="growth",
                    ),
                    ReflectionPrompt(
                        prompt_text="Describe a recent challenge. What did you learn from it?",
                        category="challenge",
                    ),
                    ReflectionPrompt(
                        prompt_text="What is one fear that has been holding you back lately?",
                        category="challenge",
                    ),
                    ReflectionPrompt(
                        prompt_text="If you had a completely free day, how would you spend it creatively?",
                        category="creativity",
                    ),
                    ReflectionPrompt(
                        prompt_text="Write about a time when you surprised yourself with your creativity.",
                        category="creativity",
                    ),
                    ReflectionPrompt(
                        prompt_text="Write a thank-you letter (you don’t have to send it) to someone who impacted you.",
                        category="gratitude",
                    ),
                    ReflectionPrompt(
                        prompt_text="Imagine your best self in five years. What daily habits does that version of you have?",
                        category="growth",
                    ),
                ]

                session.add_all(sample_prompts)
                session.commit()
                print("[DB] Default reflection prompts inserted successfully.")
            else:
                print("[DB] Reflection prompts already present; skipping seeding.")

        message = "Database initialized successfully."
        print(f"[DB] {message}")
        return message

    except SQLAlchemyError as exc:
        error_message = f"Database initialization failed: {exc}"
        print(f"[DB][ERROR] {error_message}")
        return error_message


def get_session() -> Session:
    """
    Create and return a new SQLAlchemy session.

    This helper ensures the engine and session factory are initialized and
    provides a convenient way for the rest of the app to obtain a session.

    Usage example:
        with get_session() as session:
            entries = session.query(JournalEntry).all()

    Returns:
        A `Session` instance bound to the application's SQLite database.
    """
    global _SessionLocal

    engine = _get_engine()

    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    print("[DB] Creating a new database session.")
    return _SessionLocal()
