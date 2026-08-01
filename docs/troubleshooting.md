# OpenVL 排障指南

## 通用步骤

先跑自检，一次看清环境/依赖/配置/连通：

```bash
openvl doctor
```

- Python、requests、Pillow、配置文件、API Key、API 地址、模型、连通性全查
- 逐项看 ✓/✗，按下面分主题定位。

## 按症状查

### 1. 装不上 / 命令找不到

- `npm install -g @scp3500/openvl` 后 `openvl` 不存在 → 检查 npm 全局 bin 是否在 PATH
  （Windows：`%APPDATA%\npm`；macOS/Linux：`$(npm prefix -g)/bin`）
- 一键脚本报错 → 确认 Node.js ≥ 18 已装；Git Bash 用 `install.sh`，PowerShell 用 `install.ps1`

### 2. 缺 Python 依赖

```
import requests / PIL 失败
```

```bash
pip install requests pillow
```

### 3. 配好了但报"API 地址为空 / Key 未配置"

- 用 `openvl -cfg` 看当前生效配置
- 配置优先级：环境变量 > 配置文件（只填空，不覆盖）。环境变量设了空/占位会挡住文件配置
- 占位符（`你的API密钥`、`模型ID` 等）会被跳过，视为未配置——确认 config.env 里是真实值

### 4. API 连不上 / 返回 4xx/5xx

| 现象 | 原因 | 处理 |
|------|------|------|
| 401/403 | key 无效或无权 | 检查 key 是否完整、是否过期 |
| 404 | base 地址路径不对 | 确认 `VISION_API_BASE` 以 `/v1/chat/completions` 或 `/v1/responses` 结尾 |
| 400 | payload 与网关要求不符 | 若提示 `stream` 相关，确认中转支持流式（doctor 探测已用流式） |
| 429/503 | 限流或服务暂时不可用 | 等一会重试；换中转站 |
| 超时 | 模型思考久或中转慢 | 调小 `-T` 思考档；换更快的中转；调大客户端超时 |

### 5. 升级后配置丢了

- 原因：`openvl -key` 写入的是 npm 包目录，`npm update` 会覆盖
- 解决：把 `config.env` 移到 `~/.pi/agent/skills/openvl/`（或 `~/.agents/skills/openvl/`），
  或改用环境变量。见仓库根 README「配置」。

### 6. 输出被截断 / 长文转述不全

- 默认 max_tokens 32768；不够用 `-m <更大值>`（无上限），或配置 `VISION_MAX_TOKENS`
- 图里有大量文字时，提问里明确"完整转述所有文字"

### 7. npm update 报 EBUSY（Windows）

- 原因：Cherry Studio 等客户端的 MCP 进程锁住了包目录
- 处理：先退出 MCP 会话/关掉客户端，再 `npm update -g @scp3500/openvl`，装完重启 MCP

### 8. 行为"新"但全局 CLI 还是"旧"

- skill 目录是 git 工作区（新），npm 全局包是发布版（旧）——预期差异
- 未发版时用 `python <工作区>/scripts/vision.py` 直接测；已发版 `npm update -g`

## 中转站建议

OpenVL 只是转述器，中转站不稳会直接表现为卡死/超时。经验：
- 选支持 `stream=true` 的 responses 中转（部分网关只接受流式）
- 多个中转切换对比；医生自检 `openvl doctor` 可快速验证连通
