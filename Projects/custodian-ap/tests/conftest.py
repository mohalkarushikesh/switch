"""Shared test setup — runs before any test module is imported.

Puts src/ on the path and forces deterministic, isolated defaults: no LLM keys
(heuristic scoring) and an in-memory SQLite database (no on-disk pollution).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Disable the LLM path so scoring is deterministic and offline.
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("GROQ_API_KEY", None)

# Ephemeral DB for the whole test session (must be set before config is imported).
os.environ.setdefault("CUSTODIAN_DB_PATH", ":memory:")
