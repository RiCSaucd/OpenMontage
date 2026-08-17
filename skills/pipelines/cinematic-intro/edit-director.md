# Edit Director — Cinematic Intro Pipeline

## When to Use

Convert the beat map into a **production shot list** (Intro Engine stage 03 — Storyboard): timed multishot generations, sealed Seedance prompts, continuity ledger, and graphics handoff table.

## Prerequisites

| Resource | Purpose |
|----------|---------|
| `scene_plan` with embedded beat_map | Treatments per line |
| Approved line sheet (`script`) | Word timing reference |
| `skills/creative/cinematic-intro-engine.md` | Prompt 03 |
| `.agents/skills/seedance-2-0/SKILL.md` | Block-ordered prompt structure |

## Process

### Step 1: Load Storyboard prompt

Prompt **03 — Storyboard** from `cinematic-intro-prompts.html`.

Fill:
- `[STAGE 2 OUTPUT]` — beat map from scene_plan
- `[PROP LIST]` — `@hero`, `@world`, recurring props as `@handles`
- `[MAX_SECONDS]` — target duration (~30)

### Step 2: Build generation plan

Default: **two 15-second timed multishot generations** (6–8 shots each).

Rules:
- Script-driven segment durations with `[00:00-00:03]` brackets
- HARD CUT at boundaries; "camera does not cut on its own"
- Design **seam pair**: last shot of gen1 mirrors first shot of gen2
- TYPE CARD / GFX CANVAS beats excluded from multishot — plan edit drops between segments
- Name shots `1A`, `1B`, `2A`… for isolated prompt edits

Each shot prompt: sealed standalone, block order per Seedance skill (SCENE CONTEXT → ACTIVE REFERENCES → … → POSITIVE LOCKS).

### Step 3: Graphics handoff table

Output rows: `G1`, `G2`… | beat # | type | on-screen words (verbatim, max 4) | anchor | in/out timing.

### Step 4: Write edit_decisions artifact

Standard schema plus metadata:

```json
{
  "metadata": {
    "generation_plan": [
      {"id": "gen1", "time_range": "00:00-00:15", "shots": ["1A", "1B", ...], "prompt": "..."},
      {"id": "gen2", "time_range": "00:15-00:30", "shots": ["2A", ...], "prompt": "..."}
    ],
    "graphics_handoff": [ ... ],
    "continuity_ledger": "...",
    "seam_pair": {"outgoing": "1H", "incoming": "2A", "strategy": "match_cut|continuous_vector"}
  }
}
```

Human approval before `assets` (board render).
