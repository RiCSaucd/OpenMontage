#!/usr/bin/env python3
"""
Nexus AI Media — OpenMontage Production + MCP Server
====================================================
Dual-mode server:
  • FastAPI (HTTP) for n8n / Make / agent squad / curl
  • MCP (stdio / FastMCP) so Claude Desktop & Cursor see the tools natively

Features:
  - Creates fully structured OpenMontage projects via ``lib.checkpoint.init_project``
  - Writes a precise AGENT_INSTRUCTION.md that any OpenMontage agent can execute
  - Optional spawn of Claude Code / agent CLI when available
  - Human approval gates preserved
  - On completion: distribution_manifest.json ready for CapCut MCP + Google Drive
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Optional MCP layer (official SDK)
# ---------------------------------------------------------------------------
try:
    from mcp.server.fastmcp import FastMCP

    MCP_AVAILABLE = True
except ImportError:
    try:
        from mcp.server import MCPServer as FastMCP  # type: ignore

        MCP_AVAILABLE = True
    except ImportError:
        MCP_AVAILABLE = False
        FastMCP = None  # type: ignore

# ---------------------------------------------------------------------------
# Configuration — OpenMontage canonical paths
# ---------------------------------------------------------------------------

from lib.checkpoint import init_project
from lib.paths import PROJECTS_DIR, REPO_ROOT

BASE_DIR = Path(os.getenv("OPENMONTAGE_ROOT", str(REPO_ROOT))).resolve()
# Prefer env override used by lib.paths; fall back to BASE_DIR/projects.
_PROJECTS = Path(os.getenv("OPENMONTAGE_PROJECTS_DIR") or (BASE_DIR / "projects")).resolve()

PIPELINE_NAME = "nexus-true-crime-short"
BRAND_SKILLS = [
    "brand/respected-historian-tone",
    "brand/mafia-true-crime-guidelines",
]
DEFAULT_BUDGET_USD = 1.50
API_KEY = os.getenv("NEXUS_API_KEY")
CAPCUT_DRAFTS_PATH = os.getenv("CAPCUT_DRAFTS_PATH")
DRIVE_FOLDER_ID = os.getenv("NEXUS_DRIVE_FOLDER_ID")

_PROJECTS.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nexus.openmontage")

STAGE_ORDER = [
    "research",
    "proposal",
    "script",
    "scene_plan",
    "assets",
    "edit",
    "compose",
    "completed",
]
APPROVAL_GATES = {"proposal", "script", "assets", "compose"}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ApprovalMode(str, Enum):
    guided = "guided"
    auto_noncreative = "auto_noncreative"
    full_auto = "full_auto"


class ProduceRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200)
    duration_seconds: int = Field(45, ge=15, le=90)
    aspect: str = Field("9:16", pattern=r"^(9:16|1:1|16:9)$")
    pipeline: str = Field(PIPELINE_NAME)
    approval_mode: ApprovalMode = Field(ApprovalMode.guided)
    budget_usd: float = Field(DEFAULT_BUDGET_USD, ge=0.25, le=25.0)
    notes: Optional[str] = None
    reference_url: Optional[str] = None
    auto_spawn_agent: bool = Field(
        False,
        description="Attempt to launch Claude Code / agent CLI if available",
    )

    @field_validator("topic")
    @classmethod
    def clean_topic(cls, v: str) -> str:
        return " ".join(v.strip().split())


class StageApproval(BaseModel):
    stage: str
    approved: bool = True
    comments: Optional[str] = None


class ProjectStatus(BaseModel):
    project_id: str
    title: str
    status: str
    current_stage: Optional[str] = None
    pipeline: str
    created_at: str
    updated_at: str
    budget_usd: float
    spent_usd: float = 0.0
    approval_mode: str
    brand_skills: List[str]
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None
    distribution: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:50].strip("-")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_dir(project_id: str) -> Path:
    return _PROJECTS / project_id


def load_project(project_id: str) -> Dict[str, Any]:
    path = project_dir(project_id) / "project.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return json.loads(path.read_text(encoding="utf-8"))


def save_project(project_id: str, data: Dict[str, Any]) -> None:
    path = project_dir(project_id) / "project.json"
    data["updated_at"] = now_iso()
    # Keep Backlot-compatible fields in sync.
    data.setdefault("pipeline_type", data.get("pipeline", PIPELINE_NAME))
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def create_nexus_project(project_id: str, title: str, pipeline: str) -> Path:
    """Canonical OpenMontage layout + Nexus extras (history, distribution)."""
    root = init_project(
        project_id,
        title=title,
        pipeline_type=pipeline,
        pipeline_dir=_PROJECTS,
    )
    for sub in ("history", "distribution", "scripts", "research"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def write_agent_instruction(project_id: str, req: ProduceRequest) -> Path:
    """Precise instruction any OpenMontage-compatible agent can execute."""
    root = project_dir(project_id)
    instruction_path = root / "AGENT_INSTRUCTION.md"

    content = f"""# OpenMontage Agent Instruction — Nexus True Crime Short

