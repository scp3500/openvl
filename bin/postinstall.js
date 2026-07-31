#!/usr/bin/env node
// OpenVL 安装后脚本：检查 Python 依赖，提示配置方式。
// 注意：不在此处生成 config.env 模板——模板落在包目录会遮蔽用户真实配置
// （load_config 的查找顺序中包目录排第一）。配置请用 `openvl setup` / `openvl -key ...`，
// 或手动编辑 ~/.pi/agent/skills/openvl/config.env。
const { spawnSync } = require('child_process');

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
console.log('  下一步：配置 API（二选一）');
console.log('    交互式:  openvl setup');
console.log('    或直接:  openvl -key <KEY> -api <BASE_URL> -model <MODEL>');
console.log('  推荐把 config.env 放在 ~/.pi/agent/skills/openvl/ 下，避免随 npm 升级丢失');
console.log('');
