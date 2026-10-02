"""
This file is the centerpiece of the whole project: a literal
implementation of

    Event -> State -> Deterministic Logic -> Retrieval -> Model if Needed
    -> Action -> Validation -> State Update -> Next Action

as a sequence of named, auditable steps -- not a single prompt that's
trusted to "figure it out." Every step below is commented with which
part of that pipeline it is, on purpose, so the mapping from architecture
diagram to code is never left implicit.
"""
from .models import Case, now_iso
from . import state_store
from .classifier import deterministic_triage
from .extraction import extract_urgency
from .property_directory import lookup_property
from .actions import notify_tenant, dispatch_vendor, escalate_to_human
from .notifications import send_escalation_alert

ESCALATION_URGENCY_THRESHOLD = {"critical"}  # urgencies that always escalate to a human, no exceptions


def handle_tenant_message(case_id: str, tenant_name: str, property_id: str,
                           unit_id: str, message: str) -> Case:
    # --- EVENT ---
    # A tenant message arriving is the event that starts everything else.
    case = Case(
        case_id=case_id, tenant_name=tenant_name, property_id=property_id,
        unit_id=unit_id, raw_message=message, received_at=now_iso(),
    )
    case.log("case_received", message)

    # --- STATE ---
    # Persist the case immediately so nothing downstream has to re-derive
    # context from scratch if this run is interrupted.
    state_store.save_case(case)

    # --- DETERMINISTIC LOGIC ---
    # Ask "does this even need a model?" before reaching for one.
    triage = deterministic_triage(message)
    triage_source = "deterministic"

    # --- MODEL IF NEEDED ---
    # Only called when the deterministic rules didn't confidently match.
    if triage is None:
        triage = extract_urgency(message)
        triage_source = "llm" if triage.needs_llm else "deterministic"

    case.urgency = triage.urgency
    case.issue_type = triage.issue_type
    case.triage_source = triage_source
    case.status = "triaged"
    case.log("triaged", f"urgency={triage.urgency}, issue_type={triage.issue_type}, source={triage_source}")

    # --- RETRIEVAL ---
    # Plain lookup, not a model call -- property/vendor context the
    # action step needs.
    property_info = lookup_property(property_id)
    case.log("property_lookup", property_info["address"])

    # --- ACTION ---
    if case.urgency in ESCALATION_URGENCY_THRESHOLD:
        # Critical cases: notify the tenant AND escalate immediately,
        # in parallel -- never wait on a human to decide whether a gas
        # smell report deserves an emergency contact.
        notify_tenant(case, "This has been flagged as an emergency. Please leave the unit and call 911 if you smell gas. Our after-hours contact is being notified now.")
        escalate_to_human(case, f"Critical safety issue reported: {case.issue_type}")
    elif case.urgency == "high":
        vendor = dispatch_vendor(case, _issue_category(case.issue_type))
        notify_tenant(case, f"We've dispatched {vendor} to address this. They will contact you shortly to confirm timing.")
        case.status = "dispatched"
    else:  # routine
        vendor = dispatch_vendor(case, _issue_category(case.issue_type))
        notify_tenant(case, f"Thanks for letting us know. {vendor} will reach out to schedule a non-emergency visit.")
        case.status = "dispatched"

    # --- VALIDATION ---
    # In this MVP, "validation" is a simple consistency check: an
    # escalated case must be marked escalated, a dispatched case must
    # have a vendor on file. A production system would validate against
    # real confirmation callbacks (did the vendor actually accept the
    # job?) -- see README roadmap.
    if case.status == "escalated" and not case.escalated_to_human:
        raise RuntimeError(f"Validation failed: case {case.case_id} marked escalated but escalated_to_human is False")
    if case.status == "dispatched" and not case.vendor_dispatched:
        raise RuntimeError(f"Validation failed: case {case.case_id} marked dispatched but no vendor on file")

    # --- STATE UPDATE ---
    state_store.save_case(case)

    # --- NEXT ACTION ---
    # For this MVP, escalated cases trigger a Slack alert as their next
    # action. A production system would also schedule a follow-up check
    # (did the vendor confirm within N minutes?) -- see README roadmap
    # for why that's not fully built out here.
    if case.escalated_to_human:
        send_escalation_alert(case, case.events[-1]["detail"])

    return case


def _issue_category(issue_type: str) -> str:
    """Maps a classified issue_type onto the vendor directory's
    categories. Deliberately simple keyword mapping, not a model call --
    there are only a handful of vendor categories, so a lookup table is
    more reliable and auditable than asking a model to pick one."""
    mapping = {
        "property_damage_risk": "plumbing",
        "minor_maintenance": "general",
        "plumbing_leak": "plumbing",
        "electrical_fault": "electrical",
        "appliance_issue": "general",
        "unclassified_maintenance_issue": "general",
    }
    return mapping.get(issue_type, "general")
