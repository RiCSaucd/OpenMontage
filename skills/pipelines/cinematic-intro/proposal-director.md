# Proposal Director — Cinematic Intro Pipeline

## When to Use

Intake gate for a ~30s cinematic intro. Lock input mode, brand language, wardrobe, likeness requirements, and generation provider plan **before** the line sheet.

## Runtime Selection (N/A — log explicitly)

This pipeline generates footage via **Seedance 2.0** (`higgsfield_video` or `video_selector` with `preferred_provider="seedance"`). It does **not** compose through Remotion or HyperFrames.

Per AGENT_GUIDE.md → "Present Both Composition Runtimes": the rule applies to composition-engine pipelines. Here, surface the constraint explicitly:

> "This intro is AI-filmed with Seedance 2.0, not Remotion/HyperFrames motion graphics. Remotion and HyperFrames are **not used** for the main footage."

Log `decision_log` entry:
- `category`: `render_runtime_selection`
- `subject`: `Footage generation runtime`
- `selected`: `seedance_ai_video`
- `options_considered`: include `remotion`, `hyperframes` with `rejected_because: "Pipeline uses AI video generation, not composition engine"`

## Process

### Step 1: Classify input

| Mode | User provided | Downstream behavior |
|------|---------------|---------------------|
| `finished_script` | Intro script to record | Line sheet keeps wording verbatim |
| `transcript` | Full video transcript | Distill opening or write fresh 5-beat intro |
| `topic` | Bare topic/idea | Agent drafts intro, then line-breaks |

### Step 2: Lock production parameters

Record in `proposal_packet.production_plan`:

- `target_duration_seconds`: default **30**
- `aspect_ratio`: **16:9**
- `platform`: youtube_landscape or custom intro slot
- `brand_graphic_language`: palette, type, motion rules (default in `creative/cinematic-intro-engine.md`)
- `wardrobe`: exact garments for character sheet
- `build_age_notes`: optional flattering adjustments or "match photos exactly"
- `likeness_photos_required`: true (3–6 solo photos, varied angles)
- `generation_provider`: higgsfield preferred; fallbacks via registry

### Step 3: Preflight

Run `provider_menu_summary()`. Report:
- `higgsfield_video` / Seedance availability
- `image_selector` providers for character sheet + boards
- `video_stitch` for concat

If Seedance unavailable, stop and offer setup (`HIGGSFIELD_API_KEY`) or escalate — do not substitute Remotion templated cuts.

### Step 4: Cost estimate

Typical ~30s intro:
- 2× character/board image generations (low)
- 2× 480p fast test videos (cheap gate)
- 2× 1080p std final videos (main cost)
- VO: $0 (user-recorded)

Itemize in `cost_estimate.line_items`.

## Artifact: proposal_packet

Include `selected_concept` with hook, visual approach ("hyper-real cinematic intro under recorded VO"), and `delivery_promise`:

```yaml
promise_type: cinematic_intro
motion_required: true
source_required: false
tone_mode: cinematic
quality_floor: premium
```

Human approval required before `script` stage.
