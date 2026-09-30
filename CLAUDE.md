# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**MANDATORY: Read [`AGENT_GUIDE.md`](AGENT_GUIDE.md) before responding to ANY user message.**

Do not act on the user's request until you have read AGENT_GUIDE.md. It contains the routing rules that determine your first action (onboarding, reference-video analysis, or pipeline selection) and the full operating contract for video production: Rule Zero (all production goes through a pipeline), mandatory preflight, the decision communication contract, checkpoint gates, and the reviewer protocol. That contract is authoritative for production work and is not duplicated here.

This file covers the *development* side: commands and architecture for working on OpenMontage's own code. Shared architecture notes also live in [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); the sibling files CODEX.md / CURSOR.md / COPILOT.md are pointer files for other assistants — keep them consistent if you change the contract.

## Commands

Python 3.10+ project with a Node.js Remotion engine under `remotion-composer/`. Dependencies install into `.venv/`; the Make targets find and use it automatically (run Python as `.venv/bin/python` if calling directly).

```bash
make setup              # One-command install: venv, requirements.txt, remotion-composer npm install, Piper TTS, HyperFrames npx cache, .env from .env.example
make install-dev        # Dev deps (pytest, pytest-asyncio)
make test               # Full pytest suite (tests/, ~435 tests, no API keys required)
make test-contracts     # Contract tests only (tests/contracts/)
make lint               # py_compile checks on core tool files
make preflight          # Tool registry discovery + provider menu (capability envelope)
make demo-list          # List zero-key demo renders
make demo               # Render demo videos via Remotion (no API keys; output in projects/demos/renders/)
make hyperframes-doctor # Validate the HyperFrames runtime (Node ≥ 22, ffmpeg, npx)
```

Run a single test:

```bash
.venv/bin/python -m pytest tests/contracts/test_phase0_contracts.py -v
.venv/bin/python -m pytest tests/contracts/test_phase0_contracts.py::test_name -v
```

The fastest end-to-end smoke test of the full composition path (Remotion + FFmpeg) with zero API keys: `make demo-list`, then `.venv/bin/python render_demo.py <name>`.

API keys are optional and live in `.env` (never hardcode them). With no keys, the registry still reports FFmpeg, Remotion, HyperFrames, and Piper TTS as available.

## Architecture

OpenMontage is an **instruction-driven (agent-first) video production platform**. The AI agent IS the orchestrator — there is no Python orchestrator, reviewer, or stage handler. Python exists only for tools and persistence; orchestration, creative decisions, review, and checkpoint policy live in instructions the agent reads:

```
Agent reads pipeline manifest (YAML) → reads stage director skill (MD)
→ uses tools (Python BaseTool) → self-reviews (meta skill)
→ checkpoints (Python utility) → presents to human for approval
```

### Three knowledge layers

```
Layer 1: tools/ + tools/tool_registry.py   → WHAT exists (capabilities, status, cost, install_instructions)
Layer 2: skills/                           → HOW OpenMontage uses tools (pipeline/stage conventions)
Layer 3: .agents/skills/                   → HOW the technology works (vendor prompting, API rules)
```

Each tool's `agent_skills[]` field bridges Layer 1 → Layer 3. Reading a tool's Layer 3 skill before calling any generation tool is mandatory (see AGENT_GUIDE.md). `skills/INDEX.md` has the full mapping.

### Pipeline system

- **State machine:** `idea → script → scene_plan → assets → edit → compose → publish`. The agent resumes via `checkpoint.get_next_stage()`.
- **Manifests:** declarative YAML in `pipeline_defs/` (validated by `schemas/pipelines/pipeline_manifest.schema.json`). Each stage declares its director skill, `produces`, `tools_available`, `review_focus`, and `human_approval_default`.
- **Director skills:** `skills/pipelines/<pipeline>/<stage>-director.md` teach the agent HOW to execute each stage. Meta skills (`skills/meta/`) cover the reviewer, checkpoint protocol, taste direction, and bespoke composition.
- **Canonical artifacts:** each stage produces one JSON artifact (`brief`, `script`, `scene_plan`, `asset_manifest`, `edit_decisions`, `render_report`, …) validated against `schemas/artifacts/`. Artifacts are the contract between stages.
- **Checkpoints:** written to `projects/<project-id>/checkpoint_<stage>.json` by `lib/checkpoint.py`. A gated stage (`human_approval_default: true`) cannot be written `completed` without `human_approved=True` — the writer raises a GATE VIOLATION. Superseded checkpoints archive to `projects/<project-id>/history/`.
- **Project workspaces:** every production run lives under `projects/<kebab-case-name>/` (gitignored) with `artifacts/`, `assets/{images,video,audio,music}`, and `renders/final.mp4`. All tool outputs must be written there via explicit `output_path`. `python -m backlot open <project-id>` opens the live Backlot board (FastAPI server in `backlot/`), which observes these files — it never blocks production.

