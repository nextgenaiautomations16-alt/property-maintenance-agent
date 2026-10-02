"""
Runs every synthetic tenant message through the real orchestrator
pipeline (not a shortcut) and scores two things:

  1. Urgency accuracy against labeled ground truth
  2. How many cases were resolved WITHOUT a model call at all -- this is
     the concrete evidence for the "token-efficient architecture" claim:
     not an assertion in a README, a measured number from an actual run.

Critical-urgency misses are tracked as their own metric, same principle
as every other eval in this portfolio: the worst possible failure mode
(a gas-leak report classified as routine) must never hide inside an
aggregate accuracy percentage.

Run from repo root: python -m eval.run_eval
"""
import csv
import json
from pathlib import Path

from src.orchestrator import handle_tenant_message
from src import state_store

DATA_DIR = Path(__file__).parent.parent / "data"


def load_ground_truth():
    rows = {}
    with open(DATA_DIR / "ground_truth.csv") as f:
        for row in csv.DictReader(f):
            rows[row["case_id"]] = row
    return rows


def main():
    with open(DATA_DIR / "synthetic_cases.json") as f:
        synthetic_cases = json.load(f)
    ground_truth = load_ground_truth()

    # start from a clean state store so re-running the eval is repeatable
    if state_store.STORE_PATH.exists():
        state_store.STORE_PATH.unlink()

    correct = 0
    mismatches = []
    critical_misses = 0
    deterministic_count = 0
    llm_count = 0

    for sc in synthetic_cases:
        case = handle_tenant_message(
            case_id=sc["case_id"], tenant_name=sc["tenant_name"],
            property_id=sc["property_id"], unit_id=sc["unit_id"],
            message=sc["message"],
        )
        expected = ground_truth[case.case_id]["expected_urgency"]

        if case.urgency == expected:
            correct += 1
        else:
            mismatches.append((case.case_id, expected, case.urgency, sc["message"]))
            if expected == "critical":
                critical_misses += 1

        if case.triage_source == "deterministic":
            deterministic_count += 1
        else:
            llm_count += 1

    total = len(synthetic_cases)
    accuracy = correct / total if total else 0

    print("=== Property Maintenance Agent — Evaluation Report ===")
    print(f"Total tenant messages evaluated: {total}")
    print(f"Urgency accuracy: {accuracy:.1%}  ({correct}/{total})")
    print(f"Critical-urgency cases missed (worst possible failure mode): {critical_misses}")
    print()
    print(f"Resolved with NO model call (deterministic rules only): {deterministic_count}/{total} ({deterministic_count/total:.0%})")
    print(f"Required a model call: {llm_count}/{total} ({llm_count/total:.0%})")

    if mismatches:
        print("\n--- Mismatches vs. ground truth ---")
        for case_id, expected, actual, message in mismatches:
            print(f"  {case_id}: expected {expected}, got {actual} — \"{message}\"")
    else:
        print("\nNo mismatches — every case landed in the expected urgency bucket.")


if __name__ == "__main__":
    main()
