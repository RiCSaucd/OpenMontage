# Script Director — Cinematic Intro Pipeline

## When to Use

Produce the **Line Sheet** (Intro Engine stage 00) — the numbered VO lines every downstream stage consumes. This is **checkpoint zero**.

## Prerequisites

| Resource | Purpose |
|----------|---------|
| `proposal_packet` | Input mode, duration, brand voice |
| `skills/creative/cinematic-intro-engine.md` | Line Sheet prompt (00) |
| `schemas/artifacts/script.schema.json` | Validation |

## Process

### Step 1: Load Line Sheet prompt

Copy prompt **00 — Line Sheet** from `skills/creative/cinematic-intro-prompts.html` (or follow summary in `cinematic-intro-engine.md`).

Fill:
- `[INPUT]` — script, transcript excerpt, or topic from proposal
- `[LENGTH]` — from proposal (default ~30s → ~80–95 words if drafting)

### Step 2: Execute by input mode

| Mode | Rule |
|------|------|
| Finished script | **Verbatim** wording — only split into lines at breath points |
| Transcript | Distill opening OR write fresh 5-beat intro (Hook / Payoff / Proof / Reframe / Re-hook) |
| Topic | Draft intro first, then line-break |

Output **6–9 numbered lines**, one complete filmable thought each.

### Step 3: Abstract-line audit

After the line sheet, flag any line whose meaning is abstract with no concrete noun or number. Recommend rewrite **before** beat map if flagged.

### Step 4: Write script artifact

Use standard `script` schema. Add metadata:

```json
"metadata": {
  "artifact_subtype": "line_sheet",
  "input_mode": "<from proposal>",
  "line_count": 7,
  "abstract_lines_flagged": ["line 4: ..."]
}
```

Sections: one section per line with `id: "line-1"` … `provider_text` = exact recorded words.

**Human approval required.** Do not proceed to `scene_plan` until approved.
