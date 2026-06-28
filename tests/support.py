"""Shared test helpers for locating the unpacked game resources.

Integration tests run against the *real* gitignored ``unpacked/`` when it is
present (so a local run catches real-data regressions), and fall back to the
committed mock fixture under ``tests/fixtures/unpacked/`` otherwise — which is
what happens in CI, where the real source is never checked out.

Set ``SC_TEST_UNPACKED`` to force a specific root.
"""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "unpacked"


def unpacked_root() -> Path:
    """Real ``unpacked/`` if it has a CDB, else the committed fixture."""
    override = os.environ.get("SC_TEST_UNPACKED")
    if override:
        return Path(override)
    real = REPO / "unpacked"
    if (real / "data.cdb").exists() or (real / "data.json").exists():
        return real
    return FIXTURE_ROOT


def cdb_path() -> Path:
    """The CDB file inside the resolved root (real ``.cdb`` or fixture ``.json``)."""
    root = unpacked_root()
    real = root / "data.cdb"
    return real if real.exists() else root / "data.json"


def lang_dir() -> Path:
    """Folder holding the ``export_<lang>.xml`` translation exports."""
    return unpacked_root() / "extra" / "lang"
