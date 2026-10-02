"""
Only called when classifier.deterministic_triage() returns None -- i.e.
the message didn't match a known keyword pattern confidently enough to
skip the model entirely. This is the "Model if Needed" step, and it's
deliberately the minority path, not the default one.

Token-efficiency note: only the tenant's raw message is sent here, never
the case's full event history or the property directory. If a later step
needs the model to reason about case history too, that history would be
summarized into a few structured fields first, not concatenated
verbatim -- but for this MVP's scope (single-message triage), the message
itself is already the minimum necessary context.

Same real-vs-fallback pattern as the rest of this portfolio: calls Claude
if ANTHROPIC_API_KEY is set, otherwise falls back to a conservative
heuristic so the pipeline is fully runnable offline.
"""
import os
import json
from .classifier import TriageResult

EXTRACTION_PROMPT = """A tenant sent this maintenance request. Classify it and
return ONLY valid JSON, no prose, no markdown fences:

{{
  "urgency": "critical" | "high" | "routine",
  "issue_type": string (a short category, e.g. "plumbing_leak", "electrical_fault", "appliance_issue"),
  "confidence": number between 0 and 1
}}

Guidance: "critical" = an immediate life-safety risk (gas, fire, smoke,
carbon monoxide). "high" = active property-damage risk or loss of an
essential utility. "routine" = normal wear-and-tear maintenance. If you
are unsure between two levels, choose the MORE urgent one -- a
false alarm costs a vendor visit; a missed emergency costs much more.

Tenant message:
---
{message}
---
"""


def extract_with_llm(message: str) -> TriageResult:
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(message=message)}],
    )
    text = "".join(block.text for block in response.content if hasattr(block, "text"))
    parsed = json.loads(text)
    return TriageResult(parsed["urgency"], parsed["issue_type"], parsed.get("confidence", 0.6), needs_llm=True)


def extract_with_heuristic(message: str) -> TriageResult:
    """Conservative fallback: if we can't confidently classify and don't
    have a model available, default to 'high' rather than 'routine'.
    Same principle used throughout this portfolio -- an ambiguous case
    should never silently default to the least urgent bucket."""
    return TriageResult("high", "unclassified_maintenance_issue", 0.4, needs_llm=True)


def extract_urgency(message: str) -> TriageResult:
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return extract_with_llm(message)
        except Exception as e:
            print(f"[extraction] LLM extraction failed ({e}), falling back to heuristic")
    return extract_with_heuristic(message)
