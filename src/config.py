"""Configuration, paths, constants, and date calculation rules for ZentroMart VoiceOps."""

import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base directories
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SRC_DIR)

DATASET_DIR = os.getenv("DATASET_DIR", PROJECT_DIR)
KB_DIR = os.path.join(DATASET_DIR, "kb")
DATA_DIR = os.path.join(DATASET_DIR, "data")
PRACTICE_DIR = os.path.join(DATASET_DIR, "practice")
TOOLS_DIR = os.path.join(DATASET_DIR, "tools")

# Reference Anchor Date (MANDATORY per Capstone Brief)
# 20 October 2026 (Tuesday)
REFERENCE_DATE = date(2026, 10, 20)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GNANI_API_KEY = os.getenv("GNANI_API_KEY", "")

# Voice / Gnani parameters
DEFAULT_TTS_MODEL = "timbre-v2.5"
DEFAULT_VOICE = "Kaveri"
DEFAULT_LANGUAGE = "en-IN"

# Known warehouse holidays in dataset
HOLIDAYS = {
    date(2026, 8, 15),   # Independence Day
    date(2026, 10, 2),   # Gandhi Jayanti
    date(2026, 10, 19),  # Warehouse closure (festival)
    date(2026, 11, 9),   # Warehouse closure (festival)
}

def is_business_day(d: date) -> bool:
    """Business days are Monday (0) to Saturday (5), excluding holidays. Sunday (6) is off."""
    if d.weekday() == 6:  # Sunday
        return False
    if d in HOLIDAYS:
        return False
    return True

def add_business_days(start_date: date, n_days: int) -> date:
    """Add n business days to start_date, skipping Sundays and listed holidays."""
    cur = start_date
    added = 0
    while added < n_days:
        cur += timedelta(days=1)
        if is_business_day(cur):
            added += 1
    return cur

def parse_date_str(d_str: str) -> date:
    """Parse YYYY-MM-DD string to date object."""
    return datetime.strptime(d_str.strip(), "%Y-%m-%d").date()
