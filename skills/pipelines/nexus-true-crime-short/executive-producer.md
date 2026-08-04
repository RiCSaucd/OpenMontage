# Executive Producer — Nexus True Crime Short

## When to Use

You orchestrate `nexus-true-crime-short` for Nexus AI Media: research-first vertical Shorts on Mafia / organized-crime history with a respected-historian voice.

## Prerequisites

| Layer | Resource |
|-------|----------|
| Pipeline | `pipeline_defs/nexus-true-crime-short.yaml` |
| Brand | `skills/brand/respected-historian-tone.md` |
| Brand | `skills/brand/mafia-true-crime-guidelines.md` |
| Meta | `skills/meta/reviewer.md`, `skills/meta/checkpoint-protocol.md` |
| Server (optional) | `servers/nexus_openmontage.py` → `AGENT_INSTRUCTION.md` |

## Stage order

`research → proposal → script → scene_plan → assets → edit → compose`

Hard stop for human approval at stages with `human_approval_default: true` (proposal, script, assets, compose).

## Protocol

1. If `AGENT_INSTRUCTION.md` exists in the project root, treat it as the brief of record (topic, duration, aspect, budget, notes).
2. Read both brand skills before research.
3. Init workspace with `init_project` if missing; open Backlot when possible.
4. Run each stage’s director skill; checkpoint; present approval gates.
5. Prefer archival / stock over lifestyle AI video. Cap spend at project `budget_usd` (default $1.50).
6. User records final VO — never ship TTS as the master without explicit override.
7. On compose approval, write `distribution/distribution_manifest.json` when the Nexus server (or this EP) prepares CapCut / Drive hand-off.

## Escalate when

- Seedance/Kling/Runway unavailable and archival search also fails
- Brief demands glorified violence
- Budget would be exceeded by sample renders
