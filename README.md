# OpenVL

让没有视觉能力的 AI 模型也能看懂图片。

## 安装（所有用户都需要）

```bash
npm install -g @scp3500/openvl
```

## 使用方式

### 方式一：AI IDE / CLI（如 Pi、OpenCode、Cursor 等）

安装后把 `node_modules/@scp3500/openvl` 复制到你的 AI 的 skills 目录即可。然后直接使用命令行：

```bash
openvl <图片路径或URL>       # 看图
openvl --clip                # 从剪贴板读图
openvl <图片> -t 0.5         # 调强度
openvl --show-config         # 查看配置
```

### 方式二：Cherry Studio（通过 MCP）

#### 1. 配置 API Key

编辑 `config.env` 文件：
- **npm 全局安装路径：** `C:\Users\你的用户名\AppData\Roaming\npm\node_modules\@scp3500\openvl\config.env`
- **或 Pi skills 路径：** `C:\Users\你的用户名\.pi\agent\skills\openvl\config.env`

内容模板：

```ini
VISION_API_KEY=你的API密钥
VISION_API_BASE=https://你的中转站/v1
VISION_MODEL=模型ID
```

### 环境变量配置（可选）

也可通过系统环境变量配置，优先级高于 config.env：

```bash
set VISION_API_KEY=sk-xxx
set VISION_API_BASE=https://你的中转站
set VISION_MODEL=模型ID
```

#### 2. MCP 服务器配置

Cherry Studio → 设置 → MCP 服务器 → 添加：

| 字段 | 值 |
|------|-----|
| 名称 | `openvl` |
| 命令 | `openvl` |
| 参数 | `--mcp` |
| 超时 | `90` |
| 环境变量 | 留空（配 config.env 文件即可） |

#### 3. 使用方法

**截图分析：** 截图 → Ctrl+C → 告诉 AI "用 describe_clipboard 看我的截图"

**图片路径：** 告诉 AI "用 describe_image 看这张图 D:\xxx.png"

#### 4. 系统提示词（推荐）

在 Cherry Studio 助手设置中添加：

> 当用户需要查看图片或截图时，使用 openvl 的 describe_image 或 describe_clipboard 工具。

## 原理

```
用户发图片 → OpenVL 调用多模态 API → 返回文字描述 → AI 根据描述回复
```

## 手机端使用

### 方式一：电脑 + RikkaHub（同 WiFi）

电脑上启动 HTTP 模式的 MCP 服务器：

```bash
openvl --mcp http
```

手机安装 RikkaHub → 设置 → MCP 客户端 → 添加服务器：

| 字段 | 值 |
|------|-----|
| 名称 | `openvl` |
| 类型 | `HTTP` / `URL` |
| 地址 | `http://电脑的局域网IP:8932` |

查看电脑局域网 IP：Windows 上运行 `ipconfig`，找 IPv4 地址。

### 方式二：Termux（手机本地运行）

1. 安装 Termux（F-Droid 版本）

2. 安装 Node.js：
```bash
pkg upgrade && pkg install nodejs
```

3. 安装 OpenVL：
```bash
npm install -g @scp3500/openvl
```

4. 编辑 `config.env` 填入 API Key：
```bash
nano $PREFIX/lib/node_modules/@scp3500/openvl/config.env
```

5. 启动 MCP 服务器：
```bash
openvl --mcp http
```

6. RikkaHub 配置 MCP：

| 字段 | 值 |
|------|-----|
| 名称 | `openvl` |
| 类型 | `HTTP` / `URL` |
| 地址 | `http://localhost:8932` |

## 许可证

MIT
