# OpenVL

[中文](README.md) | [English](README.en.md)

**Give eyes to AI models that can't see images**: transcribe images into text so DeepSeek / text-only models can "see".

```
User sends image → OpenVL calls a multimodal API → returns text description → AI responds
```

Who it's for:
- **Terminal users**: view images, OCR screenshots from the command line
- **AI IDE users** (Claude Code / Pi / Cursor): let your AI read images automatically
- **Chat app users** (Cherry Studio): add vision to your bot via MCP

> ⚠️ **Prerequisite**: OpenVL ships no model of its own — it's a "transcriber" that calls
> *your* OpenAI-compatible multimodal API (relay or official). See [Prepare a vision API](#prepare-a-vision-api).

---

## Quick Start

Pick the path that matches how you use it. No need to install everything.

### A. Terminal CLI

```bash
npm install -g @scp3500/openvl     # install
openvl -key sk-your-key             # configure (one line per step)
openvl -api https://your-proxy/v1/chat/completions
openvl -model your-vision-model
openvl doctor                       # self-check: config & API connectivity
openvl D:\screenshot.png            # view an image
openvl -c "what's in this image"    # clipboard screenshot + question
```

### B. AI IDE (Claude Code / Pi)

Clone the skill so your AI auto-calls openvl when it sees images:

```bash
# Claude Code
git clone https://github.com/scp3500/openvl.git ~/.claude/skills/openvl
# Pi
git clone https://github.com/scp3500/openvl.git ~/.pi/agent/skills/openvl
```

You still need to configure the API with `openvl -key/-api/-model` (see below).

### C. Chat app (Cherry Studio)

Configure as an MCP server:

| Field | Value |
|-------|-------|
| Command | `openvl` |
| Args | `--mcp` |
| Timeout | `90` |

The AI will use the `describe_image` / `describe_clipboard` tools.

---

## Prepare a vision API

OpenVL calls **your** multimodal API (OpenAI-compatible; Chat Completions / Responses / Gemini / Claude are auto-detected).

- Already have a relay: use any of its vision models (e.g. `gpt-5.x`, `gemini-*`)
- Don't have one: sign up with any provider offering an OpenAI-compatible vision endpoint, and note your `base_url` + `key` + model name.

---

## Configuration

Three ways, **priority: env vars > config file** (a file only fills gaps, never overrides env).

**Way 1: command line** (easy, but lost on npm upgrade — see note below)

```bash
openvl -key sk-xxx -api https://xxx/v1/chat/completions -model gpt-5.4-mini
```

**Way 2: config file** (recommended, survives upgrades)

```bash
mkdir -p ~/.pi/agent/skills/openvl
notepad ~/.pi/agent/skills/openvl/config.env
```

```ini
VISION_API_KEY=sk-your-key
VISION_API_BASE=https://your-proxy/v1/chat/completions
VISION_MODEL=your-vision-model
VISION_MAX_TOKENS=32768   # optional, default 32768
```

**Way 3: environment variables**

```bash
export VISION_API_KEY=sk-xxx
export VISION_API_BASE=https://xxx/v1/chat/completions
export VISION_MODEL=gpt-5.4-mini
```

> 💡 **Why put config under `~/.pi/agent/skills/openvl/`**: `openvl -key` writes into the npm
> package dir, which is **overwritten on every `npm update`**; the skills dir or env vars survive.

Run `openvl doctor` after configuring — it checks Python, dependencies, config loading and API connectivity in one shot.

---

## CLI Reference

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
| `openvl <img> -m 8192` | Max output tokens (default 32768) |
| `openvl -P` | Skip default description prompt |
| `openvl -cfg` | Show config |
| `openvl doctor` | Self-check |

Multiple images: `openvl a.png b.png describe these`

---

## Tool Integration

| Tool | Method | Effect |
|------|--------|--------|
| **OpenCode** | plugin | Pasted images analyzed automatically |
| **Claude Code** | skills | Auto-calls openvl on image paths |
| **Pi** | skills | Same as above |
| **Cherry Studio** | MCP | Via `describe_image` tool |

**OpenCode**: copy the plugin file and restart

```bash
mkdir -p ~/.config/opencode/plugin
cp integrations/opencode/openvl-image.mjs ~/.config/opencode/plugin/
```

Add `"plugin": ["./plugin/openvl-image.mjs"]` to `~/.config/opencode/opencode.json` (full example in `integrations/opencode/opencode.example.json`).

**Claude Code / Pi**: clone the skills (see Quick Start B).

**Cherry Studio**: MCP config in Quick Start C. `describe_clipboard` needs a screenshot in your clipboard first.

---

## FAQ

**Q: Isn't this just OCR?**
Not really. OpenVL "talks about the image" — it can extract text, but also describe scenes, objects, UI, people, and answer arbitrary questions about the image.

**Q: Which model should I use as the backend?**
Any OpenAI-compatible model that accepts image input. Cheap relay vision models for cost, flagship models for quality.

**Q: Text in the image comes out incomplete?**
The default prompt transcribes text scenes fully. Use `-P` with your own prompt, or ask explicitly "transcribe all text".

**Q: `openvl doctor` says the API is unreachable?**
Check that `VISION_API_BASE` ends with `/v1/chat/completions` or `/v1/responses`, the key is valid, and the relay supports the model.

**Q: Config lost after upgrading?**
You likely wrote config into the npm package dir (`openvl -key` target). Move `config.env` to `~/.pi/agent/skills/openvl/` and reconfigure.

---

## Maintainers

- Tests: `npm test` (offline) / `npm run test:e2e` (requires config)
- Structure & release: see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- Local copies (git workspace / skills / npm package) sync notes are in there too.

## License

MIT
