import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env")
PROJECT_DIR = Path(__file__).resolve().parent

OLLAMA_URL = os.getenv("OLLAMA_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GMAIL_CLIENT_SECRET_FILE = os.getenv(
    "GMAIL_CLIENT_SECRET_FILE",
    str(PROJECT_DIR / "client_secret.json"),
)
GMAIL_TOKEN_FILE = os.getenv(
    "GMAIL_TOKEN_FILE",
    str(PROJECT_DIR / "gmail_token.json"),
)

CATEGORY_LABELS = [
    label.strip()
    for label in os.getenv(
        "CATEGORY_LABELS",
        "Work,Finance,Shopping,Personal,News,Bills,Security,Travel,Health,Education,Subscriptions,Government,Social,Other",
    ).split(",")
    if label.strip()
]

INBOX_QUERY = "in:inbox newer_than:1d"
OLLAMA_MODEL = "gemma4:e2b"


def ensure_required_settings():
    if not OLLAMA_URL or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError(
            "OLLAMA_URL, TELEGRAM_BOT_TOKEN, and TELEGRAM_CHAT_ID must be set (e.g. in .env)."
        )
    if not Path(GMAIL_CLIENT_SECRET_FILE).is_file():
        raise RuntimeError(
            f"Gmail client secret file not found: {GMAIL_CLIENT_SECRET_FILE}"
        )
