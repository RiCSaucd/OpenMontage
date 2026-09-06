"""Stdlib Backlot server — same routes as ``backlot.server``, no FastAPI.

Used when fastapi/uvicorn are not installed (PyPI-blocked Cloud VMs).
The board is an observer: this process never writes to ``projects/``.
"""

from __future__ import annotations

import json
import mimetypes
import os
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse

from backlot import state as state_mod

UI_DIR = Path(__file__).resolve().parent / "ui"
THUMB_WIDTHS = (320, 640, 960)
SSE_HEARTBEAT_SECONDS = 15
_IGNORE_PARTS = {"node_modules", ".git", "__pycache__", ".cache"}

MIME_OVERRIDES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
}


class ChangeHub:
    def __init__(self) -> None:
        self._subscribers: dict[queue.Queue, Optional[str]] = {}
        self._lock = threading.Lock()

    def subscribe(self, project_id: Optional[str] = None) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=64)
        with self._lock:
            self._subscribers[q] = project_id
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            self._subscribers.pop(q, None)

    def publish(self, project_id: str) -> None:
        with self._lock:
            items = list(self._subscribers.items())
        for q, only in items:
            if only is not None and only != project_id:
                continue
            try:
                q.put_nowait(project_id)
            except queue.Full:
                pass


hub = ChangeHub()
_summary_cache: dict[str, dict] = {}
_cache_lock = threading.Lock()


def _thumb_cache_dir() -> Path:
    return state_mod.REPO_ROOT / ".backlot" / "thumbs"


def _invalidate_summary(project_id: str) -> None:
    with _cache_lock:
        _summary_cache.pop(project_id, None)


def _cached_summaries() -> list[dict]:
    root = state_mod.PROJECTS_DIR
    if not root.is_dir():
        return []
    summaries = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith(("_", ".")):
            continue
        with _cache_lock:
            cached = _summary_cache.get(entry.name)
        if cached is None:
            try:
                cached = state_mod.summarize_project(entry)
            except Exception:
                cached = {
                    "project_id": entry.name, "title": entry.name,
                    "pipeline_type": "unknown", "has_pipeline_state": False,
                    "poster": None, "live": False, "last_activity": 0,
                    "active_stage": None, "awaiting_human": False,
                    "stage_states": [], "completed_count": 0,
                    "render_count": 0, "scene_count": 0, "error": "unreadable",
                }
            with _cache_lock:
                _summary_cache[entry.name] = cached
        summaries.append(cached)
    summaries.sort(key=lambda s: (not s["live"], -(s["last_activity"] or 0)))
    return summaries


def _project_of_change(path_str: str) -> Optional[str]:
    root = os.path.normcase(str(state_mod.PROJECTS_DIR.resolve()))
    norm = os.path.normcase(os.path.normpath(path_str))
    if not norm.startswith(root):
        return None
    rel = norm[len(root):].lstrip("\\/")
    if not rel:
        return None
    parts = rel.replace("\\", "/").split("/")
    if _IGNORE_PARTS.intersection(parts):
        return None
    return parts[0]


def _projects_fingerprint() -> tuple:
    root = state_mod.PROJECTS_DIR
    if not root.is_dir():
        return ()
    rows = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _IGNORE_PARTS]
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                st = os.stat(path)
            except OSError:
                continue
            rows.append((path, st.st_mtime_ns, st.st_size))
    rows.sort()
    return tuple(rows)


def _watch_loop(stop: threading.Event) -> None:
    """Poll ``projects/`` when watchfiles is missing."""
    last = _projects_fingerprint()
    while not stop.wait(0.4):
        current = _projects_fingerprint()
        if current == last:
            continue
        changed_paths = {p for p, *_ in current} ^ {p for p, *_ in last}
        # Also treat size/mtime changes as the same path.
        old = {p: (m, s) for p, m, s in last}
        new = {p: (m, s) for p, m, s in current}
        for path, meta in new.items():
            if old.get(path) != meta:
                changed_paths.add(path)
        touched: set[str] = set()
        for path in changed_paths:
            pid = _project_of_change(path)
            if pid:
                touched.add(pid)
        for pid in touched:
            _invalidate_summary(pid)
            hub.publish(pid)
        last = current


