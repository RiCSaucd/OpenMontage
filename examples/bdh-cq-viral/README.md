# BDH-CQ — last-30-days viral short

Mute-first **9:16 / 30s** explainer about the #1 Hugging Face paper of the last 30 days
(observed **2026-09-04** via `hf_fs`: `ls hf://papers/trending` + `search hf://models --sort likes30d`).

**A-story:** [BDH-CQ](https://arxiv.org/abs/2608.09888) — 150M params, 29.5% pass@2 on public ARC-AGI-1, $0.0007/task, latent recurrent reasoning (no CoT dump).

## Rebuild

```bash
python3 examples/bdh-cq-viral/scripts/render_short.py
```

Requires: `ffmpeg`, `python3` + `numpy`, Inter at `/usr/share/fonts/truetype/macos/`.

Output: `examples/bdh-cq-viral/artifacts/bdh_cq_last30days_short.mp4` (1080×1920, H.264 High, AAC).

## Runtime lock

Remotion and HyperFrames were evaluated and are **not installed** in this cloud image.
Compose is locked to **ffmpeg** (see `decision_log.json` → `render_runtime_selection`).
