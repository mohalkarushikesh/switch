"""Convert raw user/assistant pairs into Azure fine-tuning chat JSONL.

Input  (one JSON object per line):
    {"user": "...", "assistant": "...", "system": "...optional..."}

Output (one JSON object per line, Azure fine-tuning format):
    {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}

The train/validation split is deterministic (no RNG) so repeated runs and CI
produce identical files.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_SYSTEM_PROMPT = (
    "You are FineTune Forge, a helpful assistant fine-tuned for this application."
)


def load_raw(path: Path) -> list[dict]:
    rows: list[dict] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{lineno}: invalid JSON: {exc}")
        user = (obj.get("user") or "").strip()
        assistant = (obj.get("assistant") or "").strip()
        if not user or not assistant:
            raise SystemExit(
                f"{path}:{lineno}: each line needs non-empty 'user' and 'assistant'"
            )
        rows.append(obj)
    if not rows:
        raise SystemExit(f"{path}: no examples found")
    return rows


def to_chat(obj: dict, system_prompt: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": obj.get("system") or system_prompt},
            {"role": "user", "content": obj["user"].strip()},
            {"role": "assistant", "content": obj["assistant"].strip()},
        ]
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path("data/sample_raw.jsonl"))
    ap.add_argument("--outdir", type=Path, default=Path("data"))
    ap.add_argument("--val-split", type=float, default=0.2, help="0..0.9")
    ap.add_argument("--system-prompt", default=DEFAULT_SYSTEM_PROMPT)
    args = ap.parse_args(argv)

    if not 0.0 <= args.val_split <= 0.9:
        raise SystemExit("--val-split must be between 0.0 and 0.9")

    raw = load_raw(args.input)
    chat = [to_chat(o, args.system_prompt) for o in raw]

    # Deterministic split: every Nth example goes to validation.
    n_val = max(1, round(len(chat) * args.val_split)) if args.val_split else 0
    step = max(1, len(chat) // n_val) if n_val else 0
    val_idx = set(range(0, len(chat), step)[:n_val]) if n_val else set()

    train = [row for i, row in enumerate(chat) if i not in val_idx]
    val = [row for i, row in enumerate(chat) if i in val_idx]

    write_jsonl(args.outdir / "train.jsonl", train)
    if val:
        write_jsonl(args.outdir / "val.jsonl", val)

    print(f"Wrote {len(train)} train and {len(val)} val examples to {args.outdir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