**MANDATORY:** Read `AGENT_GUIDE.md` and the two brand skills before any creative work.

## Project
- **ID:** `{project_id}`
- **Title / Topic:** {req.topic}
- **Pipeline:** `{req.pipeline}` (must exist in `pipeline_defs/`)
- **Target runtime:** {req.duration_seconds}s
- **Aspect:** {req.aspect}
- **Budget cap:** ${req.budget_usd:.2f}
- **Approval mode:** {req.approval_mode.value}
- **Brand skills (REQUIRED):** {', '.join(BRAND_SKILLS)}

## Exact Task
Using the pipeline `{req.pipeline}` and brand skills under `skills/brand/`:

1. Run the **research** stage. Produce a `research_brief` that separates documented record from myth. Cite sources.
2. Stop at the **proposal** stage and write a `proposal_packet` with 2–3 concept options that all obey the respected-historian tone.
3. Wait for human approval (do not continue past proposal until approved).
4. After approval, continue through script → scene_plan → assets → edit → compose.
5. All outputs must live under `projects/{project_id}/` (artifacts, assets, renders).
6. Enforce human approval at every stage marked `human_approval_default: true` in the pipeline YAML.
7. Never glorify violence or criminal lifestyle. Prefer archival footage and measured language.

## Brand Rules (non-negotiable)
- Documented history first.
- Human cost and historical context required.
- No cinematic blood / hero-weapon framing.
- User will record the final voiceover; supply timing cues only.
- Sparse, non-triumphant music.

## Reference (if any)
{req.reference_url or "None provided"}

## Notes from requester
{req.notes or "None"}

