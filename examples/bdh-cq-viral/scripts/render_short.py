#!/usr/bin/env python3
"""Render the BDH-CQ 9:16 kinetic short with ffmpeg.

Cloud constraint: Remotion/HyperFrames/Piper and Hub image downloads are
unavailable here. Stills and the music bed are generated locally; captions
are burned from ASS. Output is 1080x1920, ~30s, H.264 + AAC.
"""
from __future__ import annotations

import math
import os
import struct
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
CYAN = np.array([0.0, 0.90, 1.0], dtype=np.float32)
AMBER = np.array([1.0, 0.69, 0.13], dtype=np.float32)
NAVY = np.array([0.02, 0.035, 0.07], dtype=np.float32)


def _yyxx() -> tuple[np.ndarray, np.ndarray]:
    y = np.linspace(-1.0, 1.0, H, dtype=np.float32)[:, None]
    x = np.linspace(-1.0, 1.0, W, dtype=np.float32)[None, :]
    return y, x


def vignette() -> np.ndarray:
    y, x = _yyxx()
    r = np.sqrt(x * x + y * y)
    return np.clip(1.15 - 0.78 * np.power(r, 1.35), 0.12, 1.0).astype(np.float32)


def grain(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 0.028, size=(H, W, 1)).astype(np.float32)


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


def still_lattice() -> np.ndarray:
    img = np.broadcast_to(NAVY, (H, W, 3)).copy()
    rng = np.random.default_rng(150)
    n = 36
    ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
    rad = 0.22 + 0.08 * rng.random(n)
    nx = 0.50 + rad * np.cos(ang)
    ny = 0.46 + rad * np.sin(ang) * 0.72
    px = nx * W
    py = ny * H
    for i in range(n):
        for j in range(i + 1, n):
            d = math.hypot(float(px[i] - px[j]), float(py[i] - py[j]))
            if d < 210:
                steps = int(d)
                ts = np.linspace(0, 1, steps, dtype=np.float32)
                xs = (px[i] + (px[j] - px[i]) * ts).astype(np.int32)
                ys = (py[i] + (py[j] - py[i]) * ts).astype(np.int32)
                ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
                img[ys[ok], xs[ok]] = np.minimum(img[ys[ok], xs[ok]] + CYAN * 0.22, 1.0)
    for i in range(n):
        add_glow(img, float(py[i]), float(px[i]), CYAN, 18.0, 0.55)
        add_glow(img, float(py[i]), float(px[i]), np.array([0.8, 1.0, 1.0]), 6.0, 0.95)
    add_glow(img, H * 0.46, W * 0.50, CYAN, 160.0, 0.18)
    img *= vignette()[:, :, None]
    img += grain(150)
    return np.clip(img, 0, 1)


def still_cards() -> np.ndarray:
    img = np.broadcast_to(NAVY, (H, W, 3)).copy()
    y, x = _yyxx()
    img += (0.04 * (0.5 + 0.5 * np.sin(18 * y + 3 * x)))[:, :, None] * CYAN * 0.15
    cards = [
        (0.22, AMBER, 0.95),
        (0.38, CYAN, 0.35),
        (0.52, CYAN, 0.28),
        (0.66, CYAN, 0.18),
        (0.80, CYAN, 0.10),
    ]
    for cy_n, color, amp in cards:
        m = rounded_rect_mask(cy_n * H, W * 0.5, 210, 620, 22)
        img += m[:, :, None] * color * amp * 0.55
        edge = rounded_rect_mask(cy_n * H, W * 0.5, 214, 624, 22) - m
        img += np.clip(edge, 0, 1)[:, :, None] * color * amp
    add_glow(img, 0.22 * H, W * 0.5, AMBER, 140.0, 0.35)
    img *= vignette()[:, :, None]
    img += grain(772)
    return np.clip(img, 0, 1)


