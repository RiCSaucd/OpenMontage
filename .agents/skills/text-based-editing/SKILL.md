---
name: text-based-editing
description: |
  Descript-style text-based video editing using word-level transcripts and CutScript OSS.
  Use when: (1) Cutting video by deleting words from a transcript, (2) Removing filler words
  (um, uh, like), (3) Exporting kept speech segments with stream-copy or re-encode,
  (4) Applying Studio Sound noise reduction on talking-head footage.
---

# Text-Based Editing (Descript-style)

OpenMontage integrates **CutScript** (MIT, Descript-like open source) for transcript-driven cuts.
Official Descript Inc. libraries (`descript-audio-codec`, `audiotools`) are separate — see
https://github.com/descriptinc.

## Tool: `text_based_editor`

### Workflow

1. **Transcribe** with `transcriber` → `word_timestamps`
2. **Plan cuts** — agent or user picks `deleted_indices`, or set `auto_remove_fillers: true`
3. **Compute segments** (optional) — `operation: compute_segments`
4. **Export** — `operation: export` with `words` + `deleted_indices` or precomputed `keep_segments`
5. **Studio Sound** (optional) — `enhance_audio: true` on export, or `operation: studio_sound`

### compute_segments

```python
text_based_editor.execute({
    "operation": "compute_segments",
    "words": transcript["word_timestamps"],
    "deleted_indices": [12, 13, 45],
    "auto_remove_fillers": True,
})
```

Returns `keep_segments: [{start, end}, ...]` for FFmpeg.

### export (fast stream-copy)

```python
text_based_editor.execute({
    "operation": "export",
    "input_path": "projects/my-talk/assets/source.mp4",
    "output_path": "projects/my-talk/assets/edited.mp4",
    "words": transcript["word_timestamps"],
    "auto_remove_fillers": True,
    "export_mode": "fast",
    "enhance_audio": False,
})
```

Use `export_mode: "quality"` when multiple segments need concat with re-encode, or resolution changes.

### detect_fillers

```python
text_based_editor.execute({
    "operation": "detect_fillers",
    "words": transcript["word_timestamps"],
})
```

Returns `filler_indices` for agent review before cutting.

### studio_sound

```python
text_based_editor.execute({
    "operation": "studio_sound",
    "input_path": "projects/my-talk/assets/source.mp4",
    "output_path": "projects/my-talk/assets/clean.wav",
})
```

Uses DeepFilterNet when `pip install deepfilternet` is available; otherwise FFmpeg `anlmdn`.

## Pipelines

Best fit: `talking-head`, `clip-factory`, `podcast-repurpose`.

Pair with:
- `transcriber` — word timestamps (required)
- `silence_cutter` — dead air removal (complementary)
- `video_trimmer` — manual segment ops
- `remotion_caption_burn` — captions after edit

## Quality rules

- Always cut on **word boundaries** — never mid-word
- Review filler auto-detection before batch export
- Prefer `fast` export for single continuous kept segment
- Use `quality` when stream-copy fails or multiple segments are concatenated
- Keep natural breath pauses (0.3–0.8s) — do not delete every short gap

## Attribution

FFmpeg export engine vendored from [CutScript](https://github.com/DataAnts-AI/CutScript) (MIT).
See `third_party/cutscript/NOTICE.md`.
