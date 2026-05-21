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

## Tool Integration

OpenVL supports multiple integration methods. Choose based on your workflow:

| Tool | Method | Experience | Best for |
|------|--------|------------|----------|
| **OpenCode** | Plugin + AGENTS.md | Fully automatic | Paste → auto-analyze, zero effort |
| **Claude Code** | skills | Semi-automatic | AI auto-calls openvl when image path appears |
| **Pi** | skills | Semi-automatic | Same as above |
| **Cherry Studio** | MCP | Manual | Tell AI "use describe_image tool" |

### OpenCode (Recommended, best automatic experience)

Paste an image → plugin intercepts → saves to temp file → replaces with `[Image: path]` marker → AI auto-calls `openvl`. Just paste and go.

Setup:
```bash
# 1. Copy plugin
cp integrations/opencode/openvl-image.mjs ~/.config/opencode/plugin/

# 2. Add plugin to opencode.json
# "plugin": ["./plugin/openvl-image.mjs"]

# 3. Add image rules to AGENTS.md (see integrations/README.md)
```

### Claude Code / Pi (skills)

AI detects image paths or user mentions images, then auto-calls `openvl` via skills rules. No plugin needed, simple setup.

```bash
git clone https://github.com/scp3500/openvl.git ~/.claude/skills/openvl
```

### Cherry Studio (MCP)

Connect via MCP protocol. Users manually ask the AI to use `describe_image` or `describe_clipboard` tools. For users already in an MCP workflow.

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
