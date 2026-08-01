# OpenVL 一键安装脚本
$Repo = "https://github.com/scp3500/openvl"

Write-Host "=== OpenVL 安装 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Node.js
Write-Host "[1/3] 检查 Node.js ..." -ForegroundColor Yellow
$nodeVer = & node --version 2>$null
if ($nodeVer) {
    Write-Host "  找到: Node.js $nodeVer" -ForegroundColor Green
} else {
    Write-Host "  ✗ 未找到 Node.js，请先安装 https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# 2. npm 安装
Write-Host "[2/3] 安装 openvl ..." -ForegroundColor Yellow
try {
    npm install -g @scp3500/openvl
    Write-Host "  ✓ 安装完成" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 安装失败: $_" -ForegroundColor Red
    exit 1
}

# 3. 复制 skills
Write-Host "[3/3] 复制 skills（Pi/Claude Code/OpenCode）..." -ForegroundColor Yellow
$skillsDirs = @(
    "$env:USERPROFILE\.pi\agent\skills\openvl",
    "$env:USERPROFILE\.claude\skills\openvl",
    "$env:USERPROFILE\.agents\skills\openvl"
)
$npmDir = "$env:APPDATA\npm\node_modules\@scp3500\openvl"
if (Test-Path $npmDir) {
    foreach ($dir in $skillsDirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
            Copy-Item -Path "$npmDir\*" -Destination $dir -Recurse -Force
            Write-Host "  ✓ $dir" -ForegroundColor Green
        } else {
            Write-Host "  - $dir (已存在，跳过)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  ⚠ npm 包目录未找到，请手动克隆 skills：" -ForegroundColor Yellow
    Write-Host "    git clone $Repo.git ~/.agents/skills/openvl" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== 安装完成 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 配置 API（可一行连写）:" -ForegroundColor White
Write-Host "     openvl -key sk-你的密钥 -api https://你的中转站/v1/chat/completions -model 你的视觉模型" -ForegroundColor Gray
Write-Host "  2. 测试:" -ForegroundColor White
Write-Host "     openvl <图片路径>" -ForegroundColor Gray
Write-Host ""
