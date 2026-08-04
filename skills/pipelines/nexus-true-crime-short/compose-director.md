# Compose Director — Nexus True Crime Short

## When to Use

Render the approved edit to `projects/<project_id>/renders/final.mp4`.

## Prerequisites

- `edit_decisions`, `asset_manifest`
- Tools: `video_compose` (required); `video_stitch` / `ffmpeg_toolkit` optional
- Schema: `schemas/artifacts/render_report.schema.json`

## Process

1. Confirm aspect / runtime locks from proposal.
2. Present Remotion vs HyperFrames when both are available and composition inserts need a runtime (AGENT_GUIDE hard rule); for simple FFmpeg archival assemblies, say so and log `render_runtime_selection`.
3. Render to `projects/<id>/renders/final.mp4` with explicit `output_path`.
4. Leave headroom for user VO if mix is scratch-only.
5. Write `render_report` + optional `distribution/distribution_manifest.json` (CapCut draft notes + Drive upload list).
6. Checkpoint → **human approval**.

## Brand exit check

Could this cut be mistaken for lifestyle crime glamor? If yes, revise before presenting.
