# FineTune Forge

An end-to-end Generative AI web application: a **React** frontend talking to a
**fine-tuned LLM** served through a **FastAPI** backend, with a fine-tuning
pipeline targeting **Azure AI Foundry** and a **CI/CD + IaC** setup that deploys
the frontend to **Amazon S3** via **AWS CodePipeline**.

> Based on the project brief in [`Todo.md`](./Todo.md). Built **hybrid**: the app
> runs fully on your machine today using a local mock model, and every cloud
> integration (Azure fine-tuning, S3 hosting, CodePipeline) ships as real,
> ready-to-apply config you can turn on when you have cloud access.

## Architecture

```
                    ┌──────────────────────────────────────────┐
                    │              CI/CD (AWS)                   │
                    │  CodePipeline → CodeBuild (buildspec.yml)  │
                    │        └── builds frontend, syncs to S3    │
                    └───────────────────┬────────────────────────┘
                                        │ deploy
                                        ▼
  ┌────────────┐   HTTP/JSON   ┌────────────────┐   adapter   ┌──────────────────┐
  │  React UI  │ ───────────▶ │  FastAPI API    │ ──────────▶ │  LLM provider    │
  │  (Vite)    │ ◀─────────── │  /api/chat      │ ◀────────── │  mock | azure    │
  │  on S3     │              │  /api/health    │             │  foundry         │
  └────────────┘              └────────────────┘             └──────────────────┘
                                        ▲
                                        │ model deployment
                              ┌─────────┴──────────┐
                              │ Fine-tuning pipeline│
                              │ prepare → Azure job │
                              └─────────────────────┘
```

## Repository layout

| Path            | What it is                                                        |
| --------------- | ----------------------------------------------------------------- |
| `frontend/`     | React + Vite chat UI. Talks to the backend over `/api`.           |
| `backend/`      | FastAPI service with a pluggable LLM adapter (`mock`, `azure`).   |
| `finetuning/`   | Data prep + Azure AI Foundry fine-tuning job submission.          |
| `infra/`        | CloudFormation for the S3 static-site hosting.                    |
| `ci/`           | `buildspec.yml` + CodePipeline CloudFormation for automated deploy.|
| `Todo.md`       | Original project brief (owned by you — not modified).             |

## Quick start (local)

Two terminals. No cloud account needed — the backend defaults to a local mock model.

**Backend**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
copy .env.example .env
npm run dev                       # http://localhost:5173
```

Open http://localhost:5173 and chat. The Vite dev server proxies `/api` to the
backend on port 8000, so there are no CORS issues in development.

## Switching from mock to a real fine-tuned model

1. Fine-tune a model — see [`finetuning/README.md`](./finetuning/README.md).
2. In `backend/.env`, set `LLM_PROVIDER=azure` and fill in the
   `AZURE_FOUNDRY_*` values printed by the fine-tuning job.
3. Restart the backend. No frontend changes needed.

## Deploying to the cloud

- **Frontend hosting** → [`infra/README.md`](./infra/README.md) (S3 static site).
- **CI/CD** → [`ci/README.md`](./ci/README.md) (CodePipeline + CodeBuild).

## Notes for this environment

- `huggingface.co` is blocked on the corp network, so the fine-tuning pipeline
  and local model **do not** download HF weights. The local provider is a
  dependency-free mock; the real model lives in Azure AI Foundry.
- No Docker is required for local development.
