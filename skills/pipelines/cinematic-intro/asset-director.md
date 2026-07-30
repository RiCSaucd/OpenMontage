# Asset Director — Cinematic Intro Pipeline

## When to Use

Produce **Character Sheet** (if not done in scene_plan) and **Board Render** (Intro Engine stage 04) — the approval gate before any paid video generation.

## Prerequisites

| Resource | Purpose |
|----------|---------|
| `edit_decisions.generation_plan` | Shots per generation |
| `scene_plan` beat map + @hero | Character + register |
| `skills/creative/cinematic-intro-engine.md` | Prompts 01 + 04 |

## Process

### Step 1: Character sheet (skip if already in manifest)

Verify `assets/images/character_sheet.png` exists. If missing, rerun prompt **01** via `image_selector`.

Asset entry:

```json
{
  "id": "character-sheet",
  "type": "image",
  "path": "assets/images/character_sheet.png",
  "source_tool": "image_selector",
  "subtype": "character_reference",
  "cost_usd": 0.0
}
```

### Step 2: Storyboard board renders

For each generation in `generation_plan`:

1. Load prompt **04 — Board Render**.
2. Fill panel list from generation shots (ACTION + GFX notes, 2–4 word diegetic text in quotes).
3. Attach character sheet as reference image.
4. `generate_image`: 16:9, 2k, high.
5. Save: `assets/images/storyboard_gen1.png`, `storyboard_gen2.png`.

**Verify:**
- Spelling of every rendered word
- Seam pair: gen1 final panel mirrors gen2 first panel
- Identity matches character sheet

Iterate boards until approved — boards cost pennies, renders cost credits.

### Step 3: Write asset_manifest

Include:
- character_sheet
- storyboard boards (one per generation)
- prop stills if `@handles` require separate references

Set `total_cost_usd` from image generation spend.

**Human approval required** before compose stage runs 480p tests.
