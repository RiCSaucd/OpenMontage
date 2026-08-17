"""Contract tests for the cinematic-intro pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.pipeline_loader import get_required_tools, get_stage_order, load_pipeline


def test_cinematic_intro_manifest_contract():
    manifest = load_pipeline("cinematic-intro")

    assert manifest["name"] == "cinematic-intro"
    assert manifest["category"] == "cinematic"
    assert manifest["stability"] == "beta"

    assert get_stage_order(manifest) == [
        "proposal",
        "script",
        "scene_plan",
        "edit",
        "assets",
        "compose",
        "publish",
    ]

    required = set(get_required_tools(manifest))
    assert "higgsfield_video" in required
    assert "video_stitch" in required
    assert "image_selector" in required

    for stage in manifest["stages"]:
        skill_ref = stage.get("skill")
        assert skill_ref, f"Stage {stage['name']} missing skill"
        skill_path = PROJECT_ROOT / "skills" / f"{skill_ref}.md"
        assert skill_path.is_file(), f"Missing skill file: {skill_path}"

    core_skill = PROJECT_ROOT / "skills" / "creative" / "cinematic-intro-engine.md"
    assert core_skill.is_file()

    prompts_html = PROJECT_ROOT / "skills" / "creative" / "cinematic-intro-prompts.html"
    assert prompts_html.is_file()

    for required_skill in manifest.get("required_skills", []):
        skill_path = PROJECT_ROOT / "skills" / f"{required_skill}.md"
        assert skill_path.is_file(), f"Missing required skill: {skill_path}"
