# OpenVL 一键安装脚本
$Repo = "https://github.com/scp3500/openvl"
$Target = "$env:USERPROFILE\.pi\agent\skills\openvl"

Write-Host "=== OpenVL 安装 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Python
Write-Host "[1/4] 检查 Python ..." -ForegroundColor Yellow
$py = $null
foreach ($cmd in @("python", "python3")) {
    $ver = & $cmd --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        $py = $cmd
        Write-Host "  找到: $ver" -ForegroundColor Green
        break
    }
}
if (-not $py) {
    Write-Host "  ✗ 未找到 Python，请先安装 https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# 2. 安装依赖
Write-Host "[2/4] 安装依赖 ..." -ForegroundColor Yellow
try {
    & $py -m pip install requests -q
    Write-Host "  ✓ 依赖就绪" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ pip 安装失败，如果已经装了 requests 可忽略" -ForegroundColor Yellow
}

# 3. 下载项目
Write-Host "[3/4] 下载项目文件 ..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $Target | Out-Null
$zipUrl = "$Repo/archive/refs/heads/main.zip"
$zipPath = "$env:TEMP\openvl_install.zip"
try {
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
    Expand-Archive -Path $zipPath -DestinationPath "$env:TEMP\openvl_install" -Force
    Copy-Item -Path "$env:TEMP\openvl_install\openvl-main\*" -Destination $Target -Recurse -Force
    Remove-Item "$env:TEMP\openvl_install" -Recurse -Force
    Remove-Item $zipPath -Force
    Write-Host "  ✓ 下载完成" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 下载失败: $_" -ForegroundColor Red
    Write-Host "  请手动下载: $Repo" -ForegroundColor Yellow
    exit 1
}

# 4. 注册 openvl 命令
Write-Host "[4/4] 注册命令 ..." -ForegroundColor Yellow
$batDirs = @(
    "$env:USERPROFILE\.cargo\bin",
    "$env:LOCALAPPDATA\Microsoft\WindowsApps",
    "$env:USERPROFILE\scoop\shims"
)
$batDir = $null
foreach ($dir in $batDirs) {
    if (Test-Path $dir) {
        $batDir = $dir
        break
    }
}
if (-not $batDir) {
    $batDir = "$env:USERPROFILE\.cargo\bin"
}
New-Item -ItemType Directory -Force -Path $batDir | Out-Null
$batPath = "$batDir\openvl.bat"
@"
@echo off
python "%USERPROFILE%\.pi\agent\skills\openvl\scripts\vision.py" %*
"@ | Set-Content -Path $batPath -Encoding ASCII
Write-Host "  ✓ 命令注册: $batPath" -ForegroundColor Green

# 完成
Write-Host ""
Write-Host "=== 安装完成 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 编辑配置文件:" -ForegroundColor White
Write-Host "     notepad $Target\config.env" -ForegroundColor Gray
Write-Host "  2. 填入你的 API Key 和模型信息" -ForegroundColor White
Write-Host "  3. 打开新的终端，试试:" -ForegroundColor White
Write-Host "     openvl <图片路径>" -ForegroundColor Gray
Write-Host ""
