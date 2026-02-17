"""
High-level journal management utilities for the AI journaling app.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone  # ADD timezone here
from typing import Any, Dict, List, Optional

import logging
from sqlalchemy import desc, func, or_
from sqlalchemy.exc import SQLAlchemyError

from database.db_setup import get_session
from database.models import JournalEntry, MoodAnalysis
from utils.mood_analyzer import MoodAnalyzer


logger = logging.getLogger(__name__)


class JournalManager:
    """
    Provide a high-level interface for working with journal entries and mood data.
    """

    def __init__(self) -> None:
        self._mood_analyzer = MoodAnalyzer()
        logger.info("JournalManager initialized.")

    def create_entry(self, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new journal entry and its associated mood analysis.
        """
        if not content or not content.strip():
            return {
                "success": False,
                "entry_id": None,
                "mood": None,
                "error": "Content cannot be empty.",
            }

        word_count = len(content.split())
        now = datetime.now(timezone.utc)  # FIXED: timezone-aware

        session = get_session()

        try:
            logger.info("Creating new journal entry.")
            entry = JournalEntry(
                date=now,
                title=title,
                content=content,
                word_count=word_count,
            )
            session.add(entry)
            session.flush()

            logger.info("Running mood analysis for entry id=%s", entry.id)
            raw_mood = self._mood_analyzer.analyze_entry(content)

            # PERMANENT FIX: Validate and correct mood results
            from utils.emotion_validator import validate_and_fix
            mood_data = validate_and_fix(raw_mood, content)

            mood = MoodAnalysis(
                entry_id=entry.id,
                mood_score=mood_data.get("mood_score", 0.0),
                dominant_emotion=mood_data.get("dominant_emotion", "neutral"),
                confidence=mood_data.get("confidence", 0.0),
                keywords=",".join(mood_data.get("keywords", [])) or None,
            )
            session.add(mood)

            session.commit()
            logger.info("Journal entry created with id=%s", entry.id)

            return {
                "success": True,
                "entry_id": entry.id,
                "mood": mood_data,
                "error": None,
            }
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Failed to create journal entry: %s", exc, exc_info=True)
            return {
                "success": False,
                "entry_id": None,
                "mood": None,
                "error": str(exc),
            }
        finally:
            session.close()

    def get_all_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve the most recent journal entries with their mood data.
        """
        session = get_session()

        try:
            query = (
                session.query(JournalEntry, MoodAnalysis)
                .outerjoin(MoodAnalysis, MoodAnalysis.entry_id == JournalEntry.id)
                .order_by(desc(JournalEntry.date))
                .limit(limit)
            )

            results: List[Dict[str, Any]] = []
            for entry, mood in query.all():
                results.append(self._entry_with_mood_to_dict(entry, mood))

            return results
        except SQLAlchemyError as exc:
            logger.error("Failed to fetch all entries: %s", exc, exc_info=True)
            return []
        finally:
            session.close()

    def get_entry_by_id(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single journal entry by its ID.
        """
        session = get_session()

        try:
            result = (
                session.query(JournalEntry, MoodAnalysis)
                .outerjoin(MoodAnalysis, MoodAnalysis.entry_id == JournalEntry.id)
                .filter(JournalEntry.id == entry_id)
                .order_by(desc(MoodAnalysis.analyzed_at))
                .first()
            )

            if not result:
                return None

            entry, mood = result
            return self._entry_with_mood_to_dict(entry, mood)
        except SQLAlchemyError as exc:
            logger.error("Failed to fetch entry id=%s: %s", entry_id, exc, exc_info=True)
            return None
        finally:
            session.close()

    def update_entry(
        self,
        entry_id: int,
        content: str,
        title: Optional[str] = None,
    ) -> bool:
        """
        Update an existing journal entry and refresh its mood analysis.
        """
        session = get_session()

        try:
            entry = session.get(JournalEntry, entry_id)
            if not entry:
                logger.warning("update_entry: entry id=%s not found.", entry_id)
                return False

            if not content or not content.strip():
                logger.warning("update_entry: empty content for entry id=%s.", entry_id)
                return False

            logger.info("Updating entry id=%s", entry_id)
            entry.content = content
            entry.title = title
            entry.word_count = len(content.split())
            entry.updated_at = datetime.now(timezone.utc)  # FIXED

            raw_mood = self._mood_analyzer.analyze_entry(content)
            from utils.emotion_validator import validate_and_fix
            mood_data = validate_and_fix(raw_mood, content)

            mood = (
                session.query(MoodAnalysis)
                .filter(MoodAnalysis.entry_id == entry_id)
                .order_by(desc(MoodAnalysis.analyzed_at))
                .first()
            )

            if mood is None:
                logger.info("No existing MoodAnalysis for entry id=%s; creating new one.", entry_id)
                mood = MoodAnalysis(
                    entry_id=entry.id,
                    mood_score=mood_data.get("mood_score", 0.0),
                    dominant_emotion=mood_data.get("dominant_emotion", "neutral"),
                    confidence=mood_data.get("confidence", 0.0),
                    keywords=",".join(mood_data.get("keywords", [])) or None,
                )
                session.add(mood)
            else:
                mood.mood_score = mood_data.get("mood_score", mood.mood_score)
                mood.dominant_emotion = mood_data.get("dominant_emotion", mood.dominant_emotion)
                mood.confidence = mood_data.get("confidence", mood.confidence)
                mood.keywords = ",".join(mood_data.get("keywords", [])) or None

            session.commit()
            logger.info("Entry id=%s updated successfully.", entry_id)
            return True
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Failed to update entry id=%s: %s", entry_id, exc, exc_info=True)
            return False
        finally:
            session.close()

    def delete_entry(self, entry_id: int) -> bool:
        """
        Delete a journal entry and its associated mood analyses.
        """
        session = get_session()

        try:
            entry = session.get(JournalEntry, entry_id)
            if not entry:
                logger.warning("delete_entry: entry id=%s not found.", entry_id)
                return False

            logger.info("Deleting entry id=%s", entry_id)
            session.delete(entry)
            session.commit()
            return True
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("Failed to delete entry id=%s: %s", entry_id, exc, exc_info=True)
            return False
        finally:
            session.close()

    def get_mood_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate mood statistics over the last N days.
        """
        session = get_session()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)  # FIXED

        try:
            total_entries = (
                session.query(func.count(JournalEntry.id))
                .filter(JournalEntry.date >= cutoff)
                .scalar()
                or 0
            )

            moods = (
                session.query(
                    MoodAnalysis.mood_score,
                    MoodAnalysis.dominant_emotion,
                    MoodAnalysis.analyzed_at,
                )
                .join(JournalEntry, MoodAnalysis.entry_id == JournalEntry.id)
                .filter(JournalEntry.date >= cutoff)
                .order_by(MoodAnalysis.analyzed_at.asc())
                .all()
            )

            if not moods:
                return {
                    "average_mood_score": None,
                    "emotion_distribution": {},
                    "mood_trend": "stable",
                    "total_entries": total_entries,
                }

            scores = [float(m[0]) for m in moods]
            avg_score = sum(scores) / len(scores)

            distribution: Dict[str, int] = {}
            for _, emotion, _ in moods:
                key = (emotion or "neutral").lower()
                distribution[key] = distribution.get(key, 0) + 1

            mid = len(scores) // 2
            first_avg = sum(scores[:mid]) / max(1, mid)
            second_avg = sum(scores[mid:]) / max(1, len(scores) - mid)
            delta = second_avg - first_avg

            if delta > 0.1:
                trend = "improving"
            elif delta < -0.1:
                trend = "declining"
            else:
                trend = "stable"

            return {
                "average_mood_score": avg_score,
                "emotion_distribution": distribution,
                "mood_trend": trend,
                "total_entries": total_entries,
            }
        except SQLAlchemyError as exc:
            logger.error("Failed to compute mood statistics: %s", exc, exc_info=True)
            return {
                "average_mood_score": None,
                "emotion_distribution": {},
                "mood_trend": "stable",
                "total_entries": 0,
            }
        finally:
            session.close()

    def search_entries(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search for entries containing a keyword.
        """
        if not keyword or not keyword.strip():
            return []

        session = get_session()
        pattern = f"%{keyword.strip()}%"

        try:
            query = (
                session.query(JournalEntry, MoodAnalysis)
                .outerjoin(MoodAnalysis, MoodAnalysis.entry_id == JournalEntry.id)
                .filter(
                    or_(
                        JournalEntry.content.ilike(pattern),
                        JournalEntry.title.ilike(pattern),
                    )
                )
                .order_by(desc(JournalEntry.date))
            )

            return [
                self._entry_with_mood_to_dict(entry, mood) for entry, mood in query.all()
            ]
        except SQLAlchemyError as exc:
            logger.error("Failed to search entries with keyword '%s': %s", keyword, exc, exc_info=True)
            return []
        finally:
            session.close()

    @staticmethod
    def _entry_with_mood_to_dict(
        entry: JournalEntry,
        mood: Optional[MoodAnalysis],
    ) -> Dict[str, Any]:
        """
        Convert a JournalEntry and optional MoodAnalysis into a flat dictionary.
        """
        return {
            "id": entry.id,
            "date": entry.date,
            "title": entry.title,
            "content": entry.content,
            "word_count": entry.word_count,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
            "mood_score": getattr(mood, "mood_score", None),
            "dominant_emotion": getattr(mood, "dominant_emotion", None),
            "confidence": getattr(mood, "confidence", None),
            "keywords": (
                getattr(mood, "keywords", None).split(",")
                if getattr(mood, "keywords", None)
                else []
            ),
            "analyzed_at": getattr(mood, "analyzed_at", None),
        }