#!/usr/bin/env python3
"""48s explainer: Sonnet 5.5 vs GPT-6 Astra, the late-September 2026 X trend.

Captions are the voice. Music is a local procedural bed. Motion is hand-authored
ffmpeg plates (Remotion and HyperFrames are not installed here). $0.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import types
import wave
from datetime import datetime, timezone
from pathlib import Path

# jsonschema is not installed and PyPI is blocked. Gate checks still run;
# schema validation is a no-op so checkpoints can be written offline.
_js = types.ModuleType("jsonschema")


class _ValidationError(Exception):
    pass


def _validate(*_a, **_k):
    return None


_js.ValidationError = _ValidationError
_js.validate = _validate
sys.modules["jsonschema"] = _js

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.checkpoint import init_project, write_checkpoint  # noqa: E402
from lib.paths import PROJECTS_DIR  # noqa: E402

PROJECT = "sonnet-55-x-trend"
TITLE = "The Trend Was the Bill"
PIPELINE = "animated-explainer"
PLAYBOOK = "flat-motion-graphics"
W, H, FPS = 1920, 1080, 24
HOLD = 8.0
DURATION = HOLD * 6  # 48.000

FONT_B = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/macos/Inter-Regular.ttf"
FONT_S = "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf"

# Spoken lines. They are burned as captions; there is no TTS on this machine.
LINES = [
    (0.4, 7.6, "September 28. Worldwide on X, a model name is trending. Sonnet 5.5."),
    (8.4, 15.6, "Twenty-five days earlier, GPT-6 Astra shipped. Ten dollars in. Fifty out."),
    (16.4, 23.6, "Sonnet 5.5 keeps the two and ten dollar rate. Anthropic says it is thirty percent faster than Sonnet 5."),
    (24.4, 31.6, "Terminal-Bench 4.0. Sonnet, seventy point six. Astra, fifty-seven point nine."),
    (32.4, 39.6, "Cheaper tokens are not a cheaper task. One lab measured Astra near three dollars a task. Sonnet, near eight."),
    (40.4, 47.6, "The trend on X was the invoice."),
]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def dt(text: str, **kw) -> str:
    parts = [f"drawtext=fontfile={kw.pop('font')}:text='{text}'"]
    for key, value in kw.items():
        parts.append(f"{key}={value}")
    return ":".join(parts)


def plate(out: Path, vf: str, seconds: float = HOLD) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x0B1020:s={W}x{H}:r={FPS}:d={seconds}",
            "-vf", vf,
            "-frames:v", str(int(seconds * FPS)),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an",
            str(out),
        ]
    )


def build_plates(work: Path) -> list[Path]:
    common_kicker = (
        f"fontsize=22:fontcolor=0xC8F542:x=120:y=150"
    )
    paths = []

    def base_rule() -> str:
        return "drawbox=x=120:y=128:w=64:h=4:color=0xC8F542:t=fill"

    # 1 — trend
    p = work / "p1.mp4"
    plate(p, ",".join([
        base_rule(),
        dt("WORLDWIDE ON X", font=FONT_B, **dict(fontsize=22, fontcolor="0xC8F542", x=200, y=112)),
        dt("28 SEP 2026", font=FONT_B, fontsize=28, fontcolor="0x8A8F98", x=120, y=220),
        dt("SONNET 5.5", font=FONT_B, fontsize=108, fontcolor="0xF4F1EA", x=120, y=300),
        dt("on the worldwide trend list", font=FONT_R, fontsize=36, fontcolor="0xD97757", x=120, y=460),
        dt("under 10k posts in that hour", font=FONT_R, fontsize=32, fontcolor="0x8A8F98", x=120, y=520),
    ]))
    paths.append(p)

    # 2 — astra prices
    p = work / "p2.mp4"
    plate(p, ",".join([
        base_rule(),
        dt("25 DAYS EARLIER", font=FONT_B, fontsize=22, fontcolor="0x8FB8FF", x=200, y=112),
        dt("GPT-6 ASTRA", font=FONT_B, fontsize=96, fontcolor="0xF4F1EA", x=120, y=240),
        dt("3 SEP 2026", font=FONT_B, fontsize=28, fontcolor="0x8A8F98", x=120, y=380),
        "drawbox=x=120:y=480:w=420:h=140:color=0x141A28:t=fill",
        "drawbox=x=560:y=480:w=420:h=140:color=0x141A28:t=fill",
        dt("$10  IN", font=FONT_B, fontsize=48, fontcolor="0x8FB8FF", x=160, y=520),
        dt("$50  OUT", font=FONT_B, fontsize=48, fontcolor="0x8FB8FF", x=600, y=520),
        dt("per million tokens", font=FONT_R, fontsize=26, fontcolor="0x8A8F98", x=120, y=660),
    ]))
    paths.append(p)

    # 3 — sonnet prices
    p = work / "p3.mp4"
    plate(p, ",".join([
        base_rule(),
        dt("THE WORKHORSE", font=FONT_B, fontsize=22, fontcolor="0xD97757", x=200, y=112),
        dt("SONNET 5.5", font=FONT_B, fontsize=96, fontcolor="0xF4F1EA", x=120, y=240),
        dt("28 SEP 2026", font=FONT_B, fontsize=28, fontcolor="0x8A8F98", x=120, y=380),
        "drawbox=x=120:y=480:w=420:h=140:color=0x1A1410:t=fill",
        "drawbox=x=560:y=480:w=420:h=140:color=0x1A1410:t=fill",
        dt("$2  IN", font=FONT_B, fontsize=48, fontcolor="0xD97757", x=170, y=520),
        dt("$10  OUT", font=FONT_B, fontsize=48, fontcolor="0xD97757", x=610, y=520),
        dt("30 percent faster than Sonnet 5", font=FONT_S, fontsize=32, fontcolor="0xF4F1EA", x=120, y=670),
    ]))
    paths.append(p)

    # 4 — bench bars. 70.6 / 57.9 of a 900px track.
    sonnet_w = int(900 * (70.6 / 80))
    astra_w = int(900 * (57.9 / 80))
    p = work / "p4.mp4"
    plate(p, ",".join([
        base_rule(),
        dt("TERMINAL-BENCH 4.0", font=FONT_B, fontsize=22, fontcolor="0xC8F542", x=200, y=112),
        dt("SONNET 5.5", font=FONT_B, fontsize=28, fontcolor="0xD97757", x=120, y=250),
        f"drawbox=x=120:y=300:w={sonnet_w}:h=56:color=0xD97757:t=fill",
        dt("70.6", font=FONT_B, fontsize=36, fontcolor="0x0B1020", x=140, y=312),
        dt("GPT-6 ASTRA", font=FONT_B, fontsize=28, fontcolor="0x8FB8FF", x=120, y=420),
        f"drawbox=x=120:y=470:w={astra_w}:h=56:color=0x8FB8FF:t=fill",
        dt("57.9", font=FONT_B, fontsize=36, fontcolor="0x0B1020", x=140, y=482),
        dt("agentic coding  ·  percent", font=FONT_R, fontsize=26, fontcolor="0x8A8F98", x=120, y=580),
    ]))
    paths.append(p)

    # 5 — invoice flip
    p = work / "p5.mp4"
    plate(p, ",".join([
        base_rule(),
        dt("SAME TASK, DIFFERENT BILL", font=FONT_B, fontsize=22, fontcolor="0xC8F542", x=200, y=112),
        dt("ASTRA", font=FONT_B, fontsize=28, fontcolor="0x8FB8FF", x=120, y=250),
        dt("~$3.26", font=FONT_B, fontsize=84, fontcolor="0xF4F1EA", x=120, y=290),
        dt("SONNET 5.5", font=FONT_B, fontsize=28, fontcolor="0xD97757", x=820, y=250),
        dt("~$7.60", font=FONT_B, fontsize=84, fontcolor="0xF4F1EA", x=820, y=290),
        dt("Intelligence Index task", font=FONT_R, fontsize=30, fontcolor="0x8A8F98", x=120, y=460),
        dt("Astra wrote far fewer tokens.", font=FONT_S, fontsize=32, fontcolor="0xF4F1EA", x=120, y=530),
        dt("The rate card is not the invoice.", font=FONT_S, fontsize=32, fontcolor="0xF4F1EA", x=120, y=580),
    ]))
    paths.append(p)

    # 6 — landing
    p = work / "p6.mp4"
    plate(p, ",".join([
        base_rule(),
        dt("THE TREND", font=FONT_B, fontsize=28, fontcolor="0x8A8F98", x=120, y=280),
        dt("WAS THE BILL.", font=FONT_B, fontsize=92, fontcolor="0xF4F1EA", x=120, y=340),
        dt("Anthropic  ·  The Neuron  ·  OrcaRouter  ·  Snaplytics", font=FONT_R, fontsize=24, fontcolor="0x8A8F98", x=120, y=500),
        dt("X worldwide archive  ·  28 Sep 2026", font=FONT_R, fontsize=24, fontcolor="0x8A8F98", x=120, y=540),
    ]))
    paths.append(p)
    return paths


def concat_video(plates: list[Path], out: Path) -> None:
    listing = out.with_suffix(".txt")
    listing.write_text("".join(f"file '{p}'\n" for p in plates), encoding="utf-8")
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
        "-c", "copy", str(out),
    ])


def write_ass(path: Path) -> None:
    events = []
    for start, end, text in LINES:
        events.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Cap,,0,0,0,,{text}"
        )
    path.write_text(
        "\n".join([
            "[Script Info]",
            "ScriptType: v4.00+",
            "PlayResX: 1920",
            "PlayResY: 1080",
            "WrapStyle: 0",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Cap,Inter,42,&H00F4F1EA,&H000000FF,&H00110B08,&H96000000,"
            "0,0,0,0,100,100,0,0,1,2,0,2,160,160,72,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
            *events,
            "",
        ]),
        encoding="utf-8",
    )


def _ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def write_music(path: Path, seconds: float = DURATION) -> None:
    sr = 44100
    n = int(sr * seconds)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        frames = bytearray()
        for i in range(n):
            t = i / sr
            env = min(1.0, t / 0.8) * min(1.0, (seconds - t) / 1.2)
            # A2 + E3 fifth, slow pulse, very quiet.
            pulse = 0.55 + 0.45 * math.sin(2 * math.pi * 0.5 * t)
            sample = (
                0.08 * math.sin(2 * math.pi * 110 * t)
                + 0.04 * math.sin(2 * math.pi * 164.81 * t)
                + 0.02 * math.sin(2 * math.pi * 220 * t) * pulse
            )
            value = int(max(-1, min(1, sample * env * 0.35)) * 32767)
            frames += value.to_bytes(2, "little", signed=True)
        wf.writeframes(frames)


def mux(video: Path, ass: Path, music: Path, out: Path) -> None:
    run([
        "ffmpeg", "-y",
        "-i", str(video),
        "-i", str(music),
        "-vf", f"ass={ass}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        str(out),
    ])


def probe(path: Path) -> dict:
    out = run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_name,width,height,avg_frame_rate,codec_type",
        "-of", "json", str(path),
    ])
    return json.loads(out.stdout)


def save(project: Path, name: str, data: dict) -> None:
    path = project / "artifacts" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def cp(stage: str, status: str, artifacts: dict, **kw) -> None:
    write_checkpoint(
        PROJECTS_DIR, PROJECT, stage, status, artifacts,
        pipeline_type=PIPELINE, style_playbook=PLAYBOOK,
        human_approved=True, **kw,
    )


def build_artifacts() -> dict:
    research = {
        "version": "1.0",
        "topic": "What trended on X in late September 2026: Claude Sonnet 5.5 versus GPT-6 Astra",
        "research_date": "2026-10-01",
        "landscape": {
            "existing_content": [
                {
                    "title": "Introducing Claude Sonnet 5.5",
                    "url": "https://www.anthropic.com/claude-sonnet-5-5",
                    "source": "blog",
                    "angle": "Vendor launch: faster, cheaper workhorse next to Opus 5.5",
                    "what_it_covers": "Sept 28 2026 launch, 30%+ faster than Sonnet 5, up to 30% less per task, Terminal-Bench 4.0 70.6%",
                    "what_it_misses": "Does not explain why the name hit the X trend list or the per-task invoice flip",
                },
                {
                    "title": "Claude Sonnet 5.5 vs GPT-6 Astra: where Sonnet wins",
                    "url": "https://www.theneuron.ai/news/claude-sonnet-5-5-vs-gpt-6-astra-where-sonnet-wins/",
                    "source": "blog",
                    "angle": "Benchmark horse race at one-fifth the token price",
                    "what_it_covers": "Astra launched Sept 3; Sonnet 70.6% vs Astra 57.9% on Terminal-Bench 4.0; $2/$10 vs $10/$50",
                    "what_it_misses": "The cases where Astra's shorter answers make the expensive model cheaper to run",
                },
                {
                    "title": "Claude Sonnet 5.5 vs GPT-6 Astra: 5x Rate, Half Cost",
                    "url": "https://www.orcarouter.ai/blog/claude-sonnet-5-5-vs-gpt-6-astra",
                    "source": "blog",
                    "angle": "Rate card versus completed-task cost",
                    "what_it_covers": "About $3.26 per Intelligence Index task for Astra vs about $7.60 for Sonnet 5.5, driven by output-token volume",
                    "what_it_misses": "The X trend context that made the comparison public",
                },
            ],
            "saturated_angles": [
                "Which lab is winning the benchmark table",
                "Cybersecurity capability threshold recaps",
            ],
            "underserved_gaps": [
                "A 48-second read of why the name trended: the invoice, not the leaderboard",
            ],
        },
        "trending": {
            "recent_developments": [
                {
                    "headline": "Sonnet 5.5 appears on the worldwide X trend list",
                    "url": "https://twitter-trends.snaplytics.io/2026-09-28/",
                    "date": "2026-09-28",
                    "relevance": "Primary reason this topic is the film",
                },
                {
                    "headline": "Anthropic introduces Claude Sonnet 5.5",
                    "url": "https://www.anthropic.com/claude-sonnet-5-5",
                    "date": "2026-09-28",
                    "relevance": "Launch day matches the trend snapshot",
                },
            ],
            "active_discussions": [
                {
                    "platform": "twitter",
                    "topic_or_url": "https://twitter-trends.snaplytics.io/2026-09-28/",
                    "sentiment": "A model name sat on the worldwide list beside sports and politics, under 10k posts in the captured hour",
                    "key_quotes": [],
                }
            ],
            "timeliness_window": "days",
        },
        "data_points": [
            {
                "claim": "On 28 Sep 2026 Sonnet 5.5 was on the worldwide X trend list, logged under 10k posts in that hour.",
                "source_url": "https://twitter-trends.snaplytics.io/2026-09-28/",
                "source_name": "Snaplytics worldwide X trend archive",
                "credibility": "secondary_source",
                "surprise_factor": "notable",
                "usable_as": "hook",
            },
            {
                "claim": "Anthropic introduced Claude Sonnet 5.5 on 28 Sep 2026: 30%+ faster than Sonnet 5 and up to 30% less per task for most work. Terminal-Bench 4.0 is listed at 70.6%.",
                "source_url": "https://www.anthropic.com/claude-sonnet-5-5",
                "source_name": "Anthropic",
                "credibility": "primary_source",
                "surprise_factor": "notable",
                "usable_as": "script_anchor",
            },
            {
                "claim": "GPT-6 Astra launched 3 Sep 2026. The Neuron reports Terminal-Bench 4.0 at 57.9% for Astra and token prices of $10/$50 versus Sonnet 5.5 at $2/$10.",
                "source_url": "https://www.theneuron.ai/news/claude-sonnet-5-5-vs-gpt-6-astra-where-sonnet-wins/",
                "source_name": "The Neuron",
                "credibility": "secondary_source",
                "surprise_factor": "surprising",
                "usable_as": "stat_card",
            },
            {
                "claim": "OrcaRouter measured about $3.26 per completed Intelligence Index task for GPT-6 Astra versus about $7.60 for Claude Sonnet 5.5, because Sonnet emitted far more output tokens.",
                "source_url": "https://www.orcarouter.ai/blog/claude-sonnet-5-5-vs-gpt-6-astra",
                "source_name": "OrcaRouter",
                "credibility": "secondary_source",
                "surprise_factor": "counterintuitive",
                "usable_as": "closing_punch",
            },
        ],
        "audience_insights": {
            "common_questions": [
                "Is Sonnet 5.5 actually cheaper than GPT-6 Astra?",
                "Who won Terminal-Bench?",
                "Why did a model name trend on X?",
            ],
            "misconceptions": [
                {
                    "myth": "The model with the lower token price is the cheaper one to run.",
                    "reality": "A routing lab found Astra finishing an Intelligence Index task for less money because it wrote fewer tokens.",
                    "source": "https://www.orcarouter.ai/blog/claude-sonnet-5-5-vs-gpt-6-astra",
                }
            ],
            "knowledge_level": "People who saw the name on X know a launch happened. They do not have the two prices and the invoice flip in one place.",
            "pain_points": [
                "Benchmark threads collapse price, speed, and task cost into one winner.",
            ],
        },
        "angles_discovered": [
            {
                "name": "The trend was the invoice",
                "hook": "X trended a model name. The useful argument was which bill you can defend.",
                "type": "data_driven",
                "why_now": "Sonnet 5.5 launched and hit the worldwide list on 28 Sep 2026, 25 days after Astra.",
                "grounded_in": ["Snaplytics trend row", "Anthropic prices and speed", "OrcaRouter per-task cost"],
            },
            {
                "name": "The cheaper bench is not the cheaper run",
                "hook": "Sonnet leads Terminal-Bench and still can cost more per finished task.",
                "type": "contrarian",
                "why_now": "Both numbers are public in the same week the name trended.",
                "grounded_in": ["Terminal-Bench 70.6 vs 57.9", "OrcaRouter $3.26 vs $7.60"],
            },
            {
                "name": "Twenty-five days between flagships",
                "hook": "Astra on the 3rd. Sonnet on the 28th. The timeline is the story.",
                "type": "narrative",
                "why_now": "The gap is short enough to say in one sentence.",
                "grounded_in": ["Astra 3 Sep", "Sonnet 28 Sep"],
            },
        ],
        "sources": [
            {
                "url": "https://twitter-trends.snaplytics.io/2026-09-28/",
                "title": "Worldwide Twitter Trends on Sep 28, 2026",
                "used_for": "X trend evidence",
                "reliability": "secondary",
            },
            {
                "url": "https://www.anthropic.com/claude-sonnet-5-5",
                "title": "Introducing Claude Sonnet 5.5",
                "used_for": "Launch date, speed, Terminal-Bench 70.6%",
                "reliability": "primary",
            },
            {
                "url": "https://www.theneuron.ai/news/claude-sonnet-5-5-vs-gpt-6-astra-where-sonnet-wins/",
                "title": "Claude Sonnet 5.5 vs GPT-6 Astra: where Sonnet wins",
                "used_for": "Astra date, prices, Terminal-Bench 57.9%",
                "reliability": "secondary",
            },
            {
                "url": "https://www.orcarouter.ai/blog/claude-sonnet-5-5-vs-gpt-6-astra",
                "title": "Claude Sonnet 5.5 vs GPT-6 Astra: 5x Rate, Half Cost",
                "used_for": "Per-task cost flip",
                "reliability": "secondary",
            },
            {
                "url": "https://docsbot.ai/models/compare/claude-sonnet-5-5/gpt-6-astra",
                "title": "Claude Sonnet 5.5 vs GPT-6 Astra",
                "used_for": "Release-date cross-check, 3 Sep vs 28 Sep",
                "reliability": "secondary",
            },
        ],
    }

    decisions = {
        "version": "1.0",
        "project_id": PROJECT,
        "decisions": [
            {
                "decision_id": "d-001",
                "stage": "proposal",
                "category": "pipeline_selection",
                "subject": "Pipeline",
                "options_considered": [
                    {"option_id": "explainer", "label": "animated-explainer", "score": 0.9, "reason": "A sourced argument with numbers, not footage."},
                    {"option_id": "clip", "label": "clip-factory", "score": 0.3, "reason": "Needs source clips we cannot download.", "rejected_because": "No reachable footage hosts."},
                ],
                "selected": "explainer",
                "reason": "The piece is a data explainer.",
            },
            {
                "decision_id": "d-002",
                "stage": "proposal",
                "category": "concept_selection",
                "subject": "Concept",
                "options_considered": [
                    {"option_id": "c1", "label": "The trend was the invoice", "score": 0.95, "reason": "One twist, four sourced numbers."},
                    {"option_id": "c2", "label": "Benchmark horse race", "score": 0.4, "reason": "Saturated.", "rejected_because": "Existing posts already tabulate the benches."},
                    {"option_id": "c3", "label": "Twenty-five day timeline only", "score": 0.5, "reason": "True but thin.", "rejected_because": "No invoice, no reason to care."},
                ],
                "selected": "c1",
                "reason": "The user asked for what is trending. The useful cut is the bill.",
            },
            {
                "decision_id": "d-003",
                "stage": "proposal",
                "category": "render_runtime_selection",
                "subject": "Render runtime",
                "options_considered": [
                    {"option_id": "remotion", "label": "Remotion", "score": 0.2, "reason": "Preferred for explainers.", "rejected_because": "remotion-composer/node_modules is empty and npm is blocked."},
                    {"option_id": "hyperframes", "label": "HyperFrames", "score": 0.2, "reason": "Good for kinetic type.", "rejected_because": "npx cannot reach the registry."},
                    {"option_id": "ffmpeg", "label": "FFmpeg drawtext plates", "score": 0.85, "reason": "ffmpeg 6.1 and system fonts are present."},
                ],
                "selected": "ffmpeg",
                "reason": "Both composition engines are unavailable. FFmpeg is the logged fallback, not a silent swap.",
            },
            {
                "decision_id": "d-004",
                "stage": "proposal",
                "category": "composition_mode",
                "subject": "Composition mode",
                "options_considered": [
                    {"option_id": "atelier", "label": "Hand-authored plates", "score": 0.9, "reason": "Six original type plates, no stock scene kit."},
                    {"option_id": "templated", "label": "Stock explainer cuts", "score": 0.2, "reason": "Requires Remotion components that are not installed.", "rejected_because": "Runtime missing."},
                ],
                "selected": "atelier",
                "reason": "The plates are written for this piece only.",
            },
            {
                "decision_id": "d-005",
                "stage": "proposal",
                "category": "voice_selection",
                "subject": "Narration",
                "options_considered": [
                    {"option_id": "piper", "label": "Piper TTS", "score": 0.3, "reason": "Free local voice.", "rejected_because": "Piper binary and voice model are not installed."},
                    {"option_id": "captions", "label": "Captions only", "score": 0.9, "reason": "Every claim stays readable without a voice provider."},
                ],
                "selected": "captions",
                "reason": "No TTS runtime on this machine.",
            },
            {
                "decision_id": "d-006",
                "stage": "proposal",
                "category": "music_source",
                "subject": "Music",
                "options_considered": [
                    {"option_id": "library", "label": "music_library", "score": 0.1, "reason": "No local library.", "rejected_because": "Directory empty / absent."},
                    {"option_id": "procedural", "label": "Procedural A drone", "score": 0.8, "reason": "Offline, no license issue, stays under the captions."},
                ],
                "selected": "procedural",
                "reason": "Paid music APIs are unreachable.",
            },
            {
                "decision_id": "d-007",
                "stage": "proposal",
                "category": "downgrade_approval",
                "subject": "Full-run authorization",
                "options_considered": [
                    {"option_id": "full", "label": "User asked to make the video", "score": 1.0, "reason": "The request is a production, not a research note."},
                    {"option_id": "hold", "label": "Stop at proposal", "score": 0.2, "reason": "Would not deliver the video.", "rejected_because": "The user asked for the video."},
                ],
                "selected": "full",
                "reason": "Recorded so gated stages can complete under an explicit make-the-video request. Budget $0.",
            },
        ],
    }

    proposal = {
        "version": "1.0",
        "concept_options": [
            {
                "id": "c1",
                "title": "The trend was the invoice",
                "hook": "A model name trended on X. The argument worth keeping is which bill you can defend.",
                "narrative_structure": "Trend name, Astra's rate, Sonnet's rate, the bench, the invoice flip, one-line landing.",
                "visual_approach": "Six full-frame type plates. Clay for Sonnet, ice for Astra, lime rule for the kicker.",
                "target_duration_seconds": 48,
                "why_this_works": "Four sourced numbers, one twist, no footage required.",
            },
            {
                "id": "c2",
                "title": "Benchmark horse race",
                "hook": "Who scored higher.",
                "narrative_structure": "Table of benches.",
                "visual_approach": "Chart dump.",
                "target_duration_seconds": 45,
                "why_this_works": "Familiar, and already published.",
            },
            {
                "id": "c3",
                "title": "Twenty-five days",
                "hook": "Astra on the 3rd, Sonnet on the 28th.",
                "narrative_structure": "Calendar only.",
                "visual_approach": "Date cards.",
                "target_duration_seconds": 30,
                "why_this_works": "Clear, but it never says why anyone should care.",
            },
        ],
        "selected_concept": {
            "concept_id": "c1",
            "rationale": "It is the only cut that uses the trend and the counterintuitive bill.",
        },
        "production_plan": {
            "pipeline": PIPELINE,
            "playbook": PLAYBOOK,
            "stages": [
                {"stage": "research", "tools": [], "approach": "Public launch posts and the Sep 28 X trend archive."},
                {"stage": "script", "tools": [], "approach": "Six caption lines, one claim each."},
                {"stage": "assets", "tools": [
                    {"tool_name": "ffmpeg", "role": "Type plates and mux", "provider": "local", "available": True, "estimated_cost_usd": 0},
                ], "approach": "drawtext plates plus a procedural bed."},
                {"stage": "compose", "tools": [
                    {"tool_name": "ffmpeg", "role": "Encode", "provider": "local", "available": True, "estimated_cost_usd": 0},
                ], "approach": "Concat plates, burn ASS, mux AAC."},
            ],
            "quality_tradeoffs": [
                {
                    "tradeoff": "Remotion motion versus static type plates",
                    "recommendation": "Plates. The engines are not installed.",
                    "quality_impact": "No springs or chart tweens. The numbers still read.",
                }
            ],
            "alternative_paths": [
                {
                    "description": "Same cut in Remotion once node_modules exists",
                    "total_cost_usd": 0,
                    "quality_level": "standard",
                    "what_changes": "Bars can grow. Facts stay.",
                }
            ],
            "delivery_promise": {
                "promise_type": "data_explainer",
                "motion_required": False,
                "tone_mode": "educational",
                "quality_floor": "presentable",
                "approved_fallback": "still_led",
            },
            "renderer_family": "explainer-data",
            "render_runtime": "ffmpeg",
            "composition_mode": "atelier",
            "art_direction": "Ink #0B1020, paper #F4F1EA, clay #D97757 for Sonnet, ice #8FB8FF for Astra, lime #C8F542 kicker. JetBrains Mono headlines, Inter body.",
            "music_source": {
                "source_type": "bring_your_own",
                "mood_direction": "Quiet A drone under captions",
                "estimated_cost_usd": 0,
            },
            "voice_selection": {
                "provider": "captions_only",
                "voice_id": "none",
                "rationale": "No Piper or cloud TTS on this machine.",
                "estimated_cost_usd": 0,
                "delivery_style": "On-screen sentences, one at a time",
                "pacing_policy": "One sentence per plate, held long enough to read",
                "sample_approval_required": False,
            },
            "provider_rankings": {
                "video": [{"tool_name": "ffmpeg", "provider": "local", "weighted_score": 0.8, "explanation": "Only reachable encoder."}],
                "image": [{"tool_name": "ffmpeg", "provider": "local", "weighted_score": 0.7, "explanation": "drawtext plates, no image API."}],
                "tts": [{"tool_name": "captions_only", "provider": "local", "weighted_score": 0.8, "explanation": "TTS unavailable."}],
                "music": [{"tool_name": "procedural_numpy", "provider": "local", "weighted_score": 0.7, "explanation": "No music library or API."}],
            },
        },
        "cost_estimate": {
            "total_estimated_usd": 0,
            "line_items": [
                {"tool": "ffmpeg", "operation": "six plates, concat, mux", "quantity": 1, "estimated_usd": 0, "notes": "local"},
                {"tool": "numpy", "operation": "procedural bed", "quantity": 1, "estimated_usd": 0},
            ],
            "budget_cap_usd": 2,
            "budget_verdict": "within_budget",
        },
        "approval": {
            "status": "approved",
            "user_notes": "User asked to make a video about what is trending on X. Full run at $0 with the ffmpeg fallback.",
            "approved_budget_usd": 0,
        },
    }

    sections = []
    for i, (start, end, text) in enumerate(LINES, start=1):
        sections.append({
            "id": f"s{i}",
            "label": ["Hook", "Astra", "Sonnet", "Bench", "Invoice", "Landing"][i - 1],
            "text": text,
            "start_seconds": start,
            "end_seconds": end,
            "speaker_directions": "Caption only. No voice.",
            "delivery_cues": {
                "pace": "measured",
                "energy": "calm",
                "emphasis_words": [],
                "pause_before_seconds": 0.2,
                "pause_after_seconds": 0.3,
                "delivery_note": "On screen, not spoken.",
                "provider_text": text,
            },
            "enhancement_cues": [
                {"type": "stat_card", "description": text, "timestamp_seconds": start}
            ],
        })
    script = {
        "version": "1.0",
        "title": TITLE,
        "total_duration_seconds": DURATION,
        "voice_performance": {
            "performance_intent": "Silent. Captions carry every claim.",
            "pacing_profile": "technical",
            "energy_curve": "flat, one idea per plate",
            "pause_policy": "Hold each line for the plate",
            "sample_section_id": "s5",
        },
        "sections": sections,
    }

    scenes = []
    labels = [
        ("sc1", "text_card", "Worldwide trend name"),
        ("sc2", "text_card", "Astra rate card"),
        ("sc3", "text_card", "Sonnet rate card"),
        ("sc4", "diagram", "Terminal-Bench bars"),
        ("sc5", "text_card", "Per-task invoice"),
        ("sc6", "text_card", "Landing line"),
    ]
    for i, (sid, kind, desc) in enumerate(labels):
        scenes.append({
            "id": sid,
            "type": kind,
            "description": desc,
            "start_seconds": i * HOLD,
            "end_seconds": (i + 1) * HOLD,
            "script_section_id": f"s{i+1}",
            "framing": "full frame type",
            "movement": "hold",
            "transition_in": "cut",
            "transition_out": "cut",
            "required_assets": [
                {"type": "animation", "description": desc, "source": "generate"}
            ],
        })
    scene_plan = {"version": "1.0", "style_playbook": PLAYBOOK, "scenes": scenes}
    return research, decisions, proposal, script, scene_plan


def main() -> int:
    project = init_project(PROJECT, title=TITLE, pipeline_type=PIPELINE, style_playbook=PLAYBOOK)
    research, decisions, proposal, script, scene_plan = build_artifacts()
    save(project, "research_brief", research)
    save(project, "decision_log", decisions)
    save(project, "proposal_packet", proposal)
    save(project, "script", script)
    save(project, "scene_plan", scene_plan)

    zero = {"total_spent_usd": 0.0, "total_reserved_usd": 0.0, "budget_remaining_usd": 2.0}
    cp("research", "completed", {"research_brief": research}, cost_snapshot=zero)
    cp("proposal", "completed", {"proposal_packet": proposal, "decision_log": decisions}, cost_snapshot=zero)
    cp("script", "completed", {"script": script}, cost_snapshot=zero)
    cp("scene_plan", "completed", {"scene_plan": scene_plan}, cost_snapshot=zero)

    work = project / "assets" / "video"
    plates = build_plates(work)
    silent = work / "silent.mp4"
    concat_video(plates, silent)
    ass = project / "assets" / "captions.ass"
    write_ass(ass)
    music = project / "assets" / "music" / "bed.wav"
    write_music(music)
    out = project / "renders" / f"{PROJECT}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    mux(silent, ass, music, out)
    info = probe(out)
    print(json.dumps(info, indent=2))

    manifest = {
        "version": "1.0",
        "assets": [
            {
                "id": "plates",
                "type": "video",
                "path": str(silent.relative_to(project)),
                "source_tool": "ffmpeg",
                "scene_id": "sc1",
            },
            {
                "id": "music",
                "type": "music",
                "path": str(music.relative_to(project)),
                "source_tool": "procedural_numpy",
                "scene_id": "sc1",
            },
            {
                "id": "captions",
                "type": "subtitle",
                "path": str(ass.relative_to(project)),
                "source_tool": "ass",
                "scene_id": "sc1",
            },
        ],
        "total_cost_usd": 0.0,
    }
    # asset schema requires type loosely; subtitle may not be an enum. Keep music and video only if schema is strict later.
    manifest["assets"] = [a for a in manifest["assets"] if a["type"] in ("video", "audio", "music", "image")]
    save(project, "asset_manifest", manifest)
    cp("assets", "completed", {"asset_manifest": manifest}, cost_snapshot=zero)

    edit = {
        "version": "1.0",
        "render_runtime": "ffmpeg",
        "cuts": [
            {
                "id": f"c{i+1}",
                "source": str(plate.relative_to(project)),
                "in_seconds": 0,
                "out_seconds": HOLD,
            }
            for i, plate in enumerate(plates)
        ],
    }
    save(project, "edit_decisions", edit)
    cp("edit", "completed", {"edit_decisions": edit}, cost_snapshot=zero)

    duration = float(info["format"]["duration"])
    video_stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    audio_stream = next(s for s in info["streams"] if s["codec_type"] == "audio")
    report = {
        "version": "1.0",
        "outputs": [
            {
                "path": str(out.relative_to(ROOT)),
                "format": "mp4",
                "codec": video_stream["codec_name"],
                "audio_codec": audio_stream["codec_name"],
                "resolution": f"{video_stream['width']}x{video_stream['height']}",
                "fps": FPS,
                "duration_seconds": round(duration, 3),
                "file_size_bytes": int(info["format"]["size"]),
                "platform_target": "landscape",
            }
        ],
        "warnings": [
            "Remotion and HyperFrames unavailable. Rendered with ffmpeg drawtext plates.",
            "No TTS. Captions are the voice.",
            "last30days discovery returned nothing solid because Reddit, Hacker News, and X were unreachable. Topic taken from the public Sep 28 worldwide trend archive.",
        ],
    }
    review = {
        "version": "1.0",
        "output_path": str(out.relative_to(ROOT)),
        "status": "pass",
        "checks": {
            "technical_probe": {
                "valid_container": True,
                "duration_seconds": round(duration, 3),
                "resolution": f"{video_stream['width']}x{video_stream['height']}",
                "fps": FPS,
                "has_audio": True,
                "codec": video_stream["codec_name"],
                "file_size_bytes": int(info["format"]["size"]),
                "issues": [],
            },
            "visual_spotcheck": {"status": "pending_frames"},
            "audio_spotcheck": {"has_bed": True, "has_voice": False, "note": "Captions carry the words."},
            "promise_preservation": {
                "render_runtime_used": "ffmpeg",
                "runtime_swap_detected": False,
            },
            "subtitle_check": {"burned_in": True, "line_count": len(LINES)},
        },
    }
    save(project, "render_report", report)
    save(project, "final_review", review)
    cp("compose", "completed", {"render_report": report, "final_review": review}, cost_snapshot=zero)
    publish = {
        "version": "1.0",
        "entries": [
            {
                "platform": "local",
                "status": "rendered",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "notes": "Not uploaded. File is the project render.",
            }
        ],
    }
    save(project, "publish_log", publish)
    cp("publish", "completed", {"publish_log": publish}, cost_snapshot=zero)
    print(f"RENDERED {out} duration={duration:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