def still_penny() -> np.ndarray:
    img = np.broadcast_to(NAVY, (H, W, 3)).copy()
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    # holographic 3x3 grid behind
    gx0, gy0 = W * 0.5, H * 0.42
    for r in range(3):
        for c in range(3):
            cx = gx0 + (c - 1) * 150
            cy = gy0 + (r - 1) * 150
            m = rounded_rect_mask(cy, cx, 128, 128, 10)
            hue = CYAN * (0.4 + 0.2 * ((r + c) % 2)) + AMBER * (0.15 * (r == 1 and c == 1))
            img += m[:, :, None] * hue * 0.35
    # coin
    cx, cy, rad = W * 0.5, H * 0.62, 210.0
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    coin = np.clip((rad - d) / 3.0, 0, 1)
    rim = np.clip(1.0 - np.abs(d - rad) / 7.0, 0, 1)
    copper = np.array([0.82, 0.45, 0.18], dtype=np.float32)
    highlight = np.clip((cx - 40 - xx) / rad, 0, 1) * coin
    img += coin[:, :, None] * copper * 0.85
    img += highlight[:, :, None] * np.array([1.0, 0.85, 0.55]) * 0.35
    img += rim[:, :, None] * AMBER * 0.65
    add_glow(img, cy, cx, copper, 90.0, 0.25)
    img *= vignette()[:, :, None]
    img += grain(295)
    return np.clip(img, 0, 1)


def still_spiral() -> np.ndarray:
    img = np.broadcast_to(NAVY * 0.7, (H, W, 3)).copy()
    rng = np.random.default_rng(42)
    n = 160
    t = np.linspace(0.0, 10.5 * math.pi, n)
    r = 12 + 9.5 * t
    xs = W * 0.5 + r * np.cos(t)
    ys = H * 0.48 + r * np.sin(t) * 0.92
    for i in range(n):
        frac = i / n
        color = CYAN * (1.0 - 0.55 * frac) + AMBER * (0.45 * frac)
        sigma = 8.0 + 12.0 * (1.0 - frac)
        add_glow(img, float(ys[i]), float(xs[i]), color, sigma, 0.28 + 0.40 * (1 - frac))
    add_glow(img, H * 0.48, W * 0.5, np.array([1.0, 0.95, 0.75]), 28.0, 1.1)
    add_glow(img, H * 0.48, W * 0.5, CYAN, 220.0, 0.22)
    # extra dust
    dust_x = rng.uniform(0, W, 40)
    dust_y = rng.uniform(0, H, 40)
    for i in range(40):
        add_glow(img, float(dust_y[i]), float(dust_x[i]), CYAN, 3.5, 0.18)
    img *= vignette()[:, :, None]
    img += grain(42)
    return np.clip(img, 0, 1)


