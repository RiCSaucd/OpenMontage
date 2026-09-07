#!/usr/bin/env python3
"""Render the ghost-creators 9:16 kinetic short with ffmpeg.

Topic: YouTube/TikTok 'ghost creators' news (Semafor Sep 2, takedown Sep 3,
TNW Sep 4 2026). Remotion/HyperFrames/Piper unavailable here.
"""
from __future__ import annotations

import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ARTIFACTS = ROOT / "artifacts"
W, H = 1080, 1920
FPS = 30
DURATION = 30.0
FONTDIR = "/usr/share/fonts/truetype/macos"
RED = np.array([1.0, 0.18, 0.16], dtype=np.float32)
AMBER = np.array([1.0, 0.78, 0.16], dtype=np.float32)
WHITE = np.array([0.95, 0.95, 0.97], dtype=np.float32)
INK = np.array([0.04, 0.03, 0.04], dtype=np.float32)


def _yyxx() -> tuple[np.ndarray, np.ndarray]:
    y = np.linspace(-1.0, 1.0, H, dtype=np.float32)[:, None]
    x = np.linspace(-1.0, 1.0, W, dtype=np.float32)[None, :]
    return y, x


def vignette() -> np.ndarray:
    y, x = _yyxx()
    r = np.sqrt(x * x + y * y)
    return np.clip(1.2 - 0.85 * np.power(r, 1.25), 0.1, 1.0).astype(np.float32)


def grain(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 0.032, size=(H, W, 1)).astype(np.float32)


def add_glow(img: np.ndarray, cy: float, cx: float, color: np.ndarray, sigma: float, amp: float) -> None:
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    g = np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2.0 * sigma * sigma))
    img += g[:, :, None] * (color * amp)


def rounded_rect_mask(cy: float, cx: float, h: float, w: float, radius: float) -> np.ndarray:
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    dx = np.abs(xx - cx) - (w * 0.5 - radius)
    dy = np.abs(yy - cy) - (h * 0.5 - radius)
    dx = np.maximum(dx, 0.0)
    dy = np.maximum(dy, 0.0)
    dist = np.sqrt(dx * dx + dy * dy) - radius
    return np.clip(1.0 - dist / 2.5, 0.0, 1.0).astype(np.float32)


def still_cash() -> np.ndarray:
    img = np.broadcast_to(INK, (H, W, 3)).copy()
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    # stacked bills
    for i, cy in enumerate((0.38, 0.50, 0.62)):
        m = rounded_rect_mask(H * cy, W * 0.5 + i * 8, 220, 520, 8)
        green = np.array([0.18, 0.42, 0.22], dtype=np.float32)
        img += m[:, :, None] * green * (0.55 - i * 0.08)
        rim = rounded_rect_mask(H * cy, W * 0.5 + i * 8, 226, 526, 8) - m
        img += np.clip(rim, 0, 1)[:, :, None] * AMBER * 0.35
    # coin
    d = np.sqrt((xx - W * 0.5) ** 2 + (yy - H * 0.72) ** 2)
    coin = np.clip((90 - d) / 3.0, 0, 1)
    img += coin[:, :, None] * AMBER * 0.7
    add_glow(img, H * 0.50, W * 0.5, AMBER, 180.0, 0.22)
    img *= vignette()[:, :, None]
    img += grain(26)
    return np.clip(img, 0, 1)


def still_lens() -> np.ndarray:
    img = np.broadcast_to(INK, (H, W, 3)).copy()
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    cx, cy = W * 0.5, H * 0.48
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    for r, amp in ((340, 0.18), (260, 0.28), (180, 0.4), (90, 0.7)):
        ring = np.clip(1.0 - np.abs(d - r) / 10.0, 0, 1)
        img += ring[:, :, None] * WHITE * amp
    pupil = np.clip((70 - d) / 4.0, 0, 1)
    img += pupil[:, :, None] * RED * 0.85
    add_glow(img, cy, cx, RED, 80.0, 0.55)
    add_glow(img, cy, cx, WHITE, 22.0, 0.9)
    # scanlines
    scan = ((yy.astype(int) % 6) < 1).astype(np.float32)
    img *= 1.0 - 0.12 * scan[:, :, None]
    img *= vignette()[:, :, None]
    img += grain(45)
    return np.clip(img, 0, 1)


