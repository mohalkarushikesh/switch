# AI Platform Reference Architecture

---

# Identity Layer

## Keycloak

**Keycloak** is an open-source Identity and Access Management (IAM) platform that provides authentication, authorization, and Single Sign-On (SSO) for applications and services.

### Key Features

- **OIDC (OpenID Connect)** → Authentication
- **OAuth 2.0** → Authorization
- **SAML** → Enterprise Single Sign-On (SSO)
- **Centralized User Management** → Users, Roles, Permissions, Groups

---

### OIDC (OpenID Connect)

**Purpose:** Authentication ("Who are you?")

#### Flow

```text
User
  │
  ▼
Application
  │
  ▼
Keycloak
  │
  ▼
Login & Verify
  │
  ▼
ID Token (JWT)
  │
  ▼
Application
```

#### Steps

1. User attempts to log in.
2. Application redirects user to Keycloak.
3. Keycloak authenticates the user.
4. Keycloak issues an ID Token (JWT).
5. Application validates the token and signs the user in.

✅ Example: *"Who are you?"*

---

### OAuth 2.0

**Purpose:** Authorization ("What can you access?")

#### Flow

```text
User
  │
  ▼
Application
  │
  ▼
Request Access
  │
  ▼
Keycloak
  │
  ▼
Access Token
  │
  ▼
API / Service
```

#### Steps

1. User grants permissions.
2. Keycloak generates an Access Token.
3. Application uses the token to call APIs.
4. APIs validate the token before granting access.

✅ Example: *"What are you allowed to do?"*

---

### SAML : Security Assertion Markup Language   

**Purpose:** Enterprise Single Sign-On

#### Flow

```text
User
  │
  ▼
Corporate Portal
  │
  ▼
SAML Request
  │
  ▼
Identity Provider
  │
  ▼
SAML Assertion
  │
  ▼
Application
```

#### Steps

1. User logs in once to a corporate identity provider.
2. Identity provider generates a SAML Assertion.
3. Application validates the assertion.
4. User gains access without re-entering credentials.

✅ Example: *"Log in once, access many enterprise applications."*

---

### Quick Memory Trick

```text
OIDC  → Authentication → Who are you?
OAuth → Authorization  → What can you access?
SAML  → Enterprise SSO → Login once everywhere
```

---

### Keycloak in an AI Platform

```text
Keycloak
├── OIDC  → User login to AI applications
├── OAuth → Agent/API access tokens
└── SAML  → Corporate SSO integrations
```

---

## SPIRE

**SPIRE** (Secure Production Identity Framework for Everyone) provides cryptographically verifiable identities for workloads and services.

### Key Features

- **Workload Identity** → Unique identity for services and agents
- **Short-Lived Credentials** → Automatic certificate rotation
- **Zero Static Secrets** → No hardcoded passwords or API keys
- **Authentication Only** → Authorization handled by external policy engines (OPA)

### Flow

```text
Workload
   │
   ▼
SPIRE Agent
   │
   ▼
SPIRE Server
   │
   ▼
X.509 / JWT-SVID
   │
   ▼
Authenticated Service
```

---

# Data Layer

## Presidio

**Microsoft Presidio** is an open-source framework for detecting and protecting sensitive data.

### Key Features

- **PII Detection**
  - Names
  - Emails
  - Phone Numbers
  - Credit Cards
  - Addresses

- **Data Anonymization**
  - Masking
  - Redaction
  - Replacement

### Example

```text
Input:
John Doe's email is john@email.com

Output:
<PERSON> email is <EMAIL_ADDRESS>
```

---

## OpenMetadata

**OpenMetadata** is an open-source metadata platform used for data discovery, governance, and cataloging.

### Key Features

- **Data Catalog**
- **Data Discovery**
- **Data Lineage**
- **Data Governance**
- **Ownership Tracking**
- **Classification & Compliance**

### Example

```text
Database
   │
   ▼
Table
   │
   ▼
Dashboard
```

Tracks where data originated and how it is used.

---

# Model Layer

## LiteLLM

**LiteLLM** is a unified gateway for accessing multiple Large Language Models (LLMs) through a common API.

### Key Features

- Unified API
- Model Routing
- Load Balancing
- Usage Monitoring
- Cost Tracking

