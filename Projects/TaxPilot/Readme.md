# TaxPilot — Autonomous Indian Income-Tax Copilot

A production-style multi-agent system that turns a folder of tax documents into a
reviewed, explainable **draft** income-tax return for a resident individual
(**FY 2024-25 / AY 2025-26**). It is built with LangGraph, a pure-Python knowledge
base over the Income-tax Act (BM25, no downloads), a **deterministic tax engine**
that computes both the old and new regimes and keeps the cheaper, a heuristic
audit-risk scorer, a human-in-the-loop review gate, a FastAPI service and a web
console (a static single-page app served by FastAPI — no Node build).

The one idea the whole design turns on:

> **The LLM reads, retrieves, explains and spots anomalies. A deterministic Python
> engine does every rupee of arithmetic and names the section behind each figure.
> Nothing the model "says" ever becomes a number on the return.**

Tax law and tax math both change every Budget and both carry legal liability, so
the skill this project teaches is separating what a model is good at (reading
messy documents, retrieving and explaining sections) from what must be
deterministic and grounded (the computation and the cited authority).

The LLM backend is Claude (`claude-opus-4-8`) via the Anthropic SDK, or Google
Gemini with `LLM_PROVIDER=gemini`. **No key is required to run:** extraction,
classification and the report all have deterministic fallbacks, so the whole
pipeline — and the entire test suite — runs offline.

> `Todo.md` holds the original project brief and is maintained by hand. This
> README documents what is implemented and how to run it.

## The agent pipeline

```
intake ─blocked──────────────────────────────────────────────┐
   │                                                          │
extract → classify → research(RAG) → calculate → audit → review_gate
                                        ▲                    │  │
                                        └──corrections───────┘  │ (approved / none)
                                                                ▼
                                    report → guardrail_output → finalize → END
```

| Agent / stage | Where | What it does | Model? |
| --- | --- | --- | --- |
| Intake | `intake/` | Read files (OCR only when needed), route by document type | no |
| Guardrail (intake) | `guardrails/` | Shape, injection-in-document, PAN/Aadhaar inventory, LLM "is this tax docs" | partial |
| Extractor | `extraction/extractor.py` | Pull fields with per-field confidence | LLM, heuristic fallback |
| Classifier | `graph/nodes.py` · `classify_node` | Age band, residential status, regime preference; income normalized deterministically | LLM, text-parse fallback |
| Deduction researcher | `graph/nodes.py` · `research_node` | Propose deductions **grounded in retrieved Income-tax Act sections** | LLM (RAG), proofs deterministic |
| **Calculator** | **`calc/engine.py`** | **The deterministic engine. Computes both regimes, keeps the cheaper. No model call, ever.** | **no** |
| Audit-risk scorer | `audit/scorer.py` | Weighted red-flag heuristic → 0–100 score + band | no |
| Reviewer gate | `graph/nodes.py` · `review_gate_node` | `interrupt()` on low confidence / high risk / big rupees | no |
| Reporter | `graph/nodes.py` · `report_node` | Plain-language explanation, figures only from the engine | LLM, template fallback |
| Guardrail (output) | `guardrails/` | **Figure integrity**, section grounding, PAN/Aadhaar redaction, disclaimer, LLM review | partial |

### The founding rule, enforced

`guardrails` layer 4 (`figure_integrity`) is deterministic and is what makes "the
model never decides a number" an *enforced invariant*: every `₹`-amount in the
report must be a figure the engine computed, a published constant (a slab
threshold, the ₹1,50,000 80C ceiling, the ₹75,000 standard deduction …), or a
grounded deduction amount. A hallucinated refund is caught here no matter how
convincing the prose is. Offline the report is generated from the engine's lines
directly, so it passes by construction.

Every figure the engine emits is a `TaxLine` carrying the `rule_id` it applied,
and `knowledge/rules.py` is the single catalog both the engine and the grounding
check resolve against.

## What the engine computes (FY 2024-25)

Both regimes, side by side, keeping the lower tax (or the one you force):

