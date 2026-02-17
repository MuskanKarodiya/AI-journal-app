"""
Mood analysis utilities using an Ollama-hosted language model.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from config import OLLAMA_API_ENDPOINT, OLLAMA_MODEL_NAME


logger = logging.getLogger(__name__)

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    )


SYSTEM_PROMPT = """Analyze this journal entry for emotional tone. Return ONLY valid JSON.

Rules:
- happy/calm entries MUST have POSITIVE mood_score (0.1 to 1.0)
- sad/anxious/angry entries MUST have NEGATIVE mood_score (-0.1 to -1.0)
- neutral entries have mood_score between -0.1 and 0.1
- Extract meaningful keywords, avoid common words like "today", "really", "because"

Examples:
- "peaceful walk, mindful morning" → {"mood_score": 0.4, "dominant_emotion": "calm", "confidence": 0.85, "keywords": ["peaceful", "mindful", "morning"]}
- "excited and proud of myself" → {"mood_score": 0.9, "dominant_emotion": "happy", "confidence": 0.95, "keywords": ["excited", "proud"]}
- "worried and stressed out" → {"mood_score": -0.6, "dominant_emotion": "anxious", "confidence": 0.85, "keywords": ["worried", "stressed"]}
- "regular uneventful day" → {"mood_score": 0.0, "dominant_emotion": "neutral", "confidence": 0.7, "keywords": ["regular", "uneventful"]}

