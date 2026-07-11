#!/usr/bin/env bash
# Clip-factory helper for Theswampdon stream VODs.
# Usage: run-clip-factory.sh <source_video> [--smoke-test]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
VENV="$REPO_ROOT/.venv/bin/python"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

SOURCE="${1:?Usage: run-clip-factory.sh <video_path> [--smoke-test]}"
SMOKE="${2:-}"

if [[ ! -f "$SOURCE" ]]; then
  echo "Source not found: $SOURCE" >&2
  exit 1
fi

BASENAME="$(basename "$SOURCE" .mkv)"
BASENAME="${BASENAME%.mp4}"
DATE_PREFIX="$(echo "$BASENAME" | grep -oE '^[0-9]{4}-[0-9]{2}-[0-9]{2}' || date +%F)"
OUT_DIR="$ROOT/renders/clips/$DATE_PREFIX"
mkdir -p "$OUT_DIR"

echo "==> Theswampdon clip-factory"
echo "    Source:  $SOURCE"
echo "    Output:  $OUT_DIR"

# Step 1: Transcribe
TRANSCRIPT_DIR="$OUT_DIR/transcript"
mkdir -p "$TRANSCRIPT_DIR"
echo "==> Transcribing..."
$VENV -c "
from tools.analysis.transcriber import Transcriber
import json
t = Transcriber()
r = t.execute({'input_path': '$SOURCE', 'output_dir': '$TRANSCRIPT_DIR', 'model_size': 'tiny'})
print(json.dumps({'success': r.success, 'error': r.error}, indent=2))
if not r.success:
    raise SystemExit(1)
"

# Step 2: Detect scenes
echo "==> Detecting scenes..."
SCENES_JSON="$OUT_DIR/scenes.json"
$VENV -c "
from tools.analysis.scene_detect import SceneDetect
import json
s = SceneDetect()
r = s.execute({'input_path': '$SOURCE', 'output_path': '$SCENES_JSON', 'threshold': 27.0})
print(json.dumps({'success': r.success, 'error': r.error, 'scenes': len(r.data.get('scenes', [])) if r.data else 0}, indent=2))
if not r.success:
    raise SystemExit(1)
"

# Step 3: Build clip plan (smoke = 1 clip, full = up to 3)
MAX_CLIPS=1
if [[ "$SMOKE" != "--smoke-test" ]]; then
  MAX_CLIPS=3
fi

PLAN_JSON="$OUT_DIR/clip-plan.json"
$VENV << PY
import json
from pathlib import Path

scenes = json.loads(Path("$SCENES_JSON").read_text())
items = scenes.get("scenes") or scenes.get("data", {}).get("scenes") or []
# Normalize scene list
if isinstance(items, dict):
    items = items.get("scenes", [])

clips = []
for i, sc in enumerate(items[: int($MAX_CLIPS) * 2]):
    start = float(sc.get("start_seconds") or sc.get("start", 0))
    end = float(sc.get("end_seconds") or sc.get("end", start + 30))
    dur = end - start
    if dur < 8 or dur > 120:
        continue
    clips.append({
        "id": f"clip_{len(clips)+1:02d}",
        "start_seconds": round(start, 2),
        "end_seconds": round(min(start + (45 if "$SMOKE" == "--smoke-test" else 60), end), 2),
        "platform": "tiktok_vertical",
        "hook": "GTA mafia RP highlight",
    })
    if len(clips) >= int($MAX_CLIPS):
        break

if not clips:
    # Fallback: first 45s of source
    clips = [{"id": "clip_01", "start_seconds": 0, "end_seconds": 45, "platform": "tiktok_vertical", "hook": "Channel intro"}]

Path("$PLAN_JSON").write_text(json.dumps({"clips": clips}, indent=2))
print(f"Planned {len(clips)} clip(s)")
PY

# Step 4: Render clips with FFmpeg
echo "==> Rendering clips..."
$VENV << PY
import json, subprocess
from pathlib import Path

plan = json.loads(Path("$PLAN_JSON").read_text())
source = "$SOURCE"
out_dir = Path("$OUT_DIR")

for clip in plan["clips"]:
    cid = clip["id"]
    start = clip["start_seconds"]
    end = clip["end_seconds"]
    dur = end - start
    out_16 = out_dir / f"{cid}_yt.mp4"
    out_9 = out_dir / f"{cid}_shorts.mp4"

    # 16:9 extract
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start), "-i", source, "-t", str(dur),
        "-c:v", "libx264", "-crf", "23", "-c:a", "aac", "-movflags", "+faststart",
        str(out_16),
    ], check=True)

    # 9:16 crop for Shorts/TikTok
    subprocess.run([
        "ffmpeg", "-y", "-i", str(out_16),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264", "-crf", "23", "-c:a", "aac", "-movflags", "+faststart",
        str(out_9),
    ], check=True)
    print(f"  ✓ {cid}: {start}s–{end}s → {out_9.name}, {out_16.name}")
PY

# Step 5: Publish metadata stub
cat > "$OUT_DIR/publish-pack.md" << EOF
# Publish pack — $DATE_PREFIX

Source: \`$BASENAME\`

## Clips

$(ls "$OUT_DIR"/*_shorts.mp4 2>/dev/null | while read f; do echo "- **$(basename "$f")** — TikTok / Shorts"; done)

## Suggested title
Vince Genovese GTA RP highlight | Theswampdon

## Hashtags
#GTARP #MafiaRP #GTA5 #Roleplay #Brooklyn #FiveM

## CTA
Full RP live on Twitch & Kick @Theswampdon
EOF

echo "==> Done. Clips + publish-pack.md in $OUT_DIR"
