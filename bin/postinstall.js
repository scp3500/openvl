#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const pkgDir = path.join(__dirname, '..');
const example = path.join(pkgDir, 'config.env.example');
const config = path.join(pkgDir, 'config.env');

// 复制配置模板
if (!fs.existsSync(config) && fs.existsSync(example)) {
    fs.copyFileSync(example, config);
}

// 检测 Python 依赖
function checkDep(name, importName) {
    const r = spawnSync('python', ['-c', `import ${importName || name}`], { encoding: 'utf8', timeout: 5000 });
    return r.status === 0;
}

const missing = [];
if (!checkDep('requests')) missing.push('requests');
if (!checkDep('PIL', 'PIL')) missing.push('pillow');

if (missing.length > 0) {
    console.log('');
    console.log('  OpenVL 需要 Python 依赖: ' + missing.join(', '));
    console.log('  请运行: pip install ' + missing.join(' '));
    console.log('');
}

console.log('');
console.log('  OpenVL 安装完成！');
console.log('');
console.log('  下一步：编辑 config.env 填入 API Key');
if (config) console.log('    notepad ' + config);
console.log('');
console.log('  然后运行: openvl <图片路径>');
console.log('');
