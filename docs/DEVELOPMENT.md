# OpenVL 开发与目录说明

这份文档说明：**代码真相源在哪、本地多份副本是什么、怎么测、怎么发版**。  
面向维护者；普通用户看根目录 `README.md` 即可。

---

## 1. 仓库结构（现行）

```
openvl/
├── bin/
│   ├── openvl            # Node 入口：找 Python / 转发 --mcp
│   ├── openvl.cmd        # Windows shim
│   └── postinstall.js    # npm 安装后检查依赖（不再生成 config.env 模板，见下）
├── scripts/
│   ├── vision.py         # 核心：配置、读图、多 API、CLI
│   └── mcp_server.js     # MCP 薄封装（stdio/http → vision.py）
├── prompts/
│   └── describe.md       # 默认描述提示词
├── integrations/
│   └── opencode/         # OpenCode 插件与示例
├── tests/
│   └── test_openvl.py    # 单元 / 冒烟 / 可选 e2e
├── docs/
│   ├── index.html        # 产品落地页
│   └── DEVELOPMENT.md    # 本文件
├── SKILL.md              # Pi / Claude Code 等 skill 定义
├── package.json          # npm 包 @scp3500/openvl
├── config.env.example    # 配置模板（真实 config.env 不入库）
└── README.md / README.en.md
```

### 各层职责

| 层 | 文件 | 职责 |
|----|------|------|
| 入口 | `bin/openvl` | 发现 Python、启动 MCP 或调 `vision.py` |
| 核心 | `scripts/vision.py` | 配置、缩放、API（chat/responses/gemini/claude）、CLI |
| MCP | `scripts/mcp_server.js` | 协议适配，实际看图仍走 Python |
| 提示词 | `prompts/describe.md` | 默认真描述模板，可改 |
| Skill | `SKILL.md` | 教宿主 AI 何时/如何调用 openvl |
| 测试 | `tests/test_openvl.py` | 防回归 |

`vision.py` 目前偏大（配置 + provider + CLI 同文件）。能跑、边界清楚；若再膨胀，优先拆成 `config` / `providers` / `cli`，而不是先铺新目录。

---

## 2. 唯一真相源（Source of Truth）

**开发与提交只认 Git 仓库本身。**

- GitHub：`https://github.com/scp3500/openvl`
- 维护者本机常见检出路径（示例）：
  - `~/.pi/agent/skills/openvl`（Pi skill 直接用这份）
  - 或任意你 `git clone` 的工作副本

原则：

1. **改代码只在一个 git 工作区改**，改完 `git commit`。
2. 其他目录若只是 skill 安装结果，用同步命令更新，不要各改各的。
3. `config.env` 是本机密钥，已在 `.gitignore`，**不要提交**。

---

## 3. 本地多份副本（为什么看起来乱）

OpenVL 会以多种方式被“装”到机器上，所以同一台电脑可能出现多份目录。  
**这不等于仓库结构乱**，而是安装形态叠加。

| 路径（示例） | 是什么 | 怎么处理 |
|--------------|--------|----------|
| git 工作区（如 `~/.pi/agent/skills/openvl`） | **开发真相源** | 在这里改、提交 |
| `~/.agents/skills/openvl` | 通用 agents skill 副本 | 从 git 工作区同步，勿分叉开发 |
| `~/.claude/skills/openvl` | Claude Code skill 副本 | 同上 |
| 全局 npm：`npm root -g` 下的 `@scp3500/openvl` | 已发布包安装结果 | 只通过 `npm publish` / `npm i -g` 更新 |
| `~/openvl`、`~/openvl-backup` 等 | 历史骨架 / 备份 | 可归档或删除，**不要当现行代码** |

### 推荐同步方式（开发机）

在**已是 git 工作区**的目录提交后，把 skill 文件同步到其他 skill 路径（示例，按需改路径）：

```bash
# 在 git 工作区
npm test

# 同步到其他 skill 目录（覆盖代码，保留对方 config.env）
rsync -a --exclude config.env --exclude .git \
  ./ ~/.agents/skills/openvl/
rsync -a --exclude config.env --exclude .git \
  ./ ~/.claude/skills/openvl/
```

Windows 没有 rsync 时，可用 `openvl setup` 里的 skills 安装逻辑，或手动复制（同样跳过 `config.env`）。

