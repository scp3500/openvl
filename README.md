# OpenVL

让没有视觉能力的 AI 模型也能看懂图片。

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
openvl <图片路径或URL>       # 看图
openvl -c                    # 从剪贴板读图
openvl <图片> -t 0.3         # 调推理强度（0~1，越低越严谨）
openvl -cfg                  # 查看配置
```

### Cherry Studio（MCP）

| 字段 | 值 |
|------|-----|
| 命令 | `openvl` |
| 参数 | `--mcp` |
| 超时 | `90` |

告诉 AI 使用 `describe_image` 或 `describe_clipboard` 工具。

## 配置

编辑 `config.env`：

```ini
VISION_API_KEY=你的API密钥
VISION_API_BASE=https://你的中转站/v1
VISION_MODEL=模型ID
```

也支持通过系统环境变量配置。

## 原理

用户发图片 → OpenVL 调用多模态 API → 返回文字描述 → AI 根据描述回复

## 许可证

MIT
