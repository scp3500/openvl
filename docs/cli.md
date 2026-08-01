# OpenVL CLI 完整参考

用法总览：`openvl <命令> [参数]`。支持多张图、URL、剪贴板、管道、base64。

## 看图方式

| 命令 | 说明 |
|------|------|
| `openvl <路径>` | 本地图片文件 |
| `openvl <URL>` | 网络图片（自动下载） |
| `openvl -c` | 剪贴板截图 |
| `openvl -c 你的问题` | 剪贴板截图 + 提问 |
| `openvl --stdin` | 从 stdin 读 data URI（`cat img.txt \| openvl --stdin`） |
| `openvl --base64 iVBOR...` | 直接传 raw base64 |
| `openvl a.png b.png 描述这些图` | 多图一次传，问题放最后 |

> 路径不存在、URL 下载失败时明确报错，不会静默回退。

## 可选参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `-t <0~1>` | 温度，越低越严谨 | 模型默认 |
| `-T <low\|medium\|high>` | 思考深度（reasoning effort） | 模型默认 |
| `-s <像素>` | 图片最大边长（超过则等比缩放） | 1024 |
| `-m <token>` | 最大输出 token（无上限） | 32768 |
| `-P` | 跳过默认描述提示词（用自己的提问风格） | 关 |
| `-cfg` | 查看当前生效配置 | - |

## 配置命令

| 命令 | 说明 |
|------|------|
| `openvl -key <KEY>` | 设置 API Key |
| `openvl -api <BASE_URL>` | 设置 API 地址（自动识别 chat/responses/gemini/claude） |
| `openvl -model <MODEL>` | 设置默认模型 |
| `openvl -max-tokens <N>` | 设置默认 max_tokens |
| `openvl -cfg` | 查看当前配置 |
| `openvl doctor` | 自检：Python / 依赖 / 配置 / API 连通 |
| `openvl setup` | 交互式配置向导 |

> 注意：`openvl -key/-api/-model` 写入 npm 包目录的 `config.env`，npm 升级会被覆盖；
> 长期使用推荐写 `~/.pi/agent/skills/openvl/config.env` 或用环境变量（见仓库根 README「配置」）。

## 输入/输出细节

- 文本在前、图片在后组装请求，利于 API 前缀缓存命中
- 输出是纯文本描述（或对提问的直接回答），可进任何 AI 上下文
- 大图（超 `-s`）会先缩放到临时目录再发送，不污染工作目录

## MCP

`openvl --mcp [http|stdio]` 启动 MCP 服务器，详见 [mcp.md](mcp.md)。
