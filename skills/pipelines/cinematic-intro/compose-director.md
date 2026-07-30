# Compose Director — Cinematic Intro Pipeline

## When to Use

Execute **Cinematic Render** (stage 05) and **Final Cut** (stage 06): 480p test gate → 1080p finals → ffmpeg stitch.

## Runtime Routing (AI video — not Remotion/HyperFrames)

This pipeline does **not** route through `video_compose` Remotion or HyperFrames for main footage.

- `render_runtime` in proposal is **`seedance_ai_video`** — not remotion/hyperframes/ffmpeg composition.
- HyperFrames is **explicitly not used** — there is no HTML/GSAP composition path for the main film.
- If an agent reaches for `video_compose` with Remotion, stop — that is the wrong engine for this pipeline.

Main tools: `higgsfield_video` (model `seedance_2_0`), `video_stitch`, ffmpeg concat fallback.

Read `.agents/skills/seedance-2-0/SKILL.md` before every generation call.

## Prerequisites

| Resource | Purpose |
|----------|---------|
| Approved `edit_decisions.generation_plan` | Sealed prompts |
| Approved `asset_manifest` | Character sheet + storyboard boards |
| `skills/creative/cinematic-intro-engine.md` | Prompts 05 + 06 |

## Process

### Phase A — 480p test gate (mandatory)

For each generation, in parallel:

```python
higgsfield_video.execute({
    "prompt": "<approved prompt from edit_decisions — verbatim>",
    "model": "seedance_2_0",
    "duration": 15,
    "aspect_ratio": "16:9",
    "resolution": "480p",
    "mode": "fast",
    "generate_audio": True,  # diegetic SFX only
    "reference_images": ["character_sheet", "storyboard_board"],
    ...
})
```

References attach order: **character sheet first**, then that generation's **storyboard board** (whole sheet, uncropped).

**Judge stitched test:**
1. Concat gen1 + gen2 test MP4s (`video_stitch` or ffmpeg).
2. Evaluate motion, story logic, seam in **stitched** cut.
3. Do **not** judge skin realism or text fidelity at 480p fast — fix composition on board, motion in prompt.

Iterate until user approves stitched test.

### Phase B — 1080p finals

Same prompts **verbatim** — change only:
- `resolution`: `1080p`
- `mode`: `std`
- `bitrate_mode`: `high`

Run both in parallel; poll patiently (~7 min per 15s).

Verify spelling + identity on one frame per generation. Use provider retake rules on drift — never accept wrong words or wrong face.

### Phase C — Stitch

```bash
ffmpeg -i gen1.mp4 -i gen2.mp4 \
  -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -crf 18 -pix_fmt yuv420p \
  projects/<id>/renders/<project>_FINAL_30s.mp4
```

Judge seam in stitched final.

### Phase D — final_review

- `technical_probe`: ffprobe duration, resolution, audio present
- `visual_spotcheck`: sample frames at beat boundaries
- `audio_spotcheck`: diegetic bed present; no VO baked in
- `transcript_comparison`: mark `skipped` with note "VO recorded separately from line sheet"
- `promise_preservation`: `delivery_promise_honored: true`; log `runtime_swap_check: "seedance_ai_video — Remotion/HyperFrames not applicable"`

Write `render_report` + embedded `final_review` per checkpoint protocol.

## Audio rule

`generate_audio: true` for diegetic SFX only. **No music, no dialogue, no subtitles** in render. Script words never enter the Seedance prompt.
