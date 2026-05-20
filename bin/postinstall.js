#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const pkgDir = path.join(__dirname, '..');
const example = path.join(pkgDir, 'config.env.example');
const config = path.join(pkgDir, 'config.env');

if (!fs.existsSync(config) && fs.existsSync(example)) {
    fs.copyFileSync(example, config);
    console.log('');
    console.log('  OpenVL 安装完成！');
    console.log('');
    console.log('  下一步：编辑 config.env 填入 API Key');
    console.log('    notepad ' + config);
    console.log('');
    console.log('  然后运行: openvl <图片路径>');
    console.log('');
}
