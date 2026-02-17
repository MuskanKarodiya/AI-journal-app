"""
Configuration settings for the AI journaling app.
"""

# Database configuration
DATABASE_PATH: str = "./database/journal.db"

# Ollama / LLM configuration
OLLAMA_MODEL_NAME: str = "llama3.2:1b"
OLLAMA_API_ENDPOINT: str = "http://localhost:11434/api/generate"

# App display settings
APP_TITLE: str = "My AI Journal"

# Pinterest-inspired soft pastel color palette
COLOR_PALETTE: list[str] = [
    "#FFE5E5",  # Soft pink
    "#E5F3FF",  # Soft blue
    "#FFF5E5",  # Soft peach
    "#E5FFE5",  # Soft green
]

# Journal constraints
MAX_JOURNAL_ENTRY_LENGTH: int = 5000
