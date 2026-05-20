#!/usr/bin/env node
/**
 * OpenVL MCP Runner - 一行命令启动 MCP 服务器
 */
const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const PKG_DIR = path.join(__dirname, '..');
const CONFIG = path.join(PKG_DIR, 'config.env');
const MCP_SCRIPT = path.join(PKG_DIR, 'scripts', 'mcp_server.js');
const VISION_SCRIPT = path.join(PKG_DIR, 'scripts', 'vision.py');

const log = process.stderr.write.bind(process.stderr);

function ensureConfig() {
    if (!fs.existsSync(CONFIG)) {
        const example = path.join(PKG_DIR, 'config.env.example');
        if (fs.existsSync(example)) fs.copyFileSync(example, CONFIG);
    }
    const content = fs.readFileSync(CONFIG, 'utf8');
    if (content.includes('你的API密钥') || content.includes('你的密钥')) {
        log('\n  ⚠ 需要配置 API Key\n');
        log(`  运行: npx @scp3500/openvl openvl --set-key sk-xxx\n\n`);
        return false;
    }
    return true;
}

function main() {
    const mode = process.argv[2] || 'stdio';
    if (!ensureConfig()) process.exit(1);

    const proc = spawn(process.execPath, [MCP_SCRIPT], {
        stdio: 'inherit',
        env: { ...process.env, OPENVL_MCP_MODE: mode },
        cwd: PKG_DIR
    });
    proc.on('exit', code => process.exit(code || 0));
}

main();

main();
