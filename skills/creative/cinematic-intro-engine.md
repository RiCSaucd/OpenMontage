# Cinematic Intro Engine

Hyper-realistic ~30s intro films for creator channels. This is the OpenMontage integration of the **Cinematic Intro Engine** prompt workflow (Higgsfield / Seedance 2.0, footage + in-frame graphics, separate VO layover).

**Pipeline:** `cinematic-intro` (`pipeline_defs/cinematic-intro.yaml`)

**Interactive prompt cards (copy buttons):** `skills/creative/cinematic-intro-prompts.html`

**Layer 3 skills to read before calling tools:**
- `.agents/skills/seedance-2-0/SKILL.md` — Seedance 2.0 parameters, provider routing, prompt structure
- `.claude/skills/ai-video-gen/SKILL.md` — general video generation hygiene
- `.claude/skills/bfl-api/SKILL.md` — only if falling back to FLUX for still frames

## When to Use

Route here when the user wants:
- A **cinematic channel intro** (~30s, 16:9) with hyper-real footage under recorded narration
- **Character-consistent** on-screen presence from likeness photos
- **Beat-mapped** visuals that literalize each VO line (Netflix-doc energy, creator intros, premium hooks)
- **Seedance 2.0 / Higgsfield** generation with board approval gates

Do **not** use for:
- Templated Remotion explainer cards (`animated-explainer`)
- Source-footage montages without AI generation (`documentary-montage`, `cinematic`)
- Vertical viral parodies that need zero-cost Piper + motion graphics only

## Stage Map (Intro Engine → OpenMontage)

| Intro # | Engine step | OpenMontage stage | Artifact |
|--------|-------------|-------------------|----------|
| — | Intake | `proposal` | `proposal_packet` |
| 00 | Line Sheet | `script` | `script` (line_sheet metadata) |
| 01 + 02 | Character + Beat Map | `scene_plan` | `scene_plan` (character ref + beat map) |
| 03 | Storyboard | `edit` | `edit_decisions` (generation prompts) |
| 04 | Board Render | `assets` | `asset_manifest` (boards + character sheet) |
| 05 + 06 | Test + Final Cut | `compose` | `render_report` + `final_review` |
| — | Delivery + VO | `publish` | `publish_log` |

## Default Brand Language (override in proposal)

From the engine design system — replace via `[BRAND]` in proposal:

```
ink-orange #E96A3C / charcoal #1C1B17 / bone #F2E9D6
Anton display, JetBrains Mono meta
RISO print texture; spring/physics motion only, no fades
```

## Tool Routing

| Step | Primary tool | Notes |
|------|--------------|-------|
| Character sheet | `image_selector` → Higgsfield GPT Image 2 or FLUX | 3-panel 16:9, neutral grey cyclorama |
| Storyboard board | `image_selector` | One composite per 15s generation |
| 480p test render | `higgsfield_video` (`seedance_2_0`, 480p, fast) | Judge stitched cut, not skin at 480p |
| 1080p final | `higgsfield_video` (`seedance_2_0`, 1080p, std, high) | Same prompts as approved test |
| Stitch | `video_stitch` or ffmpeg concat | Two 15s halves → ~30s |
| VO | **Separate recording** | Never in Seedance prompt; lay over in publish |

**render_runtime:** N/A for this pipeline. Log `render_runtime_selection` in `decision_log` with `selected: "seedance_ai_video"` and note that Remotion/HyperFrames are not used.

## Prompt Library

Read the stage director skill first for artifact shape; use these prompts verbatim (fill bracketed fields).

### 00 — Line Sheet (`script` stage)

See `cinematic-intro-prompts.html` → **Line Sheet** (prompt 00).

Summary:
1. Detect input: finished script (verbatim lines), transcript (distill or fresh 5-beat intro), or topic (write then line-break).
2. Output 6–9 numbered lines, one filmable thought each.
3. Flag abstract lines with no concrete noun/number.
4. **Human approval required** before beat map.

### 01 — Character Sheet (`scene_plan` prerequisite or `assets`)

See HTML → **Character Sheet** (prompt 01).

Run `media_upload_widget` (Higgsfield MCP) for 3–6 likeness photos, then `generate_image` with `gpt_image_2`, 16:9, 2k, high, multi-reference.

Fill: `[WARDROBE]`, `[BUILD + AGE NOTES]`.

### 02 — Beat Map (`scene_plan`)

See HTML → **Beat Map** (prompt 02).

Fill: `[SCRIPT TEXT]`, `[CHARACTER]` (e.g. `@hero`), `[BRAND]`.

Outputs: Step 1 subtext, Step 2 WORLD/LIGHT/PALETTE/POSE VOCABULARY, Step 3 treatment table (9 columns).

### 03 — Storyboard (`edit`)

See HTML → **Storyboard** (prompt 03).

Fill: `[STAGE 2 OUTPUT]`, `[PROP LIST]`, `[MAX_SECONDS]`.

Merge beats into **timed multishot** 15s generations; sealed standalone prompts per shot; continuity ledger + graphics handoff table.

### 04 — Board Render (`assets`)

See HTML → **Board Render** (prompt 04).

One `generate_image` call per generation; attach character sheet; iterate until spelling and seam pair approved.

### 05 — Cinematic Render (`compose` — test gate)

See HTML → **Cinematic Render** (prompt 05).

480p fast tests in parallel; stitch; judge motion + seam in **stitched** cut. Iterate prompts/boards until approved — never rewrite at final stage.

### 06 — Final Cut (`compose` — finals + stitch)

See HTML → **Final Cut** (prompt 06).

Same prompts, 1080p std high; verify spelling; ffmpeg concat; deliver with boards + halves + line sheet for VO.

## Governance Reminders

- **Numbers never render inside AI footage** — TYPE CARD / GFX CANVAS / flat accents only.
- **At most one graphic layer** on screen; enters on spoken word, exits before next beat.
- **Delete test** governs every support element.
- **480p test is mandatory** before 1080p spend.
- **Final prompts must match approved test prompts verbatim** — only resolution/mode change.
- **VO always recorded separately** from line sheet; film plays under voice, no lip-sync.

## References

- Full copy-paste prompts: `skills/creative/cinematic-intro-prompts.html`
- Seedance prompting: `.agents/skills/seedance-2-0/SKILL.md`
- Checkpoint protocol: `skills/meta/checkpoint-protocol.md`
