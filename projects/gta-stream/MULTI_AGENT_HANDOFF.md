# Multi-Agent Handoff — Theswampdon / OpenMontage

Use this file so **Cursor**, **Claude**, and **ChatGPT** work on the *same* channel package without overwriting each other.

## One source of truth

| Rule | Detail |
|------|--------|
| **Canonical folder** | `projects/gta-stream/` in the OpenMontage git repo |
| **Branch** | `defaultgta-stream-channel-launch-70d3` (PR #7) |
| **Do not edit** | The attached launch `plan.md` outside the repo |
| **Channel** | **Theswampdon** — `@theswampdon` on Twitch + Kick (registered) |
| **Character** | Vincenzo **"Vince" Genovese** |

If Claude or ChatGPT produces text/assets, **copy the final version into this folder and commit** — chats are not the archive.

## How to combine Cursor + Claude + ChatGPT

### Recommended workflow

1. **Cursor (this agent)** owns the repo: files, overlays, trailer render, clip scripts, commits, PR.
2. **Claude / ChatGPT** own *drafts*: lore riffs, stream titles, chat replies, merch ideas, FiveM server research.
3. After a Claude/ChatGPT session, paste useful output into the matching file below (or a new `artifacts/` note), then ask Cursor: *"Merge this into `projects/gta-stream/`."*

### Paste this into Claude or ChatGPT at the start of a session

```
You are helping with Theswampdon — a GTA mafia RP stream channel.
Character: Vincenzo "Vince" Genovese (Genovese family, Bensonhurst → Los Santos).
Tagline: "Same rules. Different city."
Repo source of truth: OpenMontage → projects/gta-stream/
Do NOT invent a different channel name or character name.
Twitch/Kick: @theswampdon (already registered).
Output format: markdown I can paste into the repo. Label which file it belongs in.
```

### File ownership map

| File | Owner | Safe for Claude/ChatGPT to draft? |
|------|-------|-----------------------------------|
| `NAMING.md` | Cursor / human lock | No — ask before changing |
| `character-bible.md` | Shared | Yes — append lore, don't rewrite identity sheet |
| `channel-brand-profile.md` | Shared | Yes — bios, titles, hashtags |
| `visual-style.md` | Shared | Yes — palette tweaks with hex codes |
| `stream-ops-playbook.md` | Shared | Yes — OBS tips |
| `CLIP_WORKFLOW.md` | Cursor | Commands only unless improving docs |
| `trailer/` | Cursor | Script drafts OK; render in Cursor |
| `assets/overlays/` | Cursor | Copy text; HTML edits via Cursor |
| `go-live/` | Shared | **Preferred dump zone for paste-ready copy** |
| `WORK_LOG.md` | All agents | Append a short note after each session |

## Conflict rules

1. **Newer committed file wins** over chat memory.
2. If two agents disagree on lore, check `character-bible.md` → **Canon Rules** (Fixed vs Flexible).
3. Never merge Nexus AI Media branding into Theswampdon overlays or watermarks.
4. Append to `WORK_LOG.md` instead of deleting another agent's notes.

## What each tool should do next

| Tool | Best next jobs |
|------|----------------|
| **Cursor** | Renders, overlays, scripts, git, clip-factory, repo structure |
| **Claude** | Longer lore scenes, stream episode outlines, in-character VO drafts |
| **ChatGPT** | Title A/B tests, hashtag packs, short TikTok hooks, schedule calendars |

## Status snapshot (update when things change)

- [x] Phase 1 foundation docs
- [x] Phase 2 trailer source (re-render locally after clone — MP4s are gitignored)
- [x] Phase 3 clip-factory docs + script
- [x] Phase 4 OBS HTML overlays
- [x] Twitch + Kick `@theswampdon` registered
- [ ] Paste bios on Twitch/Kick (see `go-live/`)
- [ ] OBS scenes configured on streaming PC
- [ ] YouTube + TikTok handles
- [ ] First live stream
