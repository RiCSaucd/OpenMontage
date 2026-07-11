# Stream Ops Playbook — Theswampdon

Practical go-live checklist for multistream GTA RP. OpenMontage does not configure these tools — follow on your streaming PC.

---

## 1. Software Stack

| Tool | Purpose |
|------|---------|
| **OBS Studio** (29+) | Scenes, capture, encoding |
| **Restream** or **OBS Multistream plugin** | Twitch + Kick + YouTube Live simultaneously |
| **Twitch/Kick/YouTube apps** | Chat bots (optional: StreamElements, Nightbot) |
| **TikTok** | Post clips manually or via clip-factory exports (live simulcast optional when eligible) |

---

## 2. OBS Scene Layout

### Scene: **Live — RP**

| Layer (bottom → top) | Source | Settings |
|----------------------|--------|----------|
| 1 | Game capture | GTA V / FiveM fullscreen or window |
| 2 | Webcam | 400×225, bottom-right, 24px margin |
| 3 | Browser — `live-overlay.html` | 1920×1080, transparent background |
| 4 | Optional grain PNG | 8% opacity full screen |

### Scene: **Starting Soon**
- Full-screen browser → `assets/overlays/starting-soon.html`
- Optional low-volume ambient music (royalty-free, see §6)

### Scene: **BRB**
- Full-screen browser → `assets/overlays/brb.html`

### Scene: **Ending**
- Full-screen browser → `assets/overlays/stream-ending.html`

### Scene: **OOC / Just Chatting**
- Webcam large center or left; overlay hidden or minimal

---

## 3. Multistream Setup

### Option A — Restream (recommended for simplicity)
1. Connect Twitch, Kick, YouTube accounts in Restream dashboard
2. OBS → Settings → Stream → Service: **Restream.io** → paste stream key
3. Set output: **1080p30** or **720p60** based on upload (see §5)
4. Test stream to all platforms 5 min before going live

### Option B — OBS Multistream Plugin
1. Install obs-multi-rtmp or equivalent
2. Add primary + secondary RTMP URLs per platform
3. Verify Kick ingest URL separately (changes occasionally)

### YouTube Live notes
- Enable stream in YouTube Studio → schedule or go live instant
- Title template: `[GTA RP LIVE] Vince Genovese — Theswampdon`

### TikTok
- **Primary path:** Upload vertical clips from `CLIP_WORKFLOW.md` (most reliable)
- **Live path:** TikTok Live Studio when follower threshold met — optional third Restream destination

---

## 4. Audio Chain

```
Mic → Noise suppression (RNNoise or OBS filter) → Compressor → Limiter → OBS mix
Game audio → -6 to -12 dB vs voice (voice must win)
Optional music → -20 dB under voice, mute during intense RP dialogue
```

**Recommended OBS filters (mic):**
- Noise gate: close -35 dB, open -45 dB
- Compressor: ratio 3:1, threshold -18 dB
- Limiter: -3 dB ceiling

**In-character voice:** Slight lower pitch optional via Voicemeter — keep natural; Brooklyn accent is performance, not heavy FX.

---

## 5. Encoding Presets

| Upload | Resolution | Bitrate | Encoder |
|--------|------------|---------|---------|
| ≥ 10 Mbps | 1920×1080 @ 30fps | 6000 Kbps video | x264 veryfast or NVENC |
| 5–10 Mbps | 1280×720 @ 60fps | 4500 Kbps | NVENC preferred |
| < 5 Mbps | 1280×720 @ 30fps | 3000 Kbps | Test before live RP |

Record **separate MKV** locally for VOD + clip-factory (File → Recording, same resolution as stream).

---

## 6. DMCA-Safe Music

Do **not** use Spotify/Apple Music on stream.

**Safe sources:**
- Epidemic Sound / Artlist (subscription)
- YouTube Audio Library
- In-game GTA radio (muted or low — some DMCA risk on VOD; prefer original score off for YouTube uploads)

For **starting soon** / **BRB** screens: instrumental jazz or ambient — no lyrics.

---

## 7. VOD Naming Convention

Save recordings to a folder clip-factory will ingest:

```
projects/gta-stream/source/YYYY-MM-DD_platform_session-title.mkv
```

**Examples:**
```
2026-07-15_twitch_monday-collections-rp.mkv
2026-07-18_kick_friday-heist-night.mkv
```

Include `_lore` in filename if session starts with Bensonhurst flashback (helps clip selection):

```
2026-07-15_twitch_lore-gambino-recruitment.mkv
```

---

## 8. Pre-Stream Checklist (15 min)

- [ ] Read `character-bible.md` quick reference card
- [ ] Set stream title + category on primary platform (others sync via Restream)
- [ ] Test game audio + mic in OBS
- [ ] Load **Starting Soon** → switch to **Live — RP** at go time
- [ ] Pin RP disclaimer in chat (bot timer or manual)
- [ ] Phone on DND; Discord notifications off

---

## 9. Post-Stream Checklist (30 min)

- [ ] Stop recording; verify MKV in `source/`
- [ ] Switch to **Ending** scene for 30s before disconnect
- [ ] Export or copy VOD to `projects/gta-stream/source/` if recorded locally
- [ ] Run clip-factory workflow (see `CLIP_WORKFLOW.md`) within 24h
- [ ] Update stream title to offline / schedule next

---

## 10. Weekly Rhythm

| Day | Focus |
|-----|-------|
| **Mon** | Live RP — "Monday collections" |
| **Wed** | Live RP or GTA story mode in-character |
| **Fri** | Peak-time RP session |
| **Sat** | Clip publish batch + optional bonus stream |
| **Sun** | Rest; upload full VOD to YouTube |

---

## 11. Twitch/Kick Panel Copy (paste-ready)

**About Vince**
```
Vincenzo "Vince" Genovese — Bensonhurst, Brooklyn → Los Santos.
Genovese family. Fiction/RP only. Same rules. Different city.
```

**Schedule**
```
Mon / Wed / Fri — Live RP (ET)
Clips: TikTok + YouTube Shorts
```

**Disclaimer**
```
All content is fictional GTA roleplay for entertainment.
Not affiliated with real criminal organizations. 18+
```

---

## 12. Troubleshooting

| Issue | Fix |
|-------|-----|
| Desync on multistream | Reduce bitrate; drop one platform temporarily |
| Game capture black | Run GTA borderless window; use window capture |
| Browser overlay not transparent | Check "Shutdown source when not visible"; CSS `background: transparent` |
| Kick chat not in OBS | Add Kick chat dock separately; Restream chat aggregator |
| VOD muted on YouTube | Re-export without copyrighted music; use clip-factory on local MKV |
