#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenVL - 让 AI 看懂图片
支持从文件、URL、剪贴板读取图片
"""

import os
import sys
import json
import base64
import subprocess
import requests
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = SKILL_DIR / "config.env"
PROMPT_FILE = SKILL_DIR / "prompts" / "describe.md"

# 备用配置：从 npm 包运行时，查找用户 skills 目录配置
HOME_DIR = Path(os.environ.get("USERPROFILE", "")) / ".pi" / "agent" / "skills" / "openvl"
HOME_DIR2 = Path(os.environ.get("USERPROFILE", "")) / ".agents" / "skills" / "openvl"

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def set_config(key, value):
    """写入配置项到 config.env"""
    config = load_config()
    if key == "key":
        config["api_key"] = value
    elif key == "base":
        config["api_base"] = value
    elif key == "model":
        config["model"] = value
    else:
        print(f"未知配置项: {key}")
        sys.exit(1)

    lines = []
    written = set()
    if ENV_FILE.exists():
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                line_stripped = line.strip()
                if line_stripped.startswith("VISION_API_KEY="):
                    lines.append(f"VISION_API_KEY={config['api_key']}\n")
                    written.add("key")
                elif line_stripped.startswith("VISION_API_BASE="):
                    lines.append(f"VISION_API_BASE={config['api_base']}\n")
                    written.add("base")
                elif line_stripped.startswith("VISION_MODEL="):
                    lines.append(f"VISION_MODEL={config['model']}\n")
                    written.add("model")
                else:
                    lines.append(line)
    if "key" not in written:
        lines.append(f"VISION_API_KEY={config['api_key']}\n")
    if "base" not in written:
        lines.append(f"VISION_API_BASE={config['api_base']}\n")
    if "model" not in written:
        lines.append(f"VISION_MODEL={config['model']}\n")
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"已设置: {key}={value}")


def load_config():
    config = {"api_key": "", "api_base": "", "model": ""}
    
    # 优先级：环境变量 > 配置文件
    env_key = os.environ.get("VISION_API_KEY", "")
    if env_key and "你的" not in env_key:
        config["api_key"] = env_key
    env_base = os.environ.get("VISION_API_BASE", "")
    if env_base:
        config["api_base"] = env_base.rstrip("/")
    env_model = os.environ.get("VISION_MODEL", "")
    if env_model:
        config["model"] = env_model
    
    # 环境变量不够则读配置文件
    config_files = [ENV_FILE]
    if HOME_DIR and HOME_DIR != SKILL_DIR:
        config_files.append(HOME_DIR / "config.env")
    if HOME_DIR2 and HOME_DIR2 != SKILL_DIR and HOME_DIR2 != HOME_DIR:
        config_files.append(HOME_DIR2 / "config.env")
    
    for cfg_file in config_files:
        if not cfg_file.exists():
            continue
        with open(cfg_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("VISION_API_KEY=") and "你的" not in line:
                    config["api_key"] = line.split("=", 1)[1].strip()
                elif line.startswith("VISION_API_BASE="):
                    config["api_base"] = line.split("=", 1)[1].strip().rstrip("/")
                elif line.startswith("VISION_MODEL="):
                    config["model"] = line.split("=", 1)[1].strip()
    return config

def load_prompt():
    if PROMPT_FILE.exists():
        with open(PROMPT_FILE, encoding="utf-8") as f:
            return f.read().strip()
    return "请用中文详细描述这张图片的内容"

def get_clipboard_image():
    """从剪贴板读取图片，返回 base64 和 mime 类型"""
    ps_script = '''
Add-Type -AssemblyName System.Windows.Forms
$img = [Windows.Forms.Clipboard]::GetImage()
if ($img -eq $null) { exit 1 }
$path = [System.IO.Path]::GetTempPath() + "openvl_clip.png"
$img.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
Write-Host $path
'''
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        print("剪贴板中没有图片，请先截图按 Ctrl+C")
        sys.exit(1)
    path = result.stdout.strip()
    if not path or not os.path.isfile(path):
        print("读取剪贴板图片失败")
        sys.exit(1)
    return path

def resize_image(image_path, max_size=1024):
    try:
        from PIL import Image, ImageFile
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        img = Image.open(image_path)
        w, h = img.size
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            ext = Path(image_path).suffix.lower()
            fmt = "JPEG" if ext in (".jpg", ".jpeg") else "PNG"
            buf = Path(image_path).parent / f".tmp_vision_{Path(image_path).name}"
            img.save(buf, fmt, quality=85)
            return str(buf)
    except ImportError:
        pass
    return image_path

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def detect_api_type(url):
    """根据 URL 自动识别 API 类型"""
    url = url.lower()
    if "googleapis.com" in url or "generativelanguage" in url:
        return "gemini"
    if "api.anthropic.com" in url:
        return "claude"
    if "/responses" in url:
        return "responses"
    return "chat"

def call_gemini(api_url, api_key, payload):
    """调用 Google Gemini API"""
    model = payload.pop("model", "")
    token = payload.pop("max_tokens", 1024)
    temp = payload.pop("temperature", None)

    url = api_url.rstrip("/")
    if "generateContent" not in url:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    url += f"?key={api_key}"

    content = []
    for msg in payload.get("messages", []):
        parts = []
        for item in msg.get("content", []):
            if item.get("type") == "image_url":
                url_data = item["image_url"]["url"]
                if url_data.startswith("data:"):
                    _, b64 = url_data.split(",", 1)
                    mime = url_data.split(";")[0].split(":")[1]
                    parts.append({"inlineData": {"mimeType": mime, "data": b64}})
            elif item.get("type") == "text":
                parts.append({"text": item["text"]})
        content.append({"role": "user", "parts": parts})

    body = {"contents": content, "generationConfig": {"maxOutputTokens": token}}
    if temp is not None:
        body["generationConfig"]["temperature"] = temp

    resp = requests.post(url, json=body, timeout=60)
    if resp.status_code != 200:
        print(f"API 请求失败 ({resp.status_code}): {resp.text[:500]}")
        sys.exit(1)
    result = resp.json()
    try:
        print(result["candidates"][0]["content"]["parts"][0]["text"])
    except (KeyError, IndexError):
        print(result)

def call_claude(api_url, api_key, payload):
    """调用 Claude API"""
    model = payload.get("model", "")
    token = payload.get("max_tokens", 1024)
    temp = payload.get("temperature")

    content = []
    for msg in payload.get("messages", []):
        parts = []
        for item in msg.get("content", []):
            if item.get("type") == "image_url":
                url_data = item["image_url"]["url"]
                if url_data.startswith("data:"):
                    _, b64 = url_data.split(",", 1)
                    mime = url_data.split(";")[0].split(":")[1]
                    parts.append({"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}})
            elif item.get("type") == "text":
                parts.append({"type": "text", "text": item["text"]})
        content.append({"role": "user", "content": parts})

    body = {"model": model, "max_tokens": token, "messages": content}
    if temp is not None:
        body["temperature"] = temp

    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}

    url = api_url.rstrip("/")
    if "/messages" not in url:
        url = "https://api.anthropic.com/v1/messages"

    resp = requests.post(url, headers=headers, json=body, timeout=60)
    if resp.status_code != 200:
        print(f"API 请求失败 ({resp.status_code}): {resp.text[:500]}")
        sys.exit(1)
    result = resp.json()
    try:
        print(result["content"][0]["text"])
    except (KeyError, IndexError):
        print(result)

def call_responses(api_url, api_key, payload):
    """调用 OpenAI Responses API"""
    input_items = []
    for msg in payload.get("messages", []):
        content_blocks = []
        for item in msg.get("content", []):
            if item.get("type") == "image_url":
                content_blocks.append({"type": "input_image", "image_url": item["image_url"]["url"]})
            elif item.get("type") == "text":
                content_blocks.append({"type": "input_text", "text": item["text"]})
        input_items.append({"role": msg.get("role", "user"), "content": content_blocks})

    body = {"model": payload["model"], "input": input_items, "max_output_tokens": 1024, "stream": True}
    if payload.get("temperature"):
        body["temperature"] = payload["temperature"]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(api_url, headers=headers, json=body, stream=True, timeout=60)
    if resp.status_code != 200:
        print(f"API 请求失败 ({resp.status_code}): {resp.text[:500]}")
        sys.exit(1)
    for line in resp.iter_lines():
        if not line:
            continue
        line = line.decode("utf-8", errors="replace")
        if line.startswith("data: "):
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                if chunk.get("type") == "response.output_text.delta":
                    print(chunk.get("delta", ""), end="", flush=True)
            except json.JSONDecodeError:
                pass
    print()

def call_chat(api_url, api_key, payload):
    """调用 OpenAI Chat Completions API"""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=60)
    if resp.status_code != 200:
        print(f"API 请求失败 ({resp.status_code}): {resp.text[:500]}")
        sys.exit(1)
    for line in resp.iter_lines():
        if line:
            line = line.decode("utf-8", errors="replace")
            if line.startswith("data: ") and line != "data: [DONE]":
                try:
                    chunk = json.loads(line[6:])
                    choices = chunk.get("choices")
                    if choices and len(choices) > 0:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            print(content, end="", flush=True)
                except json.JSONDecodeError:
                    pass
    print()

def describe_image(image_source, strength=None, thinking_effort=None, from_clipboard=False, query=None, max_size=1024):
    config = load_config()
    if not config["api_key"]:
        print("错误: 未配置 API Key")
        print(f"请编辑 {ENV_FILE} 文件")
        sys.exit(1)
    if not config["api_base"]:
        print("错误: 未配置 API 地址")
        sys.exit(1)

    if from_clipboard:
        image_source = get_clipboard_image()

    b64, mime = None, None
    if os.path.isfile(image_source):
        ext = Path(image_source).suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
            print(f"不支持的图片格式: {ext}")
            sys.exit(1)
        resized = resize_image(image_source, max_size=max_size)
        b64 = encode_image(resized)
        if resized != image_source:
            os.remove(resized)
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                    ".webp": "image/webp", ".gif": "image/gif", ".bmp": "image/bmp"}
        mime = mime_map.get(Path(resized).suffix.lower(), "image/jpeg")
    else:
        # 已经是 URL 或 base64 data URI
        img_data = image_source
        if img_data.startswith("data:"):
            _, b64data = img_data.split(",", 1)
            mime = img_data.split(";")[0].split(":")[1]
            b64 = b64data

    prompt = load_prompt()
    if query:
        prompt += "\n\n用户问题：" + query
    api_type = detect_api_type(config["api_base"])

    # 构建通用 payload（OpenAI 格式）
    content = [{"type": "text", "text": prompt}]
    if b64:
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    else:
        content.append({"type": "image_url", "image_url": {"url": image_source}})

    payload = {
        "model": config["model"],
        "messages": [
            {"role": "user", "content": content}
        ],
        "max_tokens": 1024,
    }
    if strength is not None:
        payload["temperature"] = strength
    if thinking_effort is not None:
        payload["reasoning_effort"] = thinking_effort
    payload["stream"] = True

    api_url = config["api_base"].rstrip("/")
    api_key = config["api_key"]

    try:
        if api_type == "gemini":
            call_gemini(api_url, api_key, payload)
        elif api_type == "claude":
            call_claude(api_url, api_key, payload)
        elif api_type == "responses":
            call_responses(api_url, api_key, payload)
        else:
            call_chat(api_url, api_key, payload)
    except requests.exceptions.Timeout:
        print("请求超时，请重试")
        sys.exit(1)
    except Exception as e:
        print(f"请求出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "-help", "help"):
        print("用法: openvl <命令> [参数]")
        print()
        print("  看图:")
        print("    openvl <图片路径或URL>       # 从文件或URL看图")
        print("    openvl -c                    # 从剪贴板读图")
        print("    openvl <图片> -t 0.3         # 温度（0~1，越低越严谨）")
        print("    openvl <图片> -T low         # 思考深度 (low|medium|high)")
        print("    openvl <图片> -s 512         # 图片最大边长（默认1024，越小越省）")
        print()
        print("  配置:")
        print("    openvl -key <密钥>           # 设置 API Key")
        print("    openvl -api <地址>           # 设置 API 地址")
        print("    openvl -model <模型>         # 设置默认模型")
        print("    openvl -cfg                  # 查看当前配置")
        print()
        print("  MCP:")
        print("    openvl --mcp [http|stdio]   # 启动 MCP 服务器")
        print()
        sys.exit(0)
    
    if sys.argv[1] in ("-v", "--version"):
        print("OpenVL v1.0.52")
        sys.exit(0)

    # 配置管理命令
    if sys.argv[1] in ("--set-key", "-key"):
        if len(sys.argv) < 3:
            print("请提供 API Key")
            sys.exit(1)
        set_config("key", sys.argv[2])
        sys.exit(0)
    if sys.argv[1] in ("--set-base", "-api"):
        if len(sys.argv) < 3:
            print("请提供 API 地址")
            sys.exit(1)
        set_config("base", sys.argv[2])
        sys.exit(0)
    if sys.argv[1] in ("--set-model", "-model"):
        if len(sys.argv) < 3:
            print("请提供模型名")
            sys.exit(1)
        set_config("model", sys.argv[2])
        sys.exit(0)
    if sys.argv[1] in ("--show-config", "-cfg"):
        c = load_config()
        print(f"API 地址: {c['api_base']}")
        print(f"默认模型: {c['model']}")
        key = c['api_key']
        if key:
            print(f"API Key: {key[:8]}...{key[-4:]}")
        else:
            print("API Key: 未设置")
        sys.exit(0)

    img = None
    strength = None
    thinking_effort = None
    max_size = 1024
    clip = False
    query_parts = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "-t":
            i += 1
            strength = float(sys.argv[i]) if i < len(sys.argv) else None
        elif sys.argv[i] in ("-T", "--think"):
            i += 1
            thinking_effort = sys.argv[i] if i < len(sys.argv) else "high"
        elif sys.argv[i] in ("-s", "--size"):
            i += 1
            max_size = int(sys.argv[i]) if i < len(sys.argv) else 1024
        elif sys.argv[i] in ("--clip", "-c"):
            clip = True
        elif img is None and not clip:
            img = sys.argv[i]
        else:
            query_parts.append(sys.argv[i])
        i += 1
    query = " ".join(query_parts) if query_parts else None

    if sys.argv[1] == "--mcp":
        import mcp_server
        if len(sys.argv) > 2:
            os.environ["OPENVL_MCP_MODE"] = sys.argv[2]
        mcp_server.main()
        sys.exit(0)

    if clip:
        describe_image(None, strength, thinking_effort, from_clipboard=True, query=query, max_size=max_size)
    elif img:
        describe_image(img, strength, thinking_effort, query=query, max_size=max_size)
    else:
        print("请提供图片路径或使用 -c")
