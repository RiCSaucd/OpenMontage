# Servers

Optional HTTP / MCP entrypoints that sit **on top of** OpenMontage pipelines.
They do not replace Rule Zero — they create projects and hand work to an agent
via `AGENT_INSTRUCTION.md`.

## Nexus OpenMontage (`nexus_openmontage.py`)

Dual-mode server for **Nexus AI Media** true-crime Shorts:

| Mode | Command |
|------|---------|
| HTTP | `.venv/bin/python -m servers.nexus_openmontage --mode http --port 8765` |
| MCP (stdio) | `.venv/bin/python -m servers.nexus_openmontage --mode mcp` |

### Pipeline

Uses `pipeline_defs/nexus-true-crime-short.yaml` with brand skills:

- `skills/brand/respected-historian-tone.md`
- `skills/brand/mafia-true-crime-guidelines.md`

### Environment

| Variable | Purpose |
|----------|---------|
| `NEXUS_API_KEY` | Optional. When set, HTTP routes require `X-API-Key` |
| `OPENMONTAGE_ROOT` | Repo root (default: auto-detected) |
| `OPENMONTAGE_PROJECTS_DIR` | Projects directory (default: `projects/`) |
| `CAPCUT_DRAFTS_PATH` | Optional CapCut drafts folder hint |
| `NEXUS_DRIVE_FOLDER_ID` | Optional Google Drive folder for distribution |
| `VIDIQ_API_KEY` | Optional. Bearer token for the **vidIQ** Cursor MCP server (YouTube/Shorts packaging). Never commit the real key. |

MCP tools need the optional SDK: `pip install 'mcp[cli]'`.

### vidIQ packaging (YouTube / Shorts)

vidIQ does **not** make footage more realistic. When the MCP server is connected, run keyword / title / competitor packaging **before** CapCut or Drive hand-off (`compose-director` writes `distribution/vidiq_packaging.json` + `distribution/publish_copy.md`).

Cloud agents cannot register desktop MCP servers. On your machine, in **Cursor Settings → MCP**, add (use env interpolation — do not paste the key into git):

```json
{
  "mcpServers": {
    "vidIQ": {
      "url": "https://mcp.vidiq.com/mcp",
      "headers": {
        "Authorization": "Bearer ${env:VIDIQ_API_KEY}"
      }
    }
  }
}
```

Repo template: `.cursor/mcp.json.example`. Set `VIDIQ_API_KEY` in gitignored `.env`. If MCP is disconnected, still write the packaging files with `mcp_status: unavailable` and brand-safe fallback copy — do not invent vidIQ scores.

### HTTP endpoints

- `GET /health`
- `POST /produce_mafia_short`
- `GET /status/{project_id}`
- `GET /projects`
- `POST /approve/{project_id}`
- `DELETE /projects/{project_id}?confirm=true`

### Flow

1. Server creates a canonical OpenMontage project (`init_project`).
2. Writes `AGENT_INSTRUCTION.md` + research scaffold.
3. Status → `awaiting_approval` at `proposal`.
4. An OpenMontage agent (Cursor / Claude Code) executes the pipeline stage-by-stage.
5. Approvals can be recorded via HTTP/MCP; completion writes `distribution/distribution_manifest.json`.