def still_views() -> np.ndarray:
    img = np.broadcast_to(INK, (H, W, 3)).copy()
    # stacked channel cards
    for i, cy in enumerate(np.linspace(0.28, 0.78, 7)):
        m = rounded_rect_mask(H * cy, W * (0.5 + 0.02 * math.sin(i)), 140, 700, 14)
        img += m[:, :, None] * (WHITE * (0.06 + 0.02 * (i % 2)) + RED * (0.08 if i == 2 else 0.0))
        play = rounded_rect_mask(H * cy, W * 0.22, 48, 48, 24)
        img += play[:, :, None] * RED * 0.7
    add_glow(img, H * 0.48, W * 0.5, RED, 200.0, 0.18)
    img *= vignette()[:, :, None]
    img += grain(45_000_000 % 10_000)
    return np.clip(img, 0, 1)


def still_takedown() -> np.ndarray:
    img = np.broadcast_to(INK, (H, W, 3)).copy()
    # 4x5 grid of dead channels
    for r in range(5):
        for c in range(4):
            cx = W * (0.22 + c * 0.19)
            cy = H * (0.28 + r * 0.12)
            m = rounded_rect_mask(cy, cx, 150, 170, 10)
            img += m[:, :, None] * np.array([0.12, 0.10, 0.10]) * 0.9
            # X
            yy = np.arange(H, dtype=np.float32)[:, None]
            xx = np.arange(W, dtype=np.float32)[None, :]
            d1 = np.abs((yy - cy) - (xx - cx))
            d2 = np.abs((yy - cy) + (xx - cx))
            xmark = ((np.minimum(d1, d2) < 4.0) & (np.abs(xx - cx) < 38) & (np.abs(yy - cy) < 38)).astype(np.float32)
            img += xmark[:, :, None] * RED * 0.85
    add_glow(img, H * 0.5, W * 0.5, RED, 220.0, 0.16)
    img *= vignette()[:, :, None]
    img += grain(20)
    return np.clip(img, 0, 1)


def still_phones() -> np.ndarray:
    img = np.broadcast_to(INK, (H, W, 3)).copy()
    # three phones receding
    for i, (cx, cy, sc) in enumerate(((0.32, 0.52, 1.0), (0.50, 0.50, 1.15), (0.70, 0.54, 0.9))):
        m = rounded_rect_mask(H * cy, W * cx, 620 * sc, 300 * sc, 36)
        screen = rounded_rect_mask(H * cy, W * cx, 560 * sc, 250 * sc, 18)
        img += m[:, :, None] * np.array([0.14, 0.14, 0.16])
        img += screen[:, :, None] * (RED if i == 1 else WHITE) * (0.18 if i != 1 else 0.28)
    add_glow(img, H * 0.50, W * 0.50, RED, 160.0, 0.22)
    img *= vignette()[:, :, None]
    img += grain(2026)
    return np.clip(img, 0, 1)


def write_ppm(path: Path, img: np.ndarray) -> None:
    rgb = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(f"P6\n{W} {H}\n255\n".encode())
        f.write(rgb.tobytes())