## Success Criteria
- Final render appears at `projects/{project_id}/renders/final.mp4`
- Decision log and checkpoints are complete
- Brand skills were applied at research, proposal, and script stages
- Distribution manifest is written when status becomes completed
"""
    instruction_path.write_text(content, encoding="utf-8")
    return instruction_path


def try_spawn_openmontage_agent(project_id: str, instruction_path: Path) -> Optional[str]:
    """Attempt to launch a real agent process if the environment supports it."""
    candidates = [
        ["claude", "code", "--project", str(BASE_DIR), "--prompt-file", str(instruction_path)],
        ["claude", "--print", f"Execute the OpenMontage instruction at {instruction_path}"],
        ["cursor", "agent", "run", str(instruction_path)],
    ]

    for cmd in candidates:
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            logger.info("Spawned agent process %s with command %s", proc.pid, cmd[0])
            return f"pid:{proc.pid}"
        except (FileNotFoundError, OSError):
            continue

    logger.info(
        "No agent CLI found — project ready for IDE agent via AGENT_INSTRUCTION.md"
    )
    return None


def prepare_distribution_manifest(project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """CapCut + Google Drive hand-off payload when status becomes completed."""
    root = project_dir(project_id)
    render_path = root / "renders" / "final.mp4"
    script_path = root / "scripts" / "script.md"
    artifact_script = root / "artifacts" / "script.json"
    assets_dir = root / "assets"

    script_file = (
        str(script_path)
        if script_path.exists()
        else (str(artifact_script) if artifact_script.exists() else None)
    )

    manifest = {
        "project_id": project_id,
        "title": data.get("title"),
        "created_at": now_iso(),
        "render": str(render_path) if render_path.exists() else None,
        "script": script_file,
        "assets_dir": str(assets_dir),
        "aspect": data.get("aspect_ratio", "9:16"),
        "duration_seconds": data.get("target_runtime_seconds"),
        "capcut": {
            "action": "create_vertical_draft",
            "draft_name": f"Nexus_{project_id}",
            "notes": (
                "Open the generated draft in CapCut desktop to fine-tune and export. "
                "CapCut has no official public API; use CapCutAPI / community MCP."
            ),
            "suggested_drafts_path": CAPCUT_DRAFTS_PATH,
        },
        "google_drive": {
            "action": "upload_folder",
            "target_folder_id": DRIVE_FOLDER_ID,
            "files_to_upload": [
                str(render_path) if render_path.exists() else None,
                script_file,
            ],
            "notes": (
                "Use the google-workspace skill or Drive MCP to upload. "
                "Filter None values before calling."
            ),
        },
        "next_steps": [
            "1. Open CapCut draft (or create via CapCut MCP) and place final voiceover + B-roll",
            "2. Export 1080x1920 mp4",
            "3. Upload master + script to the Nexus Drive folder",
            "4. Hand off to Blotato / Zapier / Make distribution scenario",
        ],
    }

    manifest["google_drive"]["files_to_upload"] = [
        f for f in manifest["google_drive"]["files_to_upload"] if f
    ]

    out = root / "distribution" / "distribution_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def apply_stage_approval(project_id: str, body: StageApproval) -> Dict[str, Any]:
    """Shared approval progression for HTTP + MCP."""
    data = load_project(project_id)

    if data.get("status") != "awaiting_approval":
        raise HTTPException(
            400, f"Not awaiting approval (status={data.get('status')})"
        )

    history_dir = project_dir(project_id) / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (history_dir / f"approval_{body.stage}_{stamp}.json").write_text(
        json.dumps(body.model_dump(), indent=2), encoding="utf-8"
    )

    if not body.approved:
        data["status"] = "rejected"
        data["message"] = f"Stage '{body.stage}' rejected: {body.comments or 'no comment'}"
        save_project(project_id, data)
        return data

    current = data.get("current_stage") or "research"
    try:
        idx = STAGE_ORDER.index(current)
        next_stage = STAGE_ORDER[min(idx + 1, len(STAGE_ORDER) - 1)]
    except ValueError:
        next_stage = "completed"

    data["current_stage"] = next_stage

    if next_stage == "completed":
        data["status"] = "completed"
        data["message"] = "Production marked complete. Distribution manifest prepared."
        data["distribution"] = prepare_distribution_manifest(project_id, data)
    else:
        data["status"] = (
            "awaiting_approval" if next_stage in APPROVAL_GATES else "running"
        )
        data["message"] = (
            f"Stage '{body.stage}' approved → now at '{next_stage}'. Continue the agent."
        )

    save_project(project_id, data)
    return data


def build_project_meta(project_id: str, req: ProduceRequest, *, message: str) -> Dict[str, Any]:
    return {
        "version": "1.0",
        "project_id": project_id,
        "title": req.topic,
        "pipeline": req.pipeline,
        "pipeline_type": req.pipeline,
        "target_runtime_seconds": req.duration_seconds,
        "aspect_ratio": req.aspect,
        "status": "queued",
        "current_stage": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "budget_usd": req.budget_usd,
        "spent_usd": 0.0,
        "approval_mode": req.approval_mode.value,
        "brand_skills": BRAND_SKILLS,
        "user_voiceover": True,
        "preferred_providers": {
            "video": ["kling", "runway", "archival"],
            "image": ["flux", "archival"],
            "tts_preview": ["elevenlabs", "piper"],
            "music": ["sparse_dark_ambient"],
        },
        "notes": req.notes,
        "reference_url": req.reference_url,
        "artifacts": {},
        "message": message,
        "distribution": None,
    }


def run_pipeline_background(project_id: str, req: ProduceRequest) -> None:
    """Write agent instruction, optional spawn, first approval gate."""
    logger.info("Starting OpenMontage hand-off for %s", project_id)
    data = load_project(project_id)

    try:
        instruction_path = write_agent_instruction(project_id, req)
        try:
            rel_instruction = str(instruction_path.relative_to(BASE_DIR))
        except ValueError:
            rel_instruction = str(instruction_path)
        data["artifacts"]["agent_instruction"] = rel_instruction

        if req.auto_spawn_agent:
            spawn_id = try_spawn_openmontage_agent(project_id, instruction_path)
            if spawn_id:
                data["artifacts"]["spawned_agent"] = spawn_id

        research_path = project_dir(project_id) / "research" / "research_brief.md"
        research_path.write_text(
            f"""# Research Brief — {req.topic}

