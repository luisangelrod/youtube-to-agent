#!/usr/bin/env python3
"""Run an offline end-to-end reconciliation smoke test."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def analysis(source: str, claims: list[dict[str, object]]) -> dict[str, object]:
    return {"source": source, "tutorial_url": "https://youtu.be/test", "claims": claims}


def claim(claim_id: str, text: str) -> dict[str, object]:
    return {"claim_id": claim_id, "claim": text, "confidence": "high", "evidence": ["00:01"]}


def main() -> int:
    script = Path(__file__).with_name("reconcile.py")
    with tempfile.TemporaryDirectory(prefix="youtube-to-agent-") as tmp:
        root = Path(tmp)
        a = analysis("transcript-and-frames", [claim("install_tool", "Install the tool."), claim("run_agent", "Run the agent with --safe.")])
        b = analysis("independent-review", [claim("install_tool", "Install the tool"), claim("run_agent", "Run the agent with --fast."), claim("export_log", "Export the log.")])
        first, second, output = root / "a.json", root / "b.json", root / "result.json"
        first.write_text(json.dumps(a), encoding="utf-8")
        second.write_text(json.dumps(b), encoding="utf-8")
        result = subprocess.run([sys.executable, str(script), str(first), str(second), "--output", str(output)], capture_output=True, text=True, check=False)
        print("COMMAND", sys.executable, script.name, "a.json b.json --output result.json")
        print("EXIT", result.returncode)
        print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        if result.returncode:
            return result.returncode
        payload = json.loads(output.read_text(encoding="utf-8"))
        expected = {"confirmed": 1, "conflict": 1, "single-source": 1}
        if payload.get("summary") != expected:
            print(f"FAIL expected {expected}, got {payload.get('summary')}", file=sys.stderr)
            return 5
        print("ASSERT summary matched", expected)
        print("SMOKE TEST PASSED")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
