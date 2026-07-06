"""Contract tests for text_based_editor (CutScript OSS integration)."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.text_edit.segments import (
    compute_keep_segments,
    detect_filler_word_indices,
    merge_deleted_indices,
)
from tools.base_tool import BaseTool
from tools.tool_registry import ToolRegistry
from tools.video.text_based_editor import TextBasedEditor


WORDS = [
    {"word": "Hello", "start": 0.0, "end": 0.4},
    {"word": "um", "start": 0.4, "end": 0.6},
    {"word": "world", "start": 0.6, "end": 1.0},
    {"word": "today", "start": 1.2, "end": 1.6},
]


class TestTextEditSegments:
    def test_compute_keep_segments_merges_words(self):
        segments = compute_keep_segments(WORDS, deleted_indices=[1])
        assert len(segments) == 3
        assert segments[0] == {"start": 0.0, "end": 0.4}
        assert segments[1] == {"start": 0.6, "end": 1.0}
        assert segments[2] == {"start": 1.2, "end": 1.6}

    def test_detect_filler_word_indices(self):
        indices = detect_filler_word_indices(WORDS)
        assert indices == [1]

    def test_merge_deleted_indices(self):
        merged = merge_deleted_indices([1, 2], [2, 3])
        assert merged == [1, 2, 3]


class TestTextBasedEditorContract:
    def test_identity(self):
        tool = TextBasedEditor()
        info = tool.get_info()
        assert info["name"] == "text_based_editor"
        assert info["provider"] == "cutscript"
        assert info["capability"] == "video_post"

    def test_is_base_tool(self):
        assert issubclass(TextBasedEditor, BaseTool)

    def test_registry_discovers_tool(self):
        reg = ToolRegistry()
        reg.discover()
        assert "text_based_editor" in reg._tools

    def test_compute_segments_operation(self):
        tool = TextBasedEditor()
        result = tool.execute({
            "operation": "compute_segments",
            "words": WORDS,
            "deleted_indices": [1],
        })
        assert result.success is True
        assert result.data["segment_count"] == 3

    def test_detect_fillers_operation(self):
        tool = TextBasedEditor()
        result = tool.execute({
            "operation": "detect_fillers",
            "words": WORDS,
        })
        assert result.success is True
        assert result.data["filler_indices"] == [1]

    def test_export_requires_input(self):
        tool = TextBasedEditor()
        result = tool.execute({
            "operation": "export",
            "output_path": "/tmp/out.mp4",
            "words": WORDS,
        })
        assert result.success is False

    def test_export_with_mock(self, tmp_path):
        tool = TextBasedEditor()
        src = tmp_path / "src.mp4"
        src.write_bytes(b"not real video")
        out = tmp_path / "out.mp4"

        with patch("tools.video.text_based_editor.video_editor.export_reencode") as mock_export:
            mock_export.return_value = str(out)
            result = tool.execute({
                "operation": "export",
                "input_path": str(src),
                "output_path": str(out),
                "words": WORDS,
                "deleted_indices": [1],
                "export_mode": "quality",
            })

        assert result.success is True
        mock_export.assert_called_once()
        assert result.data["segment_count"] == 3

    def test_cost_is_free(self):
        tool = TextBasedEditor()
        assert tool.estimate_cost({"operation": "export"}) == 0.0
