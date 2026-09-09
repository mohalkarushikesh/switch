# Custodian — Demo Speaker Script

**Total runtime:** ~12 min · **Format:** live walkthrough of the React console at `/app/` · Everything in **bold-bracketed caps** is a stage direction (what to do), the rest is what to say.

The four bundled sample invoices give a clean one-of-each outcome under the default config (no API key → the transparent heuristic scorer):

| Invoice | Vendor | Amount | Risk | Outcome |
| ------- | ------ | ------ | ---- | ------- |
| INV-001 | Acme Office Supplies | ₹1,240.50 | 0 | **auto-paid** |
| INV-002 | Skyline Construction | ₹48,250 | 25 | **human review** (over ₹5,000 auto-pay cap) |
| INV-003 | QuickPay Global | ₹75,000 | 100 | **rejected + alert** (fraud signals) |
| INV-004 | Bright Cleaning Services | ₹3,000 | 40 | **human review** (due-date-before-issue) |

---

## 0. Pre-flight (before anyone's watching)

**[START THE API: `$env:PYTHONPATH="src"; uvicorn custodian.api:app --reload`]**
**[BUILD/SERVE THE WEB APP: `cd web; npm run build` — then open `http://localhost:8000/app/`]**
**[CONFIRM the ledger is fresh and the four sample invoices are ready to submit. Leave the Dashboard tab open. Have `/health` open in a second tab to prove scoring mode.]**

> Quick sanity checklist: `/health` loads, the console renders, and the ledger shows the opening balance of ₹10,00,000. If you have no LLM key, `/health` will say `scoring_mode: "heuristic"` — that's expected and actually a *feature* we'll talk about.

---

## 1. The hook — 60 seconds

> "Every business pays invoices. In a bank's accounts-payable team, someone opens each invoice, eyeballs it for anything fishy, checks it against the rules, and either pays it, kicks it up for approval, or rejects it. It's slow, it's repetitive, and it's exactly the kind of judgment work people now want to hand to AI.
>
> So here's the uncomfortable question: **would you let an AI agent move real money out of a bank account?**
>
> Most people say no — and they're right to be nervous, because a normal AI agent is a black box. This project, **Custodian**, is my answer to that question. It's an AI system that *does* make the pay/reject decision autonomously — but it's wrapped in six governance layers so that for every single decision, you can prove, after the fact, exactly what happened and why. That's the whole idea: **autonomous, but accountable.**"

---

## 2. The mental model — 90 seconds

**[OPEN the Governance section, or point at the architecture diagram / Overview panel with the six layers.]**

> "There are two halves to Custodian.
>
> **The first half is the agent pipeline** — this is the part that does the work. An invoice flows through four agents in a line: **Ingest** validates it, **Risk** scores it 0 to 100 for fraud and risk, **Approval** routes it, and **Payment** releases the money. Ingest, score, route, pay.
>
> **The second half is what makes it safe** — six governance layers wrapped around that pipeline: **Identity, Data, Model, Policy, Agent Runtime, and Operations.** Every action the agents take passes through these, and each one leaves a trace.
>
> The two that do the heavy lifting in this demo are **Data** — which scrubs personal information *before* anything reaches the AI — and **Policy** — hard, deterministic rules that can *overrule* the AI. The AI's risk score is a probability; policy is non-negotiable. If policy says no, it doesn't matter how safe the AI thought it was. Keep that in mind — you'll see it happen."

---

## 3. The live demo — the four invoices — ~5 minutes

> "Let's run four real invoices through it. I've picked one of each outcome so you can see the whole decision space."

### INV-001 — the clean one (auto-pay)

**[SUBMIT INV-001. Open its row → detail drawer → show the pipeline dots all green and the audit trail.]**

