"""Paths. Everything is relative to this folder, so the whole dashboard folder can be moved or copied as one unit.

SUPERR_DATA_DIR is optional. Set it only to read research outputs from a different folder (used by the tests
to simulate missing files)."""
import os
from pathlib import Path

DASH = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("SUPERR_DATA_DIR") or (DASH / "data"))
ASSETS = DASH / "assets"
MANIFEST = DASH / "data" / "MANIFEST.csv"
