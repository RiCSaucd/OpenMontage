"""Stdlib Backlot server — same API as FastAPI, no extra deps."""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from pathlib import Path

import pytest

from backlot import state as state_mod
from backlot import stdlib_server as stdlib


@pytest.fixture
def projects_root(tmp_path, monkeypatch):
    root = tmp_path / "projects"
    root.mkdir()
    monkeypatch.setattr(state_mod, "PROJECTS_DIR", root)
    monkeypatch.setattr(state_mod, "REPO_ROOT", tmp_path)
    with stdlib._cache_lock:
        stdlib._summary_cache.clear()
    return root


@pytest.fixture
def stdlib_client(projects_root):
    httpd = stdlib.ThreadingHTTPServer(("127.0.0.1", 0), stdlib.BacklotHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]

    def request(path: str, headers: dict | None = None) -> tuple[int, dict, bytes]:
        conn = HTTPConnection(host, port, timeout=5)
        conn.request("GET", path, headers=headers or {})
        resp = conn.getresponse()
        body = resp.read()
        hdrs = {k.lower(): v for k, v in resp.getheaders()}
        conn.close()
        return resp.status, hdrs, body

    yield request
    httpd.shutdown()
    httpd.server_close()


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _make_project(root: Path, project_id: str = "film") -> Path:
    project = root / project_id
    (project / "artifacts").mkdir(parents=True)
    (project / "assets" / "images").mkdir(parents=True)
    (project / "renders").mkdir(parents=True)
    _write_json(
        project / "project.json",
        {
            "project_id": project_id,
            "title": "Film",
            "pipeline_type": "cinematic",
            "created_at": "2026-07-02T00:00:00Z",
        },
    )
    _write_json(
        project / "checkpoint_script.json",
        {
            "version": "1.0",
            "project_id": project_id,
            "pipeline_type": "cinematic",
            "stage": "script",
            "status": "awaiting_human",
            "timestamp": "2026-07-02T00:01:00Z",
            "artifacts": {},
        },
    )
    return project


def test_health(stdlib_client):
    status, _, body = stdlib_client("/api/health")
    assert status == 200
    assert json.loads(body) == {"ok": True, "app": "backlot"}


def test_library_and_board_state(stdlib_client, projects_root):
    _make_project(projects_root, "film")
    status, _, body = stdlib_client("/api/projects")
    assert status == 200
    projects = json.loads(body)
    assert projects[0]["project_id"] == "film"
    assert projects[0]["awaiting_human"] is True

    status, _, body = stdlib_client("/api/project/film/state")
    assert status == 200
    state = json.loads(body)
    assert state["title"] == "Film"

    status, headers, _ = stdlib_client("/p/film")
    assert status == 200
    assert "text/html" in headers["content-type"]

    status, _, _ = stdlib_client("/")
    assert status == 200


def test_bad_project_ids(stdlib_client):
    status, _, _ = stdlib_client("/api/project/C:/state")
    assert status == 400
    status, _, _ = stdlib_client("/api/project/nope/state")
    assert status == 404


def test_media_range_and_path_escape(stdlib_client, projects_root):
    project = _make_project(projects_root, "film")
    media = project / "renders" / "final.mp4"
    media.write_bytes(b"0123456789")

    status, headers, body = stdlib_client(
        "/media/film/renders/final.mp4", headers={"Range": "bytes=2-5"}
    )
    assert status == 206
    assert body == b"2345"
    assert headers["content-range"].startswith("bytes 2-5/10")

    status, _, _ = stdlib_client("/media/film/%2E%2E/project.json")
    assert status == 403


def test_thumb_never_serves_raw_video(stdlib_client, projects_root):
    project = _make_project(projects_root, "vid")
    fake = project / "renders" / "final.mp4"
    fake.write_bytes(b"\x00" * 4096)
    status, _, body = stdlib_client("/thumb/vid/renders/final.mp4")
    assert status == 404
    assert not body.startswith(b"\x00\x00")
