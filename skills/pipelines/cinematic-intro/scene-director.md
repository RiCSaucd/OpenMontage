# Scene Director — Cinematic Intro Pipeline

## When to Use

Produce the **Beat Map** (Intro Engine stage 02) and ensure **Character Sheet** (stage 01) exists before `@hero` references propagate.

## Prerequisites

| Resource | Purpose |
|----------|---------|
| Approved `script` (line sheet) | VO lines |
| `proposal_packet` | Brand, wardrobe, character notes |
| `skills/creative/cinematic-intro-engine.md` | Prompts 01 + 02 |
| `.agents/skills/seedance-2-0/SKILL.md` | Reference conditioning |

## Process

### Step 0: Character reference sheet (if not in asset_manifest)

Before beat map, generate character sheet when likeness photos are available:

1. Prompt user for 3–6 solo photos (varied angles) OR use provided paths.
2. Run prompt **01 — Character Sheet** via `image_selector` (Higgsfield GPT Image 2 preferred).
3. Save to `assets/images/character_sheet.png` (or provider path).
4. Record in `scene_plan.required_assets`:

```json
{"id": "hero", "handle": "@hero", "path": "assets/images/character_sheet.png", "type": "character_reference"}
```

If no likeness photos: stop and request them — do not proceed with generic stand-ins without user approval.

### Step 1: Beat Map

Load prompt **02 — Beat Map**. Fill:
- `[SCRIPT TEXT]` — numbered lines from line sheet
- `[CHARACTER]` — `@hero` + asset path
- `[BRAND]` — from proposal

Execute Step 1 (subtext), Step 2 (WORLD/LIGHT/PALETTE/POSE VOCABULARY), Step 3 (treatment table).

**Quality gates:**
- THE LOOK derived from subject — not default amber tungsten
- Mute test: each beat shows line's key noun/verb
- Delete test: every support element is narrative-driving
- At most one graphic layer per moment

### Step 2: Write scene_plan artifact

Embed in `scene_plan.metadata`:

```json
{
  "beat_map": {
    "subtext": "...",
    "world_block": {"WORLD": "...", "LIGHT": "...", "PALETTE": "...", "POSE_VOCABULARY": []},
    "treatment_table": [ ... ]
  },
  "register": "grounded|fantastical|grounded_luminous"
}
```

Map each line to a `scene` entry with treatment, setting, hero action, support element, camera notes.

Human approval before `edit`.
