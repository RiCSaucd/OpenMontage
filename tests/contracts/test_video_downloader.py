"""Contract tests for video_downloader source ingest tool."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.analysis.video_downloader import VideoDownloader
from tools.base_tool import BaseTool
from tools.tool_registry import ToolRegistry


class TestVideoDownloaderContract:
    def test_identity(self):
        tool = VideoDownloader()
        info = tool.get_info()
        assert info["name"] == "video_downloader"
        assert info["capability"] == "source_ingest"
        assert info["provider"] == "yt-dlp"
        assert info["version"] == "0.2.0"

    def test_is_base_tool(self):
        assert issubclass(VideoDownloader, BaseTool)

    def test_capabilities_include_playlist(self):
        tool = VideoDownloader()
        assert "download_playlist" in tool.capabilities

    def test_input_schema_has_ingest_mode(self):
        tool = VideoDownloader()
        props = tool.input_schema["properties"]
        assert "ingest_mode" in props
        assert props["ingest_mode"]["enum"] == ["reference", "production"]
        assert "allow_playlist" in props
        assert "max_playlist_items" in props

    def test_registry_discovers_tool(self):
        import tools.analysis.video_downloader as vd_module

        reg = ToolRegistry()
        reg.register_module(vd_module)
        assert reg.get("video_downloader") is not None

    def test_resolve_reference_defaults(self):
        tool = VideoDownloader()
        settings = tool._resolve_ingest_settings({})
        assert settings["ingest_mode"] == "reference"
        assert settings["max_resolution"] == "720p"
        assert settings["max_duration_seconds"] == 600
        assert settings["allow_playlist"] is False

    def test_resolve_production_defaults(self):
        tool = VideoDownloader()
        settings = tool._resolve_ingest_settings({"ingest_mode": "production"})
        assert settings["ingest_mode"] == "production"
        assert settings["max_resolution"] == "1080p"
        assert settings["max_duration_seconds"] == 3600

    def test_resolve_explicit_overrides(self):
        tool = VideoDownloader()
        settings = tool._resolve_ingest_settings({
            "ingest_mode": "production",
            "max_resolution": "720p",
            "max_duration_seconds": 120,
            "allow_playlist": True,
            "max_playlist_items": 99,
        })
        assert settings["max_resolution"] == "720p"
        assert settings["max_duration_seconds"] == 120
        assert settings["allow_playlist"] is True
        assert settings["max_playlist_items"] == 25

    def test_rejects_invalid_max_playlist_items(self):
        tool = VideoDownloader()
        result = tool.execute({
            "url": "https://example.com/watch?v=abc",
            "output_dir": "/unused",
            "max_playlist_items": "not-a-number",
        })
        assert result.success is False
        assert "max_playlist_items must be an integer" in (result.error or "")

    def test_metadata_only_skips_download(self, tmp_path):
        tool = VideoDownloader()
        with patch.object(tool, "_extract_metadata", return_value={"title": "T", "duration": 30}):
            result = tool.execute({
                "url": "https://example.com/watch?v=abc",
                "output_dir": str(tmp_path),
                "format": "metadata_only",
            })
        assert result.success is True
        assert result.data["video_path"] is None
        assert result.data["ingest_mode"] == "reference"

    def test_rejects_overlong_video(self, tmp_path):
        tool = VideoDownloader()
        with patch.object(
            tool,
            "_extract_metadata",
            return_value={"title": "Long", "duration": 9999},
        ):
            result = tool.execute({
                "url": "https://example.com/watch?v=abc",
                "output_dir": str(tmp_path),
                "format": "video",
                "ingest_mode": "reference",
            })
        assert result.success is False
        assert "exceeds max_duration_seconds" in (result.error or "")
        assert "ingest_mode=production" in (result.error or "")

    def test_rejects_overlong_video_in_production_mode(self, tmp_path):
        tool = VideoDownloader()
        with patch.object(
            tool,
            "_extract_metadata",
            return_value={"title": "Long", "duration": 9999},
        ):
            result = tool.execute({
                "url": "https://example.com/watch?v=abc",
                "output_dir": str(tmp_path),
                "format": "video",
                "ingest_mode": "production",
            })
        assert result.success is False
        assert "exceeds max_duration_seconds" in (result.error or "")
        assert "Increase max_duration_seconds to allow longer videos" in (result.error or "")
        assert "switch to ingest_mode=production" not in (result.error or "")

    def test_playlist_mode_requires_video_format(self, tmp_path):
        tool = VideoDownloader()
        with patch.object(
            tool,
            "_extract_metadata",
            return_value={"title": "Playlist", "is_playlist": True, "playlist_count": 3},
        ):
            result = tool.execute({
                "url": "https://example.com/playlist?list=xyz",
                "output_dir": str(tmp_path),
                "format": "audio_only",
                "allow_playlist": True,
            })
        assert result.success is False
        assert "Playlist download supports format=video only" in (result.error or "")

    def test_playlist_download_returns_multiple_videos(self, tmp_path):
        tool = VideoDownloader()
        playlist_meta = {
            "title": "Playlist",
            "is_playlist": True,
            "playlist_count": 2,
        }
        fake_entries = [
            {
                "video_path": str(tmp_path / "playlist" / "001_a.mp4"),
                "audio_path": None,
                "metadata": {"title": "A", "duration": 60, "id": "a", "playlist_index": 1},
                "playlist_index": 1,
            },
            {
                "video_path": str(tmp_path / "playlist" / "002_b.mp4"),
                "audio_path": None,
                "metadata": {"title": "B", "duration": 90, "id": "b", "playlist_index": 2},
                "playlist_index": 2,
            },
        ]
        with (
            patch.object(tool, "_extract_metadata", return_value=playlist_meta),
            patch.object(tool, "_download_playlist_videos", return_value=fake_entries),
        ):
            result = tool.execute({
                "url": "https://example.com/playlist?list=xyz",
                "output_dir": str(tmp_path),
                "format": "video",
                "allow_playlist": True,
                "max_playlist_items": 2,
            })
        assert result.success is True
        assert result.data["playlist_count"] == 2
        assert len(result.data["videos"]) == 2
        assert result.data["video_path"] == fake_entries[0]["video_path"]

    def test_cost_is_free(self):
        tool = VideoDownloader()
        assert tool.estimate_cost({"url": "https://example.com"}) == 0.0
