# OpenVL MCP 详细

MCP（Model Context Protocol）让聊天客户端（Cherry Studio 等）通过工具调用 openvl。

## 启动方式

```bash
openvl --mcp        # 默认 stdio
openvl --mcp stdio  # 显式 stdio
openvl --mcp http   # HTTP 模式（端口见启动输出）
```

MCP server 是 Node 薄封装（`scripts/mcp_server.js`），实际看图仍走 Python（`scripts/vision.py`），
两者共用同一套 Python 发现与配置规则。

## 提供的工具

| 工具 | 作用 |
|------|------|
| `describe_image` | 描述图片。参数：`image_path` / `image_url` / `base64` + 可选 `query` |
| `describe_clipboard` | 读取剪贴板截图。参数：可选 `query` |

用户提问时把问题放进 `query`，视觉模型会直接回答，而不是只描述。

## Cherry Studio 配置

| 字段 | 值 |
|------|-----|
| 命令 | `openvl` |
| 参数 | `--mcp` |
| 超时 | `90`（秒，长图转述建议 ≥90） |

配置后让 AI 使用 `describe_image` / `describe_clipboard` 工具即可。

## 其他 MCP 客户端

任何支持 MCP stdio 的客户端（Claude Desktop / Cline / 自研等）都能用：
command = `openvl`，args = `--mcp`。HTTP 模式适合需要远程/调试的场景。

## 注意

- 配置（API Key 等）与 CLI 完全共用，配一次两边都生效
- `describe_clipboard` 依赖系统剪贴板；无图时返回明确提示
- 超时建议设大（长图转述可能几十秒），`90` 起步
- MCP 进程常驻时会锁住 npm 包目录：`npm update -g @scp3500/openvl` 前先退出相关客户端
  （如 Cherry Studio 的 MCP 会话），否则升级会报 `EBUSY`。