def write_wav(path: Path) -> None:
    sr = 44100
    n = int(sr * DURATION)
    t = np.arange(n, dtype=np.float32) / sr
    beat = 60.0 / 108.0
    bass = 0.15 * np.sin(2 * math.pi * 49 * t) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.35 * t))
    pulse = 0.06 * np.sin(2 * math.pi * 98 * t)
    rng = np.random.default_rng(904)
    noise = rng.normal(0, 1, n).astype(np.float32)
    hat = np.zeros(n, dtype=np.float32)
    for i in range(int(DURATION / (beat / 2))):
        start = int(i * (beat / 2) * sr)
        env = np.exp(-np.arange(int(0.035 * sr), dtype=np.float32) / (0.01 * sr))
        end = min(n, start + env.size)
        hat[start:end] += 0.04 * noise[start:end] * env[: end - start]
    kick = np.zeros(n, dtype=np.float32)
    for s in (0.0, 4.0, 10.0, 18.0, 24.0):
        start = int(s * sr)
        tt = np.arange(int(0.16 * sr), dtype=np.float32) / sr
        env = np.exp(-tt / 0.04)
        tone = np.sin(2 * math.pi * (80 * np.exp(-tt / 0.035)) * tt)
        end = min(n, start + tt.size)
        kick[start:end] += 0.34 * env[: end - start] * tone[: end - start]
    mix = bass + pulse + hat + kick
    fade = int(0.55 * sr)
    mix[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    peak = float(np.max(np.abs(mix))) or 1.0
    mix = 0.85 * mix / peak
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def write_ass(path: Path) -> None:
    body = """[Script Info]
Title: Ghost creators viral short
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Inter,88,&H00FFFFFF,&H000000FF,&HAA000000,&H64000000,1,0,0,0,100,100,-2,0,1,5,0,5,90,90,0,1
Style: Giant,Inter,118,&H00FFFFFF,&H000000FF,&HAA000000,&H64000000,1,0,0,0,100,100,-3,0,1,6,0,5,90,90,0,1
Style: Red,Inter,52,&H001428FF,&H000000FF,&HAA000000,&H64000000,1,0,0,0,100,100,1,0,1,4,0,5,90,90,0,1
Style: Amber,Inter,48,&H0020C8FF,&H000000FF,&HAA000000,&H64000000,1,0,0,0,100,100,1,0,1,4,0,5,90,90,0,1
Style: Cap,Inter,36,&H00FFFFFF,&H000000FF,&HAA000000,&H78000000,1,0,0,0,100,100,0.5,0,1,3,0,2,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:04.00,Giant,,0,0,0,,{\\pos(540,620)\\fad(70,120)\\t(0,200,\\fscx108\\fscy108)}$26
Dialogue: 0,0:00:00.60,0:00:04.00,Hook,,0,0,0,,{\\pos(540,760)\\fad(80,120)}A VIDEO
Dialogue: 0,0:00:01.80,0:00:04.00,Amber,,0,0,0,,{\\pos(540,900)\\fad(80,120)}THAT'S THE GIG RATE
Dialogue: 0,0:00:00.00,0:00:04.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}Twenty-six dollars a video.
Dialogue: 0,0:00:04.00,0:00:10.00,Hook,,0,0,0,,{\\pos(540,560)\\fad(60,120)}REAL ACTORS
Dialogue: 0,0:00:04.80,0:00:10.00,Hook,,0,0,0,,{\\pos(540,700)\\fad(80,120)}AI SCRIPTS
Dialogue: 0,0:00:06.20,0:00:10.00,Giant,,0,0,0,,{\\pos(540,880)\\fad(80,120)}45 MILLION
Dialogue: 0,0:00:07.60,0:00:10.00,Amber,,0,0,0,,{\\pos(540,1040)\\fad(80,120)}YOUTUBE VIEWS
Dialogue: 0,0:00:04.00,0:00:10.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}Plus millions more on TikTok.
Dialogue: 0,0:00:10.00,0:00:18.00,Hook,,0,0,0,,{\\pos(540,560)\\fad(60,120)}THE DETECTOR
Dialogue: 0,0:00:11.00,0:00:18.00,Hook,,0,0,0,,{\\pos(540,700)\\fad(80,120)}HUNTS FAKE FACES
Dialogue: 0,0:00:13.20,0:00:18.00,Giant,,0,0,0,,{\\pos(540,880)\\fad(80,120)}SO THEY HIRED
Dialogue: 0,0:00:15.00,0:00:18.00,Red,,0,0,0,,{\\pos(540,1040)\\fad(80,120)}REAL ONES
Dialogue: 0,0:00:10.00,0:00:18.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}A real face beats every AI label.
Dialogue: 0,0:00:18.00,0:00:24.00,Hook,,0,0,0,,{\\pos(540,600)\\fad(60,120)}SEMAFOR PUBLISHED
Dialogue: 0,0:00:19.40,0:00:24.00,Giant,,0,0,0,,{\\pos(540,760)\\fad(80,120)}20 CHANNELS
Dialogue: 0,0:00:21.20,0:00:24.00,Red,,0,0,0,,{\\pos(540,920)\\fad(80,120)}GONE
Dialogue: 0,0:00:22.40,0:00:24.00,Amber,,0,0,0,,{\\pos(540,1060)\\fad(80,80)}FOR SPAM. NOT LIES.
Dialogue: 0,0:00:18.00,0:00:24.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}YouTube took them down this week.
Dialogue: 0,0:00:24.00,0:00:30.00,Hook,,0,0,0,,{\\pos(540,600)\\fad(60,120)}THE CLIPS
Dialogue: 0,0:00:25.20,0:00:30.00,Giant,,0,0,0,,{\\pos(540,760)\\fad(80,120)}STILL LIVE
Dialogue: 0,0:00:26.80,0:00:30.00,Red,,0,0,0,,{\\pos(540,920)\\fad(80,120)}ON TIKTOK
Dialogue: 0,0:00:28.20,0:00:30.00,Amber,,0,0,0,,{\\pos(540,1060)\\fad(80,80)}SEPT 2026
Dialogue: 0,0:00:24.00,0:00:30.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}The loophole was a person.
"""
    path.write_text(body, encoding="utf-8")


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def ppm_to_png(ppm: Path, png: Path) -> None:
    run(["ffmpeg", "-y", "-i", str(ppm), "-frames:v", "1", str(png)])


def ken_burns(png: Path, out: Path, frames: int, zoom_end: float) -> None:
    z_expr = f"1+{zoom_end - 1:.4f}*on/{frames}"
    vf = (
        f"scale=1296:2304,zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps={FPS},format=yuv420p"
    )
    run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", str(png), "-vf", vf,
            "-frames:v", str(frames), "-c:v", "libx264", "-preset", "fast",
            "-crf", "18", "-pix_fmt", "yuv420p", str(out),
        ]
    )


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    stills = [
        ("s1_cash", still_cash, 4.0, 1.12),
        ("s2_views", still_views, 6.0, 1.10),
        ("s3_lens", still_lens, 8.0, 1.14),
        ("s4_takedown", still_takedown, 6.0, 1.10),
        ("s5_phones", still_phones, 6.0, 1.12),
    ]
    clips: list[Path] = []
    for name, fn, dur, zoom in stills:
        ppm = ASSETS / f"{name}.ppm"
        png = ASSETS / f"{name}.png"
        print(f"generating {name}", flush=True)
        write_ppm(ppm, fn())
        ppm_to_png(ppm, png)
        ppm.unlink(missing_ok=True)
        clip = ASSETS / f"{name}.mp4"
        ken_burns(png, clip, int(dur * FPS), zoom)
        clips.append(clip)

    concat_list = ASSETS / "concat.txt"
    concat_list.write_text("".join(f"file '{c}'\n" for c in clips), encoding="utf-8")
    visual = ASSETS / "visual.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(visual)])

    wav = ASSETS / "bed.wav"
    write_wav(wav)
    loud = ASSETS / "bed_loudnorm.wav"
    run(["ffmpeg", "-y", "-i", str(wav), "-af", "loudnorm=I=-22:TP=-2:LRA=11", str(loud)])

    ass = ASSETS / "captions.ass"
    write_ass(ass)
    (ARTIFACTS / "captions.ass").write_text(ass.read_text(encoding="utf-8"), encoding="utf-8")

    out = ARTIFACTS / "ghost_creators_viral_short.mp4"
    run(
        [
            "ffmpeg", "-y", "-i", str(visual), "-i", str(loud),
            "-vf", f"ass={ass}:fontsdir={FONTDIR},format=yuv420p",
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.2",
            "-preset", "medium", "-b:v", "10M", "-maxrate", "12M", "-bufsize", "20M",
            "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-shortest", "-movflags", "+faststart", str(out),
        ]
    )
    for t, name in [(0.4, "frame_hook"), (7.0, "frame_views"), (14.5, "frame_loophole"), (26.5, "frame_end")]:
        run(["ffmpeg", "-y", "-ss", str(t), "-i", str(out), "-frames:v", "1", str(ARTIFACTS / f"{name}.png")])
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
