# Property Maintenance Agent

**A 24/7 tenant maintenance-intake agent, built around a specific architecture philosophy: Event → State → Deterministic Logic → Retrieval → Model if Needed → Action → Validation → State Update → Next Action — not a "trigger → send everything to GPT → response" wrapper.**

This project was purpose-built to answer a real job posting's own example scenario: *a tenant emails at 11:30 PM saying water is coming through the ceiling and nobody answered the phone — how do you handle that without a human monitoring the inbox all night, and without wasting tokens re-sending full context to a model on every step?*

See [docs/demo_script.md](docs/demo_script.md) for the full walkthrough (written as a Loom video script) and [docs/architecture.md](docs/architecture.md) for the detailed reasoning behind every design decision.

## The problem

Property-management teams need to respond to tenant maintenance requests around the clock, but most requests are completely unambiguous — "my faucet is dripping" doesn't need a language model, and a reported gas smell should never wait on one either. The hard part isn't connecting an LLM to an inbox; it's building a system that knows when *not* to use one, keeps reliable state across a case's lifecycle, and knows exactly when a human genuinely needs to be involved.

## What this does

1. **Classify, deterministically, first** — keyword-based rules (not a model) confidently resolve the large majority of real tenant messages into critical / high / routine urgency, checked in that severity order so a critical signal can never be missed by falling through other logic
2. **Call a model only for the genuinely ambiguous remainder** — and only the tenant's raw message is sent, never the case's full history
3. **Look up property/vendor context deterministically** — a plain lookup, not RAG, not a model call, because this is structured data a property-management system already has
4. **Act through discrete, named tools** — `notify_tenant`, `dispatch_vendor`, `escalate_to_human` — the model never directly triggers an action; it only ever produces structured classification data the orchestrator decides what to do with
5. **Persist full, auditable state** — every case keeps a timestamped event log from intake through resolution or escalation
6. **Alert a human only for genuine judgment calls** — critical safety cases escalate to Slack immediately; everything else resolves without interrupting anyone

## Quickstart

```bash
git clone <your-repo-url>
cd property-maintenance-agent
pip install -r requirements.txt

# 1. generate the synthetic tenant-message dataset (15 messages, including
#    the exact water-leak scenario from the job posting this was built for)
python data/generate_synthetic_cases.py

# 2. run the evaluation harness
python -m eval.run_eval

# 3. run the API and try it yourself
uvicorn src.api:app --reload
# then POST to http://127.0.0.1:8000/maintenance/intake
```

Set `ANTHROPIC_API_KEY` to use real LLM-based extraction for ambiguous messages; without it, a conservative heuristic fallback is used. Set `SLACK_WEBHOOK_URL` to actually post critical escalations to a channel; without it, alerts print to the console.

## Evaluation results (on the included synthetic dataset)

```
Total tenant messages evaluated: 15
Urgency accuracy: 100.0%  (15/15)
Critical-urgency cases missed: 0

Resolved with NO model call (deterministic rules only): 14/15 (93%)
Required a model call: 1/15 (7%)
```

That 93% figure is the concrete evidence behind this project's core design claim — not an assertion, a number from an actual run against a labeled test set.

## A real bug this project's own eval caught

An earlier version of the classifier matched fixed phrases verbatim and missed a real gas-smell report and a burning-electrical-smell report, scoring both as merely "high" instead of "critical," because tenants don't write in fixed phrases. Fixed to use tolerant word-presence matching instead — see [docs/architecture.md](docs/architecture.md) for the full story. Left in the code and the docs on purpose.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full pipeline, mapped explicitly to each stage of the Event→State→Deterministic→Retrieval→Model→Action→Validation→StateUpdate→NextAction philosophy.

## Tech stack

Python, FastAPI, a file-based persistent state store (swap for Redis/Postgres in production), Anthropic Claude API (optional, with a heuristic fallback), flat-file property/vendor directory (swap for a real Rentvine integration in production).

## Roadmap

- Wire real Twilio SMS/email delivery in place of the simulated, logged notifications
- Add async vendor-confirmation callbacks with automatic timeout-based escalation (the state model already supports this; the scheduling layer doesn't exist yet)
- Replace the local property/vendor directory with a real Rentvine API integration
- Add an Ollama/local-model tier as a cost-efficient first option before Claude for the extraction step
- Support multi-message case threads with incremental state updates, instead of treating every case as a single intake message
