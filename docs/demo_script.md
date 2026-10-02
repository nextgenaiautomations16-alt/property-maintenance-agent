# Demo / Loom Video Script (4-5 minutes)

This script is written to directly answer the job posting's own request:
"show us the problem you solved, architecture/workflow, actual code or
orchestration, models used and why, APIs and systems integrated,
state/memory approach, how failures were handled, what you personally
built, what didn't work initially, what you would redesign today."

---

**0:00-0:30 — The problem, in their own words**

"I built this specifically in response to [company]'s own example: a
tenant emails at 11:30 PM saying water is coming through the ceiling and
nobody answered the phone. The question is how to handle that without a
human monitoring an inbox all night — but also without just wiring a
trigger straight into GPT and hoping for the best."

**0:30-1:30 — Architecture, screen-share `docs/architecture.md`**

"I built this around the exact pipeline shape your posting describes:
Event, State, Deterministic Logic, Retrieval, Model if Needed, Action,
Validation, State Update, Next Action. Let me walk through each step in
the code." [Open `src/orchestrator.py`, scroll through each commented
section in order.]

**1:30-2:15 — Show the deterministic-first design and the real numbers**

"Here's the part I think matters most: before this ever calls a model,
it asks whether it needs to." [Open `src/classifier.py`.] "I ran this
against 15 synthetic tenant messages, including your exact water-leak
example, and measured — not assumed — how often a model call was
actually needed." [Run `python -m eval.run_eval` live, point at the
output: 93% of cases resolved with zero model calls, 100% urgency
accuracy, 0 critical misses.]

**2:15-3:00 — Show the water-leak case end to end**

[Hit the API with the exact job-posting scenario, show the full JSON
response: deterministic triage, property lookup via `property_directory.py`,
vendor dispatched, tenant notified, full event log with timestamps —
all without touching a model.]

**3:00-3:45 — Show a critical case and the human-escalation path**

[Hit the API with a gas-smell message. Show it short-circuits straight
to critical, notifies the tenant with safety instructions, and escalates
to Slack immediately — point out this never waits for a model call or a
human to make the emergency judgment call; that's hard-coded on purpose.]

**3:45-4:15 — What didn't work initially, and what I'd redesign**

"My first version of the classifier used exact phrase matching —
'dripping faucet,' 'gas smell' — and my own eval harness caught that it
missed a real gas-smell report and a burning-electrical-smell report,
scoring them as merely 'high' instead of 'critical,' because tenants
don't write in fixed phrases. I fixed it to use tolerant word-presence
matching instead, and I left that bug and the fix documented in
`docs/architecture.md` rather than hiding it — that's genuinely how I
work.

If I were redesigning this for production, the biggest gap is that
vendor dispatch is currently simulated, not wired to a real confirmation
callback — a real version needs an async retry/timeout path: if a vendor
doesn't confirm within N minutes, escalate automatically. The state
model already supports this; the scheduling to check it doesn't exist
yet, and I'd build that next."

**4:15-4:45 — Close**

"This is one project out of nine I've built with the same underlying
principle — deterministic rules make the auditable decisions, a model
is used only where it earns its cost, and a human is only interrupted
when there's a genuine judgment call. Happy to walk through the code
further or talk through how this would extend to the lead-gen and
leasing workflows in your posting."
