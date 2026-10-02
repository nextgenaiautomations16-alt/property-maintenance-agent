"""
This is the piece of the architecture the job posting is explicitly
asking candidates to demonstrate: "before calling an LLM, ask whether
this actually requires one." Most tenant messages are not ambiguous --
"gas smell," "no heat," and "dripping faucet" don't need a language model
to classify; they need a keyword rule a property manager could write
themselves and audit later. The LLM (extraction.py) is only invoked for
the genuinely ambiguous remainder, which keeps the system both cheaper
and more predictable for the cases that matter most.

IMPORTANT, found via this project's own eval harness: an earlier version
of this file matched fixed phrases ("gas smell", "dripping faucet",
"squeaky door") verbatim. Real tenant messages don't write in fixed
phrases -- "I smell gas" and "the faucet has been dripping" are both
completely ordinary phrasings that a literal phrase match missed
entirely, including under-classifying a gas-smell report and a burning-
electrical-smell report as merely "high" instead of "critical". That's
exactly the kind of miss this system cannot afford. The fix below checks
for the PRESENCE of relevant words anywhere in the message, not an exact
phrase in an exact order -- left in the code and documented here on
purpose, same as the Support Triage AI bug earlier in this portfolio.

Category severity, most to least urgent:
  critical -> life-safety risk: gas, fire, smoke, carbon monoxide, burning
  high     -> active property-damage risk: flooding, burst pipe, no
              heat in freezing conditions, sewage backup, power loss
  routine  -> normal maintenance: leaky faucet, squeaky door, light bulb
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TriageResult:
    urgency: str            # "critical", "high", or "routine"
    issue_type: str
    confidence: float
    needs_llm: bool


def _has_all(lower_msg: str, words: list) -> bool:
    return all(w in lower_msg for w in words)


def _has_any(lower_msg: str, words: list) -> bool:
    return any(w in lower_msg for w in words)


def deterministic_triage(message: str) -> Optional[TriageResult]:
    """Returns a confident triage result if the message clearly matches a
    known pattern, or None if it's ambiguous and needs the LLM extraction
    step instead. Checked in severity order so a message that happens to
    mention both a routine keyword and a critical one is never
    under-classified."""
    lower = message.lower()

    # --- CRITICAL: life-safety risk ---
    if (
        (("gas" in lower) and _has_any(lower, ["smell", "leak"]))
        or "fire" in lower
        or "smoke" in lower
        or "carbon monoxide" in lower
        or "co detector" in lower
        or "burning" in lower  # burning smell, burning electrical panel/outlet, etc.
    ):
        return TriageResult("critical", "safety_hazard", 1.0, needs_llm=False)

    # --- HIGH: active property-damage risk or loss of an essential utility ---
    if (
        "flood" in lower  # flooding, flooded
        or (("water" in lower) and _has_any(lower, ["ceiling", "coming through", "inch deep"]))
        or (("burst" in lower) and ("pipe" in lower))
        or (("no heat" in lower) or (("heat" in lower) and ("freez" in lower)))
        or (("no electricity" in lower) or (("power" in lower) and _has_any(lower, ["out", "went out"])))
        or "sewage" in lower
    ):
        return TriageResult("high", "property_damage_risk", 0.9, needs_llm=False)

    # --- ROUTINE: normal wear-and-tear maintenance ---
    if (
        (("faucet" in lower) and ("drip" in lower))
        or "light bulb" in lower or "bulb" in lower
        or (("door" in lower) and _has_any(lower, ["squeak", "screen"]))
        or (("toilet" in lower) and ("running" in lower))
        or (("handle" in lower) and ("loose" in lower))
    ):
        return TriageResult("routine", "minor_maintenance", 0.85, needs_llm=False)

    return None