Respond with EXACTLY this JSON format:
{"mood_score": <-1.0 to 1.0>, "dominant_emotion": "<happy/sad/anxious/calm/angry/neutral>", "confidence": <0 to 1>, "keywords": ["word1", "word2", "word3"]}"""


@dataclass
class MoodResult:
    """Structured representation of the mood analysis result."""

    mood_score: float
    dominant_emotion: str
    confidence: float
    keywords: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mood_score": self.mood_score,
            "dominant_emotion": self.dominant_emotion,
            "confidence": self.confidence,
            "keywords": self.keywords,
        }


class MoodAnalyzer:
    """Analyze journal entries using an Ollama-hosted LLM."""

    def __init__(
        self,
        ollama_model: Optional[str] = None,
        ollama_url: Optional[str] = None,
    ) -> None:
        self.ollama_model = ollama_model or OLLAMA_MODEL_NAME
        self.ollama_url = ollama_url or OLLAMA_API_ENDPOINT
        self._session = requests.Session()
        logger.info(
            "Initialized MoodAnalyzer with model '%s' at '%s'",
            self.ollama_model,
            self.ollama_url,
        )

    def analyze_entry(self, text: str) -> Dict[str, Any]:
        """Analyze a journal entry with optimized settings and consistency checks."""
        if not text or not text.strip():
            logger.warning("analyze_entry called with empty text.")
            return self._neutral_result().to_dict()

        payload = {
            "model": self.ollama_model,
            "prompt": f"{SYSTEM_PROMPT}\n\nJournal entry: \"{text.strip()}\"\n\nJSON response:",
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 150,
                "top_p": 0.9,
                "top_k": 40,
            }
        }

        try:
            logger.info("Sending request to Ollama (20s timeout).")
            response = self._session.post(
                self.ollama_url,
                json=payload,
                timeout=20
            )
            response.raise_for_status()
        except requests.Timeout:
            logger.warning("Ollama timed out - using fallback")
            return self._fallback_analysis(text).to_dict()
        except requests.RequestException as exc:
            logger.error("Ollama API error: %s", exc)
            return self._fallback_analysis(text).to_dict()

        try:
            data = response.json()
        except ValueError:
            logger.error("Ollama response not valid JSON.")
            return self._fallback_analysis(text).to_dict()

        raw_output = data.get("response")
        if not isinstance(raw_output, str):
            logger.error("Missing response text from Ollama.")
            return self._fallback_analysis(text).to_dict()

        try:
            result = self._parse_model_json(raw_output)

            # CRITICAL: Fix any emotion/score inconsistencies
            result = self._fix_emotion_score_consistency(result, text)

            return result.to_dict()
        except Exception as exc:
            logger.error("Failed to parse Ollama JSON: %s - using fallback", exc)
            return self._fallback_analysis(text).to_dict()

    def _fix_emotion_score_consistency(
        self, result: MoodResult, original_text: str
    ) -> MoodResult:
        """
        CRITICAL FIX: Ensure mood_score sign always matches dominant_emotion.

        Fixes cases where AI returns contradictory results like:
        - emotion='calm' but score=-0.8 → corrected to +0.4
        - emotion='neutral' but score=-0.8 → re-analyzed
        - emotion='happy' but score=-0.5 → corrected to +0.5
        """
        emotion = result.dominant_emotion
        score = result.mood_score

        positive_emotions = {"happy", "calm"}
        negative_emotions = {"sad", "anxious", "angry"}

        corrected_score = score

        # FIX 1: Positive emotion with NEGATIVE score → flip to positive
        if emotion in positive_emotions and score < 0:
            corrected_score = abs(score)
            logger.warning(
                "Fixed: emotion='%s' had negative score %.2f → corrected to +%.2f",
                emotion, score, corrected_score
            )

        # FIX 2: Negative emotion with POSITIVE score → flip to negative
        elif emotion in negative_emotions and score > 0:
            corrected_score = -abs(score)
            logger.warning(
                "Fixed: emotion='%s' had positive score %.2f → corrected to %.2f",
                emotion, score, corrected_score
            )

        # FIX 3: Neutral with extreme score → use fallback
        elif emotion == "neutral" and abs(score) > 0.3:
            logger.warning(
                "Neutral emotion with extreme score %.2f → running fallback",
                score
            )
            fallback = self._fallback_analysis(original_text)
            if fallback.dominant_emotion != "neutral":
                return fallback
            else:
                corrected_score = 0.0

        return MoodResult(
            mood_score=corrected_score,
            dominant_emotion=emotion,
            confidence=result.confidence,
            keywords=result.keywords
        )

    def _fallback_analysis(self, text: str) -> MoodResult:
        """
        FAST rule-based mood analysis - instant fallback when AI fails.
        FIXED: Correct signs + whole word matching + better calm detection.
        """
        text_lower = text.lower()

        # Enhanced keyword matching with EXPANDED calm keywords
        emotions = {
            "happy": ["amazing", "excited", "proud", "wonderful", "great", "fantastic",
                     "love", "joy", "thrilled", "excellent", "awesome", "brilliant",
                     "delighted", "happy", "grateful", "blessed", "favorite"],
            "sad": ["sad", "depressed", "unhappy", "disappointed", "miserable",
                   "awful", "terrible", "heartbroken", "devastated"],
            "anxious": ["anxious", "worried", "stressed", "nervous", "overwhelmed",
                       "scared", "fearful", "panic", "tense"],
            "calm": ["calm", "peaceful", "relaxed", "serene", "tranquil",
                    "content", "comfortable", "patient", "grounded",
                    "present", "mindfulness", "mindful", "simple", "gentle",
                    "stillness", "quiet", "steady", "slow"],
            "angry": ["angry", "furious", "irritated", "annoyed", "rage"]
        }

        # Count matches (WHOLE WORD ONLY)
        words = set(w.strip('.,!?;:\'"') for w in text_lower.split())
        match_counts = {}
        for emotion, keywords in emotions.items():
            match_counts[emotion] = sum(1 for kw in keywords if kw in words)

        total_matches = sum(match_counts.values())

        if total_matches == 0:
            dominant = "neutral"
            mood_score = 0.0
            confidence = 0.5
            match_count = 0
        else:
            dominant = max(match_counts, key=match_counts.get)
            match_count = match_counts[dominant]

            # FIXED: Correct score calculation with proper signs
            if dominant == "happy":
                mood_score = min(0.85, match_count * 0.25)  # POSITIVE
                confidence = min(0.85, 0.65 + (match_count * 0.1))
            elif dominant == "calm":
                mood_score = min(0.55, match_count * 0.18)  # POSITIVE but moderate
                confidence = min(0.85, 0.65 + (match_count * 0.1))
            elif dominant in ["sad", "anxious", "angry"]:
                mood_score = max(-0.85, -(match_count * 0.25))  # NEGATIVE
                confidence = min(0.85, 0.65 + (match_count * 0.1))
            else:
                mood_score = 0.0
                confidence = 0.6

            logger.info(
                "Fallback: '%s...' → emotion=%s, score=%.2f, confidence=%.2f",
                text[:40], dominant, mood_score, confidence
            )

        # Extract keywords (WHOLE WORD MATCHING only)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'during', 'have',
            'has', 'had', 'been', 'was', 'were', 'is', 'am', 'are', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my',
            'your', 'his', 'her', 'its', 'our', 'their', 'because', 'really', 'today',
            'just', 'even', 'when', 'not', 'too', 'very', 'so', 'how', 'what', 'when',
            'where', 'who', 'which', 'than', 'then', 'now', 'here', 'there', 'been',
            'myself', 'sometimes', 'went', 'made', 'woke', 'found', 'came', 'went'
        }

        # Emotion keywords found (whole word match)
        found_keywords = []
        for emotion_keywords in emotions.values():
            for kw in emotion_keywords:
                if kw in words and kw not in found_keywords:
                    found_keywords.append(kw)

        # Other meaningful words
        word_list = [w.strip('.,!?;:\'"') for w in text_lower.split()]
        other_words = [
            w for w in word_list
            if len(w) > 4
            and w.isalpha()
            and w not in stop_words
            and w not in found_keywords
        ]

        # Combine keywords
        final_keywords = (found_keywords + other_words)[:5]

        if not final_keywords:
            final_keywords = ["journal", "entry"]

        return MoodResult(
            mood_score=mood_score,
            dominant_emotion=dominant,
            confidence=confidence,
            keywords=final_keywords
        )

    def _parse_model_json(self, raw_text: str) -> MoodResult:
        """Parse the model's raw text output into a MoodResult."""
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            cleaned = match.group(0)

        parsed = json.loads(cleaned)

        mood_score = float(parsed.get("mood_score", 0.0))
        dominant_emotion = str(parsed.get("dominant_emotion", "neutral")).lower()
        confidence = float(parsed.get("confidence", 0.0))
        keywords_raw = parsed.get("keywords", [])

        if isinstance(keywords_raw, str):
            keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        elif isinstance(keywords_raw, list):
            keywords = [str(k).strip() for k in keywords_raw if str(k).strip()]
        else:
            keywords = []

        mood_score = max(-1.0, min(1.0, mood_score))
        confidence = max(0.0, min(1.0, confidence))

        valid_emotions = {"happy", "sad", "anxious", "calm", "angry", "neutral"}
        if dominant_emotion not in valid_emotions:
            dominant_emotion = "neutral"

        return MoodResult(
            mood_score=mood_score,
            dominant_emotion=dominant_emotion,
            confidence=confidence,
            keywords=keywords,
        )

    def _neutral_result(self) -> MoodResult:
        """Return safe neutral fallback."""
        return MoodResult(
            mood_score=0.0,
            dominant_emotion="neutral",
            confidence=0.5,
            keywords=["entry"],
        )

    def get_emotion_color(self, emotion: str) -> str:
        """Map emotion to hex color."""
        color_map = {
            "happy": "#FFE5E5",
            "sad": "#E5F3FF",
            "anxious": "#FFF5E5",
            "calm": "#E5FFE5",
            "angry": "#FFE5F0",
            "neutral": "#F5F5F5",
        }
        return color_map.get((emotion or "").strip().lower(), "#F5F5F5")

    def generate_reflection_prompt(self, recent_moods: List[float]) -> str:
        """Generate reflection prompt based on mood trend."""
        if not recent_moods:
            return (
                "Take a moment to check in with yourself. "
                "How are you really feeling right now, and what do you need?"
            )

        clamped = [max(-1.0, min(1.0, float(m))) for m in recent_moods]
        avg_mood = sum(clamped) / len(clamped)

        if avg_mood >= 0.2:
            return (
                "You've been in a good place lately! "
                "What's contributing to your positive energy, and how can you nurture it?"
            )
        if avg_mood <= -0.2:
            return (
                "I notice you've been going through a tough time. "
                "What's one small thing that brought you comfort or relief recently?"
            )

        return (
            "Your recent days seem a bit mixed. "
            "What patterns do you notice in your mood, and is there one small change "
            "you'd like to try this week?"
        )