> "Acme Office Supplies, ₹1,240.50, normal vendor account, itemized, sensible dates. The risk agent scores it **zero** — no signals at all. It's under our auto-pay risk limit *and* under the ₹5,000 amount cap, so the system **pays it automatically**. No human touched it.
>
> But watch this — **[point at the audit trail in the drawer]** — even for the boring happy path, every step is logged: ingested, PII checked, risk-scored zero, approval decision, payment released with a transaction ID. That trail is the product. That's what 'provable' means."

### INV-002 — the big one (human review)

**[SUBMIT INV-002. Show it land in the Review Queue.]**

> "Skyline Construction, ₹48,250 — a progress payment on a construction contract. The AI scores it **25**: not fraudulent, just a large amount. And here's a nice bit of design: 25 is actually *below* our risk threshold for auto-pay — the AI is fairly comfortable — **but the amount is over the ₹5,000 auto-pay cap.** So instead of trusting the score alone, the system routes it to a **human reviewer**.
>
> A big legitimate payment shouldn't be blocked, but it also shouldn't be paid by a robot at 2 a.m. with no one watching. So it goes to the queue."

**[SWITCH to the Review Queue. Show it sorted highest-risk-first. Approve it.]**

> "This is the reviewer's workspace — everything a human needs to sign off, highest-risk first, with bulk approve/reject. I approve it… and *now* it pays and hits the ledger. Human in the loop, exactly where a human belongs."

### INV-003 — the fraudulent one (rejected + alert)

**[SUBMIT INV-003. Open the drawer — read the flags aloud.]**

> "Now the fun one. QuickPay Global, ₹75,000. Look at this invoice: the vendor account is just 'X12' — three characters, that's not a real account. There are no line items. And the memo says **'URGENT: wire now, vendor changed bank details, please process immediately.'**
>
> If you've ever seen a business-email-compromise scam, that memo is the *textbook* version — urgency, a sudden change of bank details, pressure to skip the process. The risk agent stacks it all up: very large amount, suspiciously round number, malformed account, urgency language, no line items — and the score pegs at **100 out of 100.** That's over our reject threshold, so the system **rejects it outright and fires a notification.** No human even has to look at it first.
>
> **[point at the flags list in the drawer]** And critically — it doesn't just say 'rejected.' It says *why*: here are the five specific signals. That's an explanation a fraud analyst or an auditor can actually act on."

### INV-004 — the subtle one (human review)

**[SUBMIT INV-004. Open the drawer — highlight the date flag.]**

> "Last one, and it's my favorite because it's sneaky. Bright Cleaning Services, ₹3,000 — small, routine, would sail straight through most systems. But look at the dates: the **due date is *before* the issue date.** That's impossible — it's either a data-entry error or someone fiddling with the paperwork. The system catches it, adds 25 risk points for the date problem plus points for the round amount, lands at **40**, and routes it to a human.
>
> That's the point of layering rules on top of the AI: a ₹3,000 invoice isn't scary, but a *broken* ₹3,000 invoice deserves a second look."

---

## 4. Governance close-ups — ~2 minutes

### PII redaction (Data layer)

**[POINT at an audit-trail line reading something like "Data layer: redacted PII types … before LLM."]**

> "Remember I said Data governance scrubs personal information *before* the AI sees it? Here's the proof, in the trail. The invoice the LLM scores is a **redacted** copy — account numbers and personal identifiers stripped out. So even though we're calling a real external AI provider, we're not leaking a customer's banking details to it. Privacy isn't a promise here; it's a step in the pipeline that logs itself."

### Policy override (Policy layer)

**[OPEN the Governance section — show the risk-band ruler: auto-pay / review / reject, the hard ceiling, the vendor denylist.]**

> "This is the Policy layer, made visible. These thresholds — auto-pay zone, review zone, reject zone — and this absolute spending ceiling of ₹2,50,000, and the vendor deny-list — these are the *deterministic* rules. If an invoice trips a 'block' rule — a duplicate submission, a denylisted vendor, an amount over the ceiling — it gets **rejected no matter what the AI said.** The AI advises; policy decides. That inversion is what makes people comfortable letting the agent run."

### The audit log (Operations)