全局 CLI 与 skill 版本不一致时：

```bash
npm list -g @scp3500/openvl
# 开发未发布：用 skill 目录里的 scripts 直接测
# 已发布：npm update -g @scp3500/openvl
```

---

## 4. 配置优先级

运行时配置项：`VISION_API_KEY` / `VISION_API_BASE` / `VISION_MODEL` / `VISION_MAX_TOKENS`

**优先级：环境变量 > 配置文件（文件只填空，不覆盖 env）**

查找顺序（文件侧）：

1. 当前包 / skill 目录下的 `config.env`
2. `~/.pi/agent/skills/openvl/config.env`
3. `~/.agents/skills/openvl/config.env`

> **1.1.73 起 postinstall 不再自动复制 `config.env.example` 到包目录**（旧版会在包目录生成模板，
> 且 `load_config` 曾只过滤 KEY 的“你的”占位、BASE/MODEL 不过滤，导致模板遮蔽真实配置）。
> 现在安装后提示用 `openvl setup` 或手动放 `~/.pi/agent/skills/openvl/config.env`；
> `load_config` 对占位值（你的/模型ID/your 等）统一跳过。

CLI 也可写配置：

```bash
openvl -key sk-xxx
openvl -api https://.../v1/chat/completions
openvl -model your-model
openvl -max-tokens 32768
openvl -cfg
openvl doctor
```

默认 `max_tokens` 为 **32768**；单次可 `openvl 图 -m 8192`。

---

## 5. 测试

```bash
# 默认：离线安全（不强制真实看图）
npm test
# 或
python -X utf8 tests/test_openvl.py

# 含真实 API 看图（需已配置）
npm run test:e2e
# 或
python -X utf8 tests/test_openvl.py --e2e
```

覆盖大致包括：

- `detect_api_type` / `load_config`（env 优先、默认 max_tokens）
- CLI query 分离（含 `openvl -c "问题"`）
- setup 结构守卫、流式/token 源码守卫
- 缩放写 TEMP
- help / version / cfg / 坏 URL
- MCP initialize + tools/list
- 可选 e2e 真图描述

改 CLI 解析、配置加载、provider 行为后，至少跑 `npm test`；动到请求路径再跑 `--e2e`。

---

## 6. 发版清单（git ≠ npm）

git 提交不会自动发 npm。建议顺序：

1. `npm test`（必要时 `npm run test:e2e`）
2. 改 `package.json` 版本号（如 `1.1.72`）
3. commit + tag（可选）
4. `git push`（含 tag）
5. `npm publish --access public`（包名 `@scp3500/openvl`）
6. 本机：`npm update -g @scp3500/openvl`，并同步 skill 副本

未发布前：IDE skill 可用 git 工作区最新代码；全局 `openvl` 命令仍是上次 publish 的版本——这是预期差异，不是“装坏了”。

---

## 7. 常见坑

| 现象 | 原因 | 处理 |
|------|------|------|
| skill 里行为新，终端 `openvl` 行为旧 | npm 全局版落后 | 发版后 update，或直接 `python scripts/vision.py` |
| 改了 A 目录，B 目录没变 | 多 skill 副本 | 只维护 git 工作区，再同步 |
| MCP 正常 CLI 不正常（或相反） | Python 路径 / 配置源不同 | `openvl doctor`；MCP 与 CLI 应共用 `findPython` 与 config 规则 |
| 剪贴板带问题像“没生效” | 旧版丢 query | 升级到含 fix 的版本；用法 `openvl -c "你的问题"` |
| doctor 显示 API 类型不对 | base URL 不像标准路径 | 检查 `VISION_API_BASE` 是否含 `/responses`、`/chat/completions` 等 |

---

## 8. 文档索引

| 文档 | 给谁看 |
|------|--------|
| `README.md` / `README.en.md` | 用户安装与使用 |
| `docs/index.html` | 产品介绍页 |
| `docs/DEVELOPMENT.md` | 维护者：目录、副本、测试、发版 |
| `integrations/README.md` | OpenCode / 各工具集成 |
| `SKILL.md` | 宿主 AI 的调用约定 |

有结构性变更（新目录、新配置项、发版流程变化）时，优先更新本文件。
