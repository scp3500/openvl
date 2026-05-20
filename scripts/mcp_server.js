#!/usr/bin/env node
/**
 * OpenVL MCP Server - 纯 Node.js
 */
const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawnSync } = require('child_process');

const PKG_DIR = path.join(__dirname, '..');
const HOME = process.env.USERPROFILE || process.env.HOME || '';
const SKILL_DIR = path.join(HOME, '.pi', 'agent', 'skills', 'openvl');

// 优先查找用户 skills 目录，再找 npm 包目录
function findConfig() {
    const paths = [
        path.join(SKILL_DIR, 'config.env'),
        path.join(PKG_DIR, 'config.env'),
    ];
    for (const p of paths) {
        if (fs.existsSync(p)) return p;
    }
    return paths[0];
}
function findPrompt() {
    const paths = [
        path.join(SKILL_DIR, 'prompts', 'describe.md'),
        path.join(PKG_DIR, 'prompts', 'describe.md'),
    ];
    for (const p of paths) {
        if (fs.existsSync(p)) return p;
    }
    return paths[0];
}

const CONFIG = findConfig();
log('配置来源: ' + CONFIG);
const PROMPT_FILE = findPrompt();
const MODE = process.env.OPENVL_MCP_MODE || 'stdio';
const PORT = parseInt(process.env.OPENVL_MCP_PORT || '8932');

function log(m) { process.stderr.write('[OpenVL] ' + m + '\n'); }

function loadConfig() {
    // 优先级：环境变量 > 配置文件
    const cfg = { apiKey: '', apiBase: 'https://www.yysc.top/v1', model: 'gpt-5.4-mini' };
    
    // 1. 读环境变量（可在 Cherry Studio MCP 配置的环境变量栏设置）
    if (process.env.VISION_API_KEY && !process.env.VISION_API_KEY.includes('你的'))
        cfg.apiKey = process.env.VISION_API_KEY;
    if (process.env.VISION_API_BASE)
        cfg.apiBase = process.env.VISION_API_BASE.replace(/\/+$/, '') + '/v1';
    if (process.env.VISION_MODEL)
        cfg.model = process.env.VISION_MODEL;
    
    log('API Key 状态: ' + (cfg.apiKey ? '已设置 (' + cfg.apiKey.substring(0,8) + '...)' : '未设置'));
    log('API Base: ' + cfg.apiBase);
    log('Model: ' + cfg.model);
    
    // 2. 环境变量不够则读配置文件
    if (!cfg.apiKey) {
        try {
            const text = fs.readFileSync(CONFIG, 'utf8');
            for (const line of text.split('\n')) {
                const s = line.trim();
                if (s.startsWith('VISION_API_KEY=') && !s.includes('你的'))
                    cfg.apiKey = s.split('=')[1].trim();
                else if (s.startsWith('VISION_API_BASE='))
                    cfg.apiBase = s.split('=')[1].trim().replace(/\/+$/, '') + '/v1';
                else if (s.startsWith('VISION_MODEL='))
                    cfg.model = s.split('=')[1].trim();
            }
        } catch (e) {}
    }
    return cfg;
}

function loadPrompt() {
    try { return fs.readFileSync(PROMPT_FILE, 'utf8').trim(); }
    catch (e) { return '请用中文详细描述这张图片的内容'; }
}

function getImageData(source) {
    if (source.startsWith('data:') || source.startsWith('http://') || source.startsWith('https://'))
        return source;
    const data = fs.readFileSync(source);
    const ext = path.extname(source).toLowerCase();
    const mimeMap = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                      '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp' };
    return `data:${mimeMap[ext] || 'image/jpeg'};base64,${data.toString('base64')}`;
}

// 剪贴板：尝试用 PowerShell 读取
function getClipboardImage() {
    const cp = require('child_process');
    const ps = `Add-Type -AssemblyName System.Windows.Forms
$img = [Windows.Forms.Clipboard]::GetImage()
if ($img -eq $null) { exit 1 }
$path = [System.IO.Path]::GetTempPath() + 'openvl_clip.png'
$img.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
Write-Host $path`;
    const result = cp.spawnSync('powershell', ['-NoProfile', '-Command', ps], { timeout: 10000, encoding: 'utf8' });
    if (result.status !== 0) throw new Error('剪贴板无图片');
    const imgPath = result.stdout.trim();
    if (!imgPath || !fs.existsSync(imgPath)) throw new Error('读取失败');
    return imgPath;
}

