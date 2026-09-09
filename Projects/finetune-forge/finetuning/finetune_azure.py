"""Submit a fine-tuning job to Azure AI Foundry (Azure OpenAI) and poll it.

Uses the Azure OpenAI REST API directly via httpx — no heavyweight SDK — so the
steps (upload files -> create job -> poll) are explicit and easy to follow.

Credentials come from the environment (see .env.example):
    AZURE_FOUNDRY_ENDPOINT, AZURE_FOUNDRY_API_KEY, AZURE_FOUNDRY_API_VERSION
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import httpx

TERMINAL_STATES = {"succeeded", "failed", "cancelled"}


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _load_dotenv(path: Path = Path(".env")) -> None:
    """Minimal .env loader so the script works without extra deps."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


class FoundryClient:
    def __init__(self, endpoint: str, api_key: str, api_version: str) -> None:
        if not endpoint or not api_key:
            raise SystemExit(
                "Set AZURE_FOUNDRY_ENDPOINT and AZURE_FOUNDRY_API_KEY "
                "(env or finetuning/.env)."
            )
        self._base = endpoint.rstrip("/")
        self._params = {"api-version": api_version}
        self._client = httpx.Client(
            headers={"api-key": api_key}, timeout=120.0
        )

    def _url(self, path: str) -> str:
        return f"{self._base}/openai/{path}"

    def upload_file(self, path: Path) -> str:
        print(f"Uploading {path} …")
        with path.open("rb") as fh:
            resp = self._client.post(
                self._url("files"),
                params=self._params,
                data={"purpose": "fine-tune"},
                files={"file": (path.name, fh, "application/jsonl")},
            )
        resp.raise_for_status()
        file_id = resp.json()["id"]
        print(f"  -> file id {file_id}")
        return file_id

    def create_job(
        self, *, model: str, training_file: str, validation_file: str | None
    ) -> str:
        body: dict = {"model": model, "training_file": training_file}
        if validation_file:
            body["validation_file"] = validation_file
        resp = self._client.post(
            self._url("fine_tuning/jobs"), params=self._params, json=body
        )
        resp.raise_for_status()
        job_id = resp.json()["id"]
        print(f"Created fine-tuning job {job_id}")
        return job_id

    def get_job(self, job_id: str) -> dict:
        resp = self._client.get(
            self._url(f"fine_tuning/jobs/{job_id}"), params=self._params
        )
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train", type=Path, default=Path("data/train.jsonl"))
    ap.add_argument("--val", type=Path, default=Path("data/val.jsonl"))
    ap.add_argument("--base-model", default="gpt-4o-mini-2024-07-18")
    ap.add_argument("--poll-seconds", type=int, default=30)
    ap.add_argument(
        "--no-wait", action="store_true", help="submit the job and exit without polling"
    )
    args = ap.parse_args(argv)

    _load_dotenv()
    client = FoundryClient(
        endpoint=_env("AZURE_FOUNDRY_ENDPOINT"),
        api_key=_env("AZURE_FOUNDRY_API_KEY"),
        api_version=_env("AZURE_FOUNDRY_API_VERSION", "2024-08-01-preview"),
    )

    try:
        if not args.train.exists():
            raise SystemExit(
                f"{args.train} not found — run prepare_data.py first."
            )

        training_file = client.upload_file(args.train)
        validation_file = client.upload_file(args.val) if args.val.exists() else None

        job_id = client.create_job(
            model=args.base_model,
            training_file=training_file,
            validation_file=validation_file,
        )

        if args.no_wait:
            print(f"Submitted. Track it with: get_job({job_id})")
            return 0

        while True:
            job = client.get_job(job_id)
            status = job.get("status", "unknown")
            print(f"  status: {status}")
            if status in TERMINAL_STATES:
                break
            time.sleep(args.poll_seconds)

        if status != "succeeded":
            print(f"Job ended in state {status!r}: {job.get('error')}")
            return 1

        model_id = job.get("fine_tuned_model")
        print("\nFine-tuning succeeded.")
        print(f"  fine_tuned_model: {model_id}")
        print(
            "\nNext: deploy this model in the Azure AI Foundry portal, then set "
            "AZURE_FOUNDRY_DEPLOYMENT (the deployment name) plus LLM_PROVIDER=azure "
            "in backend/.env."
        )
        return 0
    except httpx.HTTPStatusError as exc:
        print(
            f"Azure API error {exc.response.status_code}: {exc.response.text[:800]}",
            file=sys.stderr,
        )
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
