# Executive Producer — Cinematic Intro Pipeline

## When to Use

You orchestrate the **Cinematic Intro Engine** pipeline (`cinematic-intro`): hyper-real ~30s intro films with AI-generated footage (Seedance 2.0), character reference sheets, beat-mapped visuals, board approval gates, and separate VO layover.

## Prerequisites

| Resource | Purpose |
|----------|---------|
| `pipeline_defs/cinematic-intro.yaml` | Stage definitions |
| `skills/creative/cinematic-intro-engine.md` | Full prompt library + tool routing |
| `skills/creative/cinematic-intro-prompts.html` | Copy-paste prompt cards |
| All stage director skills below | Stage execution |
| `meta/reviewer` | Self-review |

## Execution Protocol

Stages run serially:

`proposal → script → scene_plan → edit → assets → compose → publish`

### Hard gates

1. **Line sheet approval** (`script`) — checkpoint zero; no beat map until approved.
2. **Board approval** (`assets`) — no 480p test spend until boards pass spelling + seam pair.
3. **480p test approval** (`compose`) — no 1080p finals until stitched test plays right.

### Budget discipline

Default budget ~$5. Seedance credits dominate cost. Always run **480p fast tests** before 1080p std finals. Log every generation in `decision_log`.

### Runtime note

This pipeline does **not** use Remotion or HyperFrames. Footage is AI-generated. Do not invoke `video_compose` for the main film unless adding a simple VO layover in publish.

## Cross-Stage Checks

| After stage | Verify |
|-------------|--------|
| proposal | Input mode, brand, wardrobe, likeness photo plan locked |
| script | 6–9 lines; abstract lines flagged |
| scene_plan | @hero exists; mute test passes on beat map |
| edit | Graphics handoff complete; seam pairs designed |
| assets | Boards approved; character sheet on disk |
| compose | Test prompts == final prompts; stitch seam clean |
| publish | VO instructions + full reference package |
