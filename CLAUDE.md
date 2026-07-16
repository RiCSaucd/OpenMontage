# OpenMontage — CLAUDE.md

> **MANDATORY FIRST ACTION: Read [`AGENT_GUIDE.md`](AGENT_GUIDE.md) before responding to ANY user message.**
>
> `AGENT_GUIDE.md` contains the routing rules ("Rule Zero", onboarding, reference-video
> handling) that determine your *first action* based on what the user asked. Skipping it
> **will** cause you to take the wrong action on a production request. This file (CLAUDE.md)
> is orientation and a codebase map — it does **not** replace `AGENT_GUIDE.md`.

This file exists because contributors and AI assistants regularly need one thing the operating
contract doesn't cover: *how the codebase is laid out and how to work in it*. For the
agent-facing production contract (pipelines, stages, tools, checkpoints, decision logging),
`AGENT_GUIDE.md` is authoritative. For architecture and conventions,
[`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) is the declared single source of truth — this file
summarizes and links, it does not fork that content.

## Two kinds of work in this repo

Be clear which one you're doing — they have different rules:

1. **Producing video (the product).** Any request to make/create/generate a video. This MUST
   go through the pipeline system per `AGENT_GUIDE.md` → *Rule Zero*. Do not write ad-hoc
   scripts that call generation tools directly. Read the pipeline manifest, then the stage
   director skill, then the tool's Layer 3 skill, then act.
2. **Developing the codebase (tools, pipelines, skills, infra, docs).** Ordinary software
   work — the subject of the rest of this file. Rule Zero does not apply to editing Python,
   YAML manifests, or markdown skills; normal engineering discipline does.

## What OpenMontage is

An open-source, **instruction-driven** (agent-first) AI video production platform. The AI
agent *is* the intelligence. Python exists only for **tools and persistence** — there is no
Python orchestrator, reviewer, or creative-decision code. Orchestration, creative choices,
review, and stage transitions all live in instructions the agent reads:

```
Agent reads pipeline manifest (YAML) → reads stage director skill (MD)
→ uses tools (Python BaseTool) → self-reviews (meta skill)
→ checkpoints (Python utility) → presents to human for approval
```

Production state machine: `idea → script → scene_plan → assets → edit → compose → publish`.

## Repository map

```
OpenMontage/
├── AGENT_GUIDE.md          # THE agent operating contract (read first). Rule Zero, protocols.
├── PROJECT_CONTEXT.md      # Single source of truth for architecture & conventions.
├── CLAUDE.md               # This file — codebase map + dev workflows for AI assistants.
├── AGENTS.md / CODEX.md / CURSOR.md / COPILOT.md  # Sibling pointers for other assistants.
├── README.md               # User-facing product overview (also README_zh-CN.md).
├── Makefile                # Canonical dev commands (setup, test, lint, preflight, demo).
├── config.yaml             # Global config (llm, budget, checkpoint policy, output defaults).
├── .env.example            # Provider API-key template — copy to .env; never hardcode keys.
│
├── tools/                  # Layer 1: Python tools. All inherit tools/base_tool.py (BaseTool).
│   ├── base_tool.py        #   Tool contract (ToolResult, support envelope).
│   ├── tool_registry.py    #   Discovery + capability/provider catalogs + provider menu.
│   ├── cost_tracker.py     #   Budget governance (estimate → reserve → reconcile).
│   ├── audio/ video/ image via graphics/ enhancement/ analysis/ avatar/
│   ├── subtitle/ capture/ character/ publishers/ _comfyui/   # capability packages
├── lib/                    # Persistence/infra: checkpoint.py, pipeline_loader.py,
│   │                       #   config_model.py, media_profiles.py, hyperframes_style_bridge.py
├── pipeline_defs/          # Declarative pipeline manifests (YAML). One per pipeline.
├── skills/                 # Layer 2: how OpenMontage uses tools (project conventions).
│   ├── INDEX.md            #   Skill index + Layer 1→3 mapping.
│   ├── meta/               #   reviewer, checkpoint-protocol, onboarding, taste-direction, …
│   ├── pipelines/<pipe>/   #   Per-stage director skills (idea..publish -director.md).
│   ├── core/ creative/     #   Cross-cutting skills (e.g. core/hyperframes.md, ink-theater).
├── .agents/skills/         # Layer 3: vendor/tech knowledge (skills.sh format, per-provider).
├── schemas/                # JSON schemas: artifacts/, checkpoints/, pipelines/, styles/, tools/
├── styles/                 # Style playbooks (YAML) + playbook_loader.py (validate + design AI).
├── remotion-composer/      # Node.js Remotion composition engine (React scene components).
├── ink-theater/            # Ink Theater / Ink Puppet hand-drawn doodle animation engine.
├── backlot/                # "Backlot" — local FastAPI board that watches projects/ live.
├── third_party/            # Vendored OSS (e.g. CutScript for text-based editing).
├── tests/                  # pytest suites (see Testing below).
├── docs/                   # ARCHITECTURE.md, PROVIDERS.md, PR_REVIEW_GUIDE.md, platform notes.
├── projects/               # (gitignored) per-run workspaces — artifacts, assets, renders.
└── music_library/          # (gitignored) user-supplied royalty-free tracks.
```

## Knowledge architecture (3 layers)

This is the central mental model — see `PROJECT_CONTEXT.md` and `AGENT_GUIDE.md` → *Layer Map*.

| Layer | Location | Answers |
|-------|----------|---------|
| 1 | `tools/tool_registry.py` (+ each tool) | *What tools exist* — runtime, status, cost, capability, provider |
| 2 | `skills/` | *How OpenMontage uses them* — pipeline/stage conventions |
| 3 | `.agents/skills/` | *How the technology works* — generic vendor/API prompting knowledge |

Each tool's `agent_skills[]` field bridges Layer 1 → Layer 3. **Read a generation tool's
Layer 3 skill before writing prompts for it** — it is not optional (Rule Zero).

## Development workflows

All standard commands are **Make targets** (they auto-manage the `.venv/` virtualenv and point
Python at it). Python is pinned to **3.10+** (`.python-version`). Node ≥ 22, FFmpeg, and `npx`
are required for the composition engines.

| Command | What it does |
|---------|--------------|
| `make setup` | One-command setup: venv, `requirements.txt`, Remotion `npm install`, Piper TTS, HyperFrames npx warm, `.env` from `.env.example`. |
| `make install` / `install-dev` / `install-gpu` | Core / dev (pytest) / GPU (diffusers, transformers) deps. |
| `make test` | Full pytest suite (`tests/`, ~400+ tests). No API keys required. |
| `make test-contracts` | Contract tests only (`tests/contracts/`). |
| `make lint` | `py_compile` sanity check on core tool modules. |
| `make preflight` | Registry discovery → `provider_menu()`. The capability envelope. |
| `make demo-list` / `make demo` | Zero-key end-to-end render via Remotion → `projects/demos/renders/`. Fastest proof the composition path works. |
| `make hyperframes-doctor` / `hyperframes-warm` | Validate / refresh the HyperFrames runtime. |
| `make clean` | Remove `__pycache__` and `.pyc`. |

Notes:
- **Run Python through the venv** (`.venv/bin/python`) or activate it; `make` targets already do.
- **API keys are optional.** With no keys the registry still reports FFmpeg + Remotion +
  HyperFrames + Piper (offline TTS) as available. Add keys to `.env` to unlock cloud providers.
- **Preflight before any capability claim.** The registry is the source of truth for what's
  available — never assume tool strengths or availability from memory or stale docs.
- **Fast E2E smoke:** `make demo-list` then `.venv/bin/python render_demo.py <name>` (e.g.
  `world-in-numbers`) renders a real 1080p MP4 with zero API keys.

## Key conventions

**Tools** (`tools/`):
- Every tool inherits `BaseTool` from `tools/base_tool.py` and returns a `ToolResult`
  (`.success`, `.data`, `.error`). Call via `.execute(params_dict)` — **not** `.run()`.
- Class names are **PascalCase without a `Tool` suffix** (e.g. `MusicGen`, `VideoCompose`,
  `ElevenLabsTTS`). Verify with `grep "^class " tools/<path>.py`.
- Prefer the **selector + provider** pattern: one capability router (`tts_selector`,
  `image_selector`, `video_selector`) plus one concrete tool per real provider/runtime.
  Selectors auto-discover providers from the registry — adding a provider needs no selector edit.
- Discovery flows through `tools/tool_registry.py`; do **not** rely on ad-hoc imports.
- Set all contract fields (name, version, tier, capability, provider, supports,
  fallback_tools, agent_skills, runtime, status, install_instructions). Read them from the
  registry rather than hardcoding provider names / env-var names / setup URLs.

**Pipelines** (`pipeline_defs/*.yaml`): declarative manifests validated by
`schemas/pipelines/pipeline_manifest.schema.json`. Each stage declares `skill` (director-skill
path), `produces`, `tools_available`, `review_focus`, `success_criteria`, and
`human_approval_default` (binding — the checkpoint writer enforces gated stages).

**Artifacts & checkpoints**: each stage produces one canonical artifact (`brief`, `script`,
`scene_plan`, `asset_manifest`, `edit_decisions`, `render_report`, `publish_log`) validated
against `schemas/artifacts/`. Checkpoints live at `projects/<id>/checkpoint_<stage>.json`
(schema in `schemas/checkpoints/`). See `lib/checkpoint.py` and
`skills/meta/checkpoint-protocol.md`.

**Composition runtimes**: `tools/video/video_compose.py` routes to **FFmpeg**, **Remotion**, or
**HyperFrames** based on `edit_decisions.render_runtime` (locked at proposal). Runtime swaps are
forbidden without a logged decision — see `AGENT_GUIDE.md` → *Composition Runtimes* and
`skills/core/hyperframes.md`.

**Style playbooks** (`styles/*.yaml`): validated by `schemas/styles/playbook.schema.json`;
loaded by `styles/playbook_loader.py` (also provides color/type/a11y design intelligence).

## Adding things

**A new pipeline:**
1. Write `pipeline_defs/<name>.yaml` (validate against the manifest schema).
2. Add stage director skills under `skills/pipelines/<name>/` (idea → publish).
3. Reference meta skills (reviewer, checkpoint-protocol) and compatible playbooks in the manifest.
4. Add contract tests in `tests/contracts/`.

**A new tool:**
1. Inherit `BaseTool`; place it in the right capability package
   (`tools/audio/`, `tools/video/`, `tools/image` via `graphics/`, `tools/enhancement/`,
   `tools/analysis/`, `tools/avatar/`, `tools/subtitle/`, `tools/capture/`, `tools/character/`,
   `tools/publishers/`).
2. Prefer selector-plus-provider; set every contract field including `agent_skills` (Layer 3).
3. Implement `execute()` → `ToolResult`. Let discovery happen via the registry.
4. Add a `schemas/tools/` schema if I/O is complex; add tests once the runtime path is correct.

## Testing

`pytest` suites live under `tests/`, organized by concern: `contracts/` (pipeline/artifact
contracts), `tools/`, `lib/`, `pipelines/`, `styles/`, `backlot/`, `qa/` (per-tool output
inspection), and `eval/`. Run everything with `make test`; contracts alone with
`make test-contracts`. The suite runs with **no API keys** — provider-dependent paths are
mocked or skipped.

## Where to look next

| Question | Source |
|----------|--------|
| What's my first action for a user request? | `AGENT_GUIDE.md` (Rule Zero, onboarding) |
| Architecture & conventions (canonical) | `PROJECT_CONTEXT.md`, `docs/ARCHITECTURE.md` |
| What tools/providers exist right now? | `make preflight` → `registry.provider_menu()` |
| How should a pipeline stage behave? | `skills/pipelines/<pipeline>/<stage>-director.md` |
| Review / checkpoint policy | `skills/meta/reviewer.md`, `skills/meta/checkpoint-protocol.md` |
| Provider setup & keys | `.env.example`, `docs/PROVIDERS.md` |
| Skill index & Layer 1→3 mapping | `skills/INDEX.md` |
| PR review expectations | `docs/PR_REVIEW_GUIDE.md` |
```