async function callAPI(imageSource, fromClipboard) {
    const config = loadConfig();
    if (!config.apiKey || config.apiKey.includes('你的'))
        throw new Error('请配置 API Key: npx @scp3500/openvl openvl --set-key sk-xxx');

    // 用 Python 做 API 请求（更稳定的 TLS 兼容性）
    const VISION_PY = path.join(PKG_DIR, 'scripts', 'vision.py');
    const args = fromClipboard ? ['--clip'] : [imageSource];
    
    const result = spawnSync('python', [VISION_PY, ...args], {
        encoding: 'utf8',
        timeout: 90000,
        env: {
            ...process.env,
            VISION_API_KEY: config.apiKey,
            VISION_API_BASE: config.apiBase.replace(/\/v1$/, ''),
            VISION_MODEL: config.model
        }
    });
    
    if (result.status !== 0) {
        throw new Error((result.stderr || result.stdout || '调用失败').slice(0, 300));
    }
    return result.stdout;
}

// ====== MCP 协议 ======
const tools = [
    { name: 'describe_image', description: '描述图片内容，支持 OCR。参数 source：图片路径/URL/base64',
      inputSchema: { type: 'object', properties: { source: { type: 'string' } }, required: ['source'] } },
    { name: 'describe_clipboard', description: '读取剪贴板截图并描述（仅 Windows）',
      inputSchema: { type: 'object', properties: {} } }
];

async function handleToolsCall(toolName, args) {
    if (toolName === 'describe_image') {
        if (!args.source) throw new Error('请提供图片路径');
        return await callAPI(args.source, false);
    }
    if (toolName === 'describe_clipboard') {
        return await callAPI('', true);
    }
    throw new Error(`未知工具: ${toolName}`);
}

// ====== stdio 模式 ======
function runStdio() {
    log('MCP Server 启动 (stdio)');
    let buf = '';
    process.stdin.on('data', chunk => {
        buf += chunk.toString();
        const lines = buf.split('\n');
        buf = lines.pop();
        for (const line of lines) {
            if (!line.trim()) continue;
            try {
                const req = JSON.parse(line);
                handleRequest(req).then(resp => {
                    if (resp) process.stdout.write(JSON.stringify(resp) + '\n');
                });
            } catch (e) {
                log('错误: ' + e.message);
            }
        }
    });
    process.stdin.on('end', () => process.exit(0));
}

// ====== HTTP 模式 ======
function runHttp() {
    const server = http.createServer((req, res) => {
        if (req.method === 'OPTIONS') {
            res.writeHead(200, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST', 'Access-Control-Allow-Headers': 'Content-Type' });
            res.end(); return;
        }
        let body = '';
        req.on('data', c => body += c);
        req.on('end', async () => {
            try {
                const reqJson = JSON.parse(body);
                const resp = await handleRequest(reqJson);
                res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify(resp || { jsonrpc: '2.0', id: reqJson.id, result: null }));
            } catch (e) {
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: e.message }));
            }
        });
    });
    server.listen(PORT, '0.0.0.0', () => log(`HTTP 模式: http://0.0.0.0:${PORT}`));
}

async function handleRequest(req) {
    const method = req.method; const params = req.params || {}; const id = req.id;

    if (method === 'initialize')
        return { jsonrpc: '2.0', id, result: { protocolVersion: '2025-03-26', capabilities: { tools: {} }, serverInfo: { name: 'openvl', version: '1.0.0' } } };
    if (method === 'notifications/initialized') return null;
    if (method === 'tools/list')
        return { jsonrpc: '2.0', id, result: { tools } };
    if (method === 'tools/call') {
        try {
            const text = await handleToolsCall(params.name, params.arguments || {});
            return { jsonrpc: '2.0', id, result: { content: [{ type: 'text', text }] } };
        } catch (e) {
            return { jsonrpc: '2.0', id, error: { code: -1, message: e.message } };
        }
    }
    return { jsonrpc: '2.0', id, error: { code: -32601, message: `不支持: ${method}` } };
}

if (MODE === 'http') runHttp();
else runStdio();
