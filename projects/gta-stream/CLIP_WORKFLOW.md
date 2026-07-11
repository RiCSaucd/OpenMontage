# Clip Factory Workflow — Theswampdon

Turn stream VODs into TikTok, YouTube Shorts, and YouTube highlight clips using the OpenMontage **clip-factory** pipeline.

---

## Quick Start

```bash
# 1. Place your stream recording in source/
cp ~/Videos/2026-07-15_twitch_monday-collections-rp.mkv \
   projects/gta-stream/source/

# 2. Run the clip batch script
./projects/gta-stream/scripts/run-clip-factory.sh \
  projects/gta-stream/source/2026-07-15_twitch_monday-collections-rp.mkv

# 3. Outputs land in projects/gta-stream/renders/clips/<date>/
```

---

## Pipeline

**Manifest:** [`pipeline_defs/clip-factory.yaml`](../../pipeline_defs/clip-factory.yaml)

| Stage | Output | What happens |
|-------|--------|--------------|
| idea | brief | Clip count, platforms, selection criteria (RP drama, lore, hooks) |
| script | script + transcript | Full VOD transcription with timestamps |
| scene | scene_plan | Clip boundaries, hooks, aspect ratios |
| asset | asset_manifest | Caption styling from `visual-style.md` |
| edit | edit_decisions | Per-clip in/out, subtitle burn |
| compose | MP4 clips | 9:16 TikTok/Shorts + 16:9 YouTube |
| publish | metadata pack | Titles, descriptions, hashtags |

---

## Clip Selection Criteria (GTA RP)

Prioritize moments that work **without** full stream context:

1. **Hook in first 2 seconds** — conflict line, lore punchline, or visual action
2. **Lore drops** — "Back in Bensonhurst…" flashbacks
3. **Character beats** — Gambino refusal, Sal's rule, Tony phone call
4. **RP drama** — beef, heist payoff, close call
5. **Funny fish-out-of-water** — Brooklyn guy in LS

**Skip:** Long silent driving, menu navigation, OOC chat, DMCA-risk music segments

---

## Platform Specs

| Platform | Aspect | Resolution | Max length | File suffix |
|----------|--------|------------|------------|-------------|
| TikTok | 9:16 | 1080×1920 | 60–180s | `_tiktok.mp4` |
| YouTube Shorts | 9:16 | 1080×1920 | ≤60s ideal | `_shorts.mp4` |
| YouTube highlight | 16:9 | 1920×1080 | 2–8 min | `_yt.mp4` |

---

## Brand Application

From [`visual-style.md`](../visual-style.md):

- **Watermark:** `THESWAMPDON` lower-left, 40% opacity, `#C5A46E`
- **Captions:** Off-white on charcoal box, Bebas Neue for emphasis words
- **End slate (optional):** "Full RP on Twitch" + handle

---

## Publish Metadata Templates

### TikTok / Shorts title patterns
```
Vince Genovese said NO to the Gambino crew 👀 #GTARP #MafiaRP
Brooklyn mafia RP — this lore drop goes hard #GTA5 #Roleplay
When the Genovese kid runs Los Santos streets #GTAV #FiveM
```

### YouTube highlight title
```
[GTA RP] Vince Genovese — Monday Collections | Theswampdon
```

### Description block (paste all platforms)
```
🎮 Live GTA mafia roleplay as Vincenzo "Vince" Genovese — Bensonhurst → Los Santos.
Fiction/RP only. Not real crime.

🔴 Live: Twitch & Kick @Theswampdon
📺 Full streams on YouTube

#GTARP #MafiaRP #GTA5 #Roleplay #Brooklyn #FiveM
```

### Hashtag rotation
```
#GTARP #GTA5 #MafiaRP #FiveM #Roleplay #Brooklyn #GTAV #LosSantos #StreamClip #Genovese
```

---

## Agent Execution (OpenMontage Rule Zero)

When running through the agent:

1. Read `pipeline_defs/clip-factory.yaml`
2. Read stage directors under `skills/pipelines/clip-factory/`
3. Run preflight (`make preflight`)
4. Create brief with:
   - `source_path`: VOD in `source/`
   - `clip_count`: 3–5 per 2hr stream
   - `platforms`: tiktok, youtube_shorts, youtube
   - `brand_style`: `projects/gta-stream/visual-style.md`
5. Execute stages with checkpoints
6. Output to `renders/clips/YYYY-MM-DD/`

---

## Post-Stream SLA

| When | Action |
|------|--------|
| **+0h** | Save MKV to `source/` with dated filename |
| **+24h** | Run clip-factory batch |
| **+24–48h** | Publish 1 Short/TikTok per day (stagger) |
| **+48h** | Upload full VOD to YouTube with chapter markers |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Transcription poor on accent | Re-run with larger Whisper model if available; manually fix key hook lines in script stage |
| Clip has copyrighted music | Trim segment or mute game audio for that clip |
| 9:16 crops facecam badly | Re-compose with facecam-safe crop box (top third) |
| No hooks found | Mark `_lore` sessions; run with lower clip count and longer min duration |

---

## Smoke Test (no stream required)

Validate tooling with the channel trailer as synthetic source:

```bash
./projects/gta-stream/scripts/run-clip-factory.sh \
  projects/gta-stream/renders/channel-trailer.mp4 \
  --smoke-test
```

This runs transcription + single-clip extraction to verify FFmpeg and transcriber availability.
