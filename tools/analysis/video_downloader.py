"""Video downloader tool wrapping yt-dlp.

Downloads video, audio, or subtitles from YouTube, Shorts, Instagram Reels,
TikTok, and 1000+ other sites. Supports reference analysis (720p default)
and production ingest (1080p, longer duration). Optional limited playlist
download for clip-factory workflows.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolStability,
    ToolTier,
    ToolRuntime,
)


logger = logging.getLogger(__name__)


class VideoDownloader(BaseTool):
    name = "video_downloader"
    version = "0.2.0"
    tier = ToolTier.SOURCE
    capability = "source_ingest"
    provider = "yt-dlp"
    stability = ToolStability.PRODUCTION
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["python:yt_dlp"]
    install_instructions = (
        "Install yt-dlp: pip install yt-dlp\n"
        "For YouTube support, also install Deno (JS runtime): "
        "https://deno.land/#installation\n"
        "Without Deno, YouTube downloads may fail but other platforms still work."
    )
    agent_skills = ["video-download"]

    capabilities = [
        "download_video",
        "download_audio",
        "download_subtitles",
        "extract_metadata",
        "download_playlist",
    ]

    best_for = [
        "downloading reference video from URL",
        "production-quality source ingest for clip-factory",
        "downloading a limited number of playlist items",
        "extracting audio from online video",
        "downloading subtitles from YouTube",
        "getting video metadata without downloading",
    ]

    not_good_for = [
        "downloading very large playlists (use max_playlist_items cap)",
        "downloading DRM-protected content",
    ]

    input_schema = {
        "type": "object",
        "required": ["url", "output_dir"],
        "properties": {
            "url": {"type": "string", "description": "Video or playlist URL to download"},
            "output_dir": {"type": "string", "description": "Directory for downloaded files"},
            "format": {
                "type": "string",
                "enum": ["video", "audio_only", "subtitles_only", "metadata_only"],
                "default": "video",
                "description": "What to download",
            },
            "ingest_mode": {
                "type": "string",
                "enum": ["reference", "production"],
                "default": "reference",
                "description": (
                    "reference: 720p cap, 10 min duration limit (analysis). "
                    "production: 1080p cap, 60 min duration limit (clip-factory ingest)."
                ),
            },
            "max_resolution": {
                "type": "string",
                "enum": ["360p", "480p", "720p", "1080p"],
                "description": (
                    "Override max resolution. Defaults to 720p for reference mode "
                    "and 1080p for production mode."
                ),
            },
            "max_duration_seconds": {
                "type": "integer",
                "description": (
                    "Reject videos longer than this. Defaults to 600 (reference) "
                    "or 3600 (production)."
                ),
            },
            "allow_playlist": {
                "type": "boolean",
                "default": False,
                "description": "When true, download multiple items from a playlist URL",
            },
            "max_playlist_items": {
                "type": "integer",
                "default": 5,
                "minimum": 1,
                "maximum": 25,
                "description": "Maximum playlist entries to download when allow_playlist is true",
            },
        },
    }

    output_schema = {
        "type": "object",
        "properties": {
            "video_path": {"type": ["string", "null"]},
            "audio_path": {"type": ["string", "null"]},
            "subtitle_path": {"type": ["string", "null"]},
            "videos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "video_path": {"type": ["string", "null"]},
                        "audio_path": {"type": ["string", "null"]},
                        "metadata": {"type": "object"},
                        "playlist_index": {"type": "integer"},
                    },
                },
            },
            "playlist_count": {"type": "integer"},
            "metadata": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "duration": {"type": "number"},
                    "uploader": {"type": "string"},
                    "upload_date": {"type": "string"},
                    "description": {"type": "string"},
                    "view_count": {"type": "integer"},
                    "like_count": {"type": "integer"},
                },
            },
            "platform": {"type": "string"},
            "ingest_mode": {"type": "string"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=1, ram_mb=512, vram_mb=0, disk_mb=2000,
        network_required=True,
    )
    idempotency_key_fields = [
        "url",
        "format",
        "max_resolution",
        "ingest_mode",
        "allow_playlist",
        "max_playlist_items",
        "max_duration_seconds",
    ]
    side_effects = ["downloads media files to output_dir"]
    resume_support_value = "from_start"
    user_visible_verification = [
        "Check downloaded file plays correctly",
        "Verify resolution matches requested max",
    ]

    _RES_MAP = {
        "360p": 360,
        "480p": 480,
        "720p": 720,
        "1080p": 1080,
    }

    _MODE_DEFAULTS = {
        "reference": {"max_resolution": "720p", "max_duration_seconds": 600},
        "production": {"max_resolution": "1080p", "max_duration_seconds": 3600},
    }

    def _parse_bounded_int(
        self,
        value: Any,
        *,
        field: str,
        default: int,
        minimum: int = 1,
        maximum: int | None = None,
    ) -> int:
        if value is None:
            parsed = default
        else:
            try:
                parsed = int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{field} must be an integer") from exc
        if parsed < minimum:
            raise ValueError(f"{field} must be >= {minimum}")
        if maximum is not None:
            return min(parsed, maximum)
        return parsed

    def _resolve_ingest_settings(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Apply ingest_mode defaults with explicit overrides."""
        mode = inputs.get("ingest_mode", "reference")
        if mode not in self._MODE_DEFAULTS:
            mode = "reference"
        defaults = self._MODE_DEFAULTS[mode]
        return {
            "ingest_mode": mode,
            "max_resolution": inputs.get("max_resolution") or defaults["max_resolution"],
            "max_duration_seconds": self._parse_bounded_int(
                inputs.get("max_duration_seconds", defaults["max_duration_seconds"]),
                field="max_duration_seconds",
                default=defaults["max_duration_seconds"],
            ),
            "allow_playlist": bool(inputs.get("allow_playlist", False)),
            "max_playlist_items": self._parse_bounded_int(
                inputs.get("max_playlist_items", 5),
                field="max_playlist_items",
                default=5,
                maximum=25,
            ),
        }

    def _duration_limit_hint(self, ingest_mode: str) -> str:
        if ingest_mode == "production":
            return "Increase max_duration_seconds to allow longer videos."
        return "Increase max_duration_seconds or switch to ingest_mode=production."

    def _extract_audio(self, video_path: str, audio_out: Path) -> str | None:
        """Extract mono 16 kHz WAV audio for transcription workflows."""
        try:
            audio_cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(audio_out),
            ]
            self.run_command(audio_cmd, timeout=120)
            if audio_out.exists():
                return str(audio_out)
        except Exception as exc:
            logger.warning("Audio extraction failed for %s: %s", video_path, exc)
        return None

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        url_lower = url.lower()
        if "youtube.com/shorts" in url_lower or "youtu.be" in url_lower and "/shorts" in url_lower:
            return "shorts"
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        if "instagram.com" in url_lower:
            return "instagram"
        if "tiktok.com" in url_lower:
            return "tiktok"
        if "vimeo.com" in url_lower:
            return "vimeo"
        if "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter"
        return "other_url"

    def _normalize_metadata(self, info: dict | None) -> dict:
        if info is None:
            return {"error": "No info extracted", "title": "", "duration": 0}
        return {
            "title": info.get("title", ""),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", info.get("channel", "")),
            "upload_date": info.get("upload_date", ""),
            "description": (info.get("description", "") or "")[:500],
            "view_count": info.get("view_count", 0),
            "like_count": info.get("like_count", 0),
            "resolution": f"{info.get('width', 0)}x{info.get('height', 0)}",
            "fps": info.get("fps", 0),
            "playlist_index": info.get("playlist_index"),
            "id": info.get("id", ""),
        }

    def _extract_metadata(
        self,
        url: str,
        *,
        allow_playlist: bool = False,
        max_playlist_items: int = 5,
    ) -> dict:
        """Extract metadata without downloading."""
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": not allow_playlist,
            "extract_flat": allow_playlist,
        }
        if allow_playlist:
            ydl_opts["playlistend"] = max_playlist_items
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info is None:
                    return {"error": "No info extracted", "title": "", "duration": 0}

                if allow_playlist and info.get("_type") == "playlist":
                    entries = info.get("entries") or []
                    return {
                        "title": info.get("title", ""),
                        "duration": info.get("duration", 0),
                        "uploader": info.get("uploader", info.get("channel", "")),
                        "upload_date": info.get("upload_date", ""),
                        "description": (info.get("description", "") or "")[:500],
                        "view_count": info.get("view_count", 0),
                        "like_count": info.get("like_count", 0),
                        "playlist_count": len(entries),
                        "is_playlist": True,
                    }

                return self._normalize_metadata(info)
        except Exception as e:
            return {"error": str(e), "title": "", "duration": 0}

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        url = inputs["url"]
        output_dir = Path(inputs["output_dir"])
        dl_format = inputs.get("format", "video")
        try:
            settings = self._resolve_ingest_settings(inputs)
        except ValueError as exc:
            return ToolResult(success=False, error=str(exc))

        max_res = settings["max_resolution"]
        max_duration = settings["max_duration_seconds"]
        allow_playlist = settings["allow_playlist"]
        max_playlist_items = settings["max_playlist_items"]

        output_dir.mkdir(parents=True, exist_ok=True)
        platform = self._detect_platform(url)
        start = time.time()

        metadata = self._extract_metadata(
            url,
            allow_playlist=allow_playlist,
            max_playlist_items=max_playlist_items,
        )

        if allow_playlist and metadata.get("is_playlist"):
            return self._execute_playlist(
                url=url,
                output_dir=output_dir,
                dl_format=dl_format,
                max_res=max_res,
                max_duration=max_duration,
                max_playlist_items=max_playlist_items,
                metadata=metadata,
                platform=platform,
                ingest_mode=settings["ingest_mode"],
                start=start,
            )

        duration = metadata.get("duration", 0)
        if duration and duration > max_duration:
            return ToolResult(
                success=False,
                error=(
                    f"Video is {duration}s, exceeds max_duration_seconds={max_duration} "
                    f"for ingest_mode={settings['ingest_mode']}. "
                    f"{self._duration_limit_hint(settings['ingest_mode'])}"
                ),
                data={
                    "metadata": metadata,
                    "platform": platform,
                    "ingest_mode": settings["ingest_mode"],
                },
            )

        if dl_format == "metadata_only":
            return ToolResult(
                success=True,
                data={
                    "video_path": None,
                    "audio_path": None,
                    "subtitle_path": None,
                    "videos": [],
                    "playlist_count": 0,
                    "metadata": metadata,
                    "platform": platform,
                    "ingest_mode": settings["ingest_mode"],
                },
                duration_seconds=round(time.time() - start, 2),
            )

        video_path = None
        audio_path = None
        subtitle_path = None

        try:
            if dl_format == "video":
                video_path, audio_path = self._download_video(
                    url, output_dir, max_res, allow_playlist=False
                )
            elif dl_format == "audio_only":
                audio_path = self._download_audio(url, output_dir)
            elif dl_format == "subtitles_only":
                subtitle_path = self._download_subtitles(url, output_dir)
        except Exception as e:
            elapsed = time.time() - start
            return ToolResult(
                success=False,
                error=f"Download failed: {e}",
                data={
                    "metadata": metadata,
                    "platform": platform,
                    "ingest_mode": settings["ingest_mode"],
                },
                duration_seconds=round(elapsed, 2),
            )

        elapsed = time.time() - start
        artifacts = [p for p in [video_path, audio_path, subtitle_path] if p]

        return ToolResult(
            success=True,
            data={
                "video_path": video_path,
                "audio_path": audio_path,
                "subtitle_path": subtitle_path,
                "videos": [],
                "playlist_count": 0,
                "metadata": metadata,
                "platform": platform,
                "ingest_mode": settings["ingest_mode"],
            },
            artifacts=artifacts,
            duration_seconds=round(elapsed, 2),
        )

    def _execute_playlist(
        self,
        *,
        url: str,
        output_dir: Path,
        dl_format: str,
        max_res: str,
        max_duration: int,
        max_playlist_items: int,
        metadata: dict,
        platform: str,
        ingest_mode: str,
        start: float,
    ) -> ToolResult:
        if dl_format != "video":
            return ToolResult(
                success=False,
                error="Playlist download supports format=video only.",
                data={
                    "metadata": metadata,
                    "platform": platform,
                    "ingest_mode": ingest_mode,
                },
            )

        try:
            downloaded = self._download_playlist_videos(
                url, output_dir, max_res, max_playlist_items
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Playlist download failed: {e}",
                data={
                    "metadata": metadata,
                    "platform": platform,
                    "ingest_mode": ingest_mode,
                },
                duration_seconds=round(time.time() - start, 2),
            )

        videos: list[dict[str, Any]] = []
        artifacts: list[str] = []
        for item in downloaded:
            item_duration = item.get("metadata", {}).get("duration", 0)
            if item_duration and item_duration > max_duration:
                continue
            videos.append(item)
            if item.get("video_path"):
                artifacts.append(item["video_path"])
            if item.get("audio_path"):
                artifacts.append(item["audio_path"])

        if not videos:
            return ToolResult(
                success=False,
                error=(
                    "No playlist items downloaded within duration limits. "
                    f"max_duration_seconds={max_duration}, ingest_mode={ingest_mode}."
                ),
                data={
                    "metadata": metadata,
                    "platform": platform,
                    "ingest_mode": ingest_mode,
                    "videos": [],
                    "playlist_count": 0,
                },
                duration_seconds=round(time.time() - start, 2),
            )

        first = videos[0]
        return ToolResult(
            success=True,
            data={
                "video_path": first.get("video_path"),
                "audio_path": first.get("audio_path"),
                "subtitle_path": None,
                "videos": videos,
                "playlist_count": len(videos),
                "metadata": metadata,
                "platform": platform,
                "ingest_mode": ingest_mode,
            },
            artifacts=artifacts,
            duration_seconds=round(time.time() - start, 2),
        )

    def _download_video(
        self,
        url: str,
        output_dir: Path,
        max_res: str,
        *,
        allow_playlist: bool,
        out_prefix: str = "reference_video",
    ) -> tuple[str | None, str | None]:
        """Download video + extract audio track."""
        import yt_dlp

        height = self._RES_MAP.get(max_res, 720)
        video_out = str(output_dir / f"{out_prefix}.%(ext)s")

        ydl_opts = {
            "format": f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
            "merge_output_format": "mp4",
            "outtmpl": video_out,
            "noplaylist": not allow_playlist,
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        video_path = self._find_downloaded(output_dir, out_prefix, ["mp4", "mkv", "webm"])

        audio_path = None
        if video_path:
            audio_path = self._extract_audio(video_path, output_dir / f"{out_prefix}_audio.wav")

        return video_path, audio_path

    def _download_playlist_videos(
        self,
        url: str,
        output_dir: Path,
        max_res: str,
        max_playlist_items: int,
    ) -> list[dict[str, Any]]:
        """Download up to max_playlist_items videos from a playlist."""
        import yt_dlp

        playlist_dir = output_dir / "playlist"
        playlist_dir.mkdir(parents=True, exist_ok=True)
        height = self._RES_MAP.get(max_res, 720)

        ydl_opts = {
            "format": f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
            "merge_output_format": "mp4",
            "outtmpl": str(playlist_dir / "%(playlist_index)03d_%(id)s.%(ext)s"),
            "noplaylist": False,
            "playlistend": max_playlist_items,
            "quiet": True,
            "no_warnings": True,
        }

        entries: list[dict[str, Any]] = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                return []
            raw_entries = info.get("entries") or [info]
            for entry in raw_entries:
                if entry is None:
                    continue
                normalized = self._normalize_metadata(entry)
                video_id = normalized.get("id") or "unknown"
                playlist_index = normalized.get("playlist_index") or len(entries) + 1
                prefix = f"{int(playlist_index):03d}_{video_id}"
                video_path = self._find_downloaded(
                    playlist_dir, prefix, ["mp4", "mkv", "webm"]
                )
                if not video_path:
                    candidates = sorted(playlist_dir.glob(f"{prefix}*"))
                    video_path = str(candidates[0]) if candidates else None

                audio_path = None
                if video_path:
                    audio_path = self._extract_audio(
                        video_path,
                        playlist_dir / f"{prefix}_audio.wav",
                    )

                entries.append({
                    "video_path": video_path,
                    "audio_path": audio_path,
                    "metadata": normalized,
                    "playlist_index": playlist_index,
                })

        return entries

    def _download_audio(self, url: str, output_dir: Path) -> str | None:
        """Download audio only."""
        import yt_dlp

        audio_out = str(output_dir / "reference_audio.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }],
            "outtmpl": audio_out,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return self._find_downloaded(output_dir, "reference_audio", ["wav", "mp3", "m4a", "opus"])

    def _download_subtitles(self, url: str, output_dir: Path) -> str | None:
        """Download subtitles only."""
        import yt_dlp

        sub_out = str(output_dir / "reference_subs.%(ext)s")
        ydl_opts = {
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "subtitlesformat": "srt",
            "skip_download": True,
            "outtmpl": sub_out,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception:
            pass
        return self._find_downloaded(output_dir, "reference_subs", ["srt", "vtt", "ass"])

    def _find_downloaded(
        self, output_dir: Path, prefix: str, extensions: list[str]
    ) -> str | None:
        """Find a downloaded file by prefix and possible extensions."""
        for ext in extensions:
            candidates = list(output_dir.glob(f"{prefix}*.{ext}"))
            if candidates:
                return str(candidates[0])
        return None
