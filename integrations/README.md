# OpenVL 集成配置

各工具的配置方法。

## OpenCode

插件自动把粘贴的图片转为文本，AI 通过 `openvl --base64` 读取。

1. 复制插件文件：
   ```bash
   mkdir -p ~/.config/opencode/plugin
   cp integrations/opencode/openvl-image.ts ~/.config/opencode/plugin/
   ```
2. 编辑 `~/.config/opencode/opencode.json`，添加 `plugin` 字段：
   ```json
   "plugin": ["./plugin/openvl-image.ts"]
   ```
   完整示例见 `integrations/opencode/opencode.example.json`。
3. 重启 OpenCode

## Claude Code

Claude Code 粘贴图片后会把图片存为临时文件，AI 看到路径后自动调 `openvl <路径>`。需要先安装 skills：

```bash
git clone https://github.com/scp3500/openvl.git ~/.claude/skills/openvl
```

## Cherry Studio

用 MCP 模式：

| 字段 | 值 |
|------|-----|
| 命令 | `openvl` |
| 参数 | `--mcp` |
| 超时 | `90` |

告诉 AI 使用 `describe_image` 或 `describe_clipboard` 工具。
