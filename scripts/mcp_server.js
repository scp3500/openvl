#!/usr/bin/env node
/**
 * OpenVL MCP Server - 薄封装，实际看图走 vision.py
 */
const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawnSync } = require('child_process');

function log(m) { process.stderr.write('[OpenVL] ' + m + '\n'); }

const PKG_DIR = path.join(__dirname, '..');
const HOME = process.env.USERPROFILE || process.env.HOME || '';
const SKILL_DIR = path.join(HOME, '.pi', 'agent', 'skills', 'openvl');
const VISION_PY = path.join(PKG_DIR, 'scripts', 'vision.py');

function findPython() {
    if (process.env.OPENVL_PYTHON) return process.env.OPENVL_PYTHON;

    const tryRun = (cmd) => {
        try {
            const r = spawnSync(cmd, ['--version'], { encoding: 'utf8', timeout: 2000 });
            return r.status === 0 ? cmd : null;
        } catch (e) { return null; }
    };

    let found = tryRun('python3') || tryRun('python');
    if (found) return found;

    if (process.platform === 'win32') {
        const home = process.env.USERPROFILE || '';
        const candidates = [
            path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Python'),
            path.join(home, 'AppData', 'Local', 'Programs', 'Python'),
            path.join(home, '.local', 'bin'),
        ];
        for (const dir of candidates) {
            try {
                if (fs.existsSync(dir)) {
                    const items = fs.readdirSync(dir);
                    for (const item of items.sort().reverse()) {
                        const py = path.join(dir, item, 'python.exe');
                        if (fs.existsSync(py)) return py;
                    }
                }
            } catch (e) {}
        }
    }
    return 'python';
}

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

const CONFIG = findConfig();
log('配置来源: ' + CONFIG);
const MODE = process.env.OPENVL_MCP_MODE || 'stdio';
const PORT = parseInt(process.env.OPENVL_MCP_PORT || '8932', 10);
const PYTHON = findPython();
log('Python: ' + PYTHON);

function loadConfig() {
    // 优先级：环境变量 > 配置文件（文件只填空）
    const cfg = { apiKey: '', apiBase: '', model: '' };

    if (process.env.VISION_API_KEY && !process.env.VISION_API_KEY.includes('你的'))
        cfg.apiKey = process.env.VISION_API_KEY;
    if (process.env.VISION_API_BASE)
        cfg.apiBase = process.env.VISION_API_BASE.replace(/\/+$/, '');
    if (process.env.VISION_MODEL)
        cfg.model = process.env.VISION_MODEL;

    if (!cfg.apiKey || !cfg.apiBase || !cfg.model) {
        try {
            const text = fs.readFileSync(CONFIG, 'utf8');
            for (const line of text.split('\n')) {
                const s = line.trim();
                if (s.startsWith('VISION_API_KEY=') && !s.includes('你的')) {
                    if (!cfg.apiKey) cfg.apiKey = s.split('=').slice(1).join('=').trim();
                } else if (s.startsWith('VISION_API_BASE=')) {
                    if (!cfg.apiBase) cfg.apiBase = s.split('=').slice(1).join('=').trim().replace(/\/+$/, '');
                } else if (s.startsWith('VISION_MODEL=')) {
                    if (!cfg.model) cfg.model = s.split('=').slice(1).join('=').trim();
                }
            }
        } catch (e) {}
    }

    log('API Key: ' + (cfg.apiKey ? '已设置' : '未设置'));
    log('API Base: ' + (cfg.apiBase || '(空)'));
    log('Model: ' + (cfg.model || '(空)'));
    return cfg;
}

async function callAPI(imageSource, fromClipboard, opts = {}) {
    const config = loadConfig();
    if (!config.apiKey || config.apiKey.includes('你的'))
        throw new Error('请配置 API Key: openvl -key sk-xxx');

    const args = [];
    if (fromClipboard) args.push('-c');
    if (imageSource && !fromClipboard) args.push(imageSource);
    if (opts.query) args.push(opts.query);
    if (opts.size) args.push('-s', String(opts.size));
    if (opts.thinking) args.push('-T', opts.thinking);

    const result = spawnSync(PYTHON, [VISION_PY, ...args], {
        encoding: 'utf8',
        timeout: 90000,
        env: {
            ...process.env,
            VISION_API_KEY: config.apiKey,
            VISION_API_BASE: config.apiBase,
            VISION_MODEL: config.model
        }
    });

    if (result.error) {
        throw new Error('启动 Python 失败: ' + result.error.message);
    }
    if (result.status !== 0) {
        throw new Error((result.stderr || result.stdout || '调用失败').slice(0, 300));
    }
    return result.stdout;
}

// ====== MCP 协议 ======
const tools = [
    { name: 'describe_image', description: '描述图片内容。用户有提问时请将问题填入 query 参数，视觉模型会直接回答。',
      inputSchema: { type: 'object', properties: { source: { type: 'string' }, query: { type: 'string' }, size: { type: 'number' }, thinking: { type: 'string' } }, required: ['source'] } },
    { name: 'describe_clipboard', description: '读取剪贴板截图。用户有提问时请将问题填入 query 参数，视觉模型会直接回答。',
      inputSchema: { type: 'object', properties: { query: { type: 'string' }, size: { type: 'number' }, thinking: { type: 'string' } } } }
];

async function handleToolsCall(toolName, args) {
    const opts = {};
    if (args.query) opts.query = args.query;
    if (args.size) opts.size = args.size;
    if (args.thinking) opts.thinking = args.thinking;

    if (toolName === 'describe_image') {
        if (!args.source) throw new Error('请提供图片路径');
        return await callAPI(args.source, false, opts);
    }
    if (toolName === 'describe_clipboard') {
        return await callAPI('', true, opts);
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