def still_aisle() -> np.ndarray:
    img = np.broadcast_to(NAVY, (H, W, 3)).copy()
    y, x = _yyxx()
    # perspective floor
    floor = np.clip((y - 0.15) * 1.4, 0, 1)
    img += floor[:, :, None] * np.array([0.04, 0.05, 0.07])
    # vanishing racks as repeating vertical bars that converge
    for side in (-1.0, 1.0):
        for k in range(14):
            depth = 0.12 + k * 0.06
            px = 0.5 + side * (0.42 * (1.0 - depth))
            height = 0.18 + 0.72 * (1.0 - depth)
            width = 0.07 * (1.0 - 0.7 * depth)
            m = rounded_rect_mask(H * 0.48, W * px, H * height, W * width, 4)
            col = np.array([0.05, 0.07, 0.09]) + CYAN * (0.04 * (k % 2))
            img += m[:, :, None] * col
            # cyan edge strip
            edge = rounded_rect_mask(H * 0.48, W * (px + side * width * 0.35), H * height * 0.92, 6, 1)
            img += edge[:, :, None] * CYAN * (0.12 + 0.02 * k)
    add_glow(img, H * 0.72, W * 0.5, CYAN, 70.0, 0.85)
    add_glow(img, H * 0.78, W * 0.5, CYAN, 180.0, 0.25)
    # ceiling lights
    for k in range(8):
        add_glow(img, H * 0.08, W * (0.5 + (k - 3.5) * 0.04), np.array([0.9, 0.95, 1.0]), 18.0, 0.25)
    img *= vignette()[:, :, None]
    img += grain(826)
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
    # 100 BPM dark explainer bed
    beat = 60.0 / 100.0
    bass = 0.16 * np.sin(2 * math.pi * 55 * t) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.4 * t))
    fifth = 0.07 * np.sin(2 * math.pi * 82.5 * t + 0.2)
    sub = 0.10 * np.sin(2 * math.pi * 27.5 * t)
    # filtered noise hats
    rng = np.random.default_rng(2026)
    noise = rng.normal(0, 1, n).astype(np.float32)
    hat = np.zeros(n, dtype=np.float32)
    for i in range(int(DURATION / (beat / 2))):
        start = int(i * (beat / 2) * sr)
        env = np.exp(-np.arange(int(0.04 * sr), dtype=np.float32) / (0.012 * sr))
        end = min(n, start + env.size)
        hat[start:end] += 0.045 * noise[start:end] * env[: end - start]
    # slams at scene cuts
    slams = [0.0, 4.0, 10.0, 18.0, 24.0]
    kick = np.zeros(n, dtype=np.float32)
    for s in slams:
        start = int(s * sr)
        tt = np.arange(int(0.18 * sr), dtype=np.float32) / sr
        env = np.exp(-tt / 0.045)
        tone = np.sin(2 * math.pi * (90 * np.exp(-tt / 0.04)) * tt)
        end = min(n, start + tt.size)
        kick[start:end] += 0.32 * env[: end - start] * tone[: end - start]
    mix = bass + fifth + sub + hat + kick
    # fade out last 0.6s
    fade = int(0.6 * sr)
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
    # PlayRes 1080x1920. Safe zone 900x1400 centered => x 90-990, y 260-1660.
    # Kinetic slam copy, 3-5 words per block, Inter Bold.
    body = """[Script Info]
Title: BDH-CQ viral short
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Inter,92,&H00FFFFFF,&H000000FF,&HAA000000,&H64000000,1,0,0,0,100,100,-2,0,1,5,0,5,90,90,0,1
Style: Sub,Inter,44,&H00E5FF00,&H000000FF,&HAA000000,&H64000000,1,0,0,0,100,100,1,0,1,4,0,5,90,90,0,1
Style: Giant,Inter,120,&H00FFFFFF,&H000000FF,&HAA000000,&H64000000,1,0,0,0,100,100,-3,0,1,6,0,5,90,90,0,1
Style: Amber,Inter,52,&H0020B0FF,&H000000FF,&HAA000000,&H64000000,1,0,0,0,100,100,1,0,1,4,0,5,90,90,0,1
Style: Cap,Inter,36,&H00FFFFFF,&H000000FF,&HAA000000,&H78000000,1,0,0,0,100,100,0.5,0,1,3,0,2,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:04.00,Giant,,0,0,0,,{\\pos(540,640)\\fad(70,120)\\t(0,220,\\fscx108\\fscy108)}150 MILLION
Dialogue: 0,0:00:00.70,0:00:04.00,Hook,,0,0,0,,{\\pos(540,780)\\fad(80,120)}PARAMETERS
Dialogue: 0,0:00:02.00,0:00:04.00,Amber,,0,0,0,,{\\pos(540,900)\\fad(80,120)}THAT'S IT.
Dialogue: 0,0:00:00.00,0:00:04.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}150 million parameters. That's it.
Dialogue: 0,0:00:04.00,0:00:10.00,Hook,,0,0,0,,{\\pos(540,560)\\fad(60,120)}#1 TRENDING PAPER
Dialogue: 0,0:00:04.40,0:00:10.00,Sub,,0,0,0,,{\\pos(540,680)\\fad(80,120)}LAST 30 DAYS ON HUGGING FACE
Dialogue: 0,0:00:06.00,0:00:10.00,Giant,,0,0,0,,{\\pos(540,860)\\fad(80,120)\\t(0,200,\\fscx106\\fscy106)}BDH-CQ
Dialogue: 0,0:00:07.40,0:00:10.00,Amber,,0,0,0,,{\\pos(540,1020)\\fad(80,120)}LATENT REASONING
Dialogue: 0,0:00:04.00,0:00:10.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}Hottest paper of the last 30 days.
Dialogue: 0,0:00:10.00,0:00:18.00,Giant,,0,0,0,,{\\pos(540,560)\\fad(60,120)\\t(0,240,\\fscx110\\fscy110)}29.5%
Dialogue: 0,0:00:10.80,0:00:18.00,Hook,,0,0,0,,{\\pos(540,720)\\fad(80,120)}PASS@2 · ARC-AGI-1
Dialogue: 0,0:00:13.00,0:00:18.00,Sub,,0,0,0,,{\\pos(540,860)\\fad(80,120)}$0.0007 PER TASK
Dialogue: 0,0:00:15.20,0:00:18.00,Amber,,0,0,0,,{\\pos(540,1000)\\fad(80,120)}NEW COST FRONTIER
Dialogue: 0,0:00:10.00,0:00:18.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}Less than a tenth of a cent.
Dialogue: 0,0:00:18.00,0:00:24.00,Hook,,0,0,0,,{\\pos(540,620)\\fad(60,120)}NO CHAIN OF THOUGHT
Dialogue: 0,0:00:19.40,0:00:24.00,Giant,,0,0,0,,{\\pos(540,800)\\fad(80,120)}LATENT SPACE
Dialogue: 0,0:00:21.20,0:00:24.00,Amber,,0,0,0,,{\\pos(540,960)\\fad(80,120)}THEN IT ANSWERS
Dialogue: 0,0:00:18.00,0:00:24.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}Thinks in latent space. Not tokens.
Dialogue: 0,0:00:24.00,0:00:30.00,Hook,,0,0,0,,{\\pos(540,600)\\fad(60,120)}THE GIANTS GOT
Dialogue: 0,0:00:25.20,0:00:30.00,Giant,,0,0,0,,{\\pos(540,760)\\fad(80,120)}OUT-EFFICIENT
Dialogue: 0,0:00:27.00,0:00:30.00,Amber,,0,0,0,,{\\pos(540,920)\\fad(80,120)}AUGUST 2026
Dialogue: 0,0:00:28.20,0:00:30.00,Sub,,0,0,0,,{\\pos(540,1060)\\fad(80,80)}arxiv.org/abs/2608.09888
Dialogue: 0,0:00:24.00,0:00:30.00,Cap,,0,0,0,,{\\pos(540,1480)\\fad(80,80)}The giants got out-efficient.
"""
    path.write_text(body, encoding="utf-8")


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def ppm_to_png(ppm: Path, png: Path) -> None:
    run(["ffmpeg", "-y", "-i", str(ppm), "-frames:v", "1", str(png)])


