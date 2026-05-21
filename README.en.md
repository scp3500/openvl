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
| `openvl <img> -t 0.3` | Temperature |
| `openvl <img> -T high` | Reasoning effort |
| `openvl <img> -s 512` | Max dimension (default 1024) |
| `openvl -cfg` | Show config |

Multiple images: `openvl a.png b.png describe these`

### MCP (Cherry Studio)

| Field | Value |
|-------|-------|
| Command | `openvl` |
| Args | `--mcp` |
| Timeout | `90` |

## Configuration

Priority: env vars > npm package dir > skills dir

```ini
VISION_API_KEY=your-api-key
VISION_API_BASE=https://your-proxy/v1/chat/completions
VISION_MODEL=model-id
```

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

## License

MIT
