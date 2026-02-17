"""
Simple script to test database initialization and seed data.
Run this from the project root with:
    python -m database.test_db
"""

from database.db_setup import init_database, get_session
from database.models import ReflectionPrompt


def main() -> None:
    # Initialize database and seed prompts
    result = init_database()
    print(result)

    # List all reflection prompts
    with get_session() as session:
        prompts = session.query(ReflectionPrompt).all()

        print("\nReflection prompts in database:")
        for prompt in prompts:
            print(f"- [{prompt.category}] {prompt.prompt_text}")


if __name__ == "__main__":
    main()
