from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Emotion keyword definitions (comprehensive)
# ---------------------------------------------------------------------------

EMOTION_KEYWORDS: Dict[str, List[str]] = {
    "happy": [
        "happy", "joy", "joyful", "excited", "excitement", "proud", "pride",
        "wonderful", "amazing", "fantastic", "great", "excellent", "awesome",
        "brilliant", "delighted", "delight", "grateful", "gratitude", "blessed",
        "thrilled", "elated", "cheerful", "content", "pleased", "glad",
        "celebrating", "celebrate", "achievement", "accomplished", "success",
        "love", "loved", "loving", "beautiful", "incredible", "euphoric",
    ],
    "sad": [
        "sad", "sadness", "unhappy", "down", "depressed", "depression",
        "disappointed", "disappointment", "miserable", "misery", "grief",
        "grieving", "heartbroken", "devastated", "devastation", "hopeless",
        "hopelessness", "crying", "cried", "tears", "lonely", "loneliness",
        "loss", "lost", "empty", "emptiness", "heavy", "hurt", "pain",
        "rejected", "rejection", "failure", "failed", "worthless", "helpless",
        "gloomy", "melancholy", "sorrow", "sorrowful", "suffering", "suffer",
        "ache", "aching", "miss", "missing", "missed",
    ],
    "anxious": [
        "anxious", "anxiety", "worried", "worry", "worrying", "stress",
        "stressed", "stressful", "nervous", "nervousness", "overwhelmed",
        "overwhelming", "panic", "panicking", "scared", "fear", "fearful",
        "afraid", "dread", "dreading", "tense", "tension", "uneasy",
        "unease", "restless", "restlessness", "uncertain", "uncertainty",
        "overthinking", "racing", "overthink",
    ],
    "calm": [
        "calm", "peaceful", "peace", "relaxed", "relaxing", "relax",
        "serene", "serenity", "tranquil", "tranquility", "content",
        "contentment", "comfortable", "patient", "patience", "grounded",
        "present", "mindful", "mindfulness", "gentle", "stillness", "still",
        "quiet", "steady", "slow", "breathe", "breathing", "meditate",
        "meditation", "balanced", "harmony", "ease",
    ],
    "angry": [
        "angry", "anger", "furious", "fury", "rage", "raging", "mad",
        "frustrated", "frustration", "irritated", "irritation", "annoyed",
        "annoyance", "outraged", "outrage", "infuriated", "livid", "fuming",
        "resentful", "resentment", "bitter", "bitterness", "hostile",
        "hatred", "hate", "disgusted", "disgust",
    ],
    "neutral": [
        "okay", "fine", "alright", "regular", "normal", "usual", "average",
        "ordinary", "standard", "typical", "moderate", "so-so",
    ],
}


# Score ranges for each emotion
EMOTION_SCORE_RANGES: Dict[str, Tuple[float, float]] = {
    "happy":   (0.2,  1.0),
    "calm":    (0.1,  0.6),
    "neutral": (-0.15, 0.15),
    "anxious": (-0.8, -0.1),
    "sad":     (-0.9, -0.2),
    "angry":   (-0.9, -0.3),
}


def _tokenize(text: str) -> List[str]:
    """
    Tokenize text into lowercase words, stripping punctuation.
    Handles contractions and hyphenated words gracefully.
    """
    text = text.lower()
    # Replace punctuation with spaces
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = text.split()
    return tokens


def _count_emotion_matches(tokens: List[str]) -> Dict[str, int]:
    """
    Count how many emotion keywords appear in the token list.
    Uses WHOLE WORD matching only.
    """
    token_set = set(tokens)
    counts: Dict[str, int] = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        counts[emotion] = sum(1 for kw in keywords if kw in token_set)
    return counts