def ken_burns(png: Path, out: Path, frames: int, zoom_end: float) -> None:
    # Scale up so zoompan has room, then output 1080x1920.
    z_expr = f"1+{zoom_end - 1:.4f}*on/{frames}"
    vf = (
        f"scale=1296:2304,zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps={FPS},format=yuv420p"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(png),
            "-vf",
            vf,
            "-frames:v",
            str(frames),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(out),
        ]
    )


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    stills = [
        ("s1_lattice", still_lattice, 4.0, 1.12),
        ("s2_cards", still_cards, 6.0, 1.10),
        ("s3_penny", still_penny, 8.0, 1.14),
        ("s4_spiral", still_spiral, 6.0, 1.16),
        ("s5_aisle", still_aisle, 6.0, 1.10),
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
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(visual),
        ]
    )

    wav = ASSETS / "bed.wav"
    write_wav(wav)
    loud = ASSETS / "bed_loudnorm.wav"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(wav),
            "-af",
            "loudnorm=I=-22:TP=-2:LRA=11",
            str(loud),
        ]
    )

    ass = ASSETS / "captions.ass"
    write_ass(ass)

    out = ARTIFACTS / "bdh_cq_last30days_short.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(visual),
            "-i",
            str(loud),
            "-vf",
            f"ass={ass}:fontsdir={FONTDIR},format=yuv420p",
            "-c:v",
            "libx264",
            "-profile:v",
            "high",
            "-level",
            "4.2",
            "-preset",
            "medium",
            "-b:v",
            "10M",
            "-maxrate",
            "12M",
            "-bufsize",
            "20M",
            "-r",
            str(FPS),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-shortest",
            "-movflags",
            "+faststart",
            str(out),
        ]
    )

    # Review frames at hook / mid / climax / end
    for t, name in [(0.3, "frame_hook"), (12.0, "frame_stat"), (20.0, "frame_latent"), (27.5, "frame_end")]:
        run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(t),
                "-i",
                str(out),
                "-frames:v",
                "1",
                str(ARTIFACTS / f"{name}.png"),
            ]
        )
    print(f"wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
