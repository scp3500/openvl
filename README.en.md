# OpenVL

Give vision capability to any non-vision AI model.

User sends image → OpenVL calls a multimodal API → returns text description → AI responds based on the description.

[中文](README.md) | [English](README.en.md)

## Install

All users need the `openvl` command:

```bash
npm install -g @scp3500/openvl
```

AI IDE/CLI users also need to clone the repo to the skills directory:

```bash
git clone https://github.com/scp3500/openvl.git ~/.agents/skills/openvl
```

## Usage

### CLI (Pi / Claude Code / OpenCode etc.)

```bash
openvl <image-path-or-url>         # View image
openvl -c                           # Read clipboard image
openvl --stdin                      # Read data URI from stdin
openvl --base64 iVBOR...            # Pass raw base64 data
openvl <path> your question         # Image + question, vision model answers directly
openvl -c your question             # Clipboard + question
openvl <image> -t 0.3               # Temperature (0-1, lower = more precise)
openvl <image> -T high              # Reasoning effort (low|medium|high)
openvl <image> -s 512               # Max image dimension (default 1024, lower = fewer tokens)
openvl -cfg                         # Show current config
```

### Cherry Studio (MCP)

| Field | Value |
|-------|-------|
| Command | `openvl` |
| Args | `--mcp` |
| Timeout | `90` |

Tell the AI to use the `describe_image` or `describe_clipboard` tool.

## Configuration

Priority order (higher = more priority):

| Priority | Location | Description |
|----------|----------|-------------|
| 3 | Environment variables | `set VISION_API_KEY=...` |
| 2 | npm package dir | `node_modules/@scp3500/openvl/config.env` |
| 1 | Pi skills dir | `~/.pi/agent/skills/openvl/config.env` |

Edit `config.env` with the full API URL as `VISION_API_BASE`:

```ini
VISION_API_KEY=your-api-key
# Chat Completions endpoint
VISION_API_BASE=https://your-proxy/v1/chat/completions
# Responses API endpoint (OpenAI new format)
# VISION_API_BASE=https://your-proxy/v1/responses
VISION_MODEL=model-id
```

## Tool Integration

| Tool | Method | Details |
|------|--------|---------|
| OpenCode | Plugin + AGENTS.md | Pasted images auto-saved to temp files → AI auto-calls `openvl`. Add rules to `~/.config/opencode/AGENTS.md`. See `integrations/opencode/` |
| Claude Code | skills | Copy to `~/.claude/skills/openvl`, pasted images auto-read |
| Cherry Studio | MCP | `openvl --mcp`, configure MCP in Cherry Studio |
| Pi | skills | Copy to `~/.pi/agent/skills/openvl`, auto-enabled |

See `integrations/README.md` for details.

## Temp Files

When pasting images in OpenCode, the plugin saves them to `%TEMP%`:

- Filename: `openvl_timestamp_index.png` (e.g. `openvl_1747712345678_1.png`)
- Keeps latest 100 files, auto-cleans oldest
- Multiple images in one message increment by index; different messages distinguished by timestamp
- Historical images remain accessible during the session

## Request Order

Requests sent to the vision model are concatenated in this order:

1. **Prompt** — content of `prompts/describe.md` (static instruction)
2. **User question** — text passed with the `openvl` command (if any)
3. **Image** — base64-encoded image data

Text first, image last — this allows prefix caching at the API level to save compute costs.

## Project Files

| File | Purpose |
|------|---------|
| `prompts/describe.md` | Image description prompt template |
| `SKILL.md` | AI skill definition (Pi / Claude Code), tells the AI when and how to call `openvl` |
| `scripts/vision.py` | Core script: read image → call API → output description |
| `scripts/mcp_server.js` | MCP server (for Cherry Studio etc.) |

## License

MIT