- **New regime (Section 115BAC)** — the 0/5/10/15/20/30% slabs, the ₹75,000
  standard deduction, the Section 87A rebate up to ₹25,000 (tax-free to ₹7 lakh,
  with marginal relief), and no Chapter VI-A deductions.
- **Old regime** — the 0/5/20/30% slabs with the age-based basic exemption
  (₹2.5L / ₹3L senior / ₹5L super-senior), the ₹50,000 standard deduction, the
  Section 87A rebate up to ₹12,500, self-occupied home-loan interest under Section
  24(b) (capped ₹2 lakh), and Chapter VI-A deductions: 80C (₹1.5L), 80CCD(1B)
  (₹50k), 80D, 80TTA/80TTB, 80G.
- Surcharge above ₹50 lakh (with marginal relief; new-regime cap 25%), the 4%
  Health & Education Cess, and reconciliation against TDS to a refund or balance
  payable.

**Deliberately out of scope** (an input that needs one is a reviewer-gate
candidate, not a silent wrong answer): capital gains, business income, HRA
computation (a rent receipt is sent to review), and the Section 288A/288B
round-to-ten. The engine ships one year of constants and refuses any other year.

## Requirements

- Python 3.11+
- Optional: an Anthropic key (`ANTHROPIC_API_KEY`) or `ant auth login` profile —
  only needed to engage the LLM agents; the deterministic paths need nothing.
- Optional: the `ocr` extra + a Tesseract binary — only to read scanned images/PDFs.

## Quickstart (no key, no Docker, no downloads)

```bash
uv venv --python 3.13
uv pip install -e ".[dev]"

cp .env.example .env         # optional: add ANTHROPIC_API_KEY to engage the agents

tax-ingest                    # verify the rule corpus and the catalog agree
python scripts/smoke.py       # prepare the sample return end-to-end
tax-api                       # serves the web console AND the JSON API
```

Then open **http://127.0.0.1:8000/** for the web console (upload documents or use
the sample set, watch the pipeline run, and act on the reviewer gate). The same
server exposes the JSON API and its OpenAPI docs at `/docs`.

The sample documents under `data/documents/` describe a salaried resident (below
60) with a Form 16, a bank interest certificate, 80C and 80D proofs, a home-loan
interest certificate and Form 26AS.

## Using the web console

```bash
tax-api                 # then open http://127.0.0.1:8000/
```

The console is styled after a US-government portal (USWDS-inspired: a navy
masthead, an expandable official banner, alert boxes, a slim step indicator,
tabbed sections and an identifier footer) in **Public Sans** (the USWDS typeface)
on a single seven-step type scale. It has a **light/dark toggle** (top right,
remembered per browser) and a status pill. Content is split across tabs —
Summary, Report, Sources, Audit, Guardrails and Trace.

1. Pick one of the **sample shoeboxes** (five scenarios, from a ₹4.5 LPA single
   professional to a return that trips human review) or switch to **Upload** for
   your own `.txt`/`.md` documents, then click **Prepare return**.
2. The result shows a **pipeline step indicator** (which of the eight agent stages
   ran), the computed metrics, and an **old-vs-new regime comparison** with the
   rupee saving of the chosen regime — every line tagged with its section, plus the
   audit meter and guardrail chips. **Download draft (JSON)** or **Print** the draft.
3. If a return trips the reviewer gate (for example an HRA claim from a rent
   receipt), a review alert appears — force a regime or drop a deduction, then
   **Approve / apply corrections** to recompute.

Notes:

- With no `ANTHROPIC_API_KEY` set, the console runs fully offline (deterministic
  extraction, classification and report). Add a key to `.env` and restart to
  engage the LLM agents.
- Run the server from the project's virtualenv. `tax-api` works when the venv is
  active; otherwise call it explicitly (works from any directory — the package is
  installed editable):

  ```bash
  # Windows
  .venv/Scripts/python -m uvicorn taxpilot.api.main:app --host 127.0.0.1 --port 8000
  # macOS/Linux
  .venv/bin/python -m uvicorn taxpilot.api.main:app --host 127.0.0.1 --port 8000
  ```

  A globally-installed server won't have `taxpilot` or its dependencies on its path.

