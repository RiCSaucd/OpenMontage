# OpenMontage

**MANDATORY: Read `AGENT_GUIDE.md` before responding to ANY user message.**

Do not act on the user's request until you have read AGENT_GUIDE.md.
It contains routing rules that determine your first action based on what the user asked.
Skipping it WILL cause you to take the wrong action.

All product, routing, and production instructions are in AGENT_GUIDE.md — read it first.
The only instructions in this file itself are the durable Cursor Cloud environment/setup
notes in the section below; they do not replace AGENT_GUIDE.md.

## Cursor Cloud specific instructions

Environment setup (deps) is handled automatically by the startup update script; the notes
below are the non-obvious, durable facts for working in this repo. Standard commands live in
the `Makefile` and `README.md` — use those rather than reinventing them.

- **Two runtimes.** This is a Python (agent tools + persistence) project with a Node.js
  Remotion composition engine under `remotion-composer/`. FFmpeg, Node ≥ 22, and npx are all
  present. Piper (free offline TTS) is installed.
- **Python lives in a venv.** Dependencies install into `.venv/`. Run Python through
  `.venv/bin/python` (or activate `.venv`). The `make` targets already point at it.
- **Lint / test / preflight** are all Make targets, no API keys required:
  `make lint`, `make test` (full pytest, ~435 tests), `make test-contracts`,
  `make preflight` (registry/provider discovery).
- **End-to-end smoke test with zero API keys:** `make demo-list` then
  `.venv/bin/python render_demo.py <name>` (e.g. `world-in-numbers`) renders a real 1080p MP4
  via Remotion to `projects/demos/renders/`. This is the fastest proof the full
  composition path (Remotion + FFmpeg) works without any provider keys.
- **API keys are optional.** `.env` (copied from `.env.example`) drives which cloud providers
  are configured; with no keys the registry still reports FFmpeg/Remotion/HyperFrames + Piper
  as available. Add keys to `.env` to unlock more tools — never hardcode them.
- **Outbound HTTPS is allowlisted.** This Cloud Agent environment currently reaches
  `github.com` and `api.github.com` only. TLS to Cloudflare and most provider APIs
  (`api.x.ai`, fal.ai, HeyGen, OpenAI, PyPI, npm) is reset at handshake. Keys in `.env`
  do not unlock Grok/FLUX/HeyGen generation here until those hosts are allowlisted.
  Run paid provider tools on a machine that can reach them, or add the hosts to the
  environment allowlist.
- **HyperFrames** is consumed on demand via `npx hyperframes` (no repo checkout); the first
  render fetches it if the npx cache is cold. `make hyperframes-doctor` validates the runtime.
