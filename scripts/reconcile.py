#!/usr/bin/env python3
"""Reconcile two independently produced tutorial analyses."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CLAIM_ID = re.compile(r"^[a-z0-9_]+$")
CONFIDENCE = {"high", "medium", "low"}


def load_analysis(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: cannot read valid JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        raise ValueError(f"{path}: top level must contain a claims array")
    seen: set[str] = set()
    for index, claim in enumerate(data["claims"]):
        prefix = f"{path}: claims[{index}]"
        if not isinstance(claim, dict):
            raise ValueError(f"{prefix} must be an object")
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not CLAIM_ID.fullmatch(claim_id):
            raise ValueError(f"{prefix}.claim_id must use lower snake-case")
        if claim_id in seen:
            raise ValueError(f"{path}: duplicate claim_id {claim_id}")
        seen.add(claim_id)
        if not isinstance(claim.get("claim"), str) or not claim["claim"].strip():
            raise ValueError(f"{prefix}.claim must be non-empty text")
        if claim.get("confidence") not in CONFIDENCE:
            raise ValueError(f"{prefix}.confidence must be high, medium, or low")
        evidence = claim.get("evidence")
        if not isinstance(evidence, list) or not evidence or not all(isinstance(v, str) and v.strip() for v in evidence):
            raise ValueError(f"{prefix}.evidence must contain non-empty strings")
    return data


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.casefold()).split())


def by_id(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {claim["claim_id"]: claim for claim in data["claims"]}


def reconcile(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    a = by_id(first)
    b = by_id(second)
    entries = []
    for claim_id in sorted(set(a) | set(b)):
        left = a.get(claim_id)
        right = b.get(claim_id)
        if left and right:
            status = "confirmed" if normalize(left["claim"]) == normalize(right["claim"]) else "conflict"
        else:
            status = "single-source"
        entries.append({"claim_id": claim_id, "status": status, "analysis_a": left, "analysis_b": right})
    counts = {status: sum(item["status"] == status for item in entries) for status in ("confirmed", "conflict", "single-source")}
    return {
        "analysis_a_source": first.get("source", "unknown"),
        "analysis_b_source": second.get("source", "unknown"),
        "summary": counts,
        "claims": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_a", type=Path)
    parser.add_argument("analysis_b", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = reconcile(load_analysis(args.analysis_a), load_analysis(args.analysis_b))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"WROTE {args.output}")
    else:
        print(rendered, end="")
    print("SUMMARY " + " ".join(f"{key}={value}" for key, value in result["summary"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
