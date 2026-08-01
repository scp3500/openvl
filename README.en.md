# OpenVL

[中文](README.md) | [English](README.en.md)

Give vision capability to any non-vision AI model.

```
User sends image → OpenVL calls multimodal API → returns text description → AI responds
```

## Quick Start

### 1. Install

```bash
npm install -g @scp3500/openvl
```

### 2. Configure API

```bash
openvl -key sk-your-key
openvl -api https://your-proxy/v1/chat/completions
```

### 3. View an image

Read a file directly:

```bash
openvl D:\screenshot.png
```

Or screenshot to clipboard and ask:

```bash
openvl -c "what's in this image"
```

### 4. AI IDE users: install skills

```bash
git clone https://github.com/scp3500/openvl.git ~/.agents/skills/openvl
```

This allows AI tools (Pi / Claude Code etc.) to auto-call openvl when they encounter images. Non-IDE users can skip this step.

## Usage

### CLI

| Command | Description |
|---------|-------------|
| `openvl <path/URL>` | View image |
| `openvl -c` | Read clipboard image |
| `openvl -c your question` | Clipboard + question |
| `openvl --stdin` | Read data URI from stdin |
| `openvl --base64 iVBOR...` | Pass raw base64 |
| `openvl <img> -t 0.3` | Temperature (0~1) |
| `openvl <img> -T high` | Reasoning effort |
| `openvl <img> -s 512` | Max dimension (default 1024) |
| `openvl <img> -m 8192` | Max output tokens (default 16384) |
| `openvl -P` | Skip the default description prompt |
| `openvl -cfg` | Show config |
| `openvl doctor` | Self-check: Python/deps/config/API connectivity |

Multiple images: `openvl a.png b.png describe these`

### MCP (Cherry Studio)

| Field | Value |
|-------|-------|
| Command | `openvl` |
| Args | `--mcp` |
| Timeout | `90` |

## Configuration

Priority: env vars > package-dir config.env > skills-dir config.env (files only fill gaps, never override env)

```ini
VISION_API_KEY=your-api-key
VISION_API_BASE=https://your-proxy/v1/chat/completions
VISION_MODEL=model-id
VISION_MAX_TOKENS=16384   # optional, default 16384
```

- `VISION_API_BASE` auto-detects three endpoint types: `/v1/chat/completions` (OpenAI), `/v1/responses` (Responses API), and Gemini / Claude native URLs
- **Recommended: put config.env under `~/.agents/skills/openvl/`** (or `~/.pi/agent/skills/openvl/`). Writing with `openvl -key/-api/-model` targets the npm package dir, which is **overwritten on npm upgrade**; skills dir or env vars survive upgrades
- Run `openvl doctor` to self-check environment, dependencies, config loading and API connectivity in one shot

## Tool Integration

| Tool | Method | Description |
|------|--------|-------------|
| **OpenCode** | Plugin + AGENTS.md | Pasted images are analyzed automatically |
| **Claude Code** | skills | AI auto-calls openvl when it sees image paths |
| **Pi** | skills | Same as above |
| **Cherry Studio** | MCP server | Manual invocation via describe_image tool |

### OpenCode

After installing the plugin, pasting an image into the chat triggers openvl automatically.

```bash
mkdir -p ~/.config/opencode/plugin
cp integrations/opencode/openvl-image.mjs ~/.config/opencode/plugin/
```

Add the plugin declaration to `opencode.json` and configure image handling rules in `AGENTS.md` (see `integrations/README.md`).

### Claude Code / Pi

Clone the repository to the skills directory:

```bash
git clone https://github.com/scp3500/openvl.git ~/.claude/skills/openvl
```

### Cherry Studio

Configure as an MCP server. The AI invokes `describe_image` or `describe_clipboard` as needed:

| Field | Value |
|-------|-------|
| Command | `openvl` |
| Args | `--mcp` |
| Timeout | `90` |

See `integrations/README.md`.

## Request Order

```
prompt(describe.md) → user question → image data
```

Text first, image last — for API prefix caching.

## Project Files

| File | Purpose |
|------|---------|
| `scripts/vision.py` | Core: read image → API → description |
| `scripts/mcp_server.js` | MCP server |
| `prompts/describe.md` | Description prompt template |
| `SKILL.md` | AI skill definition |
| `tests/test_openvl.py` | Unit/smoke tests |

## Testing

```bash
npm test                  # or: python -X utf8 tests/test_openvl.py
npm run test:e2e          # live API test (requires config)
```

Offline-safe by default; `--e2e` hits the real vision API.

## License

MIT
