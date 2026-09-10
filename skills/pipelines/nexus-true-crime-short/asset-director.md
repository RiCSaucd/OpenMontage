# Asset Director — Nexus True Crime Short

## When to Use

Acquire visuals and sparse music for the scene plan. Stay inside the budget cap.

## Prerequisites

- `scene_plan`, `script`
- Brand visual rules
- Schema: `schemas/artifacts/asset_manifest.schema.json`

## Process

1. Search archival / stock first (Pexels, Pixabay, Unsplash, Archive.org, Wikimedia as available).
2. Use `image_selector` / `video_selector` only for atmospheric gap fills — announce provider/model before paid calls.
3. Music: sparse dark ambient via `music_gen` or `music_library/` — never triumphant.
4. Optional TTS scratch for timing; path under `assets/audio/scratch/` — not final VO.
5. Record provenance (provider, URL, license) on every asset.
6. Write `asset_manifest`. Checkpoint → **human approval** before expensive batch regen.