def _safe_project_dir(project_id: str) -> Path:
    if any(c in project_id for c in "/\\:") or project_id in (".", ".."):
        raise _HttpError(400, "invalid project id")
    project_dir = state_mod.PROJECTS_DIR / project_id
    if not project_dir.is_dir():
        raise _HttpError(404, f"unknown project: {project_id}")
    return project_dir


def _safe_project_file(project_id: str, file_path: str) -> Path:
    project_dir = _safe_project_dir(project_id)
    target = (project_dir / file_path).resolve()
    try:
        target.relative_to(project_dir.resolve())
    except ValueError:
        raise _HttpError(403, "path escapes project")
    if not target.is_file():
        raise _HttpError(404, "media not found")
    return target


class _HttpError(Exception):
    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail


def _sse(payload: dict) -> bytes:
    return f"data: {json.dumps(payload)}\n\n".encode("utf-8")


def _content_type(path: Path) -> str:
    override = MIME_OVERRIDES.get(path.suffix.lower())
    if override:
        return override
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def _thumbnail_for(source: Path, width: int) -> Optional[Path]:
    suffix = source.suffix.lower()
    is_image = suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    is_video = suffix in {".mp4", ".webm", ".mov"}
    if not (is_image or is_video):
        return None
    try:
        import hashlib
        import subprocess
        import uuid

        stat = source.stat()
        key = hashlib.sha1(
            f"{source}|{stat.st_mtime_ns}|{stat.st_size}|{width}".encode()
        ).hexdigest()[:20]
        cache_dir = _thumb_cache_dir()
        cached = cache_dir / f"{key}.jpg"
        if cached.is_file():
            return cached
        cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = cache_dir / f"{key}.{uuid.uuid4().hex[:8]}.tmp.jpg"
        if is_video:
            result = subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.5",
                 "-i", str(source), "-frames:v", "1",
                 "-vf", f"scale={width}:-2", str(tmp)],
                capture_output=True, timeout=30,
            )
            if result.returncode != 0 or not tmp.is_file():
                return None
        else:
            try:
                from PIL import Image
                with Image.open(source) as img:
                    img = img.convert("RGB")
                    img.thumbnail((width, width * 3))
                    img.save(tmp, "JPEG", quality=82)
            except ImportError:
                result = subprocess.run(
                    ["ffmpeg", "-y", "-loglevel", "error",
                     "-i", str(source), "-frames:v", "1",
                     "-vf", f"scale={width}:-2", str(tmp)],
                    capture_output=True, timeout=30,
                )
                if result.returncode != 0 or not tmp.is_file():
                    return None
        tmp.replace(cached)
        return cached
    except Exception:
        return None


def _parse_range(header: str, size: int) -> Optional[tuple[int, int]]:
    if not header.startswith("bytes="):
        return None
    spec = header[6:].split(",", 1)[0].strip()
    if "-" not in spec:
        return None
    start_s, end_s = spec.split("-", 1)
    try:
        if start_s == "":
            length = int(end_s)
            if length <= 0:
                return None
            start = max(size - length, 0)
            end = size - 1
        else:
            start = int(start_s)
            end = int(end_s) if end_s else size - 1
    except ValueError:
        return None
    if start < 0 or end < start or start >= size:
        return None
    return start, min(end, size - 1)


class BacklotHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        qs = parse_qs(parsed.query)
        try:
            if path == "/api/health":
                return self._send_json(200, {"ok": True, "app": "backlot"})
            if path == "/api/projects":
                return self._send_json(200, _cached_summaries())
            if path == "/api/library/events":
                return self._stream_sse(None)
            if path == "/":
                return self._send_file(UI_DIR / "index.html")
            if path.startswith("/ui/"):
                return self._send_ui(path[4:])
            if path.startswith("/api/project/"):
                return self._api_project(path[len("/api/project/"):])
            if path.startswith("/p/"):
                return self._send_file(UI_DIR / "board.html")
            if path.startswith("/thumb/"):
                return self._thumb(path[len("/thumb/"):], qs)
            if path.startswith("/media/"):
                return self._media(path[len("/media/"):])
            raise _HttpError(404, "not found")
        except _HttpError as err:
            self._send_json(err.status, {"detail": err.detail})
        except BrokenPipeError:
            return
        except Exception:
            try:
                self._send_json(500, {"detail": "internal error"})
            except Exception:
                return

    def _api_project(self, rest: str) -> None:
        if rest.endswith("/state"):
            project_id = rest[: -len("/state")]
            project_dir = _safe_project_dir(project_id)
            return self._send_json(200, state_mod.load_board_state(project_dir))
        if rest.endswith("/events"):
            project_id = rest[: -len("/events")]
            _safe_project_dir(project_id)
            return self._stream_sse(project_id)
        raise _HttpError(404, "not found")

    def _send_ui(self, rel: str) -> None:
        if not rel or ".." in rel.split("/"):
            raise _HttpError(404, "not found")
        target = (UI_DIR / rel).resolve()
        try:
            target.relative_to(UI_DIR.resolve())
        except ValueError:
            raise _HttpError(404, "not found")
        if not target.is_file():
            raise _HttpError(404, "not found")
        self._send_file(target)

    def _thumb(self, rest: str, qs: dict) -> None:
        project_id, _, file_path = rest.partition("/")
        target = _safe_project_file(project_id, file_path)
        try:
            width = int((qs.get("w") or ["640"])[0])
        except ValueError:
            width = 640
        width = min(THUMB_WIDTHS, key=lambda x: abs(x - width))
        cached = _thumbnail_for(target, width)
        if cached is None:
            if target.suffix.lower() in {".mp4", ".webm", ".mov"}:
                raise _HttpError(404, "no poster frame available")
            return self._send_file(target)
        self._send_file(cached, content_type="image/jpeg")

    def _media(self, rest: str) -> None:
        project_id, _, file_path = rest.partition("/")
        target = _safe_project_file(project_id, file_path)
        self._send_file(target, allow_range=True)

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(
        self,
        path: Path,
        *,
        content_type: Optional[str] = None,
        allow_range: bool = False,
    ) -> None:
        data = path.read_bytes()
        ctype = content_type or _content_type(path)
        rng = self.headers.get("Range") if allow_range else None
        if rng:
            parsed = _parse_range(rng, len(data))
            if parsed is None:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{len(data)}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            start, end = parsed
            chunk = data[start : end + 1]
            self.send_response(206)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Range", f"bytes {start}-{end}/{len(data)}")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(len(chunk)))
            self.end_headers()
            self.wfile.write(chunk)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if allow_range:
            self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self.wfile.write(data)

    def _stream_sse(self, project_id: Optional[str]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        hello = {"type": "hello"}
        if project_id:
            hello["project_id"] = project_id
        q = hub.subscribe(project_id)
        try:
            self.wfile.write(_sse(hello))
            self.wfile.flush()
            while True:
                try:
                    changed = q.get(timeout=SSE_HEARTBEAT_SECONDS)
                except queue.Empty:
                    self.wfile.write(_sse({"type": "heartbeat", "ts": time.time()}))
                    self.wfile.flush()
                    continue
                while True:
                    try:
                        q.get_nowait()
                    except queue.Empty:
                        break
                payload = {"type": "change"}
                if project_id:
                    payload["project_id"] = project_id
                else:
                    payload["project_id"] = changed
                self.wfile.write(_sse(payload))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return
        finally:
            hub.unsubscribe(q)


def serve(host: str = "127.0.0.1", port: int = 4750) -> int:
    stop = threading.Event()
    watcher = threading.Thread(target=_watch_loop, args=(stop,), daemon=True)
    watcher.start()
    httpd = ThreadingHTTPServer((host, port), BacklotHandler)
    print(f"backlot: stdlib server on http://{host}:{port}/ (fastapi/uvicorn not installed)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        httpd.server_close()
    return 0
