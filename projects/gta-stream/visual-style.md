---
name: "Theswampdon"
version: "1.0"
tags:
  - streaming
  - gta-rp
  - brooklyn-noir
  - mafia-rp
author: "Eric Hatch / ElevatestAug"
source_url: ""
created: "2026-07-11"

style_prompt_short: >
  Bensonhurst noir stream brand — 1980s Brooklyn brownstone grit meets Los Santos
  neon night. Charcoal blacks, sodium-vapor amber, aged gold accents, deep burgundy.
  Film grain, condensed bold titles, clean sans body. Never glam gangster, never Nexus crimson.

style_prompt_full: >
  Visual identity for a GTA mafia roleplay live stream channel "Theswampdon".
  Mood: late-1970s/1980s Brooklyn working-class Italian-American neighborhood at night —
  sodium-vapor streetlights (#E8A838 warm amber glow), wet asphalt reflections, brownstone
  stoops, social club doorways, muted winter coats. Transition aesthetic to modern Los Santos
  2013 — charcoal sky (#1A1A1E), distant city bokeh, subtle teal in shadows (#1E2A32).
  Primary background: Deep Charcoal (#1C1C1C). Secondary: Warm Slate (#2A2A2E). Text:
  Off-White (#F2EDE4) and Aged Gold (#C5A46E) for emphasis. Accent: Deep Burgundy (#6B1D2A)
  — NOT bright blood red (#8B0000 Nexus crimson is forbidden). Typography: condensed bold
  sans-serif for alerts and titles (Bebas Neue, Oswald, or similar); clean sans for chat
  panels (Inter, system-ui). Motion: slow push-ins, 0.4s ease-out fades, subtle 35mm film
  grain overlay at 8% opacity. Avoid: neon pink cyberpunk, Sopranos clone fonts, gold chains
  and glam gangster imagery, skulls, guns as logo focus, instructional crime graphics.
  Stream overlay safe zones: 1920x1080 — top 120px for alerts, bottom 200px for captions/game
  HUD, right 380px optional chat dock. Webcam frame: thin gold (#C5A46E) 2px border, 8px
  radius, drop shadow. "LIVE" badge: burgundy pill, white text, subtle pulse. End cards: centered
  wordmark "THESWAMPDON" with tagline "Same rules. Different city."

colors:
  primary:
    - name: "Deep Charcoal"
      hex: "#1C1C1C"
      role: "overlay backgrounds, panels, primary canvas"
    - name: "Warm Slate"
      hex: "#2A2A2E"
      role: "secondary panels, chat box, BRB screens"
  accent:
    - name: "Sodium Amber"
      hex: "#E8A838"
      role: "streetlight glow, LIVE accent highlights, warm rim"
    - name: "Aged Gold"
      hex: "#C5A46E"
      role: "titles, webcam border, premium emphasis"
    - name: "Deep Burgundy"
      hex: "#6B1D2A"
      role: "LIVE badge, alerts, Genovese loyalty accent — not bright red"
  neutral:
    - name: "Off-White"
      hex: "#F2EDE4"
      role: "primary text on dark backgrounds"
    - name: "Muted Gray"
      hex: "#8A8580"
      role: "secondary text, timestamps, labels"
    - name: "Shadow Teal"
      hex: "#1E2A32"
      role: "Los Santos night sky gradient, depth in shadows"

typography:
  display:
    family: "Bebas Neue, Oswald, sans-serif"
    weight: "bold"
    style: "uppercase, letter-spacing 0.08em, tight lines"
  body:
    family: "Inter, system-ui, sans-serif"
    weight: "regular"
    style: "sentence case, line-height 1.5"
  caption:
    family: "Inter, system-ui, sans-serif"
    weight: "medium"
    style: "small caps for labels, 11-12px equivalent"
  rules:
    - "Display font for channel name, scene titles, and alert headers only"
    - "Never use script or gothic blackletter — avoids cosplay gangster cliché"
    - "Minimum 18px body equivalent for stream overlay readability"
    - "White/off-white text always on dark panel — never reverse on busy game footage without scrim"

layout:
  grid: "16:9 stream canvas, 8px base unit, 24px panel padding"
  alignment: "Lower-third for name/title; top-left for LIVE badge; bottom-right optional webcam"
  aspect_ratio: "16:9 primary; 9:16 for Shorts/TikTok clip exports"
  notes:
    - "Keep center 70% clear for game action — overlays on edges only"
    - "Webcam: 320x180 or 400x225 bottom-right, 24px margin"
    - "Chat overlay: 340px wide right column, 60% opacity charcoal scrim"

motion:
  transitions:
    - "fade 400ms ease-out"
    - "slow push-in 1.2s on title cards"
    - "subtle grain flicker static overlay"
  animation_style: >
    Restrained and cinematic. Elements fade in; no bounce or elastic easing.
    LIVE badge: gentle opacity pulse 2s loop. Stinger: 0.8s gold line wipe left-to-right.
  pacing: "Slow for lore moments; snappy 0.3s for alert pop-ins during action"
  audio_cues:
    - "Low vinyl crackle optional under lore segments"
    - "Single muted thud for scene transition — no gunshot SFX in brand stinger"

mood:
  keywords:
    - "Brooklyn noir"
    - "neighborhood grit"
    - "quiet loyalty"
    - "sodium night"
    - "invisible power"
  era: "1980s Bensonhurst primary reference; 2013 Los Santos secondary"
  cultural_reference: "Mean Streets restraint, A Bronx Tale neighborhood tone — not Scarface glam"
  avoid:
    - "Nexus AI Media crimson (#8B0000)"
    - "Gold chains, champagne, nightclub promoter aesthetic"
    - "Skulls, crosshairs, bullet hole motifs"
    - "Neon cyberpunk palette"
    - "Comic-book mafia caricature"

assets:
  reference_images: []
  gsep_elements: []
  html_snippets:
    - "assets/overlays/live-overlay.html"
    - "assets/overlays/starting-soon.html"
    - "assets/overlays/brb.html"
    - "assets/overlays/stream-ending.html"
  color_palette_image:
    url: ""

x_heygen:
  video_id: ""
  orientation: "landscape"

x_figma:
  library_id: ""
---

## Design Principles

1. **Neighborhood over empire** — brownstone stoops, not penthouse views
2. **Invisible power** — typography and color do the work; no weapon iconography
3. **Dual city** — Brooklyn warmth (amber) meets LS cool (teal shadows)
4. **Stream-first** — readable at 1080p on mobile crop; never block HUD center

## OBS / Streamlabs Application

- Import HTML overlays as **Browser Source** at 1920×1080
- Set webcam frame via CSS border on separate source or integrated in overlay
- Use **starting-soon**, **brb**, **stream-ending** scenes as full-screen browser sources
- Film grain: optional 8% opacity PNG overlay on top of composite

## Clip Factory / Shorts

- Captions: Off-White text, Deep Charcoal box at 85% opacity, Bebas Neue for hook words
- Watermark: "THESWAMPDON" lower-left, 40% opacity, Aged Gold
- 9:16 safe zone: keep text in center 80% width; hook in top third

## FLUX / B-Roll Prompt Base

```
Cinematic 1980s Bensonhurst Brooklyn street at night, sodium-vapor streetlights,
wet asphalt, brownstone row houses, Italian-American neighborhood, men in coats
near social club doorway, dramatic low-key lighting, film grain, muted warm palette
charcoal and amber #E8A838, photorealistic cinematic still --ar 16:9
```

## Asset Checklist

| Asset | File | Status |
|-------|------|--------|
| Live overlay (game + webcam frame) | `assets/overlays/live-overlay.html` | Created |
| Starting soon | `assets/overlays/starting-soon.html` | Created |
| BRB | `assets/overlays/brb.html` | Created |
| Stream ending | `assets/overlays/stream-ending.html` | Created |
| Offline banner spec | 1920×1080, centered wordmark | In HTML |
| Channel trailer | `renders/channel-trailer.mp4` | Phase 2 |
