"""Contract tests for the nexus-true-crime-short pipeline and Nexus server."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.pipeline_loader import get_stage_order, load_pipeline


def test_nexus_true_crime_manifest_contract():
    manifest = load_pipeline("nexus-true-crime-short")

    assert manifest["name"] == "nexus-true-crime-short"
    assert manifest["category"] == "custom"
    assert manifest["stability"] == "beta"

    assert get_stage_order(manifest) == [
        "research",
        "proposal",
        "script",
        "scene_plan",
        "assets",
        "edit",
        "compose",
    ]

    for stage in manifest["stages"]:
        skill_ref = stage.get("skill")
        assert skill_ref, f"Stage {stage['name']} missing skill"
        skill_path = PROJECT_ROOT / "skills" / f"{skill_ref}.md"
        assert skill_path.is_file(), f"Missing skill file: {skill_path}"

    for required_skill in manifest.get("required_skills", []):
        skill_path = PROJECT_ROOT / "skills" / f"{required_skill}.md"
        assert skill_path.is_file(), f"Missing required skill: {skill_path}"

    brand_a = PROJECT_ROOT / "skills" / "brand" / "respected-historian-tone.md"
    brand_b = PROJECT_ROOT / "skills" / "brand" / "mafia-true-crime-guidelines.md"
    assert brand_a.is_file()
    assert brand_b.is_file()

    server = PROJECT_ROOT / "servers" / "nexus_openmontage.py"
    assert server.is_file()


def test_nexus_vidiq_packaging_docs():
    """vidIQ is packaging-only; docs must not commit keys or invent a live-score path."""
    compose = (
        PROJECT_ROOT
        / "skills"
        / "pipelines"
        / "nexus-true-crime-short"
        / "compose-director.md"
    ).read_text(encoding="utf-8")
    assert "vidIQ" in compose
    assert "mcp_status" in compose

    ep = (
        PROJECT_ROOT
        / "skills"
        / "pipelines"
        / "nexus-true-crime-short"
        / "executive-producer.md"
    ).read_text(encoding="utf-8")
    assert "vidIQ" in ep
    assert "mcp_status: unavailable" in ep

    readme = (PROJECT_ROOT / "servers" / "README.md").read_text(encoding="utf-8")
    assert "VIDIQ_API_KEY" in readme
    assert "mcp.vidiq.com" in readme

    example = PROJECT_ROOT / ".cursor" / "mcp.json.example"
    assert example.is_file()
    example_text = example.read_text(encoding="utf-8")
    assert "mcp.vidiq.com" in example_text
    assert "${env:VIDIQ_API_KEY}" in example_text
    assert "YOUR_REAL" not in example_text
    assert "YOUR_API_KEY" not in example_text


def test_nexus_server_create_project(tmp_path):
    import servers.nexus_openmontage as nexus

    nexus._PROJECTS = tmp_path

    req = nexus.ProduceRequest(topic="Lucky Luciano and the Commission")
    meta = nexus.create_and_queue(req, sync=True)

    project_id = meta["project_id"]
    root = tmp_path / project_id
    assert (root / "project.json").is_file()
    assert (root / "AGENT_INSTRUCTION.md").is_file()
    assert (root / "artifacts").is_dir()
    assert (root / "renders").is_dir()
    assert meta["status"] == "awaiting_approval"
    assert meta["current_stage"] == "proposal"
    assert meta["pipeline_type"] == "nexus-true-crime-short"

    body = nexus.StageApproval(stage="proposal", approved=True)
    updated = nexus.apply_stage_approval(project_id, body)
    assert updated["current_stage"] == "script"