### Changing the font

The whole console draws from one CSS variable. Edit **`--font`** in
[`web/styles.css`](web/styles.css) (in the `:root` block, marked "CHANGE THE FONT
HERE") and refresh the browser — no restart, the server serves the file fresh:

```css
--font: "Public Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
```

- Fonts already loaded (just swap the first name): `"Public Sans"`,
  `"Source Sans 3"`, `"Libre Franklin"`, `"Merriweather"` (serif).
- A locally-installed font (no download) works too, e.g. `"Georgia"`, `"Segoe UI"`.
- For a **new** Google font, add its `family=` to the `<link>` in
  [`web/index.html`](web/index.html), then name it in `--font`. The `<link>` alone
  does nothing — `--font` is what applies it.

Verify without spending tokens:

```bash
tax-ingest                    # corpus/catalog consistency check
pytest -q                     # offline suite
```

## API

```bash
# Prepare from the configured documents directory
curl -s localhost:8000/prepare -H 'content-type: application/json' -d '{}' \
  | jq '.regime, .tax_return.total_tax, .tax_return.refund_or_due, .awaiting_review'

# Or send documents inline
curl -s localhost:8000/prepare -H 'content-type: application/json' -d '{
  "documents": [
    {"filename":"profile.txt","text":"Age category: below 60\nTax regime: new"},
    {"filename":"form16.txt","text":"FORM 16\nGross salary: 12,00,000\nTotal tax deducted: 0"}
  ]}' | jq '.tax_return.total_income, .tax_return.total_tax'

# A return that needs review comes back awaiting_review with the reasons
curl -s localhost:8000/pending/<thread_id> | jq
curl -s localhost:8000/resume -H 'content-type: application/json' \
  -d '{"thread_id":"<thread_id>","corrections":[{"target":"regime","value":"old"}]}'
```

## Configuration

All settings live in `.env` (see `.env.example`). The knobs that matter most:

| Variable | Default | Effect |
| --- | --- | --- |
| `LLM_PROVIDER` | `anthropic` | `anthropic` or `gemini`; blank key → deterministic paths |
| `TAX_YEAR` | `2024` | FY start year (2024 == FY 2024-25); the only year the engine has |
| `EXTRACTION_CONFIDENCE_FLOOR` | `0.75` | Below this a field flags the return for review |
| `REVIEW_RISK_THRESHOLD` | `60` | Audit score at/above which a human must sign off |
| `REVIEW_AMOUNT_THRESHOLD` | `100000` | Refund/payable magnitude (₹) that also forces review |
| `ENABLE_RAG` / `_AUDIT` / `_REVIEW` / `_GUARDRAILS` | `true` | Turning a flag off removes those nodes from the compiled graph |

## Why the design looks like this

- **The engine is a separate, model-free module.** Given the same inputs it always
  produces the same return, which is what makes a figure defensible to the
  assessing officer. `tests/test_engine.py` checks it against hand-computed
  FY 2024-25 numbers, including the regime comparison and the 87A rebate.
- **Citations come from one catalog.** `knowledge/rules.py` is the single source of
  truth; `tax-ingest` fails if a corpus file cites a section the catalog does not
  know, because that drift is exactly what silently breaks grounding.
- **Failing open is reported, not hidden.** The LLM-backed guardrail layers degrade
  to `action="skip"` with `passed=False` during an outage, and the UI/smoke output
  reads "N of M layers ran" rather than a row of green ticks.
- **Human corrections write back.** A resolved review appends to
  `feedback/corrections.jsonl`; the recompute loop applies the correction through
  the deterministic engine exactly once.

## Project layout

```
src/taxpilot/
  config.py            settings; blank keys select deterministic fallbacks
  money.py             rupee formatting with Indian (lakh/crore) grouping
  models.py            shared pydantic models (money is whole-rupee ints)
  certs.py             OS trust-store injection for TLS-inspecting proxies
  observability.py     logging + per-node timing
  llm/                 provider-agnostic client (Anthropic/Gemini) + frozen prompts
  intake/              OCR abstraction + document loader/type routing
  extraction/          field extraction (LLM/heuristic) + deterministic normalization
  knowledge/           section catalog, BM25 store, retriever, `tax-ingest`
  calc/                the deterministic engine — no LLM below this line
  audit/               weighted red-flag audit-risk scorer
  guardrails/          detectors + inbound/outbound pipeline (figure integrity)
  graph/               state, nodes, builder, public prepare()/resume()
  api/                 FastAPI service (JSON API + serves the web console at /)
data/corpus/           Income-tax Act excerpts (one topic per file)
data/documents/        a sample set of Indian tax documents
web/                   static single-page console (index.html, app.js, styles.css)
tests/                 offline suite (no API key needed)
```

## Status

Verified on this machine (Windows, Python 3.13, no API key, `huggingface.co`
blocked — none of it needed):

- **The engine matches hand-computed FY 2024-25 figures** — new-regime slabs, the
  old-regime age exemptions, the 87A rebate (both regimes), the regime comparison,
  the Chapter VI-A caps and the standard deduction (`tests/test_engine.py`).
- **The full pipeline is exactly reproducible offline.** Over the sample documents
  it picks the **new regime**, computes total income **₹13,55,000**, total tax
  **₹1,15,440** and a **₹4,560 refund** (old-regime tax **₹1,18,560** shown for
  comparison), every line tagged with its section. `python scripts/smoke.py`
  prints the full return, trace and guardrail panel.
- **The founding invariant holds.** `figure_integrity` blocks a report that states
  a rupee figure the engine did not compute; the deterministic report passes it by
  construction.
- **The reviewer gate interrupts and resumes.** An HRA rent receipt forces review;
  resuming with a correction recomputes through the engine once and finishes.
- **Guardrails fail open honestly**, PAN is redacted and Aadhaar masked to its last
  four, and retrieval finds the right section for salary/80C/24(b)/slab/87A queries.

Not yet verified here (no `ANTHROPIC_API_KEY` was exercised): the LLM paths for
extraction, classification, the researcher's RAG proposals, the report narrative
and the two LLM guardrail layers. Each has a deterministic fallback the suite
covers; `python scripts/smoke.py` with a key set closes the gap.

## Known gaps

- The engine models the common salaried-resident path (see "What the engine
  computes"); capital gains, business income, HRA computation and the 288A/288B
  round-to-ten are out of scope and route to review rather than being approximated.
- Surcharge marginal relief is implemented but lightly tested (sample incomes are
  below ₹50 lakh).
- The checkpointer is `MemorySaver`, so a paused review is lost on restart and does
  not survive more than one API worker. Swap in `langgraph-checkpoint-postgres`.
- "Write-back to improve future runs" is a feedback log, not model retraining.
- The audit scorer is a transparent heuristic, not a model trained on real
  selection data. The corpus is a small hand-written set of excerpts, not the full
  Income-tax Act.
- `figure_integrity` checks `₹`/`Rs`-prefixed amounts of ₹100 or more (avoiding
  false positives on years and counts); the LLM output-review layer backs it up.

## Execution 
Without an API key (deterministic mode) — nothing to configure:

```
cd "C:/Users/2327238/Documents/dev/ai/Internal Switch/Projects/TaxPilot"
.venv/Scripts/python.exe -m uvicorn taxpilot.api.main:app --host 127.0.0.1 --port 8000
```

With an API key (LLM mode):

```
cd "C:/Users/2327238/Documents/dev/ai/Internal Switch/Projects/TaxPilot"
$env:ANTHROPIC_API_KEY = "sk-ant-..."
.venv/Scripts/python.exe -m uvicorn taxpilot.api.main:app --host 127.0.0.1 --port 8000
```