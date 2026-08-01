#!/usr/bin/env bash
# OpenVL 一键安装脚本（Linux / macOS / Windows Git Bash）
# 用途：AI 助手或用户执行本脚本即可完成：检测环境 → 装 CLI → 装 skills → 验证
# 用法：
#   bash <(curl -fsSL https://raw.githubusercontent.com/scp3500/openvl/main/install.sh)
#   或本地： bash install.sh
set -euo pipefail

REPO_URL="https://github.com/scp3500/openvl.git"

echo "=== OpenVL install ==="

# 1. Node.js
echo "[1/4] Node.js ..."
if command -v node >/dev/null 2>&1; then
  echo "  found: $(node --version)"
else
  echo "  ERROR: Node.js not found. Install from https://nodejs.org/ and retry." >&2
  exit 1
fi

# 2. npm install CLI
echo "[2/4] npm install -g @scp3500/openvl ..."
npm install -g @scp3500/openvl

# 3. Python + deps check (npm postinstall does this too; explicit here for clarity)
echo "[3/4] Python deps ..."
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "  WARN: Python not found. OpenVL needs Python + requests + Pillow." >&2
else
  PY=$(command -v python3 || command -v python)
  if ! "$PY" -c "import requests, PIL" 2>/dev/null; then
    echo "  WARN: missing 'requests' or 'pillow'. Run: $PY -m pip install requests pillow"
  else
    echo "  ok: requests + pillow present"
  fi
fi

# 4. Install skills for AI IDEs (skip dirs that already exist)
echo "[4/4] skills ..."
SKILL_DIRS=(
  "$HOME/.agents/skills/openvl"
  "$HOME/.claude/skills/openvl"
  "$HOME/.pi/agent/skills/openvl"
)
for dir in "${SKILL_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    echo "  - $dir (exists, skip)"
    continue
  fi
  mkdir -p "$(dirname "$dir")"
  git clone --depth 1 "$REPO_URL" "$dir" 2>/dev/null && echo "  + $dir" || echo "  WARN: clone failed for $dir"
done

echo ""
echo "=== Done ==="
echo "Next: configure an API then verify:"
echo "  openvl -key sk-xxx -api https://host/v1/chat/completions -model your-vision-model"
echo "  openvl doctor"
echo "Tip: put config in ~/.pi/agent/skills/openvl/config.env so it survives npm upgrades."
echo "Docs (installed with the package):"
echo "  $(npm root -g 2>/dev/null)/@scp3500/openvl/docs/   (CLI/MCP/troubleshooting)"
