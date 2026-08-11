#!/usr/bin/env python3
"""Extract captions and sampled frames from a YouTube tutorial."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    print("RUN " + " ".join(command[:3]) + (" ..." if len(command) > 3 else ""))
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"command failed ({result.returncode}): {detail[-2000:]}")
    return result


def validate_url(value: str) -> str:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or host not in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
        raise argparse.ArgumentTypeError("expected a youtube.com or youtu.be URL")
    return value


def vtt_to_text(content: str) -> str:
    lines: list[str] = []
    previous = ""
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or "-->" in line or line.isdigit():
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = html.unescape(line).strip()
        if line and line != previous:
            lines.append(line)
            previous = line
    return "\n".join(lines) + ("\n" if lines else "")


def find_one(directory: Path, patterns: list[str]) -> Path | None:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(directory.glob(pattern))
    return sorted(set(matches))[0] if matches else None


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


def js_runtime_args() -> list[str]:
    node = shutil.which("node")
    return ["--js-runtimes", f"node:{node}"] if node else []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", type=validate_url)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--language", default="en")
    parser.add_argument("--max-frames", type=int, default=24)
    args = parser.parse_args()
    if args.max_frames < 1 or args.max_frames > 120:
        parser.error("--max-frames must be between 1 and 120")
    yt_dlp = yt_dlp_command()
    ffmpeg = ffmpeg_command()
    missing = [name for name, command in (("yt-dlp", yt_dlp), ("ffmpeg", ffmpeg)) if not command]
    if missing:
        print("ERROR missing required executables: " + ", ".join(missing), file=sys.stderr)
        return 3
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    frames = output / "frames"
    frames.mkdir(exist_ok=True)
    try:
        assert yt_dlp and ffmpeg
        runtime_args = js_runtime_args()
        ffmpeg_args = ["--ffmpeg-location", ffmpeg[0]]
        metadata_result = run([*yt_dlp, *runtime_args, "--dump-single-json", "--skip-download", args.url], output)
        metadata = json.loads(metadata_result.stdout)
        try:
            run([
                *yt_dlp, *runtime_args, *ffmpeg_args, "--skip-download", "--write-subs", "--write-auto-subs",
                "--sub-langs", args.language, "--sub-format", "vtt",
                "-o", "source.%(ext)s", args.url,
            ], output)
        except RuntimeError as exc:
            print(f"WARNING captions unavailable: {exc}", file=sys.stderr)
        run([
            *yt_dlp, *runtime_args, *ffmpeg_args, "-f", "bv*[height<=720]+ba/b[height<=720]", "--merge-output-format", "mp4",
            "-o", "source-video.%(ext)s", args.url,
        ], output)
        video = find_one(output, ["source-video.mp4", "source-video.webm", "source-video.mkv"])
        if not video:
            raise RuntimeError("download completed but no video file was found")
        subtitle = find_one(output, ["source*.vtt"])
        transcript = output / "transcript.txt"
        if subtitle:
            transcript.write_text(vtt_to_text(subtitle.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
        else:
            transcript.write_text("", encoding="utf-8")
        duration = float(metadata.get("duration") or 0)
        interval = max(1, math.ceil(duration / args.max_frames)) if duration else 30
        run([
            *ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(video),
            "-vf", f"fps=1/{interval},scale=1280:-2", "-q:v", "3", str(frames / "frame-%04d.jpg"),
        ], output)
        manifest = {
            "url": args.url,
            "video_id": metadata.get("id"),
            "title": metadata.get("title"),
            "channel": metadata.get("channel") or metadata.get("uploader"),
            "duration_seconds": duration,
            "frame_interval_seconds": interval,
            "frame_count": len(list(frames.glob("frame-*.jpg"))),
            "transcript_available": transcript.stat().st_size > 0,
        }
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        video.unlink()
        print(json.dumps(manifest, indent=2))
        print("STATUS ok")
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
