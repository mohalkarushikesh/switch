# Custodian Web App

React (Vite) front-end for the Custodian API. Governance overview, per-invoice
pipeline visualization, risk/PII/policy breakdown, OCR + form submission, stats,
a "needs attention" feed, and the approve/reject review queue.

> Note: it's `npm run build` / `npm run dev` — npm has no bare `build`/`dev`
> command; custom scripts always go through `npm run`.

## Prerequisites

- Node.js + npm (project built with Node 20+/npm 10+).
- The Custodian API running on `http://localhost:8000` (for live data).

```bash
cd web
npm install        # first time only
```

## Workflow A — build once, let FastAPI serve it (simplest)

Build the static bundle; FastAPI then serves it at `/app`. After building you
do **not** run any further npm command — just run the backend.

```bash
npm run build                                  # -> web/dist/
cd ..                                          # back to project root
```

Then run the API (pick your shell):

```bash
# bash / macOS / Linux / Git Bash
PYTHONPATH=src uvicorn custodian.api:app --reload
```

```powershell
# PowerShell (Windows)
$env:PYTHONPATH="src"; uvicorn custodian.api:app --reload
```

```
# open http://localhost:8000/app/
```

Re-run `npm run build` only when you change the React code.

## Workflow B — live dev server with hot reload (for editing the UI)

No build step. Run the backend and the Vite dev server together (two terminals);
Vite proxies API calls to the backend, so writes/reads just work.

```bash
# terminal 1 — backend  (bash / Git Bash)
PYTHONPATH=src uvicorn custodian.api:app --reload      # :8000
```

```powershell
# terminal 1 — backend  (PowerShell)
$env:PYTHONPATH="src"; uvicorn custodian.api:app --reload   # :8000
```

```bash
# terminal 2 — Vite dev server (hot reload; same in any shell)
cd web && npm run dev                                   # :5173
# open http://localhost:5173/app/
```

## Scripts

| Command           | What it does                                              |
| ----------------- | --------------------------------------------------------- |
| `npm run dev`     | Hot-reload dev server on :5173 (proxies API to :8000)     |
| `npm run build`   | Production build into `web/dist/` (served by FastAPI at `/app`) |
| `npm run preview` | Serve the built `dist/` locally for a quick check         |

## Auth

If the backend has auth enabled (`CUSTODIAN_API_KEYS`), paste a key into the
"API key" field in the header — it's sent as `X-API-Key` on write requests.

## Notes

- `node_modules/` and `dist/` are gitignored; a fresh clone runs
  `npm install && npm run build` once to populate `/app`.
- The zero-build single-file dashboard at `/ui` is always available and needs
  no Node toolchain — handy if you just want to click around without building.