**Project:** {project_id}
**Pipeline:** {req.pipeline}
**Brand skills:** {', '.join(BRAND_SKILLS)}
**Status:** Scaffold — agent must replace with schema-valid artifact under `artifacts/`

## Agent Task
Perform the research stage of the `{req.pipeline}` pipeline.
Separate documented historical record from popular myth.
Cite primary or high-quality secondary sources.
Include at least one human-cost / historical-context beat.

Then produce the proposal_packet and stop for human approval.
""",
            encoding="utf-8",
        )
        try:
            data["artifacts"]["research_brief_scaffold"] = str(
                research_path.relative_to(BASE_DIR)
            )
        except ValueError:
            data["artifacts"]["research_brief_scaffold"] = str(research_path)

        data["status"] = "awaiting_approval"
        data["current_stage"] = "proposal"
        data["message"] = (
            "OpenMontage agent instruction written. "
            "Open the project in Claude Code / Cursor (or let the spawned agent run) "
            "and execute AGENT_INSTRUCTION.md. Stop at proposal for approval."
        )
        save_project(project_id, data)
        logger.info(
            "Project %s ready for OpenMontage agent (instruction at %s)",
            project_id,
            instruction_path,
        )

    except Exception as exc:
        logger.exception("Hand-off failed for %s", project_id)
        data["status"] = "failed"
        data["message"] = str(exc)
        save_project(project_id, data)


def create_and_queue(req: ProduceRequest, *, sync: bool = False) -> Dict[str, Any]:
    """Create project + queue (or run) hand-off. Shared by HTTP and MCP."""
    project_id = f"{slugify(req.topic)}-{uuid.uuid4().hex[:8]}"
    create_nexus_project(project_id, title=req.topic, pipeline=req.pipeline)
    meta = build_project_meta(
        project_id,
        req,
        message="Project created. Writing OpenMontage agent instruction…",
    )
    save_project(project_id, meta)
    if sync:
        run_pipeline_background(project_id, req)
        return load_project(project_id)
    return meta


# ---------------------------------------------------------------------------
# FastAPI (HTTP) layer
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Nexus OpenMontage Server",
    description="Produce brand-compliant Mafia true-crime Shorts + MCP tools",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # Starlette rejects allow_origins=["*"] combined with allow_credentials=True.
    # Auth is via X-API-Key header, not cookies.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "openmontage_root": str(BASE_DIR),
        "projects_dir": str(_PROJECTS),
        "mcp_available": MCP_AVAILABLE,
        "pipeline": PIPELINE_NAME,
        "brand_skills": BRAND_SKILLS,
    }


@app.post(
    "/produce_mafia_short",
    response_model=ProjectStatus,
    dependencies=[Depends(verify_api_key)],
)
def produce_mafia_short(req: ProduceRequest, background_tasks: BackgroundTasks):
    meta = create_and_queue(req, sync=False)
    background_tasks.add_task(run_pipeline_background, meta["project_id"], req)
    return ProjectStatus(**meta)


@app.get(
    "/status/{project_id}",
    response_model=ProjectStatus,
    dependencies=[Depends(verify_api_key)],
)
def get_status(project_id: str):
    data = load_project(project_id)
    return ProjectStatus(**_status_fields(data))


@app.get("/projects", dependencies=[Depends(verify_api_key)])
def list_projects(limit: int = 50):
    projects: List[Dict[str, Any]] = []
    if not _PROJECTS.exists():
        return {"count": 0, "projects": []}
    for p in sorted(_PROJECTS.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if p.is_dir() and (p / "project.json").exists():
            try:
                projects.append(json.loads((p / "project.json").read_text(encoding="utf-8")))
            except Exception:
                continue
        if len(projects) >= limit:
            break
    return {"count": len(projects), "projects": projects}


@app.post(
    "/approve/{project_id}",
    response_model=ProjectStatus,
    dependencies=[Depends(verify_api_key)],
)
def approve_stage(project_id: str, body: StageApproval):
    data = apply_stage_approval(project_id, body)
    return ProjectStatus(**_status_fields(data))


@app.delete("/projects/{project_id}", dependencies=[Depends(verify_api_key)])
def delete_project(project_id: str, confirm: bool = False):
    if not confirm:
        raise HTTPException(400, "Pass ?confirm=true to delete")
    path = project_dir(project_id)
    if not path.exists():
        raise HTTPException(404, "Not found")
    shutil.rmtree(path)
    return {"deleted": project_id}


def _status_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize project.json → ProjectStatus (Backlot marker may omit Nexus fields)."""
    return {
        "project_id": data.get("project_id", ""),
        "title": data.get("title", ""),
        "status": data.get("status", "unknown"),
        "current_stage": data.get("current_stage"),
        "pipeline": data.get("pipeline") or data.get("pipeline_type") or PIPELINE_NAME,
        "created_at": data.get("created_at") or now_iso(),
        "updated_at": data.get("updated_at") or now_iso(),
        "budget_usd": float(data.get("budget_usd", DEFAULT_BUDGET_USD)),
        "spent_usd": float(data.get("spent_usd", 0.0)),
        "approval_mode": data.get("approval_mode", ApprovalMode.guided.value),
        "brand_skills": data.get("brand_skills") or BRAND_SKILLS,
        "artifacts": data.get("artifacts") or {},
        "message": data.get("message"),
        "distribution": data.get("distribution"),
    }


