# Publish Director — Cinematic Intro Pipeline

## When to Use

Deliver the intro package and **VO layover instructions** (Intro Engine stage 06 delivery + separate recording).

## Prerequisites

| Resource | Purpose |
|----------|---------|
| `render_report` | Stitched final + generation halves |
| `final_review` | Pass status |
| Approved line sheet (`script`) | Exact VO words |

## Process

### Step 1: Export bundle

Use `export_bundle` when available. Package:

```
renders/
  <project>_FINAL_30s.mp4      # stitched film (diegetic audio only)
  gen1_final.mp4
  gen2_final.mp4
  gen1_test_480p.mp4           # optional reference
  gen2_test_480p.mp4
assets/images/
  character_sheet.png
  storyboard_gen1.png
  storyboard_gen2.png
checkpoints/                   # or pipelines/<id>/ copies
  line_sheet (script checkpoint)
  beat_map (scene_plan)
  generation_prompts (edit)
docs/
  VO_LAYOVER.md
```

### Step 2: VO layover instructions

Write `VO_LAYOVER.md`:

1. Record from line sheet **verbatim** — one line per take or full pass.
2. Film plays **under** voice; no lip-sync expected.
3. Suggested DAW workflow: import stitched MP4, record VO track, mix narration forward of diegetic bed (~+6 dB relative).
4. Target total with VO: match proposal duration (~30s).

### Step 3: publish_log

Schema-valid `publish_log` with:
- Hero export path
- Platform: 16:9 intro
- Metadata title/description for channel intro slot
- Reference to `decision_log` and all checkpoint paths

Human approval before calling production complete.
