"""
This is the "Retrieval" step in the pipeline -- a plain lookup, not a
model call, not a vector search. Most of what an agent needs to act on a
maintenance case (which vendor to call, whether the unit has a history of
this issue, out-of-hours contact info) is a deterministic lookup keyed by
property_id, not something that benefits from an LLM or even RAG. This
file exists specifically to make that point concrete rather than just
asserting it in a README: retrieval and "AI" are not the same step.

A real deployment would replace this with a call into Rentvine (or
whatever property-management system holds this data) instead of a local
dict -- the interface stays the same either way.
"""

PROPERTY_DIRECTORY = {
    "PROP-101": {
        "address": "412 Alder St, Unit 3B",
        "vendors": {
            "plumbing": "Rapid Response Plumbing — (555) 010-2231",
            "electrical": "Bayline Electric — (555) 010-4471",
            "hvac": "Coastal HVAC Services — (555) 010-8890",
            "general": "Handy Property Services — (555) 010-1123",
        },
        "after_hours_emergency_contact": "Property Manager: J. Reyes — (555) 010-9911",
    },
    "PROP-204": {
        "address": "88 Wren Court, Unit 12",
        "vendors": {
            "plumbing": "Metro Plumbing Co — (555) 020-3312",
            "electrical": "Spark Electric — (555) 020-7765",
            "hvac": "Coastal HVAC Services — (555) 010-8890",
            "general": "Handy Property Services — (555) 010-1123",
        },
        "after_hours_emergency_contact": "Property Manager: A. Kim — (555) 020-2200",
    },
}

DEFAULT_ENTRY = {
    "address": "Unknown address — property not in directory",
    "vendors": {},
    "after_hours_emergency_contact": "On-call property manager (directory lookup failed)",
}


def lookup_property(property_id: str) -> dict:
    return PROPERTY_DIRECTORY.get(property_id, DEFAULT_ENTRY)


def find_vendor_for_issue(property_id: str, issue_category: str) -> str:
    entry = lookup_property(property_id)
    return entry["vendors"].get(issue_category, entry["vendors"].get("general", "No vendor on file — needs manual dispatch"))
