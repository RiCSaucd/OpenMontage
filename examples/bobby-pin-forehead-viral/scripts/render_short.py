#!/usr/bin/env python3
"""Render the bobby-pin forehead 9:16 kinetic short with ffmpeg.

Topic: TikTok/YouTube bobby-pin-on-forehead trend (Khaleej Times Sep 2 2026;
Dr Sara Webb / Swinburne via news.com.au). Remotion/HyperFrames/Piper
unavailable here. Palette is cream/brass/navy — not ghost-creators red/ink
and not BDH-CQ cyan.
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
CREAM = np.array([0.98, 0.93, 0.86], dtype=np.float32)
NAVY = np.array([0.09, 0.13, 0.22], dtype=np.float32)
BRASS = np.array([0.84, 0.62, 0.16], dtype=np.float32)
CORAL = np.array([0.90, 0.34, 0.30], dtype=np.float32)
MINT = np.array([0.18, 0.55, 0.48], dtype=np.float32)
SKIN = np.array([0.93, 0.74, 0.62], dtype=np.float32)
WHITE = np.array([0.99, 0.98, 0.96], dtype=np.float32)


def _yyxx() -> tuple[np.ndarray, np.ndarray]:
    y = np.linspace(-1.0, 1.0, H, dtype=np.float32)[:, None]
    x = np.linspace(-1.0, 1.0, W, dtype=np.float32)[None, :]
    return y, x


def vignette() -> np.ndarray:
    y, x = _yyxx()
    r = np.sqrt(x * x + y * y)
    return np.clip(1.15 - 0.55 * np.power(r, 1.4), 0.35, 1.0).astype(np.float32)


def grain(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 0.018, size=(H, W, 1)).astype(np.float32)


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


def still_pin() -> np.ndarray:
    img = np.broadcast_to(CREAM, (H, W, 3)).copy()
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    # forehead oval
    face = np.exp(-(((yy - H * 0.52) / 420) ** 2 + ((xx - W * 0.5) / 280) ** 2))
    img += face[:, :, None] * (SKIN - CREAM) * 0.95
    # pin: two parallel brass bars + rounded ends
    cx, cy = W * 0.5, H * 0.46
    bar = ((np.abs(xx - cx) < 8) & (np.abs(yy - cy) < 95)).astype(np.float32)
    bar2 = ((np.abs(xx - (cx + 22)) < 8) & (np.abs(yy - cy) < 95)).astype(np.float32)
    d1 = np.sqrt((xx - cx) ** 2 + (yy - (cy - 92)) ** 2)
    d2 = np.sqrt((xx - (cx + 22)) ** 2 + (yy - (cy - 92)) ** 2)
    d3 = np.sqrt((xx - (cx + 11)) ** 2 + (yy - (cy + 96)) ** 2)
    ends = ((d1 < 14) | (d2 < 14) | (d3 < 16)).astype(np.float32)
    pin = np.clip(bar + bar2 + ends, 0, 1)
    img += pin[:, :, None] * (BRASS - img) * 0.92
    add_glow(img, cy, cx + 10, BRASS, 90.0, 0.28)
    img *= vignette()[:, :, None]
    img += grain(2)
    return np.clip(img, 0, 1)


def still_stick() -> np.ndarray:
    img = np.broadcast_to(CREAM * 0.97, (H, W, 3)).copy()
    # empty hands / no-glue icons as two crossed-out bottles
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    for cx in (W * 0.32, W * 0.68):
        m = rounded_rect_mask(H * 0.48, cx, 280, 160, 20)
        img = img * (1.0 - 0.72 * m[:, :, None]) + WHITE * (0.72 * m[:, :, None])
        rim = np.clip(rounded_rect_mask(H * 0.48, cx, 296, 176, 22) - m, 0, 1)
        img += rim[:, :, None] * CORAL * 0.85
        d1 = np.abs((yy - H * 0.48) - 1.15 * (xx - cx))
        d2 = np.abs((yy - H * 0.48) + 1.15 * (xx - cx))
        xmark = (
            (np.minimum(d1, d2) < 11.0)
            & (np.abs(xx - cx) < 62)
            & (np.abs(yy - H * 0.48) < 108)
        ).astype(np.float32)
        img = img * (1.0 - 0.95 * xmark[:, :, None]) + CORAL * (0.95 * xmark[:, :, None])
    add_glow(img, H * 0.48, W * 0.5, MINT, 220.0, 0.12)
    img *= vignette()[:, :, None]
    img += grain(10)
    return np.clip(img, 0, 1)


def still_myth() -> np.ndarray:
    img = np.broadcast_to(NAVY * 0.35 + CREAM * 0.65, (H, W, 3)).copy()
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    cx, cy = W * 0.5, H * 0.48
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    # eye
    eye = np.clip((160 - d) / 6.0, 0, 1)
    pupil = np.clip((48 - d) / 3.0, 0, 1)
    img += eye[:, :, None] * WHITE * 0.55
    img += pupil[:, :, None] * NAVY * 0.85
    # magnet U below
    mag = rounded_rect_mask(H * 0.68, W * 0.5, 120, 220, 18)
    img += mag[:, :, None] * CORAL * 0.35
    # big X
    d1 = np.abs((yy - cy) - 0.85 * (xx - cx))
    d2 = np.abs((yy - cy) + 0.85 * (xx - cx))
    xmark = ((np.minimum(d1, d2) < 10.0) & (np.abs(xx - cx) < 210) & (np.abs(yy - cy) < 210)).astype(np.float32)
    img += xmark[:, :, None] * CORAL * 0.9
    add_glow(img, cy, cx, CORAL, 160.0, 0.16)
    img *= vignette()[:, :, None]
    img += grain(3)
    return np.clip(img, 0, 1)


def still_oil() -> np.ndarray:
    img = np.broadcast_to(CREAM, (H, W, 3)).copy()
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    # droplet
    drop = np.exp(-(((yy - H * 0.46) / 210) ** 2 + ((xx - W * 0.5) / 130) ** 2))
    img += drop[:, :, None] * (MINT - CREAM) * 0.55
    shine = np.exp(-(((yy - H * 0.40) / 40) ** 2 + ((xx - W * 0.46) / 22) ** 2))
    img += shine[:, :, None] * WHITE * 0.45
    # film ring
    d = np.sqrt((xx - W * 0.5) ** 2 + (yy - H * 0.62) ** 2)
    ring = np.clip(1.0 - np.abs(d - 180) / 12.0, 0, 1)
    img += ring[:, :, None] * BRASS * 0.5
    add_glow(img, H * 0.46, W * 0.5, MINT, 140.0, 0.22)
    img *= vignette()[:, :, None]
    img += grain(7)
    return np.clip(img, 0, 1)


def still_physicist() -> np.ndarray:
    img = np.broadcast_to(NAVY, (H, W, 3)).copy()
    card = rounded_rect_mask(H * 0.50, W * 0.5, 720, 780, 28)
    img += card[:, :, None] * (CREAM - NAVY) * 0.92
    # small brass pin badge
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    d = np.sqrt((xx - W * 0.5) ** 2 + (yy - H * 0.36) ** 2)
    badge = np.clip((70 - d) / 4.0, 0, 1)
    img += badge[:, :, None] * BRASS * 0.85
    add_glow(img, H * 0.50, W * 0.5, BRASS, 180.0, 0.14)
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
    beat = 60.0 / 100.0
    bass = 0.10 * np.sin(2 * math.pi * 65 * t) * (0.75 + 0.25 * np.sin(2 * math.pi * 0.4 * t))
    chime = 0.045 * np.sin(2 * math.pi * 392 * t) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.5 * t))
    rng = np.random.default_rng(902)
    noise = rng.normal(0, 1, n).astype(np.float32)
    tick = np.zeros(n, dtype=np.float32)
    for i in range(int(DURATION / beat)):
        start = int(i * beat * sr)
        env = np.exp(-np.arange(int(0.04 * sr), dtype=np.float32) / (0.012 * sr))
        end = min(n, start + env.size)
        tick[start:end] += 0.05 * noise[start:end] * env[: end - start]
    accent = np.zeros(n, dtype=np.float32)
    for s in (0.0, 4.0, 10.0, 18.0, 24.0):
        start = int(s * sr)
        tt = np.arange(int(0.18 * sr), dtype=np.float32) / sr
        env = np.exp(-tt / 0.05)
        tone = np.sin(2 * math.pi * (220 * np.exp(-tt / 0.08)) * tt)
        end = min(n, start + tt.size)
        accent[start:end] += 0.22 * env[: end - start] * tone[: end - start]
    mix = bass + chime + tick + accent
    fade = int(0.5 * sr)
    mix[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    peak = float(np.max(np.abs(mix))) or 1.0
    mix = 0.82 * mix / peak
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def write_ass(path: Path) -> None:
    body = """[Script Info]
