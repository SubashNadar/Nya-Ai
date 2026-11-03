"""Filesystem locations used by the backend, defined once."""

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
SECTION_MAP_CSV = DATA_DIR / "section_map.csv"
REPO_DIR = BACKEND_DIR.parent
EVALS_DIR = REPO_DIR / "evals"
CASES_DIR = EVALS_DIR / "cases"
