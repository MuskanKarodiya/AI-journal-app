"""
Simple script to exercise the MoodAnalyzer with a few sample entries.

Run this from the project root:
    python -m utils.test_mood
"""

from __future__ import annotations

from textwrap import fill

from config import APP_TITLE
from utils.mood_analyzer import MoodAnalyzer


# Basic ANSI color codes for terminal output
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"


def color_block(hex_color: str, text: str) -> str:
    """
    Represent the emotion color nicely in the terminal.

    We can't render the exact hex color in all terminals, so we display the hex
    value with a colored label instead.
    """
    return f"{BOLD}{MAGENTA}[color]{RESET} {hex_color} ({text})"


def main() -> None:
    print(f"{BOLD}{CYAN}{APP_TITLE} – Mood Analyzer Test{RESET}\n")

    analyzer = MoodAnalyzer()

    test_entries = [
        "Today was amazing! I spent the afternoon with friends at the park, "
        "laughing and feeling so grateful for the people in my life.",
        "I feel really low today. Nothing seems to be going right and I'm "
        "worried that things won't get better.",
        "I woke up, had breakfast, worked a bit, and watched a show. "
        "It was just an average day, nothing particularly good or bad.",
    ]

    for idx, text in enumerate(test_entries, start=1):
        print(f"{BOLD}{YELLOW}Entry #{idx}{RESET}")
        print(fill(text, width=80))

        result = analyzer.analyze_entry(text)
        emotion = result.get("dominant_emotion", "neutral")
        color = analyzer.get_emotion_color(emotion)

        print(f"{BOLD}Mood score:{RESET}        {result.get('mood_score')}")
        print(f"{BOLD}Dominant emotion:{RESET} {emotion}")
        print(f"{BOLD}Confidence:{RESET}       {result.get('confidence')}")
        print(f"{BOLD}Keywords:{RESET}        {', '.join(result.get('keywords', [])) or '—'}")
        print(f"{BOLD}Emotion color:{RESET}   {color_block(color, emotion)}")
        print("\n" + "-" * 80 + "\n")


if __name__ == "__main__":
    main()
