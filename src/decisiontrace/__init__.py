# decisiontrace/__init__.py
from pathlib import Path

__version__ = "0.1.0"

# Define a base directory for the package
BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs" / "decision_log.jsonl"

# This makes it easier to import the core functions if this were used as a library
from .logger import log_decision
from .replay import replay_decision
from .schema import DecisionRecord
