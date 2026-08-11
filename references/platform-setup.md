# Platform setup

The skill itself uses Python's standard library. YouTube extraction additionally requires `yt-dlp` and FFmpeg. The scripts accept command-line installations or the Python packages `yt-dlp` and `imageio-ffmpeg`.

## macOS

```bash
brew install python yt-dlp ffmpeg
git clone https://github.com/luisangelrod/youtube-to-agent.git "${CODEX_HOME:-$HOME/.codex}/skills/youtube-to-agent"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/youtube-to-agent/scripts/doctor.py"
```

If Homebrew is unavailable, install Python 3.10 or newer and use `python3 -m pip install --user yt-dlp imageio-ffmpeg` in a Python environment that permits user packages.

Install Gemini CLI only when using Gemini as the independent reviewer. Another genuinely independent reviewer is acceptable.

## Windows

Install Python 3.10 or newer, then run `python -m pip install --user yt-dlp imageio-ffmpeg`. Command-line `yt-dlp` and FFmpeg installations also work.

Clone the repository to `%CODEX_HOME%\skills\youtube-to-agent`, or to `%USERPROFILE%\.codex\skills\youtube-to-agent` when `CODEX_HOME` is unset.

## Verification

Run:

```bash
python3 scripts/doctor.py
python3 scripts/smoke_test.py
```

On Windows, `python` may replace `python3`. The doctor exits nonzero only when a required dependency is missing; the smoke test uses no network and must exit zero.

## Claude Code personal installation

Claude Code loads personal skills from `~/.claude/skills/<skill-name>/SKILL.md` and invokes this skill as `/youtube-to-agent`.

To share one installation between Codex and Claude Code on Windows, create a directory junction in PowerShell:

```powershell
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.claude\skills\youtube-to-agent" `
  -Target "$env:USERPROFILE\.codex\skills\youtube-to-agent"
```

On macOS, install once for Codex and create a symbolic link for Claude Code:

```bash
mkdir -p "$HOME/.claude/skills"
ln -s "${CODEX_HOME:-$HOME/.codex}/skills/youtube-to-agent" "$HOME/.claude/skills/youtube-to-agent"
```

If the top-level `~/.claude/skills` directory was created after Claude Code started, restart Claude Code once. Otherwise, Claude Code detects the new skill during the current session.
