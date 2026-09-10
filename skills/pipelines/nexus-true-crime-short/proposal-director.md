# Proposal Director — Nexus True Crime Short

## When to Use

Second stage. Turn research into 2–3 brand-safe concept options and stop for human approval.

## Prerequisites

- `research_brief` present
- Brand skills applied
- Schema: `schemas/artifacts/proposal_packet.schema.json`

## Runtime Selection (required field — `render_runtime`)

Per AGENT_GUIDE.md → "Present Both Composition Runtimes (HARD RULE)": do **not** silently default to Remotion.

Most Nexus Shorts are archival stills + user VO assembled with **ffmpeg**. Motion-graphics inserts (titles, maps, lower-thirds) may use Remotion or hyperframes when those engines are available.

**MANDATORY workflow:**

1. Query `video_compose.get_info()["render_engines"]`.
2. If the cut is archival/ffmpeg-only, say so and still log `render_runtime_selection` with `ffmpeg` selected and both `remotion` and `hyperframes` in `options_considered` (`rejected_because` naming why they were not used).
3. If motion-graphics inserts need a composition engine and both `remotion` and `hyperframes` are available, **present both** runtimes with a one-line fit/tradeoff each, recommend one, and wait for approval.
4. Log `category: render_runtime_selection` in `decision_log`.

## Process

1. Lock aspect (default **9:16**), target runtime, and budget from project / AGENT_INSTRUCTION.
2. Offer **2–3 concepts**, each obeying respected-historian tone — vary angle (institutional, human-cost, myth-bust), not sensationalism.
3. State **VO plan**: user records final narration; scripts provide timing cues; optional TTS scratch only.
4. State **music plan**: sparse / non-triumphant (or user opt-out).
5. Present provider preferences honestly (archival/stock first; Kling/Runway/Higgsfield for atmospheric gaps only).
6. Write `proposal_packet` + append `decision_log` entries.
7. **Stop for human approval.**

## Decision log subjects (examples)

- `concept_selection`, `voice_selection` (user VO), `music_plan`, `provider_selection`, `render_runtime_selection`