def _detect_emotion_from_text(text: str) -> Tuple[str, float, float]:
    """
    Detect dominant emotion directly from text using keyword counts.

    Returns:
        Tuple of (dominant_emotion, mood_score, confidence)
    """
    tokens = _tokenize(text)
    counts = _count_emotion_matches(tokens)

    # Remove neutral from primary detection (use as fallback only)
    primary_counts = {e: c for e, c in counts.items() if e != "neutral"}
    total = sum(primary_counts.values())

    if total == 0:
        return "neutral", 0.0, 0.5

    dominant = max(primary_counts, key=primary_counts.get)
    match_count = primary_counts[dominant]

    # Calculate score within the correct range for this emotion
    score_min, score_max = EMOTION_SCORE_RANGES[dominant]
    score_range = score_max - score_min

    # Scale score based on match intensity (more matches = stronger score)
    intensity = min(1.0, match_count / 5.0)  # Cap at 5 matches
    base_score = score_min + (score_range * intensity)
    base_score = round(max(score_min, min(score_max, base_score)), 2)

    # Confidence based on match count
    confidence = min(0.90, 0.55 + (match_count * 0.08))

    logger.info(
        "Text-based detection: emotion=%s, score=%.2f, confidence=%.2f "
        "(matches: %s)",
        dominant, base_score, confidence,
        {e: c for e, c in counts.items() if c > 0}
    )

    return dominant, base_score, confidence


def _extract_quality_keywords(text: str, emotion: str) -> List[str]:
    """
    Extract high-quality keywords from text.

    Prioritizes:
    1. Emotion-specific keywords found in text
    2. Meaningful content words (length > 4, not stop words)
    """
    tokens = _tokenize(text)
    token_set = set(tokens)

    # Stop words to exclude
    stop_words = {
        "the", "and", "for", "are", "but", "not", "you", "all", "can",
        "had", "her", "was", "one", "our", "out", "day", "get", "has",
        "him", "his", "how", "its", "may", "now", "off", "old", "own",
        "say", "she", "too", "use", "way", "who", "with", "this", "that",
        "have", "from", "they", "will", "been", "were", "said", "each",
        "which", "their", "there", "what", "when", "where", "would",
        "make", "like", "into", "just", "know", "take", "than", "them",
        "well", "also", "back", "after", "even", "most", "such", "through",
        "those", "then", "about", "should", "since", "could", "still",
        "really", "today", "because", "right", "always", "never", "every",
        "feel", "feels", "felt", "seem", "seems", "seemed",
        "think", "thought", "trying", "tried", "want", "wanted",
        "went", "made", "came", "went", "woke", "spent", "couldn",
        "didn", "doesn", "isn", "wasn", "hasn", "haven", "hadn",
        "myself", "yourself", "himself", "herself", "itself",
        "sometimes", "something", "anything", "nothing", "everything",
        "though", "although", "while", "since", "until", "unless",
        "pass", "must", "much", "many", "more", "some", "same",
    }

    # First priority: emotion keywords found in text
    emotion_kwds = [
        kw for kw in EMOTION_KEYWORDS.get(emotion, [])
        if kw in token_set
    ]

    # Second priority: meaningful content words
    content_words = [
        t for t in tokens
        if len(t) > 4
        and t.isalpha()
        and t not in stop_words
        and t not in emotion_kwds
    ]

    # Deduplicate while preserving order
    seen = set()
    final_keywords: List[str] = []
    for kw in emotion_kwds + content_words:
        if kw not in seen:
            seen.add(kw)
            final_keywords.append(kw)
        if len(final_keywords) >= 5:
            break

    return final_keywords if final_keywords else ["journal", "entry"]


