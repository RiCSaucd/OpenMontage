# Piper 1.4.2 — `--sentence-silence` corruption quirk

## Symptom

Multi-sentence text synthesized through the `piper` CLI (v1.4.2, `piper-tts` from PyPI)
with `--sentence-silence 0.45` produces a WAV where **everything after the first
sentence is corrupted static** ("Grrrr"-like noise). Duration looks correct,
silencedetect shows continuous energy, but transcription only recovers sentence 1.

## Reproduction (verified 2026-07-05, en_US-lessac-medium, 22050 Hz)

| `--sentence-silence` | Result |
|---|---|
| (flag omitted) | clean |
| 0.3 | clean |
| 0.35 | clean |
| 0.4 | clean |
| 0.45 | **corrupted after sentence 1** (deterministic, reproduced twice) |

```bash
echo "First sentence here. Second sentence here." | \
  piper --model en_US-lessac-medium --sentence-silence 0.45 --output_file out.wav
# → second sentence is static
```

## Detection

Transcribe every generated narration file (faster-whisper, `vad_filter=False`)
and compare word counts against the source text. Word-count mismatch on a
multi-sentence section = corrupted tail. Do NOT rely on duration or
silencedetect — both look normal on corrupted files.

## Workaround

Use `sentence_silence <= 0.4` with `tools/audio/piper_tts.py`, and always run the
transcription check after batch generation. If a longer inter-sentence pause is
needed, synthesize per-sentence and assemble with ffmpeg `adelay`/`amix`.

## Root cause (suspected, unconfirmed)

Likely a sample-alignment bug in piper 1.4.x when inserting the silence buffer;
specific to certain duration values whose sample count interacts badly with the
writer. Not investigated past the empirical table above.

Source: discovered during the why-the-sky-is-blue production run; see
decision_log.json d-010.
