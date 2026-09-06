"""Simulate a pipeline run on disk to exercise the Backlot live board.

Drives a fake production through the REAL contract — init_project,
in_progress checkpoints, gated awaiting_human states, tool events,
progressively-written artifacts — so the board can be watched updating live.
Also useful as a demo driver.

    python scripts/backlot_simulate_run.py [--project backlot-demo-run]
        [--fast] [--cleanup]

--fast     compresses waits to ~0.3s (for automated verification)
--cleanup  removes the project directory at the end
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.checkpoint import PROJECTS_DIR, init_project, write_checkpoint
from lib.events import emit_event

SCENES = [
    ("sc1", "Opening — a lighthouse at dusk", 0, 4, "The coast holds its breath."),
    ("sc2", "The beam sweeps the water", 4, 9, "Every night, the same promise."),
    ("sc3", "A storm builds offshore", 9, 15, "Until the night the light went out."),
    ("sc4", "The keeper climbs the stairs", 15, 21, "Someone still has to climb."),
]


def artifacts_for(project_id: str) -> dict:
    script = {
        "version": "1.0",
        "title": "The Last Lighthouse",
        "total_duration_seconds": 21,
        "sections": [
            {"id": f"s{i+1}", "label": desc.split("—")[0].strip(), "text": narration,
             "start_seconds": s0, "end_seconds": s1}
            for i, (sid, desc, s0, s1, narration) in enumerate(SCENES)
        ],
    }
    scene_plan = {
        "version": "1.0",
        "scenes": [
            {"id": sid, "type": "generated", "description": desc,
             "start_seconds": s0, "end_seconds": s1,
             "script_section_id": f"s{i+1}",
             "hero_moment": sid == "sc3",
             "required_assets": [{"type": "image", "description": desc, "source": "generate"}]}
            for i, (sid, desc, s0, s1, _n) in enumerate(SCENES)
        ],
    }
    return {"script": script, "scene_plan": scene_plan}


def sample_research_brief(topic: str) -> dict:
    """Schema-shaped research brief — kept here so the sim doesn't import pytest tests."""
    return {
        "version": "1.0",
        "topic": topic,
        "research_date": "2026-03-27",
        "landscape": {
            "existing_content": [
                {"title": "Existing Video 1", "source": "youtube", "angle": "tutorial", "what_it_covers": "basics"},
                {"title": "Existing Video 2", "source": "blog", "angle": "deep dive", "what_it_covers": "advanced"},
                {"title": "Existing Video 3", "source": "youtube", "angle": "comparison", "what_it_covers": "alternatives"},
            ],
            "saturated_angles": ["basic tutorial"],
            "underserved_gaps": ["misconceptions about topic"],
        },
        "data_points": [
            {"claim": "73% of users prefer X", "source_url": "https://example.com/study", "credibility": "primary_source"},
            {"claim": "Market grew 40% in 2025", "source_url": "https://example.com/report", "credibility": "secondary_source"},
            {"claim": "Most experts agree on Y", "source_url": "https://example.com/survey", "credibility": "primary_source"},
        ],
        "audience_insights": {
            "common_questions": ["What is X?", "How does X work?", "Why is X important?"],
            "misconceptions": [{"myth": "X is slow", "reality": "X is fast"}],
            "knowledge_level": "Beginner to intermediate",
        },
        "angles_discovered": [
            {"name": "The Surprising Truth", "hook": "You think X is slow. It's not.", "type": "contrarian", "why_now": "New benchmark data", "grounded_in": ["data_point_1"]},
            {"name": "X From Scratch", "hook": "Build X in 5 minutes.", "type": "evergreen", "why_now": "Audience demand", "grounded_in": ["audience_q1"]},
            {"name": "Why X Matters Now", "hook": "X just changed everything.", "type": "trending", "why_now": "Recent announcement", "grounded_in": ["trending_1"]},
        ],
        "sources": [
            {"url": "https://example.com/study", "title": "Study on X", "used_for": "data_points"},
            {"url": "https://example.com/report", "title": "Market Report", "used_for": "data_points"},
            {"url": "https://example.com/survey", "title": "Expert Survey", "used_for": "data_points"},
            {"url": "https://example.com/reddit", "title": "Reddit Discussion", "used_for": "audience_insights"},
            {"url": "https://example.com/blog", "title": "Tech Blog", "used_for": "landscape"},
        ],
    }


