# OpenVL

让没有视觉能力的 AI 模型也能看懂图片。

用户发图片 → OpenVL 调用多模态 API → 返回文字描述 → AI 根据描述回复

## 安装

所有用户都需要 `openvl` 命令：

```bash
npm install -g @scp3500/openvl
```

AI IDE/CLI 用户还需要把仓库克隆到 skills 目录：

```bash
git clone https://github.com/scp3500/openvl.git ~/.agents/skills/openvl
```

## 使用方式

### CLI（Pi / Claude Code / OpenCode 等）

```bash
openvl <图片路径或URL>            # 看图
openvl -c                          # 从剪贴板读图
openvl --stdin                     # 从 stdin 读 data URI
openvl --base64 iVBOR...           # 直接传 base64 数据
openvl <路径> 你的问题             # 带问题看图，视觉模型直接回答
openvl -c 你的问题                 # 带问题读剪贴板
openvl <图片> -t 0.3               # 温度（0~1，越低越严谨）
openvl <图片> -T high              # 思考深度 (low|medium|high)
openvl <图片> -s 512               # 图片最大边长（默认1024，越小越省token）
openvl -cfg                        # 查看配置
```

### Cherry Studio（MCP）

| 字段 | 值 |
|------|-----|
| 命令 | `openvl` |
| 参数 | `--mcp` |
| 超时 | `90` |

告诉 AI 使用 `describe_image` 或 `describe_clipboard` 工具。

## 配置

按以下优先级查找（数值越高越优先）：

| 优先级 | 位置 | 说明 |
|--------|------|------|
| 3 | 系统环境变量 | `set VISION_API_KEY=...` |
| 2 | npm 包目录 | `node_modules/@scp3500/openvl/config.env` |
| 1 | Pi skills 目录 | `~/.pi/agent/skills/openvl/config.env` |

编辑对应位置的 `config.env`，`VISION_API_BASE` 填完整 API 地址：

```ini
VISION_API_KEY=你的API密钥
# Chat Completions 接口
VISION_API_BASE=https://你的中转站/v1/chat/completions
# Responses 接口（OpenAI 新格式）
# VISION_API_BASE=https://你的中转站/v1/responses
VISION_MODEL=模型ID
```

## 各工具集成

| 工具 | 方式 | 详情 |
|------|------|------|
| OpenCode | 插件 + AGENTS.md | 粘贴图片自动存临时文件 → AI 自动调 `openvl`。需在 `~/.config/opencode/AGENTS.md` 添加图片处理规则，见 `integrations/opencode/` |
| Claude Code | skills | 复制 `~/.claude/skills/openvl`，粘贴图片自动读 |
| Cherry Studio | MCP | `openvl --mcp`，Cherry Studio 里配 MCP 服务器 |
| Pi | skills | 复制到 `~/.pi/agent/skills/openvl`，已自动生效 |

详见 `integrations/README.md`。

## 临时文件

OpenCode 粘贴图片时，插件会保存到 `%TEMP%` 目录：

- 文件名：`openvl_时间戳_序号.png`（如 `openvl_1747712345678_1.png`）
- 保留最近 100 张，超出自动清理
- 多张图同一消息内按序号递增，不同消息用时间戳区分，不会覆盖
- 会话期间可追溯历史图片

## 请求拼接逻辑

发送给视觉模型的请求按以下顺序拼接：

1. **提示词** — `prompts/describe.md` 的内容（固定的描述指令）
2. **用户问题** — 运行 `openvl` 时传入的文本（如果有的话）
3. **图片** — base64 编码的图片数据

文本在前、图片在后，是为了让固定的前缀部分能被 API 缓存命中，节省计算成本。

## 项目文件

| 文件 | 作用 |
|------|------|
| `prompts/describe.md` | 图片描述提示词模板，控制返回格式和语言风格 |
| `SKILL.md` | AI 技能定义文件（Pi / Claude Code 读取），告诉 AI 何时及如何调用 `openvl` 命令 |
| `scripts/vision.py` | 核心脚本：读图 → 调 API → 输出描述 |
| `scripts/mcp_server.js` | MCP 服务器（Cherry Studio 连接用） |

## 许可证

MIT
