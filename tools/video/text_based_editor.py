"""Descript-style text-based video editor (CutScript OSS integration).

Edit video by editing the transcript: remove words by index, compute keep
segments, and export via CutScript's FFmpeg engine (stream-copy or re-encode).
Optional Studio Sound noise reduction via DeepFilterNet or FFmpeg fallback.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from lib.text_edit.segments import (
    compute_keep_segments,
    detect_filler_word_indices,
    merge_deleted_indices,
)
from third_party.cutscript import audio_cleaner, video_editor
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


class TextBasedEditor(BaseTool):
    name = "text_based_editor"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "video_post"
    provider = "cutscript"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["cmd:ffmpeg"]
    install_instructions = (
        "Requires FFmpeg (usually already installed for OpenMontage).\n"
        "Optional Studio Sound (DeepFilterNet): pip install deepfilternet\n"
        "Powered by CutScript OSS (MIT): https://github.com/DataAnts-AI/CutScript"
    )
    agent_skills = ["text-based-editing", "ffmpeg", "video-toolkit"]

    capabilities = [
        "text_based_cut",
        "transcript_driven_export",
        "filler_word_detection",
        "studio_sound",
        "stream_copy_export",
    ]

    best_for = [
        "Descript-style cuts from word-level transcript timestamps",
        "removing filler words at word boundaries",
        "fast stream-copy export of kept speech segments",
        "talking-head and podcast clip cleanup",
    ]

    not_good_for = [
        "generating new visuals or b-roll",
        "editing without a word-level transcript",
    ]

    input_schema = {
        "type": "object",
        "required": ["operation"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "compute_segments",
                    "detect_fillers",
                    "export",
                    "studio_sound",
                ],
            },
            "words": {
                "type": "array",
                "description": "Word-level transcript from transcriber",
                "items": {
                    "type": "object",
                    "properties": {
                        "word": {"type": "string"},
                        "start": {"type": "number"},
                        "end": {"type": "number"},
                    },
                },
            },
            "deleted_indices": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Transcript word indices to remove",
            },
            "auto_remove_fillers": {
                "type": "boolean",
                "default": False,
                "description": "When true, detect and remove common filler words",
            },
            "extra_fillers": {
                "type": "array",
                "items": {"type": "string"},
            },
            "keep_segments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "number"},
                        "end": {"type": "number"},
                    },
                },
            },
            "input_path": {"type": "string"},
            "output_path": {"type": "string"},
            "export_mode": {
                "type": "string",
                "enum": ["fast", "quality"],
                "default": "fast",
                "description": "fast=stream copy when possible; quality=re-encode",
            },
            "resolution": {
                "type": "string",
                "enum": ["720p", "1080p", "4k"],
                "default": "1080p",
            },
            "enhance_audio": {
                "type": "boolean",
                "default": False,
                "description": "Apply Studio Sound after export",
            },
            "gap_tolerance_seconds": {
                "type": "number",
                "default": 0.08,
            },
        },
    }

    output_schema = {
        "type": "object",
        "properties": {
            "keep_segments": {"type": "array"},
            "deleted_indices": {"type": "array"},
            "output_path": {"type": "string"},
            "filler_indices": {"type": "array"},
            "deepfilter_available": {"type": "boolean"},
        },
    }

    resource_profile = ResourceProfile(
        cpu_cores=2, ram_mb=1024, vram_mb=0, disk_mb=2000, network_required=False,
    )
    side_effects = ["writes edited video or audio files"]
    user_visible_verification = [
        "Play exported video and verify cuts land on word boundaries",
        "Check audio for clicks or pops at cut points",
    ]

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        operation = inputs["operation"]
        start = time.time()

        try:
            if operation == "compute_segments":
                result = self._compute_segments(inputs)
            elif operation == "detect_fillers":
                result = self._detect_fillers(inputs)
            elif operation == "export":
                result = self._export(inputs)
            elif operation == "studio_sound":
                result = self._studio_sound(inputs)
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")
        except Exception as exc:
            return ToolResult(
                success=False,
                error=str(exc),
                duration_seconds=round(time.time() - start, 2),
            )

        result.duration_seconds = round(time.time() - start, 2)
        return result

    def _resolve_deletions(self, inputs: dict[str, Any]) -> list[int]:
        deleted = list(inputs.get("deleted_indices") or [])
        if inputs.get("auto_remove_fillers") and inputs.get("words"):
            fillers = detect_filler_word_indices(
                inputs["words"],
                extra_fillers=inputs.get("extra_fillers"),
            )
            deleted = merge_deleted_indices(deleted, fillers)
        return deleted

    def _compute_segments(self, inputs: dict[str, Any]) -> ToolResult:
        words = inputs.get("words") or []
        if not words:
            return ToolResult(success=False, error="words is required for compute_segments")

        deleted = self._resolve_deletions(inputs)
        segments = compute_keep_segments(
            words,
            deleted,
            gap_tolerance_seconds=float(inputs.get("gap_tolerance_seconds", 0.08)),
        )

        return ToolResult(
            success=True,
            data={
                "keep_segments": segments,
                "deleted_indices": deleted,
                "segment_count": len(segments),
            },
        )

    def _detect_fillers(self, inputs: dict[str, Any]) -> ToolResult:
        words = inputs.get("words") or []
        if not words:
            return ToolResult(success=False, error="words is required for detect_fillers")

        indices = detect_filler_word_indices(
            words,
            extra_fillers=inputs.get("extra_fillers"),
        )
        return ToolResult(
            success=True,
            data={
                "filler_indices": indices,
                "filler_count": len(indices),
            },
        )

    def _export(self, inputs: dict[str, Any]) -> ToolResult:
        input_path = Path(inputs.get("input_path", ""))
        output_path = Path(inputs.get("output_path", ""))
        if not input_path.exists():
            return ToolResult(success=False, error=f"Input not found: {input_path}")
        if not output_path:
            return ToolResult(success=False, error="output_path is required for export")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        segments = inputs.get("keep_segments")
        if not segments:
            words = inputs.get("words") or []
            if not words:
                return ToolResult(
                    success=False,
                    error="Provide keep_segments or words (+ optional deleted_indices)",
                )
            deleted = self._resolve_deletions(inputs)
            segments = compute_keep_segments(
                words,
                deleted,
                gap_tolerance_seconds=float(inputs.get("gap_tolerance_seconds", 0.08)),
            )

        if not segments:
            return ToolResult(success=False, error="No segments to export after cuts")

        export_mode = inputs.get("export_mode", "fast")
        resolution = inputs.get("resolution", "1080p")

        if export_mode == "fast" and len(segments) == 1:
            video_editor.export_stream_copy(
                str(input_path), str(output_path), segments,
            )
        else:
            video_editor.export_reencode(
                str(input_path),
                str(output_path),
                segments,
                resolution=resolution,
            )

        if inputs.get("enhance_audio"):
            self._mux_cleaned_audio(str(output_path), str(output_path))

        return ToolResult(
            success=True,
            data={
                "output_path": str(output_path),
                "keep_segments": segments,
                "segment_count": len(segments),
                "export_mode": export_mode,
            },
            artifacts=[str(output_path)],
        )

    def _studio_sound(self, inputs: dict[str, Any]) -> ToolResult:
        input_path = Path(inputs.get("input_path", ""))
        output_path = Path(inputs.get("output_path", ""))
        if not input_path.exists():
            return ToolResult(success=False, error=f"Input not found: {input_path}")

        cleaned = audio_cleaner.clean_audio(
            str(input_path),
            str(output_path) if output_path else "",
        )

        return ToolResult(
            success=True,
            data={
                "output_path": cleaned,
                "deepfilter_available": audio_cleaner.is_deepfilter_available(),
            },
            artifacts=[cleaned],
        )

    def _mux_cleaned_audio(self, video_path: str, output_path: str) -> None:
        """Replace video audio with Studio Sound cleaned track."""
        tmp_audio = str(Path(video_path).with_suffix(".studio.wav"))
        audio_cleaner.clean_audio(video_path, tmp_audio)
        tmp_out = str(Path(output_path).with_suffix(".studio_tmp.mp4"))

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", tmp_audio,
            "-c:v", "copy",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            tmp_out,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Audio mux failed: {result.stderr[-300:]}")

        Path(tmp_out).replace(output_path)
        Path(tmp_audio).unlink(missing_ok=True)