### Supported Providers

```text
OpenAI
Anthropic
Azure OpenAI
Gemini
Ollama
vLLM
OpenRouter
```

### Flow

```text
Application
    │
    ▼
 LiteLLM
    │
 ┌──┼───┐
 ▼  ▼   ▼
GPT Claude Gemini
```

---

## MLflow

**MLflow** is a platform for managing the machine learning lifecycle.

### Key Features

- Experiment Tracking
- Model Registry
- Artifact Storage
- Model Versioning
- Model Deployment

### Flow

```text
Training
   │
   ▼
MLflow Tracking
   │
   ▼
Model Registry
   │
   ▼
Deployment
```

---

# Policy Layer

## Open Policy Agent (OPA)

**OPA** is a policy engine that centrally enforces authorization, compliance, and business rules.

### Key Features

- Policy as Code
- Rego Language
- Centralized Enforcement
- Fine-Grained Authorization
- Compliance Enforcement

### Flow

```text
Application
    │
    ▼
    OPA
    │
    ▼
Allow / Deny
```

### Example Policy

```text
User Role = Admin
       ↓
     Allow

User Role = Guest
       ↓
      Deny
```

---

# Agent Runtime Layer

## LangGraph

**LangGraph** is a framework for creating stateful agent workflows using graph-based execution.

### Key Features

- Multi-Agent Workflows
- Stateful Execution
- Human-in-the-Loop
- Tool Calling
- Agent Orchestration

### Flow

```text
Agent A
   │
   ▼
Agent B
   │
   ▼
Tool Call
   │
   ▼
Agent C
```

---

## CrewAI

**CrewAI** enables multiple AI agents to collaborate as a team.

### Key Features

- Role-Based Agents
- Task Delegation
- Team Collaboration
- Agent Memory

### Example

```text
Researcher Agent
        │
        ▼
Writer Agent
        │
        ▼
Reviewer Agent
```

---

# Operations Layer

## Langfuse

**Langfuse** provides observability, tracing, and evaluation for AI applications.

### Key Features

- Prompt Tracking
- Agent Tracing
- Cost Monitoring
- Latency Monitoring
- LLM Evaluation

### Flow

```text
User
  │
  ▼
AI Application
  │
  ▼
Langfuse
  │
  ▼
Trace & Analytics
```

---

## Prometheus

**Prometheus** is an open-source monitoring and alerting system for collecting time-series metrics.

### Key Features

- Metrics Collection
- Time-Series Database
- Querying with PromQL
- Alert Management

### Flow

```text
Application
    │
    ▼
 Prometheus
    │
    ▼
 Metrics Store
    │
    ▼
 Alerts
```

---

## Grafana

**Grafana** is an observability and visualization platform used to monitor metrics, logs, and traces.

### Key Features

- Dashboards
- Visualization
- Alerting
- Multi-Source Support
- Real-Time Monitoring

### Integrations

```text
Prometheus
Loki
OpenTelemetry
Elasticsearch
InfluxDB
CloudWatch
```

### Flow

```text
Prometheus
     │
     ▼
  Grafana
     │
     ▼
Dashboards & Alerts
```

---

# Complete AI Platform Architecture

```text
┌─────────────────────────────────────────────┐
│ Identity Layer                              │
│ Keycloak, SPIRE                             │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│ Data Layer                                  │
│ Presidio, OpenMetadata                      │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│ Model Layer                                 │
│ LiteLLM, MLflow                             │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│ Policy Layer                                │
│ OPA                                         │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│ Agent Runtime Layer                         │
│ LangGraph, CrewAI                           │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│ Operations Layer                            │
│ Langfuse, Prometheus, Grafana               │
└─────────────────────────────────────────────┘
```

### One-Line Summary

| Layer | Responsibility | Technologies |
|---------|---------------|--------------|
| Identity | Who are you? | Keycloak, SPIRE |
| Data | Protect & Govern Data | Presidio, OpenMetadata |
| Model | Access & Manage Models | LiteLLM, MLflow |
| Policy | Decide What Is Allowed | OPA |
| Runtime | Execute Agents | LangGraph, CrewAI |
| Operations | Observe & Monitor | Langfuse, Prometheus, Grafana |