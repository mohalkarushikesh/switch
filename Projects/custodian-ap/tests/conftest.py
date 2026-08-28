"""Shared test setup — runs before any test module is imported.

Puts src/ on the path and forces deterministic, isolated defaults: no LLM calls
(heuristic scoring) and an in-memory SQLite database (no on-disk pollution).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Force the heuristic scorer. This flag — not the absence of keys — is what
# guarantees offline runs: config.py calls load_dotenv(), so a developer's .env
# would otherwise re-supply a provider key here and the suite would start making
# real network calls. Popping the keys below is belt-and-braces.
os.environ["CUSTODIAN_DISABLE_LLM"] = "1"
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("GROQ_API_KEY", None)
os.environ.pop("HUGGINGFACE_API_KEY", None)
os.environ.pop("HF_TOKEN", None)

# Ephemeral DB for the whole test session (must be set before config is imported).
os.environ.setdefault("CUSTODIAN_DB_PATH", ":memory:")

# The Presidio suite is opt-in. Importing presidio_analyzer/spacy reaches the
# network to resolve model data, which *hangs* rather than fails where those
# endpoints are blocked — so `pytest tests/` never finishes. A pytest marker
# can't help: deselection happens after collection, and collection is what
# performs the import. The file has to be dropped before that.
#
# Run it explicitly with:  CUSTODIAN_TEST_PRESIDIO=1 pytest tests/
collect_ignore = [] if os.getenv("CUSTODIAN_TEST_PRESIDIO") else ["test_pii_presidio.py"]
