# Ghost creators — 30s viral short (Sep 4, 2026)

Mute-first 9:16 news slam about this week's YouTube / TikTok story: paid actors reading AI-aided scripts as fake independent hosts, ~$26 a video, 45M+ YouTube views, 20 channels terminated for spam, clips still recirculating on TikTok.

Does **not** restage or quote the political attack video titles.

## Sources

- [Semafor Sep 2](https://www.semafor.com/article/09/02/2026/paid-actors-ai-writing-how-a-new-kind-of-video-business-cashed-in-on-americas-divided-politics)
- [Semafor Sep 3](https://www.semafor.com/article/09/03/2026/youtube-cracks-down-on-ghost-creators)
- [TNW Sep 4](https://thenextweb.com/news/youtube-ghost-creators-paid-actors-ai-detection-loophole)

## Runtime

Locked at proposal: **ffmpeg**. Remotion and HyperFrames were considered and rejected because they are not on this machine. Piper / cloud TTS unavailable — captions are the voice.

Re-render (needs `ffmpeg` + `numpy`):

```bash
python3 examples/ghost-creators-viral/scripts/render_short.py
```

Output: `artifacts/ghost_creators_viral_short.mp4` (1080×1920, 30.00s, H.264 + AAC).

Media under `assets/` and `artifacts/*.{mp4,png,jpg}` is regenerable and gitignored.
