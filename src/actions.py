"""
Each function here is a discrete "tool" the orchestrator invokes once it
has decided what should happen -- this is the tool/function-calling
pattern requested explicitly: actions are named, typed functions with
clear side effects, not a single LLM call that's trusted to "figure out
what to do." The model (when used at all) only ever produces structured
classification data; it never directly triggers an action itself.

In this MVP, "sending" an SMS/email or "dispatching" a vendor is logged
and simulated rather than actually calling Twilio/a vendor API -- the
seam (this file) is exactly where that real integration would plug in
without touching orchestrator.py.
"""
from .property_directory import lookup_property, find_vendor_for_issue


def notify_tenant(case, message: str):
    case.log("tenant_notified", message)
    print(f"[actions] (simulated SMS/email to {case.tenant_name}): {message}")


def dispatch_vendor(case, issue_category: str) -> str:
    vendor = find_vendor_for_issue(case.property_id, issue_category)
    case.vendor_dispatched = vendor
    case.log("vendor_dispatched", f"{issue_category} -> {vendor}")
    print(f"[actions] (simulated vendor dispatch) {vendor} for case {case.case_id}")
    return vendor


def escalate_to_human(case, reason: str):
    case.escalated_to_human = True
    case.status = "escalated"
    case.log("escalated_to_human", reason)
