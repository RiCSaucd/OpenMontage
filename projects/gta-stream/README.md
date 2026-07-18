# Theswampdon — GTA Mafia Stream Channel

Launch package for **Vincenzo "Vince" Genovese** — Genovese-family GTA roleplay streamed on Twitch, Kick, YouTube, and clipped to TikTok.

## Contents

| File | Purpose |
|------|---------|
| [`NAMING.md`](NAMING.md) | Locked brand defaults (dual identity with Nexus AI Media) |
| [`character-bible.md`](character-bible.md) | Full RP backstory — pin before every stream |
| [`channel-brand-profile.md`](channel-brand-profile.md) | Platform bios, monetization, content pillars |
| [`visual-style.md`](visual-style.md) | Colors, typography, overlay specs |
| [`stream-ops-playbook.md`](stream-ops-playbook.md) | OBS, multistream, audio, weekly rhythm |
| [`CLIP_WORKFLOW.md`](CLIP_WORKFLOW.md) | VOD → TikTok/Shorts pipeline (quick start below) |
| [`source/`](source/) | Drop stream VODs here for clip-factory |
| [`assets/overlays/`](assets/overlays/) | OBS browser-source HTML overlays |
| [`trailer/`](trailer/) | HyperFrames channel trailer source |
| [`renders/`](renders/) | Trailer + clip MP4 outputs |
| [`scripts/run-clip-factory.sh`](scripts/run-clip-factory.sh) | Clip batch automation |
| [`go-live/`](go-live/) | Paste-ready bios, panels, chat commands, first-stream runbook |
| [`MULTI_AGENT_HANDOFF.md`](MULTI_AGENT_HANDOFF.md) | How Cursor + Claude + ChatGPT share this folder |
| [`WORK_LOG.md`](WORK_LOG.md) | Append-only session log across tools |

## Renders

- **16:9 trailer:** `renders/channel-trailer.mp4` (~50s, with narration)
- **9:16 teaser:** `renders/channel-trailer-teaser-9x16.mp4`

Re-render trailer:
```bash
cd trailer && npx hyperframes lint && npx hyperframes render --quality high \
  --output ../renders/channel-trailer.mp4
```

## Quick launch checklist

1. ~~Register Twitch + Kick~~ — **done** (@theswampdon)
2. Paste bios + panels from [`go-live/`](go-live/) (start with `go-live/bios.md`)
3. Follow [`go-live/first-stream-runbook.md`](go-live/first-stream-runbook.md)
4. Import overlays from `assets/overlays/` into OBS (1920×1080 browser sources)
5. Configure multistream per `stream-ops-playbook.md`
6. Register YouTube + TikTok when ready; upload `renders/channel-trailer.mp4` to YouTube
7. Go live — then follow [`CLIP_WORKFLOW.md`](CLIP_WORKFLOW.md) (drop VOD in `source/`, run clip script within 24h)

## Working with Claude / ChatGPT

This folder is the **single source of truth**. Paste the starter prompt from [`MULTI_AGENT_HANDOFF.md`](MULTI_AGENT_HANDOFF.md) into other chats, then bring finished drafts back here (prefer `go-live/` or `WORK_LOG.md`).

## Character at a glance

**Vincenzo "Vince" Genovese** — born Bensonhurst 1975, Genovese made family (Sal → Tony → Vince), teen pot empire via kid runners, refused Gambino recruitment, now in Los Santos since 2012.

**Tagline:** *Same rules. Different city.*
