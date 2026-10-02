"""
The Case is the single unit of state this whole system operates on.

Design intent: every step of the pipeline reads and writes THIS object
and its event log -- nothing downstream ever re-sends the tenant's full
message history to a model. When a model call is needed later in the
case's life, only the specific fields relevant to that decision are
included in the prompt, not the whole case. This is the "structured
state instead of re-sending full history" principle the system is built
around.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CaseEvent:
    timestamp: str
    event: str
    detail: str


@dataclass
class Case:
    case_id: str
    tenant_name: str
    property_id: str
    unit_id: str
    raw_message: str
    received_at: str

    # Populated by the pipeline, not the caller
    issue_type: Optional[str] = None
    urgency: Optional[str] = None            # "critical", "high", "routine"
    triage_source: Optional[str] = None      # "deterministic" or "llm"
    status: str = "new"                      # new -> triaged -> dispatched -> resolved / escalated
    vendor_dispatched: Optional[str] = None
    escalated_to_human: bool = False
    events: list = field(default_factory=list)

    def log(self, event: str, detail: str = ""):
        self.events.append(asdict(CaseEvent(timestamp=now_iso(), event=event, detail=detail)))

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        events = d.pop("events", [])
        case = cls(**d)
        case.events = events
        return case