def _font_path() -> str | None:
    for candidate in (
        "/usr/share/fonts/truetype/macos/Inter-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ):
        if Path(candidate).is_file():
            return candidate
    return None


def write_scene_still(path: Path, rgb: tuple[int, int, int], label: str) -> None:
    """Write a 640x360 still. Pillow if present, otherwise ffmpeg."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (640, 360), rgb)
        draw = ImageDraw.Draw(img)
        draw.text((20, 160), label, fill=(230, 225, 210))
        img.save(path)
        return
    except ImportError:
        pass
    import subprocess

    hex_color = f"0x{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    font = _font_path()
    safe = label.replace("\\", "\\\\").replace(":", "\\:").replace("'", "")
    vf = f"drawtext=text='{safe}':fontsize=22:fontcolor=0xe6e1d2:x=20:y=160"
    if font:
        vf += f":fontfile={font}"
    result = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "lavfi", "-i", f"color=c={hex_color}:s=640x360:d=1",
         "-vf", vf, "-frames:v", "1", str(path)],
        capture_output=True, timeout=20,
    )
    if result.returncode != 0 or not path.is_file():
        # Color plate is enough for the filmstrip if drawtext is missing.
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-f", "lavfi", "-i", f"color=c={hex_color}:s=640x360:d=1",
             "-frames:v", "1", str(path)],
            check=True, timeout=20,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="backlot-demo-run")
    parser.add_argument("--fast", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()

    wait = 0.3 if args.fast else 2.5
    pid = args.project
    pdir = PROJECTS_DIR / pid
    if pdir.exists():
        shutil.rmtree(pdir)

    print(f"[sim] init_project {pid}")
    init_project(pid, title="The Last Lighthouse", pipeline_type="cinematic",
                 style_playbook="clean-professional")
    art = artifacts_for(pid)

    def save_artifact(name: str, data: dict) -> None:
        path = pdir / "artifacts" / f"{name}.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def cp(stage: str, status: str, artifacts: dict, **kw) -> None:
        write_checkpoint(PROJECTS_DIR, pid, stage, status, artifacts,
                         pipeline_type="cinematic", **kw)
        print(f"[sim] checkpoint {stage} -> {status}")
        time.sleep(wait)

    cp("research", "in_progress", {})
    brief = sample_research_brief("The Last Lighthouse")
    cp("research", "completed", {"research_brief": brief})

    # script gates: awaiting_human -> approved
    cp("script", "in_progress", {})
    save_artifact("script", art["script"])
    cp("script", "awaiting_human", {"script": art["script"]},
       review={"round": 1, "decision": "pass", "critical": 0, "suggestions": 1,
               "nitpicks": 0, "summary": "Hook is strong; tightened s3."})
    time.sleep(wait)  # "user reads the script on the board"
    cp("script", "completed", {"script": art["script"]}, human_approved=True)

    # scene_plan gates too
    cp("scene_plan", "in_progress", {})
    save_artifact("scene_plan", art["scene_plan"])
    cp("scene_plan", "awaiting_human", {"scene_plan": art["scene_plan"]})
    time.sleep(wait)
    cp("scene_plan", "completed", {"scene_plan": art["scene_plan"]}, human_approved=True)

    # assets: per-scene tool events + growing manifest + partial progress
    cp("assets", "in_progress", {})
    manifest = {"version": "1.0", "assets": [], "total_cost_usd": 0.0}
    done_ids = []
    palette = [(24, 32, 48), (40, 30, 60), (60, 24, 24), (20, 48, 40)]
    for i, (sid, desc, _s0, _s1, _n) in enumerate(SCENES):
        emit_event(pdir, {"tool": "flux_image", "event": "start", "scene_id": sid})
        print(f"[sim] generating {sid}…")
        time.sleep(wait * 1.5)
        rel = f"assets/images/{sid}.png"
        write_scene_still(pdir / rel, palette[i % 4], f"{sid} — {desc[:40]}")
        emit_event(pdir, {"tool": "flux_image", "event": "finish", "scene_id": sid,
                          "success": True, "cost_usd": 0.05, "duration_s": wait * 1.5,
                          "output_path": rel})
        manifest["assets"].append({
            "id": f"img_{sid}", "type": "image", "path": rel, "scene_id": sid,
            "source_tool": "flux_image", "model": "flux-sim", "cost_usd": 0.05,
            "prompt": desc, "quality_score": 0.88,
        })
        manifest["total_cost_usd"] = round(manifest["total_cost_usd"] + 0.05, 2)
        save_artifact("asset_manifest", manifest)
        done_ids.append(sid)
        write_checkpoint(PROJECTS_DIR, pid, "assets", "in_progress", {},
                         pipeline_type="cinematic",
                         metadata={"partial_progress": {"completed_scene_ids": done_ids}},
                         cost_snapshot={"total_spent_usd": manifest["total_cost_usd"],
                                        "total_reserved_usd": 0.0,
                                        "budget_remaining_usd": 5 - manifest["total_cost_usd"]})
    # assets gate (the storyboard review)
    cp("assets", "awaiting_human", {"asset_manifest": manifest},
       cost_snapshot={"total_spent_usd": manifest["total_cost_usd"],
                      "total_reserved_usd": 0.0,
                      "budget_remaining_usd": 5 - manifest["total_cost_usd"]})
    time.sleep(wait)
    cp("assets", "completed", {"asset_manifest": manifest}, human_approved=True)

    print(f"[sim] done — board at http://127.0.0.1:4750/p/{pid}")
    if args.cleanup:
        shutil.rmtree(pdir)
        print("[sim] cleaned up")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
