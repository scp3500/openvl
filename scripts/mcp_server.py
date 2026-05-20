#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenVL MCP Server - 支持 stdio 和 HTTP 模式"""

import sys
import json
import subprocess
import os
import signal
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

SKILL_DIR = Path(__file__).resolve().parent.parent
VISION_SCRIPT = SKILL_DIR / "scripts" / "vision.py"
MODE = os.environ.get("OPENVL_MCP_MODE", "stdio")
PORT = int(os.environ.get("OPENVL_MCP_PORT", 8932))

def mcp_log(msg):
    print(f"[OpenVL MCP] {msg}", file=sys.stderr, flush=True)

tools_list = [
    {
        "name": "describe_image",
        "description": "描述图片内容，支持 OCR 文字识别",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "图片路径、URL 或 base64 数据"
                }
            },
            "required": ["source"]
        }
    },
    {
        "name": "describe_clipboard",
        "description": "从剪贴板读取截图并描述（仅限 Windows 桌面端）",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

def run_vision(args):
    result = subprocess.run(
        [sys.executable, str(VISION_SCRIPT)] + args,
        capture_output=True, text=True, timeout=90
    )
    if result.returncode != 0:
        raise Exception(result.stderr[:500] or "执行失败")
    return result.stdout

# ====== MCP stdio 模式 ======
def handle_stdio():
    buffer = ""
    while True:
        try:
            chunk = sys.stdin.read(1)
            if not chunk:
                break
            buffer += chunk
            if buffer.endswith("\n"):
                line = buffer.strip()
                if line:
                    try:
                        req = json.loads(line)
                        resp = handle_request(req)
                        if resp:
                            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                            sys.stdout.flush()
                    except json.JSONDecodeError:
                        pass
                buffer = ""
        except (EOFError, KeyboardInterrupt):
            break

# ====== MCP HTTP 模式 ======
class MCPHTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            req = json.loads(body)
            resp = handle_request(req)
            if resp is None:
                resp = {"jsonrpc": "2.0", "id": req.get("id"), "result": None}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # 不输出访问日志

def run_http():
    server = HTTPServer(("0.0.0.0", PORT), MCPHTTPHandler)
    mcp_log(f"HTTP 模式启动: http://0.0.0.0:{PORT}")
    mcp_log(f"局域网其他设备可通过 http://本机IP:{PORT} 连接")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

# ====== 请求处理 ======
def handle_request(req):
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "0.1.0",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "openvl", "version": "1.0.0"}
            }
        }
    elif method == "notifications/initialized":
        return None
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}}
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        try:
            if tool_name == "describe_image":
                source = args.get("source", "")
                if not source:
                    return error(req_id, "请提供图片路径、URL 或 base64 数据")
                text = run_vision([source])
                return success(req_id, text)
            elif tool_name == "describe_clipboard":
                text = run_vision(["--clip"])
                return success(req_id, text)
            else:
                return error(req_id, f"未知工具: {tool_name}")
        except subprocess.TimeoutExpired:
            return error(req_id, "请求超时")
        except Exception as e:
            return error(req_id, str(e))
    return error(req_id, f"不支持的方法: {method}")

def success(req_id, text):
    return {
        "jsonrpc": "2.0", "id": req_id,
        "result": {"content": [{"type": "text", "text": text}]}
    }

def error(req_id, msg):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -1, "message": msg}}

def main():
    mcp_log("启动中...")
    if MODE == "http":
        run_http()
    else:
        handle_stdio()

if __name__ == "__main__":
    main()
