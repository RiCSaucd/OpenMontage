"""Text-based edit segment computation for Descript-style cuts."""

from __future__ import annotations

import re
from typing import Any

DEFAULT_FILLER_WORDS = frozenset({
    "um", "uh", "uhh", "umm", "er", "ah", "like", "you know", "sort of", "kind of",
})

_FILLER_PATTERN = re.compile(
    r"^\s*(um+|uh+|er+|ah+|like|you know|sort of|kind of)\s*$",
    re.IGNORECASE,
)


def normalize_word(word: dict[str, Any]) -> dict[str, Any]:
    """Ensure word dict has start/end/word keys."""
    return {
        "word": str(word.get("word", word.get("text", ""))).strip(),
        "start": float(word["start"]),
        "end": float(word["end"]),
        "confidence": float(word.get("confidence", word.get("score", 1.0))),
    }


def compute_keep_segments(
    words: list[dict[str, Any]],
    deleted_indices: list[int] | None = None,
    *,
    gap_tolerance_seconds: float = 0.08,
) -> list[dict[str, float]]:
    """
    Convert word-level transcript + deleted indices into FFmpeg keep segments.

    Merges adjacent kept words when gaps are smaller than gap_tolerance_seconds.
    """
    if not words:
        return []

    normalized = [normalize_word(w) for w in words]
    deleted = set(deleted_indices or [])
    kept = [w for i, w in enumerate(normalized) if i not in deleted]
    if not kept:
        return []

    segments: list[dict[str, float]] = []
    seg_start = kept[0]["start"]
    seg_end = kept[0]["end"]

    for word in kept[1:]:
        if word["start"] <= seg_end + gap_tolerance_seconds:
            seg_end = max(seg_end, word["end"])
        else:
            segments.append({"start": seg_start, "end": seg_end})
            seg_start = word["start"]
            seg_end = word["end"]

    segments.append({"start": seg_start, "end": seg_end})
    return segments


def detect_filler_word_indices(
    words: list[dict[str, Any]],
    *,
    extra_fillers: list[str] | None = None,
) -> list[int]:
    """Return indices of common filler words for automated Descript-style cleanup."""
    fillers = set(DEFAULT_FILLER_WORDS)
    if extra_fillers:
        fillers.update(f.lower().strip() for f in extra_fillers)

    indices: list[int] = []
    for i, raw in enumerate(words):
        word = normalize_word(raw)
        text = word["word"].lower().strip(".,!?;:\"'")
        if text in fillers or _FILLER_PATTERN.match(word["word"]):
            indices.append(i)
    return indices


def merge_deleted_indices(*groups: list[int]) -> list[int]:
    """Merge multiple deletion index lists, preserving order."""
    seen: set[int] = set()
    merged: list[int] = []
    for group in groups:
        for idx in group:
            if idx not in seen:
                seen.add(idx)
                merged.append(idx)
    return merged