**[OPEN the Audit section — show the timestamped, searchable, expandable decision log.]**

> "And everything we just did lands here — an **append-only audit log**, timestamped, searchable, one expandable trail per decision. This survives restarts; it's persisted to disk. If a regulator asks 'why did you pay invoice X in August?' — the answer is right here, and no one can quietly edit it. This is the deliverable the whole system exists to produce."

---

## 5. The technology — ~2 minutes

**[OPTIONAL: show `/health`, `/docs`, or `/metrics` to prove it's a real service, not a mock.]**

> "A quick word on what this is built out of, because none of it is faked.
>
> - The backend is **Python and FastAPI** — a real REST service; here are the live API docs.
> - AI scoring goes through **LiteLLM**, a gateway that lets me swap between **four** providers — OpenAI, Groq, Hugging Face, Anthropic — just by changing the model name. No vendor lock-in.
> - And notice — I've been running this whole demo with **no API key at all.** When no LLM is reachable, it falls back to a transparent, rule-based scorer, so the system *always* produces an answer and *always* runs. `/health` tells you honestly which mode it's in — it never pretends an AI is live when it isn't.
> - Decisions and the audit trail persist to **SQLite**. There's a **Prometheus metrics** endpoint for monitoring, **MLflow** for tracking every scoring decision, and **Presidio** as an upgrade path for the PII redaction.
> - The whole thing is packaged with **Docker Compose** — a minimal stack, and a full enterprise stack that adds Keycloak, Langfuse, Prometheus, and Grafana for the identity and observability layers.
> - This front end is **React**; there's also a zero-dependency single-HTML dashboard as a fallback. And it's all covered by CI — nearly 130 tests across backend and frontend on every change."

---

## 6. The honest close — 60 seconds

> "Let me be straight about what's real today versus roadmap, because that honesty is kind of the whole spirit of the project.
>
> **Running and tested right now:** the full agent pipeline, three of the six governance layers — Data, Policy, and Audit — real LLM scoring through LiteLLM with the heuristic fallback, persistence, the API, both dashboards, role-based auth, OCR ingest, notifications, and metrics.
>
> **Roadmap:** the full identity and observability infrastructure — Keycloak, SPIRE, the containerized Langfuse and Grafana stack. Those are wired up as validated config; they just haven't been run on this locked-down machine yet.
>
> So what you've seen is a **working core** — an AP agent that makes real money decisions, wrapped in real governance — designed to slot into a full enterprise stack.
>
> The one-line takeaway: **the hard problem with AI agents isn't making them act. It's making them accountable when they do. Custodian is a working answer to that.**
>
> Happy to dig into any layer — questions?"

---

## Delivery notes

- **If a real LLM key is loaded,** change the INV-002/INV-004 patter to "the LLM scored it…" and mention scores may vary slightly — but the *routing* behavior is the same. Rehearse once with whatever mode you'll present in.
- **Timing:** if you're tight, cut §4's PII close-up and §5's list to just LiteLLM + the no-key fallback — those two land hardest.
- **The two lines that land best:** *"autonomous, but accountable"* (open) and *"the AI advises; policy decides"* (policy). Say them slowly.

---

## Default thresholds referenced above (from `src/custodian/config.py`)

| Setting | Env var | Default |
| ------- | ------- | ------- |
| Auto-pay max risk | `CUSTODIAN_AUTO_PAY_MAX_RISK` | 30 |
| Auto-pay max amount | `CUSTODIAN_AUTO_PAY_MAX_AMOUNT` | ₹5,000 |
| Reject min risk | `CUSTODIAN_REJECT_MIN_RISK` | 75 |
| Policy absolute ceiling | `CUSTODIAN_POLICY_MAX_AMOUNT` | ₹2,50,000 |
| Opening ledger balance | `CUSTODIAN_LEDGER_BALANCE` | ₹10,00,000 |
| High-risk notify threshold | `CUSTODIAN_NOTIFY_MIN_RISK` | 70 |