def validate_and_fix(mood_result: Dict[str, Any], original_text: str) -> Dict[str, Any]:
    """
    PERMANENT FIX: Validate and correct mood analysis results.

    This is the single source of truth for emotion correction.
    Call this after every mood analysis to ensure correctness.

    Fixes applied:
    1. Score/emotion sign mismatch
    2. Extreme score with wrong emotion
    3. Low confidence results (re-analyzed from text)
    4. Keyword quality issues (substrings, stop words)

    Args:
        mood_result: Raw dict from MoodAnalyzer.analyze_entry()
        original_text: The original journal entry text

    Returns:
        Corrected mood result dict
    """
    emotion = (mood_result.get("dominant_emotion") or "neutral").lower()
    score = float(mood_result.get("mood_score") or 0.0)
    confidence = float(mood_result.get("confidence") or 0.0)
    keywords = mood_result.get("keywords") or []

    # Clamp score
    score = max(-1.0, min(1.0, score))

    # -------------------------------------------------------------------
    # CHECK 1: Is confidence too low? Re-detect from text
    # -------------------------------------------------------------------
    if confidence < 0.5:
        logger.warning(
            "Low confidence (%.2f) - re-detecting emotion from text", confidence
        )
        emotion, score, confidence = _detect_emotion_from_text(original_text)

    # -------------------------------------------------------------------
    # CHECK 2: Score/emotion sign mismatch
    # -------------------------------------------------------------------
    positive_emotions = {"happy", "calm"}
    negative_emotions = {"sad", "anxious", "angry"}

    if emotion in positive_emotions and score < 0:
        old_score = score
        score = abs(score)
        logger.warning(
            "Sign fix: emotion='%s' had negative score %.2f → +%.2f",
            emotion, old_score, score
        )

    elif emotion in negative_emotions and score > 0:
        old_score = score
        score = -abs(score)
        logger.warning(
            "Sign fix: emotion='%s' had positive score %.2f → %.2f",
            emotion, old_score, score
        )

    # -------------------------------------------------------------------
    # CHECK 3: Neutral with extreme score - re-detect
    # -------------------------------------------------------------------
    elif emotion == "neutral" and abs(score) > 0.25:
        logger.warning(
            "Neutral with extreme score %.2f - re-detecting", score
        )
        emotion, score, confidence = _detect_emotion_from_text(original_text)

    # -------------------------------------------------------------------
    # CHECK 4: Clamp score to valid range for this emotion
    # -------------------------------------------------------------------
    if emotion in EMOTION_SCORE_RANGES:
        score_min, score_max = EMOTION_SCORE_RANGES[emotion]
        clamped = max(score_min, min(score_max, score))
        if clamped != score:
            logger.info(
                "Range clamp: emotion='%s' score %.2f → %.2f",
                emotion, score, clamped
            )
            score = clamped

    # -------------------------------------------------------------------
    # CHECK 5: Cross-validate emotion against text evidence
    # -------------------------------------------------------------------
    tokens = _tokenize(original_text)
    counts = _count_emotion_matches(tokens)

    # If detected emotion has ZERO keyword matches but another emotion
    # has strong matches, override
    if counts.get(emotion, 0) == 0:
        # Find emotion with most text evidence
        best_emotion = max(
            (e for e in counts if e != "neutral"),
            key=lambda e: counts[e],
            default=None
        )
        if best_emotion and counts[best_emotion] > 0:
            logger.warning(
                "Override: '%s' has 0 text evidence, switching to '%s' (%d matches)",
                emotion, best_emotion, counts[best_emotion]
            )
            old_emotion = emotion
            emotion, score, confidence = _detect_emotion_from_text(original_text)

    # -------------------------------------------------------------------
    # CHECK 6: Fix keyword quality
    # -------------------------------------------------------------------
    quality_keywords = _extract_quality_keywords(original_text, emotion)

    # -------------------------------------------------------------------
    # Final result
    # -------------------------------------------------------------------
    fixed_result = {
        "mood_score": round(score, 4),
        "dominant_emotion": emotion,
        "confidence": round(confidence, 4),
        "keywords": quality_keywords,
    }

    logger.info(
        "Validator output: emotion=%s, score=%.2f, confidence=%.2f, keywords=%s",
        emotion, score, confidence, quality_keywords
    )

    return fixed_result