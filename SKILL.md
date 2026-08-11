---
name: youtube-to-agent
description: Turn a YouTube tutorial into a tested, reusable Codex skill or agent by extracting transcript and frame evidence, producing two independent analyses, reconciling confirmed claims and conflicts, implementing the result, and validating it. Use when a user shares a YouTube tutorial and asks Codex to learn the workflow, reproduce it, create an agent, create a skill, or convert the video into automation.
---

# YouTube to Agent

Convert tutorial video evidence into an auditable implementation. Keep the two analyses independent until reconciliation, and do not invent steps missing from the evidence.

## Workflow

1. Create a clean work directory for the tutorial.
2. Run `python scripts/doctor.py` and resolve required dependency failures.
3. Run `python scripts/extract_youtube.py <url> --output <work-dir>/evidence`.
4. Inspect `<work-dir>/evidence/manifest.json`, `transcript.txt`, and sampled frames.
5. Produce analysis A from only the extracted transcript and frames.
6. Produce analysis B independently:
   - Prefer Gemini or another model with native YouTube viewing.
   - Do not provide analysis A to the second reviewer.
   - If no independent reviewer is available, stop and tell the user the evidence has only one source. Do not label claims confirmed.
7. Save both analyses as JSON using [references/analysis-schema.md](references/analysis-schema.md).
8. Run `python scripts/reconcile.py analysis-a.json analysis-b.json --output reconciliation.json`.
9. Review only entries labeled `conflict` or `single-source`. Ask the user only when a conflict materially changes the implementation.
10. Write `agent-spec.md` with the confirmed workflow, inputs, outputs, dependencies, failure modes, and unresolved claims.
11. Use `$skill-creator` to implement the target skill. Keep evidence and generated outputs outside the target skill unless they are needed at runtime.
12. Validate the generated skill and run a realistic smoke test. Report commands, exit codes, and relevant output.

## Evidence rules

- Cite transcript timestamps or frame filenames for every procedural claim.
- Use stable semantic `claim_id` values in both analyses, such as `install_dependency` or `export_report`.
- Label exact agreement as `confirmed`, disagreement as `conflict`, and one-sided claims as `single-source`.
- Treat captions as potentially inaccurate. Prefer visible UI state or repeated evidence when exact values matter.
- Never expose credentials, cookies, private browser data, or tokens while collecting evidence.
- Keep source material within fair-use analysis boundaries; do not reproduce full copyrighted transcripts in the final deliverable.

## Platform setup

Read [references/platform-setup.md](references/platform-setup.md) when a required executable is missing or when installing the skill on another computer.

## Scripts

- `scripts/doctor.py`: report Python, `yt-dlp`, `ffmpeg`, and optional Gemini availability.
- `scripts/extract_youtube.py`: download captions and a temporary video, sample frames, write a plain-text transcript and evidence manifest, then remove the temporary video.
- `scripts/reconcile.py`: deterministically classify claims from two independent JSON analyses.
- `scripts/smoke_test.py`: exercise reconciliation in an isolated temporary directory.

## Completion standard

Finish only when the generated skill validates, its smoke test passes, and the user receives a concise evidence summary including command output and exit status. Clearly separate a tested local workflow from an untested network-dependent extraction.