### Tool system

- Every tool inherits from `tools/base_tool.py` (`BaseTool`) and is auto-discovered by the singleton registry in `tools/tool_registry.py` — no ad hoc imports. Tools live in capability packages: `tools/audio/`, `tools/video/`, `tools/graphics/`, `tools/analysis/`, `tools/avatar/`, `tools/enhancement/`, `tools/subtitle/`, `tools/character/`, `tools/capture/`.
- Tools are called via `.execute(params_dict)` returning a `ToolResult` (`.success`, `.data`, `.error`) — NOT `.run()`.
- Tool classes are **PascalCase without a "Tool" suffix**: `MusicGen`, `VideoCompose`, `ElevenLabsTTS`. When in doubt: `grep "^class " tools/<path>.py`.
- **Selector pattern:** capability routers (`tts_selector`, `image_selector`, `video_selector`) auto-discover providers via `registry.get_by_capability(...)`. Adding a provider tool makes it available through the selector with no selector changes.
- Never hardcode provider names, API key names, or setup URLs — read `install_instructions` and `dependencies` from the registry at runtime.
- `tools/cost_tracker.py` handles budget governance (estimate → reserve → reconcile).

### Composition runtimes

`tools/video/video_compose.py` routes to one of **three** render engines based on `edit_decisions.render_runtime`, which is locked at the proposal stage and never silently swapped:

| Engine | For | Requires |
|--------|-----|----------|
| FFmpeg | Cuts, concat, trim, subtitle burn | `ffmpeg` binary |
| Remotion | React-based composition (`remotion-composer/`; scene types in `SCENE_TYPES.md`) | Node.js + npm install |
| HyperFrames | HTML/CSS/GSAP composition, consumed via `npx hyperframes` | Node ≥ 22 + FFmpeg |

Orthogonal to runtime is **authoring mode**: *templated* (stock scene types — fast, but generic) vs *atelier* (hand-authored composition for hero work). See AGENT_GUIDE.md for the presentation and approval rules around both choices.

### Style playbooks

YAML playbooks in `styles/` (loaded by `styles/playbook_loader.py`, validated by `schemas/styles/playbook.schema.json`) define visual language, typography, motion, and asset-generation constraints. `lib/hyperframes_style_bridge.py` converts playbooks to CSS custom properties for HyperFrames workspaces.

## Extending

**New tool:** inherit `BaseTool`, place it in the right capability package, set all contract fields (name, capability, provider, supports, fallback_tools, agent_skills, install_instructions), implement `execute()` → `ToolResult`, and let registry discovery pick it up. Prefer selector-plus-provider layout. Add a schema in `schemas/tools/` for complex I/O.

**New pipeline:** YAML manifest in `pipeline_defs/` + stage director skills in `skills/pipelines/<name>/` + contract tests in `tests/contracts/`. See PROJECT_CONTEXT.md for the full checklist.

## Quick lookup

| Question | Where |
|----------|-------|
| Full agent operating contract (production requests) | `AGENT_GUIDE.md` |
| Shared architecture + key files | `PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md` |
| What tools/providers exist right now | `make preflight` (never trust memory or stale docs) |
| Skill index (Layer 2 ↔ Layer 3 mapping) | `skills/INDEX.md` |
| Provider setup details | `docs/PROVIDERS.md`, `.env.example` |
| PR review expectations | `docs/PR_REVIEW_GUIDE.md` |
