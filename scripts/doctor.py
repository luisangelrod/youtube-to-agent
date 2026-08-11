#!/usr/bin/env python3
"""Check runtime dependencies for the YouTube-to-agent workflow."""

from __future__ import annotations

import json
import importlib.util
import platform
import shutil
import subprocess
import sys


def version(command: list[str] | None, args: list[str]) -> dict[str, str | bool]:
    if not command:
        return {"available": False, "path": "", "version": "not found"}
    try:
        result = subprocess.run(
            [*command, *args], capture_output=True, text=True, timeout=15, check=False
        )
        output = (result.stdout or result.stderr).strip().splitlines()
        rendered = output[0] if output else f"exit {result.returncode}"
        return {"available": result.returncode == 0, "path": " ".join(command), "version": rendered}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "path": " ".join(command), "version": str(exc)}


def yt_dlp_command() -> list[str] | None:
    executable = shutil.which("yt-dlp")
    if executable:
        return [executable]
    if importlib.util.find_spec("yt_dlp"):
        return [sys.executable, "-m", "yt_dlp"]
    return None


def ffmpeg_command() -> list[str] | None:
    executable = shutil.which("ffmpeg")
    if executable:
        return [executable]
    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]

        return [imageio_ffmpeg.get_ffmpeg_exe()]
    except (ImportError, OSError):
        return None


def main() -> int:
    report: dict[str, object] = {
        "platform": platform.platform(),
        "python": {
            "available": sys.version_info >= (3, 10),
            "path": sys.executable,
            "version": platform.python_version(),
        },
        "yt-dlp": version(yt_dlp_command(), ["--version"]),
        "ffmpeg": version(ffmpeg_command(), ["-version"]),
        "gemini_optional": version([shutil.which("gemini")] if shutil.which("gemini") else None, ["--version"]),
    }
    required = ["python", "yt-dlp", "ffmpeg"]
    missing = [name for name in required if not report[name]["available"]]  # type: ignore[index]
    report["status"] = "ok" if not missing else "missing-required"
    report["missing"] = missing
    print(json.dumps(report, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
