# Custodian — Bank Accounts-Payable AI Agent System with Advanced AI Governance

> A governed, multi-agent finance-ops platform where AI agents read invoices, score them for fraud and risk, route approvals, and auto-pay the safe ones — with **six real governance layers** wrapping the agent runtime so every action is **auditable and provable after the fact**.

This is a **full Docker stack calling real LLMs** (OpenAI + Groq via LiteLLM), not a mocked demo.

---

## Table of Contents

- [Custodian — Bank Accounts-Payable AI Agent System with Advanced AI Governance](#custodian--bank-accounts-payable-ai-agent-system-with-advanced-ai-governance)
  - [Table of Contents](#table-of-contents)
  - [What Is This?](#what-is-this)
  - [Why It Matters](#why-it-matters)
  - [System Architecture](#system-architecture)
  - [The Six Governance Layers](#the-six-governance-layers)
  - [The Agent Pipeline](#the-agent-pipeline)
  - [Technology Stack](#technology-stack)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Configuration](#configuration)
  - [Observability \& Audit](#observability--audit)
  - [What You'll Learn](#what-youll-learn)
    - [What You'll Build](#what-youll-build)
  - [Project Layout](#project-layout)
  - [Security Notes](#security-notes)
  - [License](#license)

---

## What Is This?

**Custodian** is a production-style, multi-agent AI system for **accounts payable (AP)** automation in a banking / finance-ops context. Instead of a chatbot, the agents make *autonomous operational decisions*:

1. **Read** incoming invoices (OCR + structured extraction).
2. **Score** each invoice for fraud and financial risk.
3. **Route** approvals based on policy and risk thresholds.
4. **Auto-pay** the invoices that are provably safe, and escalate the rest to humans.

Wrapped around the agent runtime are **six governance layers** — Identity, Data, Model, Policy, Agent Runtime, and Operations — that watch every action and can reconstruct **exactly what happened and why**, long after the fact.

---

## Why It Matters

Autonomous agents that move money are only useful if they're **trustworthy**. Custodian treats governance as a first-class architectural concern rather than an afterthought:

- **Every agent action is attributable** to a verified identity.
- **PII never leaks** into model prompts or logs unredacted.
- **Model calls are gated, versioned, and traced.**
- **Policy decides** what an agent is allowed to do, not the agent itself.
- **Everything is observable** and reconstructable for audit and compliance.

---

## System Architecture

```
                          ┌──────────────────────────────────────────┐
                          │              Console UI                    │
                          │   (operators, approvers, auditors)         │
                          └────────────────────┬───────────────────────┘
                                               │
                          ┌────────────────────▼───────────────────────┐
                          │              Control Plane                   │
                          │   orchestrates agents, enforces workflow     │
                          └────────────────────┬───────────────────────┘
                                               │
        ┌──────────────────────────────────────┼──────────────────────────────────────┐
        │                                       │                                        │
┌───────▼────────┐              ┌───────────────▼───────────────┐            ┌───────────▼──────────┐
│ OCR / Data Svc │              │        Agent Runtime           │            │        Ledger        │
│ invoice intake │──extracted──▶│  Reader → Risk → Approval →     │──pay──────▶│ balances, payments,  │
│ + extraction   │   fields     │  Payment agents                 │            │ immutable audit trail│
└────────────────┘              └───────────────┬───────────────┘            └──────────────────────┘
                                                 │
                        ┌────────────────────────┼────────────────────────┐
                        │      Governance planes surround every call        │
                        │  Identity · Data · Model · Policy · Runtime · Ops  │
                        └───────────────────────────────────────────────────┘
```

At a high level:

- **Console UI** — where operators, approvers, and auditors interact with the system.
- **Control Plane** — orchestrates the agents and enforces the AP workflow.
- **OCR / Data Services** — ingest and structure raw invoices.
- **Agent Runtime** — the multi-agent decision engine (read → score → route → pay).
- **Ledger** — the source of truth for balances, payments, and the immutable audit trail.
- **Real LLMs** — reached exclusively through the **LiteLLM** gateway (OpenAI + Groq).

---

## The Six Governance Layers

Each layer maps to concrete, running infrastructure. Nothing is hand-waved.

| # | Layer | Responsibility | Backed By |
|---|-------|----------------|-----------|
| 1 | **Identity** | Who (human or workload) is acting, and are they allowed to? Strong auth + cryptographic workload identity. | **Keycloak** (OIDC/SSO), **SPIRE** (SPIFFE workload identity) |
| 2 | **Data** | Protect and govern sensitive data; strip PII before it reaches a model or a log. | **Presidio** (PII detection/redaction), **OpenMetadata** (catalog & lineage), **Infisical** (secrets) |
| 3 | **Model** | Gate, version, and route every LLM call; track which model/version made which decision. | **LiteLLM** (model gateway), **MLflow** (model registry & tracking) |
| 4 | **Policy** | Decide what agents are *permitted* to do — approval thresholds, spend limits, segregation of duties. | Policy engine + declarative rules |
| 5 | **Agent Runtime** | Safely execute agents with guardrails, tool restrictions, and per-action authorization. | Orchestrated agent runtime |
| 6 | **Operations** | Make the whole system observable, traceable, and reconstructable after the fact. | **Langfuse** (LLM tracing), **Prometheus** + **Grafana** (metrics & dashboards) |

The core promise: **any decision the system makes can be traced back through all six layers** — who triggered it, what data was used, which model version produced it, which policy allowed it, how the runtime executed it, and what the operational telemetry recorded.

---

## The Agent Pipeline

The AP workflow is handled by cooperating agents:

1. **Reader Agent** — Consumes OCR output, normalizes invoice fields (vendor, amount, dates, line items), and flags malformed or incomplete documents.
2. **Risk / Fraud Agent** — Scores each invoice against fraud signals and risk heuristics (duplicate payments, vendor anomalies, amount outliers, mismatched terms).
3. **Approval Router** — Applies policy: low-risk within limits → auto-approve; anything above threshold → route to a human approver.
4. **Payment Agent** — Executes payment against the ledger *only* for provably-safe, policy-cleared invoices, writing an immutable audit record.

Every hop crosses the governance planes: identity is verified, PII is redacted, the model call is gated and traced, and policy has the final say before money moves.

---

## Technology Stack

| Category | Tools |
|----------|-------|
| **Identity & Auth** | Keycloak, SPIRE (SPIFFE) |
| **Data Privacy & Secrets** | Presidio, OpenMetadata, Infisical |
| **Model Gateway & Registry** | LiteLLM, MLflow |
| **LLM Providers** | OpenAI, Groq |
| **Observability** | Langfuse, Prometheus, Grafana |
| **Runtime & Packaging** | Docker / Docker Compose |
| **Application** | Console UI, Control Plane, Ledger, OCR/Data services |

---

## Prerequisites

Before you start, you should have:

- **Docker** and **Docker Compose** installed and running.
- A machine with enough headroom to run a multi-container stack (8 GB+ RAM recommended).
- **API keys** for at least one LLM provider — **OpenAI** and/or **Groq**.
- Basic familiarity with containers, environment variables, and REST APIs.
- (Helpful) Comfort reading logs and navigating dashboards like Grafana.

---

## Quick Start

> Exact service names and ports depend on your `docker-compose.yml`. Adjust as needed.

```bash
# 1. Clone
git clone <your-repo-url> custodian
cd custodian

# 2. Configure environment
cp .env.example .env
#   → fill in OPENAI_API_KEY / GROQ_API_KEY and any secrets

# 3. Bring up the full stack
docker compose up -d

# 4. Check that everything is healthy
docker compose ps

# 5. Open the interfaces (default local ports — adjust to your compose file)
#   Console UI ........ http://localhost:3000
#   Keycloak .......... http://localhost:8080
#   LiteLLM ........... http://localhost:4000
#   MLflow ............ http://localhost:5000
#   Langfuse .......... http://localhost:3001
#   Grafana ........... http://localhost:3002
#   Prometheus ........ http://localhost:9090
#   OpenMetadata ...... http://localhost:8585
```

To tear everything down:

```bash
docker compose down          # stop
docker compose down -v       # stop and remove volumes (wipes state)
```

---

## Configuration

Configuration is driven by environment variables (see `.env.example`). Typical values include:

```bash
# LLM providers (reached only through LiteLLM)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk-...

# Model gateway
LITELLM_MASTER_KEY=...

# Identity
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=...

# Secrets management
INFISICAL_TOKEN=...

# Observability
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...

# Policy thresholds (example)
AUTO_PAY_MAX_AMOUNT=5000
RISK_SCORE_APPROVAL_THRESHOLD=0.3
```

> **Never commit real secrets.** Use `Infisical` for runtime secret injection and keep `.env` out of version control.

---

## Observability & Audit

Because auditability is the whole point, Custodian ships with layered observability:

- **Langfuse** — end-to-end tracing of every LLM call: prompt, model, version, latency, cost, and output.
- **MLflow** — model registry and experiment/version tracking, so each decision links to a known model version.
- **Prometheus** — metrics collection across services.
- **Grafana** — dashboards for system health, throughput, and agent decision stats.
- **OpenMetadata** — data catalog and lineage, so you can see where invoice data came from and where it flowed.
- **Ledger audit trail** — an immutable record of every approval and payment.

Together these let you answer, for **any** past payment: *who, what data, which model, which policy, how executed, and what did the telemetry show.*

---

## What You'll Learn

This project is structured as a **21-lecture curriculum**. By the end you'll know:

- **How to build and orchestrate a real multi-agent AI system** that makes autonomous decisions (invoice approval/payment) rather than just chatting.
- **How to wrap AI agents in production-grade governance** — identity, data privacy, policy enforcement, and auditability — so their actions are trustworthy and provable.
- **How to run a full real-world microservices + observability stack** (Docker, LiteLLM, MLflow, Langfuse, Prometheus/Grafana) integrated with **actual LLM providers**, not a toy demo.

### What You'll Build

- A **multi-agent AI system** that reads invoices, scores them for fraud/risk, routes approvals, and automatically pays the safe ones.
- **Six governance layers** — Identity, Data, Model, Policy, Agent Runtime, Operations — that watch every agent action and can prove after the fact exactly what happened and why.
- A **full production-style stack** (console UI, control plane, ledger, OCR/data services) wired to real LLMs via LiteLLM, with observability through MLflow, Langfuse, Prometheus, and Grafana.

---

## Project Layout

> Illustrative structure — adapt to your actual repository.

```
custodian/
├── docker-compose.yml         # full stack definition
├── .env.example               # environment template
├── console-ui/                # operator / approver / auditor frontend
├── control-plane/             # workflow + agent orchestration
├── agents/
│   ├── reader/                # invoice reading & normalization
│   ├── risk/                  # fraud / risk scoring
│   ├── approval/              # policy-based approval routing
│   └── payment/               # ledger payment execution
├── services/
│   ├── ocr/                   # invoice OCR / extraction
│   └── ledger/                # balances, payments, audit trail
├── governance/
│   ├── identity/              # Keycloak, SPIRE config
│   ├── data/                  # Presidio, OpenMetadata, Infisical
│   ├── model/                 # LiteLLM, MLflow config
│   └── policy/                # policy rules & engine
├── observability/             # Prometheus, Grafana, Langfuse
└── docs/                      # architecture & lecture notes
```

---

## Security Notes

- All LLM traffic is routed through **LiteLLM** — no service talks to OpenAI/Groq directly.
- **PII is redacted with Presidio** before data reaches a model or a log.
- Secrets live in **Infisical**, not in source or plaintext `.env` in production.
- Workloads authenticate with **SPIRE/SPIFFE** identities; humans authenticate through **Keycloak**.
- **Policy** — not the agent — has final authority over whether money moves.
- The ledger keeps an **immutable audit trail** for every payment.

> This is a learning/reference architecture. Harden identity, secrets, network policies, and policy rules before using anything like it against real funds.

---

## License

Add your chosen license here (e.g. MIT, Apache-2.0).

---

*Custodian demonstrates that autonomous, money-moving AI agents can be **safe, governed, and provable** — the governance is the product, not the paperwork.*