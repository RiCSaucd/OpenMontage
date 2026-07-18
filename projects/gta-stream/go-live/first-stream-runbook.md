# First Stream Runbook — Theswampdon

Print or pin this. Goal: **one clean 90–120 min first live** without overbuilding.

---

## T-minus 1 day

1. Paste bios from [`bios.md`](bios.md) on **Twitch** and **Kick**.
2. Create Twitch panels from [`twitch-panels.md`](twitch-panels.md).
3. Add chat commands from [`chat-commands.md`](chat-commands.md).
4. Set schedule panel timezone.
5. Pin disclaimer panel.

---

## OBS scenes (1920×1080)

Import browser sources pointing at local files in `projects/gta-stream/assets/overlays/`:

| Scene | Browser source file |
|-------|---------------------|
| Starting Soon | `starting-soon.html` |
| Live — RP | game + webcam + `live-overlay.html` (transparent) |
| BRB | `brb.html` |
| Ending | `stream-ending.html` |

**Live — RP layers (bottom → top):**
1. Game Capture (GTA / FiveM)
2. Webcam ~400×225, bottom-right
3. Browser: `live-overlay.html` (1920×1080, Shutdown source when not visible = off for smoother)

Audio: noise gate + compressor on mic (see `../stream-ops-playbook.md`).

---

## Multistream

1. Restream (or obs-multi-rtmp): connect **Twitch** + **Kick** (`theswampdon`).
2. OBS Stream service → Restream key (or dual RTMP).
3. 5-minute test stream → confirm both platforms show video + chat.

---

## First stream structure (suggested)

| Time | Scene | What you do |
|------|-------|-------------|
| 0:00 | Starting Soon | Soft music (DMCA-safe). Chat open. |
| 0:05 | Live — RP | **OOC 60s:** "Welcome to Theswampdon — fiction RP." Then drop OOC. |
| 0:06–0:12 | Live — RP | **Lore drop:** Bensonhurst flashback (2–3 min). Use bible quick card. |
| 0:12–1:30 | Live — RP | Play — Monday collections / first LS business beat. |
| 1:30 | Ending | Thank chat. Plug Kick mirror. "Clips tomorrow." |

**Title:**
```
[RP] Vince Genovese — first night in LS | !lore !rules
```

---

## After stream (same night or +24h)

1. Save VOD as:
   ```
   projects/gta-stream/source/YYYY-MM-DD_twitch_first-stream-rp.mkv
   ```
2. Run:
   ```bash
   ./projects/gta-stream/scripts/run-clip-factory.sh \
     projects/gta-stream/source/YYYY-MM-DD_twitch_first-stream-rp.mkv
   ```
3. Post 1–2 vertical clips when TikTok/YT ready.
4. Append a note to `../WORK_LOG.md`.

---

## Quick character card (on-air)

```
VINCE GENOVESE — 38 — Bensonhurst → LS (2012)
Made family: Genovese (Sal → Tony → Vince)
Voice: Brooklyn, calm, short when hot
Never: tutorials, real names, break omertà
Hook: "Same rules. Different city."
```

Full bible: `../character-bible.md`
