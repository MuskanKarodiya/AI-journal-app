"""
Simple script to exercise the JournalManager with a few sample entries.

Run this from the project root:
    python -m utils.test_journal
"""

from __future__ import annotations

from pprint import pprint

from utils.journal_manager import JournalManager


def print_divider(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")


def main() -> None:
    jm = JournalManager()

    print_divider("Creating sample journal entries")

    entries = [
        "Today was wonderful! I learned so much about AI and felt really productive. "
        "Excited for tomorrow!",
        "Feeling a bit overwhelmed with all the new concepts. Taking it slow and being "
        "patient with myself.",
        "Had a calm, peaceful day. Went for a walk and just enjoyed the moment.",
    ]

    created_ids = []

    for idx, text in enumerate(entries, start=1):
        result = jm.create_entry(content=text, title=f"Test Entry {idx}")
        if result["success"]:
            created_ids.append(result["entry_id"])
            print(f"Created entry #{idx} with id={result['entry_id']}")
            print(f"  Mood: {result['mood']}")
        else:
            print(f"Failed to create entry #{idx}: {result['error']}")

    print_divider("All entries with mood data")
    all_entries = jm.get_all_entries()
    for entry in all_entries:
        print(f"ID: {entry['id']} | Date: {entry['date']} | Title: {entry['title']}")
        print(f"  Mood score: {entry['mood_score']}, Emotion: {entry['dominant_emotion']}")
        print(f"  Content: {entry['content']}")
        print("-" * 80)

    print_divider("Mood statistics")
    stats = jm.get_mood_statistics(days=30)
    pprint(stats)

    print_divider("Search for 'calm'")
    matches = jm.search_entries("calm")
    for entry in matches:
        print(f"ID: {entry['id']} | Title: {entry['title']}")
        print(f"  Content: {entry['content']}")
        print(f"  Mood score: {entry['mood_score']}, Emotion: {entry['dominant_emotion']}")
        print("-" * 80)


if __name__ == "__main__":
    main()
