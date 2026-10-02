"""
Runs every synthetic case through the real orchestrator (same as
eval/run_eval.py) so that critical cases trigger real Slack alerts.

Run from repo root: python -m scripts.send_demo_alerts
Requires SLACK_WEBHOOK_URL to be set (falls back to console logging if not).
"""
import json
from pathlib import Path

from src.orchestrator import handle_tenant_message
from src import state_store

DATA_DIR = Path(__file__).parent.parent / "data"


def main():
    with open(DATA_DIR / "synthetic_cases.json") as f:
        synthetic_cases = json.load(f)

    if state_store.STORE_PATH.exists():
        state_store.STORE_PATH.unlink()

    escalated = 0
    for sc in synthetic_cases:
        case = handle_tenant_message(
            case_id=sc["case_id"], tenant_name=sc["tenant_name"],
            property_id=sc["property_id"], unit_id=sc["unit_id"],
            message=sc["message"],
        )
        if case.escalated_to_human:
            print(f"{case.case_id} ({case.tenant_name}): escalated and alerted")
            escalated += 1

    print(f"\nDone — {escalated} case(s) escalated to a human and alerted.")


if __name__ == "__main__":
    main()
