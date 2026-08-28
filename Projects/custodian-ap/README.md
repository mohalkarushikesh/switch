# Custodian — Bank Accounts-Payable AI Agent System

> A governed, multi-agent finance-ops platform. AI agents read invoices, score them for
> fraud/risk, route approvals, and auto-pay the safe ones — with six real governance layers
> wrapping the runtime so every agent action is auditable and provable after the fact.

This is **not a mocked demo**. It runs a full Docker stack and calls real LLM providers
(OpenAI + Groq via LiteLLM).

---

## Table of Contents

- [Overview](#overview)
- [What You'll Build](#what-youll-build)
- [Governance Layers](#governance-layers)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [What You Will Learn](#what-you-will-learn)
- [Project Structure](#project-structure)

---

## Overview

**Custodian** is a multi-agent AI system for banking accounts-payable operations. Instead of
just chatting, the agents make **autonomous decisions**: they ingest invoices, assess fraud and
risk, route items for approval, and automatically release payment for the ones deemed safe.

Around that agent runtime sit **six governance layers** — Identity, Data, Model, Policy, Agent
Runtime, and Operations — that observe every action so the system can prove, after the fact,
exactly *what* happened and *why*.

## What You'll Build

- **A multi-agent AI system** that reads invoices, scores them for fraud/risk, routes approvals,
  and automatically pays the safe ones.
- **Six governance layers** (Identity, Data, Model, Policy, Agent Runtime, Operations) that watch
  every agent action and can reconstruct the full decision trail.
- **A production-style stack** — console UI, control plane, ledger, and OCR/data services — wired
  to real LLMs via LiteLLM, with end-to-end observability through MLflow, Langfuse, Prometheus,
  and Grafana.

## Governance Layers

| Layer             | Responsibility                                                        | Backed by            |
| ----------------- | --------------------------------------------------------------------- | -------------------- |
| **Identity**      | Authenticate and authorize agents & workloads                         | Keycloak, SPIRE      |
| **Data**          | Protect and catalog data; redact PII                                  | Presidio, OpenMetadata |
| **Model**         | Manage model access, routing, and tracking                            | LiteLLM, MLflow      |
| **Policy**        | Enforce business & compliance rules on agent decisions                | Policy engine        |
| **Agent Runtime** | Execute and coordinate the agents                                     | Agent orchestrator   |
| **Operations**    | Observe, trace, and alert on system behavior                          | Langfuse, Prometheus, Grafana |

Every agent action flows through these layers, making the entire pipeline **auditable and
provable**.

## System Architecture

The system is composed of an agent runtime surrounded by the six governance layers, fronted by a
console UI and backed by supporting services (control plane, ledger, OCR/data services).

> **Architecture diagram:** _add the high-level architecture diagram here_ (e.g.
> `docs/architecture.png`).

```
                 ┌───────────────────────────────────────────────┐
                 │                   Console UI                    │
                 └───────────────────────┬───────────────────────┘
                                         │
   ┌─────────── Governance Layers ───────┼──────────────────────────────┐
   │  Identity · Data · Model · Policy · Agent Runtime · Operations      │
   └─────────────────────────────────────┼──────────────────────────────┘
                                         │
        ┌────────────────┬───────────────┼───────────────┬────────────────┐
        │  Control Plane │     Ledger     │  OCR / Data    │  LLMs (LiteLLM)│
        └────────────────┴────────────────────────────────┴────────────────┘
```

## Technology Stack

| Category           | Tools                                              |
| ------------------ | -------------------------------------------------- |
| **Identity**       | Keycloak, SPIRE                                    |
| **Secrets**        | Infisical                                          |
| **Data / Privacy** | OpenMetadata, Presidio                             |
| **LLM Gateway**    | LiteLLM (OpenAI + Groq)                            |
| **ML / Tracking**  | MLflow                                             |
| **Observability**  | Langfuse, Prometheus, Grafana                      |
| **Runtime**        | Docker / Docker Compose                            |

## Prerequisites

- **Docker** and **Docker Compose** installed.
- API keys for the LLM providers: **OpenAI** and **Groq**.
- Familiarity with containerized microservices and basic AI-agent concepts.

> _Fill in exact versions, environment variables, and required accounts as the project takes
> shape._

## What's Built Today

The runnable slice of the platform:

- **Agent pipeline** — ingest → risk/fraud scoring → approval routing → auto-pay, over a mock ledger.
- **Real LLM scoring** via LiteLLM (OpenAI/Groq), with a transparent heuristic fallback so it runs
  with **no API keys**.
- **Three governance layers** — Data (PII redaction before anything reaches the LLM), Policy (hard
  rules that can override risk-based decisions, including duplicate-invoice blocking), and Audit
  (append-only log of every decision).
- **SQLite persistence** — processed invoices and the audit trail survive restarts; the ledger
  balance is reconstructed from paid invoices on startup.
- **REST API** (FastAPI) with **two dashboards**: a zero-build single-file console at `/ui`, and a
  richer **React (Vite) app** at `/app` — governance overview, pipeline visualization, risk
  breakdown, OCR submission, stats, a "needs attention" feed, and the review queue.
- **Prometheus `/metrics`** endpoint for the observability layer.
- **PII backend is pluggable** — dependency-free regex by default, or Microsoft **Presidio**
  (`CUSTODIAN_PII_BACKEND=presidio`), which degrades back to regex if unavailable.
- **API-key authentication with roles** — submitter / reviewer / admin on the state-changing
  endpoints (`CUSTODIAN_API_KEYS`); off by default, reads stay open.
- **OCR ingest** — parse OCR-style invoice text into structured invoices (`POST /invoices/ocr`).
- **Notifications** — rejected or high-risk invoices fire a webhook and/or JSONL log entry.
- **Two Docker stacks** — a minimal one (API + LiteLLM) and a full governance/observability stack
  (`docker-compose.infra.yml`: Keycloak, Postgres, Langfuse, Prometheus, Grafana, SPIRE).

The rest of the target architecture (Keycloak, SPIRE, Infisical, OpenMetadata, MLflow, Langfuse,
Prometheus/Grafana) is the roadmap these layers plug into.

## Getting Started

Works **with no API keys** (heuristic scoring); add an OpenAI or Groq key to switch scoring to a
real LLM via LiteLLM.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) configure an LLM provider + governance settings
cp .env.example .env          # add OPENAI_API_KEY / GROQ_API_KEY, tweak thresholds

# --- Run any of the three entry points ---

# a) CLI on the bundled sample invoices (src/ layout -> set PYTHONPATH)
PYTHONPATH=src python -m custodian.main

# b) REST API + dashboards
PYTHONPATH=src uvicorn custodian.api:app --reload
#    -> API docs:        http://localhost:8000/docs
#    -> Console UI:      http://localhost:8000/ui/       (zero-build, always available)
#    -> React app:       http://localhost:8000/app/      (after building it, see below)

# b2) Build the React web app (served at /app; dev server with live reload on :5173)
cd web && npm install && npm run build      # -> /app/ starts serving
#   npm run dev                             # optional: hot-reload dev server, proxies API to :8000
#   full front-end run instructions: web/README.md

# c) Docker stack (API + LiteLLM gateway)
docker compose up --build      # -> http://localhost:8000/ui/

# d) FULL governance/observability stack (adds Keycloak, Postgres, Langfuse,
#    Prometheus, Grafana, SPIRE). Reference config — validated, not yet run here.
docker compose -f docker-compose.infra.yml up --build
#    Keycloak http://localhost:8080 · Langfuse http://localhost:3001
#    Prometheus http://localhost:9090 · Grafana http://localhost:3002

# Run the tests (56 pass + 1 skipped without the Presidio model; offline, in-memory DB)
python -m pytest tests/ -q
```

> **PowerShell (Windows):** the `PYTHONPATH=src <cmd>` prefix is bash syntax. In PowerShell set
> the env var first, then run the command:
>
> ```powershell
> $env:PYTHONPATH="src"; python -m custodian.main
> $env:PYTHONPATH="src"; uvicorn custodian.api:app --reload
> ```

### API endpoints

Write endpoints (POST) accept an `X-API-Key` header when auth is enabled
(`CUSTODIAN_API_KEYS`); submit requires the `submitter` role, approve/reject require
`reviewer` (`admin` may do anything). Reads are open.

| Method | Path                          | Purpose                                        |
| ------ | ----------------------------- | ---------------------------------------------- |
| GET    | `/health`                     | Liveness + active scoring mode                 |
| POST   | `/invoices`                   | Submit one invoice through the pipeline        |
| POST   | `/invoices/ocr`               | Submit OCR-style invoice text (parsed → pipeline) |
| POST   | `/invoices/batch`             | Submit many invoices                           |
| GET    | `/invoices`                   | List (filter by `status`, `min_risk`, `max_risk`) |
| GET    | `/invoices/{id}`              | Fetch one processed invoice                    |
| POST   | `/invoices/{id}/approve`      | Reviewer approves a queued invoice → pays it   |
| POST   | `/invoices/{id}/reject`       | Reviewer rejects a queued invoice              |
| GET    | `/ledger`                     | Ledger balance + transactions                  |
| GET    | `/stats`                      | Aggregate counts + totals                      |
| GET    | `/policies`                   | Active policy-governance configuration         |
| GET    | `/audit`                      | Persisted audit log entries (SQLite-backed)    |
| GET    | `/metrics`                    | Prometheus metrics for the observability stack |

## What You Will Learn

- **How to build and orchestrate a real multi-agent AI system** that makes autonomous decisions
  (invoice approval/payment) instead of just answering questions.
- **How to wrap AI agents in production-grade governance** — identity, data privacy, policy
  enforcement, and auditability — so their actions are trustworthy and provable.
- **How to run a full real-world microservices + observability stack** (Docker, LiteLLM, MLflow,
  Langfuse, Prometheus/Grafana) integrating actual LLM providers, not a toy demo.

_The course spans **21 lectures** covering Overview, Prerequisites, Curriculum, and Technologies._

## Project Structure

```
BankPayeeAgent/
├── README.md                     # this file
├── requirements.txt              # Python dependencies
├── .env.example                  # config template (LLM keys, thresholds, governance)
├── Dockerfile                    # API image
├── docker-compose.yml            # minimal stack: API + LiteLLM gateway
├── docker-compose.infra.yml      # full stack: + Keycloak/Postgres/Langfuse/Prometheus/Grafana/SPIRE
├── data/
│   ├── sample_invoices/          # example invoices to run the pipeline on
│   └── sample_ocr/               # example OCR-text invoices for /invoices/ocr
├── deploy/
│   ├── litellm.config.yaml       # LiteLLM gateway model routing
│   └── infra/
│       ├── prometheus.yml        # Prometheus scrape config (targets the API)
│       ├── spire-server.conf     # SPIRE server config (illustrative)
│       └── grafana/provisioning/ # Grafana datasource auto-provisioning
├── ui/
│   └── index.html                # zero-build console dashboard (served at /ui/)
├── web/                          # React (Vite) app — served at /app/ after `npm run build`
│   └── src/
│       ├── App.jsx               # layout, data loading, polling
│       ├── api.js                # backend client (attaches X-API-Key on writes)
│       └── components/           # Overview, StatsBar, SubmitPanel, Pipeline, InvoiceTable, Attention
├── src/
│   └── custodian/
│       ├── config.py             # settings loaded from env / .env
│       ├── models.py             # typed invoice / assessment / decision / policy models
│       ├── llm.py                # LiteLLM wrapper (direct or via gateway; graceful fallback)
│       ├── ledger.py             # mock ledger / payment rail
│       ├── store.py              # in-memory processed-invoice store (legacy/fallback)
│       ├── db.py                 # SQLite persistence: durable store + audit log
│       ├── ocr.py                # OCR-text → invoice-field extraction
│       ├── notify.py             # notifications (log / webhook) for flagged invoices
│       ├── orchestrator.py       # chains agents + governance into one pipeline
│       ├── main.py               # CLI entrypoint
│       ├── api.py                # FastAPI service + dashboard mount
│       ├── agents/
│       │   ├── ingest.py         # invoice ingest / validation
│       │   ├── risk.py           # fraud & risk scoring (LLM + heuristic)
│       │   ├── approval.py       # approval routing (risk thresholds)
│       │   └── payment.py        # auto-pay against the ledger
│       └── governance/
│           ├── data.py           # PII redaction (regex or Presidio backend)
│           ├── policy.py         # hard-rule policy engine (+ duplicate detection)
│           └── audit.py          # append-only JSONL audit log
└── tests/
    ├── conftest.py               # shared test setup (src path, offline, in-memory DB)
    ├── test_pipeline.py          # end-to-end pipeline tests
    ├── test_api.py               # REST API tests
    ├── test_governance.py        # data / policy / audit tests
    ├── test_persistence.py       # SQLite store + duplicate-detection tests
    ├── test_auth.py              # API-key auth + role enforcement tests
    ├── test_notify.py            # notification (rejected / high-risk) tests
    ├── test_ocr.py               # OCR text-extraction tests
    └── test_pii_presidio.py      # Presidio backend tests (skip if model absent)
```
