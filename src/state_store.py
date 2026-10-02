"""
A minimal persistent state store for cases, keyed by case_id.

In this MVP it's a JSON file on disk. A production deployment would swap
this for Redis (hot state, fast reads for an active case) or Postgres
(durable history) without changing anything in orchestrator.py -- the
store's interface (get, save, list_open) is the seam that isolates the
rest of the system from where state actually lives.

The point being demonstrated here: the orchestrator never rebuilds
context from scratch or re-sends a case's full history anywhere. It
loads the specific Case object, reads only the fields it needs at each
step, and writes back the updated state. That's what "structured state"
means in practice, not just as an architecture-diagram word.
"""
import json
from pathlib import Path
from .models import Case

STORE_PATH = Path(__file__).parent.parent / "data" / "case_store.json"


def _load_all() -> dict:
    if not STORE_PATH.exists():
        return {}
    with open(STORE_PATH) as f:
        raw = json.load(f)
    return {cid: Case.from_dict(c) for cid, c in raw.items()}


def _save_all(cases: dict):
    with open(STORE_PATH, "w") as f:
        json.dump({cid: c.to_dict() for cid, c in cases.items()}, f, indent=2)


def get_case(case_id: str) -> Case | None:
    cases = _load_all()
    return cases.get(case_id)


def save_case(case: Case):
    cases = _load_all()
    cases[case.case_id] = case
    _save_all(cases)


def list_open_cases() -> list:
    cases = _load_all()
    return [c for c in cases.values() if c.status not in ("resolved",)]