Title: Bobby pin forehead viral short
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Inter,80,&H00FFFFFF,&H000000FF,&HAA1C2117,&H64000000,1,0,0,0,100,100,-1,0,1,5,0,5,90,90,0,1
Style: Giant,Inter,108,&H00FFFFFF,&H000000FF,&HAA1C2117,&H64000000,1,0,0,0,100,100,-2,0,1,6,0,5,90,90,0,1
Style: Brass,Inter,48,&H002EA4D1,&H000000FF,&HAA1C2117,&H64000000,1,0,0,0,100,100,1,0,1,4,0,5,90,90,0,1
Style: Mint,Inter,48,&H007A8C2E,&H000000FF,&HAA1C2117,&H64000000,1,0,0,0,100,100,1,0,1,4,0,5,90,90,0,1
Style: Coral,Inter,48,&H00525CE8,&H000000FF,&HAA1C2117,&H64000000,1,0,0,0,100,100,1,0,1,4,0,5,90,90,0,1
Style: Cap,Inter,36,&H00FFFFFF,&H000000FF,&HAA1C2117,&H78000000,1,0,0,0,100,100,0.4,0,1,3,0,2,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:04.00,Giant,,0,0,0,,{\\pos(540,600)\\fad(70,120)\\t(0,200,\\fscx108\\fscy108)}STICK THIS
Dialogue: 0,0:00:00.70,0:00:04.00,Hook,,0,0,0,,{\\pos(540,760)\\fad(80,120)}ON YOUR FOREHEAD
Dialogue: 0,0:00:02.00,0:00:04.00,Brass,,0,0,0,,{\\pos(540,920)\\fad(80,120)}TRY IT
Dialogue: 0,0:00:00.00,0:00:04.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}A bobby pin. Dead center.
Dialogue: 0,0:00:04.00,0:00:10.00,Hook,,0,0,0,,{\\pos(540,560)\\fad(60,120)}IT STAYS
Dialogue: 0,0:00:05.00,0:00:10.00,Giant,,0,0,0,,{\\pos(540,720)\\fad(80,120)}NO GLUE
Dialogue: 0,0:00:07.00,0:00:10.00,Mint,,0,0,0,,{\\pos(540,900)\\fad(80,120)}NO TAPE
Dialogue: 0,0:00:04.00,0:00:10.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}People are using forks next.
Dialogue: 0,0:00:10.00,0:00:18.00,Hook,,0,0,0,,{\\pos(540,540)\\fad(60,120)}NOT YOUR
Dialogue: 0,0:00:11.00,0:00:18.00,Giant,,0,0,0,,{\\pos(540,700)\\fad(80,120)}THIRD EYE
Dialogue: 0,0:00:13.40,0:00:18.00,Coral,,0,0,0,,{\\pos(540,880)\\fad(80,120)}NOT A MAGNET
Dialogue: 0,0:00:10.00,0:00:18.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}Your brain field is way too weak.
Dialogue: 0,0:00:18.00,0:00:24.00,Hook,,0,0,0,,{\\pos(540,560)\\fad(60,120)}IT'S OIL
Dialogue: 0,0:00:19.40,0:00:24.00,Giant,,0,0,0,,{\\pos(540,740)\\fad(80,120)}SEBUM
Dialogue: 0,0:00:21.20,0:00:24.00,Mint,,0,0,0,,{\\pos(540,920)\\fad(80,80)}PLUS SURFACE TENSION
Dialogue: 0,0:00:18.00,0:00:24.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}The flat center of your forehead wins.
Dialogue: 0,0:00:24.00,0:00:30.00,Hook,,0,0,0,,{\\pos(540,560)\\fad(60,120)}A PHYSICIST
Dialogue: 0,0:00:25.20,0:00:30.00,Giant,,0,0,0,,{\\pos(540,720)\\fad(80,120)}SAID SO
Dialogue: 0,0:00:27.00,0:00:30.00,Brass,,0,0,0,,{\\pos(540,900)\\fad(80,80)}SEPT 2026
Dialogue: 0,0:00:24.00,0:00:30.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}Your forehead is just sticky.
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
        ("s1_pin", still_pin, 4.0, 1.12),
        ("s2_stick", still_stick, 6.0, 1.10),
        ("s3_myth", still_myth, 8.0, 1.14),
        ("s4_oil", still_oil, 6.0, 1.10),
        ("s5_phys", still_physicist, 6.0, 1.12),
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

    out = ARTIFACTS / "bobby_pin_forehead_viral_short.mp4"
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
    for t, name in [(0.4, "frame_hook"), (7.0, "frame_stick"), (14.5, "frame_myth"), (26.5, "frame_end")]:
        run(["ffmpeg", "-y", "-ss", str(t), "-i", str(out), "-frames:v", "1", str(ARTIFACTS / f"{name}.png")])
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
