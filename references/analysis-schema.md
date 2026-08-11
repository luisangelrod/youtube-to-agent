# Analysis JSON schema

Save each independent review as UTF-8 JSON:

```json
{
  "source": "transcript-and-frames",
  "tutorial_url": "https://www.youtube.com/watch?v=example",
  "claims": [
    {
      "claim_id": "install_dependency",
      "claim": "Install the dependency before running the workflow.",
      "confidence": "high",
      "evidence": ["transcript 00:14-00:22", "frame-0002.jpg"]
    }
  ]
}
```

Requirements:

- Use one object per claim.
- Use lower snake-case `claim_id` values matching `^[a-z0-9_]+$`.
- Keep each ID unique within an analysis.
- Set `confidence` to `high`, `medium`, or `low`.
- Include at least one evidence string.
- Use the same ID in both analyses when the claims refer to the same step.

`reconcile.py` compares normalized claim text for identical IDs. It does not guess semantic matches. A shared ID with different text is deliberately labeled `conflict` for human review.
