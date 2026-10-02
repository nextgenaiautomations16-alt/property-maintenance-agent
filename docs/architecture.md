# Architecture

This project was built as a direct answer to a specific hiring philosophy
(from a real job posting for a property-management AI engineering role):

> Event → State → Deterministic Logic → Retrieval → Model if Needed →
> Action → Validation → State Update → Next Action

Every step in `src/orchestrator.py` is commented with which part of that
sequence it implements. This document explains the reasoning behind each
one.

```
Tenant message arrives
      |
      v
EVENT            -- a new Case object is created (src/models.py)
      |
      v
STATE            -- the case is persisted immediately (src/state_store.py)
      |
      v
DETERMINISTIC    -- classifier.py asks "does this even need a model?"
LOGIC               first. ~93% of real tenant messages in this project's
                    test set never reach a model call at all.
      |
      v
RETRIEVAL        -- property_directory.py looks up vendor contacts and
                    property info. Plain lookup, not a model call, not
                    a vector search -- this is deliberately NOT framed
                    as "RAG" because it isn't; it's structured data a
                    property-management system already has.
      |
      v
MODEL IF NEEDED  -- extraction.py is only called for the ~7% of cases
                    the deterministic rules couldn't confidently
                    classify. Only the tenant's raw message is sent,
                    never the case's full history.
      |
      v
ACTION           -- actions.py: discrete, named functions
                    (notify_tenant, dispatch_vendor, escalate_to_human).
                    The model, when used, never directly triggers an
                    action -- it only produces structured classification
                    data that the orchestrator acts on.
      |
      v
VALIDATION       -- a consistency check: an escalated case must be
                    marked escalated; a dispatched case must have a
                    vendor on file. (See "What's stubbed" below for what
                    a full validation step would add.)
      |
      v
STATE UPDATE     -- the case is saved back to the store with its new
                    status and full event log.
      |
      v
NEXT ACTION      -- for this MVP, an escalated case triggers a Slack
                    alert as its next action.
```

## Why the deterministic/model split is the actual point of this project

The job posting explicitly rejects "Trigger → send everything to GPT →
Response → Next node" as an anti-pattern, and asks "does this actually
require an LLM?" as the standing question before reaching for a model.
This project's eval harness (`eval/run_eval.py`) doesn't just claim that
principle -- it measures it: on the 15-message synthetic test set, **14
of 15 cases (93%) resolve with zero model calls**, using keyword rules a
property manager could read, audit, and edit themselves. The one case
that does need a model is a genuinely ambiguous message where no
confident rule applies -- which is exactly when a model call is the
right tool, not the default one.

## Why validation and critical escalation are checked separately

A gas-leak or fire report is checked FIRST, in its own condition, before
any other classification logic runs (`classifier.py`). This mirrors the
same principle used across this portfolio's other projects (see Claims
Intake AI's fatality check, Contract Review AI's missing-clause check):
the single worst possible outcome gets its own code path and its own
tracked eval metric (`eval/run_eval.py` reports critical-urgency misses
as a standalone number, not folded into aggregate accuracy), so it can
never silently fall through a combination of other conditions.

## A real bug this project's own eval caught

An earlier version of `classifier.py` matched fixed phrases verbatim
("gas smell", "dripping faucet", "squeaky door"). Real tenant messages
don't write in fixed phrases -- "I smell gas" and "the faucet has been
dripping" are completely ordinary phrasings a literal phrase match
missed entirely, including under-classifying an actual gas-smell report
and a burning-electrical-smell report as merely "high" instead of
"critical." The fix (see `classifier.py`'s docstring and git history)
switched to tolerant word-presence matching. Left in the code and
documented here on purpose, not quietly patched and hidden -- this is
what the evaluation harness is supposed to catch.

## What's stubbed vs. real

- Real: the full Event→State→Deterministic→Retrieval→Model→Action→
  Validation→StateUpdate→NextAction pipeline, a working FastAPI
  endpoint, a persistent (file-based) state store, Slack escalation
  alerting, an evaluation harness that measures both accuracy and
  model-call-avoidance rate as concrete numbers.
- Stubbed/roadmap: actual Twilio/SMS and email delivery (currently
  simulated and logged), real vendor-confirmation callbacks and
  retry/timeout logic (a dispatched vendor who doesn't confirm within N
  minutes should automatically escalate -- the state model supports
  this, the async scheduling to check it does not exist yet), a real
  property-management-system integration (Rentvine) in place of the
  local `property_directory.py` dict, local/open-source LLM (Ollama)
  as a fallback tier before Claude for the extraction step, and
  structured memory across multiple messages from the same tenant on
  the same case (currently each case is a single message; a real
  conversation thread would need incremental state updates rather than
  a single intake call).
