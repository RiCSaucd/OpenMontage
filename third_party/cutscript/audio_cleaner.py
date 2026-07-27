"""
Audio noise reduction (from CutScript, MIT).

Uses DeepFilterNet when installed; falls back to FFmpeg anlmdn filter.
Upstream: https://github.com/DataAnts-AI/CutScript/blob/main/backend/services/audio_cleaner.py
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from df.enhance import enhance, init_df, load_audio, save_audio

    DEEPFILTER_AVAILABLE = True
except ImportError:
    DEEPFILTER_AVAILABLE = False

_df_model = None
_df_state = None


def _init_deepfilter():
    global _df_model, _df_state
    if _df_model is None:
        logger.info("Initializing DeepFilterNet model")
        _df_model, _df_state, _ = init_df()
    return _df_model, _df_state


def clean_audio(input_path: str, output_path: str = "") -> str:
    """Apply noise reduction. Returns path to cleaned audio."""
    input_path_obj = Path(input_path)
    if not output_path:
        output_path = str(input_path_obj.with_stem(input_path_obj.stem + "_clean"))

    if DEEPFILTER_AVAILABLE:
        return _clean_with_deepfilter(str(input_path_obj), output_path)
    return _clean_with_ffmpeg(str(input_path_obj), output_path)


def _clean_with_deepfilter(input_path: str, output_path: str) -> str:
    model, state = _init_deepfilter()
    audio, _info = load_audio(input_path, sr=state.sr())
    enhanced = enhance(model, state, audio)
    save_audio(output_path, enhanced, sr=state.sr())
    logger.info("DeepFilterNet cleaned audio saved to %s", output_path)
    return output_path


def _clean_with_ffmpeg(input_path: str, output_path: str) -> str:
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af", "anlmdn=s=7:p=0.002:r=0.002:m=15",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio cleaning failed: {result.stderr[-300:]}")
    logger.info("FFmpeg cleaned audio saved to %s", output_path)
    return output_path


def is_deepfilter_available() -> bool:
    return DEEPFILTER_AVAILABLE