# ---------------------------------------------------------------------------
# MCP Server layer (Claude Desktop / Cursor)
# ---------------------------------------------------------------------------

if MCP_AVAILABLE and FastMCP is not None:
    mcp = FastMCP("Nexus OpenMontage")

    @mcp.tool(name="produce_mafia_short")
    def mcp_produce_mafia_short(
        topic: str,
        duration_seconds: int = 45,
        aspect: str = "9:16",
        budget_usd: float = 1.50,
        notes: str = "",
        auto_spawn_agent: bool = False,
    ) -> str:
        """
        Start a brand-compliant Nexus true-crime Short using the OpenMontage
        nexus-true-crime-short pipeline. Returns the new project_id.
        """
        req = ProduceRequest(
            topic=topic,
            duration_seconds=duration_seconds,
            aspect=aspect,
            budget_usd=budget_usd,
            notes=notes or None,
            auto_spawn_agent=auto_spawn_agent,
        )
        data = create_and_queue(req, sync=True)
        return (
            f"Project created: {data['project_id']}. "
            "Open AGENT_INSTRUCTION.md inside the OpenMontage project and execute it."
        )

    @mcp.tool(name="get_project_status")
    def mcp_get_project_status(project_id: str) -> str:
        """Return current status and artifacts for a Nexus OpenMontage project."""
        data = load_project(project_id)
        return json.dumps(data, indent=2)

    @mcp.tool(name="approve_stage")
    def mcp_approve_stage(
        project_id: str,
        stage: str,
        approved: bool = True,
        comments: str = "",
    ) -> str:
        """Approve or reject the current stage of a project (human gate)."""
        body = StageApproval(stage=stage, approved=approved, comments=comments or None)
        try:
            data = apply_stage_approval(project_id, body)
        except HTTPException as exc:
            return str(exc.detail)
        return data.get("message") or "ok"

    @mcp.tool(name="list_recent_projects")
    def mcp_list_recent_projects(limit: int = 10) -> str:
        """List the most recent Nexus OpenMontage projects."""
        result = list_projects(limit=limit)
        return json.dumps(result, indent=2)

else:
    mcp = None
    logger.warning(
        "MCP SDK not installed. HTTP-only mode. Run: pip install 'mcp[cli]'"
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nexus OpenMontage dual server")
    parser.add_argument("--mode", choices=["http", "mcp", "both"], default="http")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.mode in ("mcp", "both") and mcp is not None:
        logger.info("Starting MCP server (stdio)")
        mcp.run(transport="stdio")
    else:
        import uvicorn

        logger.info(
            "Starting FastAPI on %s:%s (MCP available: %s)",
            args.host,
            args.port,
            MCP_AVAILABLE,
        )
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
