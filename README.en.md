# OpenVL

[中文](README.md) | [English](README.en.md)

Give vision capability to any non-vision AI model.

```
User sends image → OpenVL calls multimodal API → returns text description → AI responds
```

## Quick Start

```bash
# 1. Install
npm install -g @scp3500/openvl

# 2. Configure API
openvl -key sk-your-key
openvl -api https://your-proxy/v1/chat/completions

# 3. Use it
openvl D:\screenshot.png        # Read a file directly
openvl -c "what's in this image" # Or screenshot to clipboard
```

AI IDE (Pi / Claude Code) users also copy skills:

```bash
git clone https://github.com/scp3500/openvl.git ~/.agents/skills/openvl
```

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

## How to Use with Each Tool

| Tool | Paste Method | Setup |
|------|-------------|-------|
| **OpenCode** | Paste directly into chat | Install plugin + AGENTS.md → auto-read |
| **Claude Code / Pi** | File path or screenshot | Install skills → AI auto-detects images |
| **Cherry Studio** | Send image to AI | Configure MCP → ask AI to use tool |

### OpenCode (Recommended)

After setup, just paste an image into the chat. The AI reads it automatically.

```bash
# 1. Install plugin
mkdir -p ~/.config/opencode/plugin
cp integrations/opencode/openvl-image.mjs ~/.config/opencode/plugin/

# 2. Add to opencode.json
# "plugin": ["./plugin/openvl-image.mjs"]

# 3. Add rules to AGENTS.md (see integrations/README.md)
```

### Claude Code / Pi

Clone the repo to the skills directory, and the AI will auto-use openvl when it sees an image.

```bash
git clone https://github.com/scp3500/openvl.git ~/.claude/skills/openvl
```

### Cherry Studio

Configure as MCP server, then ask the AI to use `describe_image`:

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
