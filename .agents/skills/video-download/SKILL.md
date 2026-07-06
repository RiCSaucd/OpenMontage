---
name: video-download
description: |
  Download video and audio from YouTube and 1000+ sites using yt-dlp. No API keys needed.
  Use when: (1) Downloading a video from YouTube or other sites, (2) Extracting audio from a video URL,
  (3) Downloading subtitles/captions from a video, (4) Getting video metadata without downloading.
---

# video-download

Download video and audio from URLs using yt-dlp directly. No wrapper scripts needed.

## Prerequisites

- **yt-dlp**: `brew install yt-dlp` or `pip install yt-dlp`
- **ffmpeg**: `brew install ffmpeg` or `apt install ffmpeg` (required for merging video+audio streams)

Update yt-dlp periodically to keep up with site changes: `yt-dlp -U` or `pip install -U yt-dlp`.

## Commands

### Download best quality

```bash
yt-dlp "URL" -o "%(title)s.%(ext)s" --merge-output-format mp4
```

### Download specific resolution

```bash
# 720p
yt-dlp "URL" -f "bestvideo[height<=720]+bestaudio/best[height<=720]" --merge-output-format mp4

# 1080p
yt-dlp "URL" -f "bestvideo[height<=1080]+bestaudio/best[height<=1080]" --merge-output-format mp4
```

### Audio only

```bash
yt-dlp "URL" -x --audio-format mp3 --audio-quality 0
```

### Download subtitles

```bash
# Download video with English subtitles
yt-dlp "URL" --write-subs --sub-langs en --merge-output-format mp4

# Download video with multiple subtitle languages
yt-dlp "URL" --write-subs --sub-langs "en,es,fr" --merge-output-format mp4

# Download only subtitles (no video)
yt-dlp "URL" --write-subs --sub-langs en --skip-download
```

### Get metadata (no download)

```bash
yt-dlp "URL" --dump-json --no-download
```

### List available formats

```bash
yt-dlp "URL" -F
```

### Specify output directory

```bash
yt-dlp "URL" -o "./downloads/%(title)s.%(ext)s" --merge-output-format mp4
```

## Quality Presets

| Quality | Format flag |
|---------|-------------|
| Best | `-f "bestvideo+bestaudio/best"` (default) |
| 1080p | `-f "bestvideo[height<=1080]+bestaudio/best[height<=1080]"` |
| 720p | `-f "bestvideo[height<=720]+bestaudio/best[height<=720]"` |
| 480p | `-f "bestvideo[height<=480]+bestaudio/best[height<=480]"` |
| Worst | `-f "worstvideo+worstaudio/worst"` |

## Output Template Variables

Common variables for `-o` templates:

| Variable | Description |
|----------|-------------|
| `%(title)s` | Video title |
| `%(ext)s` | File extension |
| `%(id)s` | Video ID |
| `%(uploader)s` | Channel/uploader name |
| `%(upload_date)s` | Upload date (YYYYMMDD) |
| `%(duration)s` | Duration in seconds |
| `%(resolution)s` | Video resolution |

## Tips

- Always use `--merge-output-format mp4` to avoid ending up with `.webm` or `.mkv` files.
- Use `--no-download` with `--dump-json` for metadata-only queries -- no files written to disk.
- If a download fails with HTTP errors, update yt-dlp first (`yt-dlp -U`).
- Use `-f "bestvideo[height<=720]+bestaudio"` to save bandwidth when full resolution is not needed.
- yt-dlp automatically handles rate limiting and retries.
- The `--dump-json` output includes `title`, `duration`, `uploader`, `view_count`, `description`, `formats`, `subtitles`, and much more.

## OpenMontage `video_downloader` tool

Use the `video_downloader` tool (not raw shell) inside pipelines. Key parameters:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `ingest_mode` | `reference` | `reference` = 720p / 10 min cap for analysis. `production` = 1080p / 60 min for clip-factory ingest. |
| `allow_playlist` | `false` | When true, download multiple items from a playlist URL |
| `max_playlist_items` | `5` | Cap playlist downloads (max 25) |
| `format` | `video` | `video`, `audio_only`, `subtitles_only`, or `metadata_only` |

**Reference analysis (default):**

```python
video_downloader.execute({
    "url": "https://youtube.com/watch?v=...",
    "output_dir": "projects/my-project/assets/reference",
    "format": "video",
    "ingest_mode": "reference",
})
```

**Production ingest for clip-factory:**

```python
video_downloader.execute({
    "url": "https://youtube.com/playlist?list=...",
    "output_dir": "projects/my-project/assets/source",
    "format": "video",
    "ingest_mode": "production",
    "allow_playlist": True,
    "max_playlist_items": 10,
})
```

Playlist responses include a `videos` array (per-item paths + metadata) and set `video_path` to the first item for backward compatibility.

## Troubleshooting

- **"yt-dlp: command not found"**: Install it (`pip install yt-dlp`) and ensure your PATH includes pip's bin directory.
- **"ffmpeg: command not found"**: Install ffmpeg. Without it, downloads fail when video and audio are separate streams (common on YouTube for HD).
- **Downloads fail or return errors**: Run `yt-dlp -U` to update. Sites change frequently and yt-dlp ships fixes regularly.
