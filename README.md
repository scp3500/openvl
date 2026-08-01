# OpenVL

[中文](README.md) | [English](README.en.md)

**给没有视觉能力的 AI 模型装上眼睛**：把图片转述成文字，让 DeepSeek / 纯文本模型也能"看图"。

```
用户发图片 → OpenVL 调用多模态 API → 返回文字描述 → AI 根据描述回复
```

适合谁：
- **终端用户**：命令行看图、OCR 截图
- **AI IDE 用户**（Claude Code / Pi / Cursor）：让 AI 自动识别你发的图
- **聊天软件用户**（Cherry Studio）：通过 MCP 给机器人加识图

> ⚠️ **前提**：OpenVL 不内置模型，它只是一个"转述器"——你需要一个支持图片输入的
> OpenAI 兼容 API（中转站或官方 API）作为后端。详见 [准备一个视觉 API](#准备一个视觉-api)。

---

## 快速开始

按你的用法选一条路，不用全部装。

### A. 终端 CLI

```bash
npm install -g @scp3500/openvl     # 安装
openvl -key sk-你的密钥              # 配置（一行一步）
openvl -api https://你的中转站/v1/chat/completions
openvl -model 你的视觉模型ID
openvl doctor                       # 自检：配置和 API 连通都没问题
openvl D:\截图.png                  # 看图
openvl -c "图里写了什么"             # 读剪贴板截图 + 提问
```

### B. AI IDE（Claude Code / Pi）

把 skills 克隆到对应目录，AI 遇到图片会自动调 openvl：

```bash
# Claude Code
git clone https://github.com/scp3500/openvl.git ~/.claude/skills/openvl
# Pi
git clone https://github.com/scp3500/openvl.git ~/.pi/agent/skills/openvl
```

装完后仍需 `openvl -key/-api/-model` 配置 API（见下）。

### C. 聊天软件（Cherry Studio）

配置为 MCP 服务器：

| 字段 | 值 |
|------|-----|
| 命令 | `openvl` |
| 参数 | `--mcp` |
| 超时 | `90` |

AI 会用 `describe_image` / `describe_clipboard` 工具。

---

## 准备一个视觉 API

OpenVL 调用的是**你提供的**多模态 API（OpenAI 兼容即可，Chat Completions / Responses / Gemini / Claude 自动识别）。

- 有中转站：直接用它支持的模型（如 `gpt-5.x`、`gemini-*` 等带视觉的模型）
- 没有：注册任意提供 OpenAI 兼容视觉接口的服务商，拿到 `base_url` + `key` + 模型名

---

## 配置

三种方式，**优先级：环境变量 > 配置文件**（配置文件只填空，不覆盖环境变量）。

**方式 1：命令行写入**（简单，但注意 npm 升级会丢，见下）

```bash
openvl -key sk-xxx -api https://xxx/v1/chat/completions -model gpt-5.4-mini
```

**方式 2：配置文件**（推荐，升级不丢）

```bash
mkdir -p ~/.pi/agent/skills/openvl
notepad ~/.pi/agent/skills/openvl/config.env
```

```ini
VISION_API_KEY=sk-你的密钥
VISION_API_BASE=https://你的中转站/v1/chat/completions
VISION_MODEL=你的视觉模型ID
VISION_MAX_TOKENS=32768   # 可选，默认 32768
```

**方式 3：环境变量**

```bash
export VISION_API_KEY=sk-xxx
export VISION_API_BASE=https://xxx/v1/chat/completions
export VISION_MODEL=gpt-5.4-mini
```

> 💡 **为什么推荐放 `~/.pi/agent/skills/openvl/`**：`openvl -key` 写入的是 npm 包目录，
> 每次 `npm update` 会被覆盖；放 skills 目录或环境变量则一劳永逸。

配置完跑 `openvl doctor`，会一次性检查 Python 环境、依赖、配置读取和 API 连通。

---

## CLI 参考

| 命令 | 说明 |
|------|------|
| `openvl <路径/URL>` | 看图 |
| `openvl -c` | 读剪贴板截图 |
| `openvl -c 你的问题` | 截屏 + 提问 |
| `openvl --stdin` | 从管道读 data URI |
| `openvl --base64 iVBOR...` | 传 raw base64 |
| `openvl <图片> -t 0.3` | 温度（0~1） |
| `openvl <图片> -T high` | 思考深度 |
| `openvl <图片> -s 512` | 最大边长（默认 1024） |
| `openvl <图片> -m 8192` | 最大输出 token（默认 32768） |
| `openvl -P` | 跳过默认描述提示词 |
| `openvl -cfg` | 查看当前配置 |
| `openvl doctor` | 自检 |

多个图片：`openvl a.png b.png 描述这些图`

---

## 工具集成

| 工具 | 方式 | 效果 |
|------|------|------|
| **OpenCode** | 插件 | 粘贴图片自动分析 |
| **Claude Code** | skills | 识别图片路径自动调用 |
| **Pi** | skills | 同上 |
| **Cherry Studio** | MCP | 通过 `describe_image` 工具调用 |

**OpenCode**：复制插件文件，重启即可

```bash
mkdir -p ~/.config/opencode/plugin
cp integrations/opencode/openvl-image.mjs ~/.config/opencode/plugin/
```

编辑 `~/.config/opencode/opencode.json` 添加 `"plugin": ["./plugin/openvl-image.mjs"]`（完整示例见 `integrations/opencode/opencode.example.json`）。

**Claude Code / Pi**：克隆 skills（见快速开始 B）。

**Cherry Studio**：MCP 配置见快速开始 C。`describe_clipboard` 需要先截图到剪贴板。

---

## 常见问题

**Q: 这不就是 OCR 吗？**
不全是。OpenVL 是"看图说话"——不仅能提文字，还能描述场景、物体、界面、人物，且可针对图片任意提问。

**Q: 用哪个模型做后端？**
任何支持图片输入的 OpenAI 兼容模型。想省钱用便宜的视觉中转模型，想要质量用旗舰。

**Q: 图里的文字转述不全/想完整提取？**
默认提示词会完整转述文字场景。可加 `-P` 用你自己的提示词，或提问时明确"完整转述文字"。

**Q: `openvl doctor` 提示 API 连不上？**
检查 `VISION_API_BASE` 是否带 `/v1/chat/completions` 或 `/v1/responses` 结尾、key 是否有效、中转站是否支持该模型。

**Q: 更新后配置丢了？**
大概率是配置写进了 npm 包目录（`openvl -key` 写入位置）。把 `config.env` 移到 `~/.pi/agent/skills/openvl/` 后重配即可。

---

## 维护者

- 测试：`npm test`（离线）/ `npm run test:e2e`（需配置）
- 项目结构与发版：见 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- 本地多份副本（git 工作区 / skills / npm 包）的同步说明也在其中

## 许可证

MIT
