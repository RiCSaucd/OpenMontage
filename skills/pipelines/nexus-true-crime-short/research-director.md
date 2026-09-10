# Research Director — Nexus True Crime Short

## When to Use

First stage of `nexus-true-crime-short`. Gather documented history and separate it from myth before any creative spend.

## Prerequisites

- Brand: `skills/brand/respected-historian-tone.md`, `skills/brand/mafia-true-crime-guidelines.md`
- Schema: `schemas/artifacts/research_brief.schema.json`
- Tools: `web_search` (and fetch as available)

## Process

1. Read brand skills. If `AGENT_INSTRUCTION.md` or a VideoAnalysisBrief exists, ground the topic there.
2. Search for primary / high-quality secondary sources (court coverage, reputable histories, archives).
3. Build a **fact vs myth** table for contested lore.
4. Capture at least one **human-cost / historical-context** beat.
5. Note visual research leads (archives, public-domain stills, maps) — do not generate assets yet.
6. Write `artifacts/research_brief` (schema-valid) under `projects/<id>/`.
7. Checkpoint. Human approval default is false — still present findings briefly.

## Review checklist

- [ ] Documented record separated from myth
- [ ] Sources cited
- [ ] Human-cost beat present
- [ ] No lifestyle glorification in framing notes
