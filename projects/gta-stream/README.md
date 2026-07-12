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
| [`CLIP_WORKFLOW.md`](CLIP_WORKFLOW.md) | VOD → TikTok/Shorts pipeline |
| [`assets/overlays/`](assets/overlays/) | OBS browser-source HTML overlays |
| [`trailer/`](trailer/) | HyperFrames channel trailer source |
| [`renders/`](renders/) | Rendered MP4 outputs |
| [`scripts/run-clip-factory.sh`](scripts/run-clip-factory.sh) | Clip batch automation |

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
2. Paste bios on Twitch/Kick from `channel-brand-profile.md`
3. Read `character-bible.md` quick reference card
4. Import overlays from `assets/overlays/` into OBS (1920×1080 browser sources)
5. Configure multistream per `stream-ops-playbook.md` (Twitch + Kick already registered)
6. Register YouTube + TikTok when ready; upload `renders/channel-trailer.mp4` to YouTube
7. Go live — then run `scripts/run-clip-factory.sh` on the VOD within 24h

## Character at a glance

**Vincenzo "Vince" Genovese** — born Bensonhurst 1975, Genovese made family (Sal → Tony → Vince), teen pot empire via kid runners, refused Gambino recruitment, now in Los Santos since 2012.

**Tagline:** *Same rules. Different city.*
