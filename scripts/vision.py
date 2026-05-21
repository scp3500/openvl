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
PKG_FILE = SKILL_DIR / "package.json"
ENV_FILE = SKILL_DIR / "config.env"
PROMPT_FILE = SKILL_DIR / "prompts" / "describe.md"

OPENVL_VERSION = "0.0.0"
try:
    with open(PKG_FILE, encoding="utf-8") as f:
        OPENVL_VERSION = json.load(f).get("version", "0.0.0")
except: pass

# 每日检查更新
import threading, time
CHECK_FILE = Path(os.environ.get("TEMP", "/tmp")) / "openvl_update_check"
def _check_update():
    try:
        if CHECK_FILE.exists() and time.time() - CHECK_FILE.stat().st_mtime < 86400:
            return
        r = requests.get("https://registry.npmjs.org/@scp3500/openvl/latest", timeout=2)
        latest = r.json().get("version", "")
        if latest and latest != OPENVL_VERSION:
            print(f"\n  新版 OpenVL {latest} 可用 (当前 {OPENVL_VERSION})", file=sys.stderr)
            print(f"  更新: npm update -g @scp3500/openvl\n", file=sys.stderr)
        CHECK_FILE.touch()
    except:
        pass
threading.Thread(target=_check_update, daemon=True).start()

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

def describe_image(image_source=None, strength=None, thinking_effort=None, from_clipboard=False, query=None, max_size=1024, image_list=None):
    config = load_config()
    if not config["api_key"]:
        print("错误: 未配置 API Key")
        print(f"请编辑 {ENV_FILE} 文件")
        sys.exit(1)
    if not config["api_base"]:
        print("错误: 未配置 API 地址")
        sys.exit(1)

    sources = image_list or []
    if from_clipboard:
        sources = [get_clipboard_image()]
    elif image_source:
        sources = [image_source] + sources
    elif not sources:
        print("请提供图片路径或使用 -c")
        sys.exit(1)

    def load_image(img_path):
        if os.path.isfile(img_path):
            ext = Path(img_path).suffix.lower()
            if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
                print(f"不支持的图片格式: {ext}")
                sys.exit(1)
            resized = resize_image(img_path, max_size=max_size)
            b = encode_image(resized)
            if resized != img_path:
                os.remove(resized)
            mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                        ".webp": "image/webp", ".gif": "image/gif", ".bmp": "image/bmp"}
            m = mime_map.get(Path(resized).suffix.lower(), "image/jpeg")
            return f"data:{m};base64,{b}"
        if img_path.startswith("data:") or img_path.startswith("http"):
            # 部分图站需要 Referer 才能访问
            headers = {}
            if "pximg.net" in img_path:
                headers["Referer"] = "https://www.pixiv.net/"
            try:
                r = requests.get(img_path, headers=headers, timeout=15)
                if r.ok:
                    ct = r.headers.get("content-type", "image/jpeg")
                    b64 = base64.b64encode(r.content).decode()
                    return f"data:{ct};base64,{b64}"
            except: pass
            return img_path
        print(f"无效的图片: {img_path}")
        sys.exit(1)

    prompt = load_prompt()
    if query:
        prompt += "\n\n用户问题：" + query
    api_type = detect_api_type(config["api_base"])

    content = [{"type": "text", "text": prompt}]
    for s in sources:
        content.append({"type": "image_url", "image_url": {"url": load_image(s)}})

    payload = {
        "model": config["model"],
        "messages": [{"role": "user", "content": content}],
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

def doctor():
    ok = True
    def chk(name, status, detail=""):
        nonlocal ok
        mark = "\u2713" if status else "\u2717"
        if not status: ok = False
        print(f"  {mark} {name} {detail}")
    print(f"OpenVL v{OPENVL_VERSION} \u8bca\u65ad")
    print()
    chk("Python", True, sys.version.split()[0])
    try: import requests; chk("requests", True, requests.__version__)
    except: chk("requests", False, "\u672a\u5b89\u88c5")
    try: from PIL import Image; chk("Pillow", True, Image.__version__)
    except: chk("Pillow", False, "\u672a\u5b89\u88c5\uff08\u53ef\u9009\uff09")
    chk("\u914d\u7f6e\u6587\u4ef6", ENV_FILE.exists(), str(ENV_FILE))
    c = load_config()
    chk("API Key", bool(c["api_key"]), "\u5df2\u8bbe\u7f6e" if c["api_key"] else "\u672a\u8bbe\u7f6e")
    chk("API \u5730\u5740", bool(c["api_base"]), c["api_base"] if c["api_base"] else "\u672a\u8bbe\u7f6e")
    chk("\u6a21\u578b", bool(c["model"]), c["model"] if c["model"] else "\u672a\u8bbe\u7f6e")
    if c["api_key"] and c["api_base"]:
        try:
            r = requests.post(c['api_base'].rstrip('/'), json={"model": c['model'] or "test", "messages":[{"role":"user","content":"hi"}], "max_tokens":1, "stream":False}, headers={"Authorization": f"Bearer {c['api_key']}", "Content-Type": "application/json"}, timeout=8)
            ok_api = r.status_code in (200, 400, 422, 429)
            msg = f"{r.status_code}" if r.status_code != 200 else "\u6b63\u5e38"
            if r.status_code == 400:
                try:
                    e = r.json().get('error',{}).get('message','') or r.json().get('message','')
                    msg = f"400 ({e[:40]})" if e else "400 (\u53ef\u8fbe)"
                except: msg = "400 (\u53ef\u8fbe)"
            chk("API \u8fde\u901a", ok_api, msg)
        except Exception as e:
            chk("API \u8fde\u901a", False, str(e)[:50])
    else:
        chk("API \u8fde\u901a", False, "\u8df3\u8fc7")
    print()
    if ok:
        print("  \u4e00\u5207\u6b63\u5e38\uff0c\u53ef\u4ee5\u770b\u56fe\u4e86\u3002")
    else:
        print("  \u6709\u95ee\u9898\u9700\u8981\u4fee\u590d\uff0c\u89c1\u4e0a\u65b9 \u2717 \u6807\u8bb0\u3002")
    sys.exit(0 if ok else 1)


def setup():
    """交互式配置向导"""
    print("OpenVL 配置向导")
    print("=" * 40)
    print()
    
    # skills 安装
    print("AI IDE 集成")
    print("-" * 30)
    import shutil
    skills_map = {
        Path.home() / ".agents" / "skills" / "openvl": ".agents/skills/openvl",
        Path.home() / ".claude" / "skills" / "openvl": ".claude/skills/openvl",
        Path.home() / ".pi" / "agent" / "skills" / "openvl": "Pi skills",
    }
    for p, name in skills_map.items():
        print(f"  {'✓' if p.exists() else '·'} {name}")
    if input("安装 skills？(y/N): ").lower() == "y":
        for p, name in skills_map.items():
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                if p.exists(): shutil.rmtree(p)
                shutil.copytree(SKILL_DIR, p)
                print(f"  ✓ {name}")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
    
    # OpenCode 插件
    print()
    print("OpenCode 插件")
    print("-" * 30)
    oc_plugin = Path.home() / ".config" / "opencode" / "plugin" / "openvl-image.mjs"
    print(f"  {'✓' if oc_plugin.exists() else '·'} OpenCode 插件")
    if not oc_plugin.exists() and input("安装？(y/N): ").lower() == "y":
        oc_plugin.parent.mkdir(parents=True, exist_ok=True)
        src = SKILL_DIR / "integrations" / "opencode" / "openvl-image.mjs"
        if src.exists():
            shutil.copy2(src, oc_plugin)
            print("  ✓ 插件已安装")
            print('  → 在 opencode.json 添加: "plugin": ["./plugin/openvl-image.mjs"]')
        else:
            print("  ✗ 插件源文件未找到")
    
    # API 配置
    print()
    print("=" * 40)
    print()
    
    cfg = load_config()
    
    # API Key
    current = cfg["api_key"]
    if current:
        print(f"当前 API Key: {current[:8]}...{current[-4:]}")
        if input("是否修改？(y/N): ").lower() != "y":
            key = current
        else:
            key = input("输入新的 API Key: ").strip()
    else:
        print("需要配置 API Key")
        key = input("输入你的 API Key: ").strip()
    if key and key != current:
        set_config("key", key)
    
    # API Base
    current_base = cfg["api_base"]
    print()
    if current_base:
        print(f"当前 API 地址: {current_base}")
        if input("是否修改？(y/N): ").lower() != "y":
            api_base = current_base
        else:
            api_base = input("输入 API 地址: ").strip()
    else:
        print("需要配置 API 地址")
        print("常见格式:")
        print("  Chat Completions: https://你的中转站/v1/chat/completions")
        print("  Responses:        https://你的中转站/v1/responses")
        print("  官方 DeepSeek:    https://api.deepseek.com/v1/chat/completions")
        api_base = input("输入 API 地址: ").strip()
    if api_base and api_base != current_base:
        set_config("base", api_base)
    
    # Model
    current_model = cfg["model"]
    print()
    if current_model:
        print(f"当前模型: {current_model}")
        if input("是否修改？(y/N): ").lower() != "y":
            model = current_model
        else:
            model = input("输入模型名: ").strip()
    else:
        model = input("输入模型名（如 deepseek-v4-flash）: ").strip()
    if model and model != current_model:
        set_config("model", model)
    
    print()
    print("=")
    def check(name, status, detail=""):
        nonlocal ok
        mark = "✓" if status else "✗"
        if not status: ok = False
        print(f"  {mark} {name} {detail}")
    
    print(f"OpenVL v{OPENVL_VERSION} 诊断")
    print()
    
    # Python
    check("Python", True, sys.version.split()[0])
    
    # 依赖
    try: import requests; check("requests", True, requests.__version__)
    except: check("requests", False, "未安装，请运行 pip install requests")
    try: from PIL import Image; check("Pillow", True, Image.__version__)
    except: check("Pillow", False, "未安装，请运行 pip install pillow（可选，用于缩放）")
    
    # 配置文件
    cfg_exists = ENV_FILE.exists()
    check("配置文件", cfg_exists, str(ENV_FILE) if cfg_exists else "未找到")
    
    # API 配置
    cfg = load_config()
    has_key = bool(cfg["api_key"])
    has_base = bool(cfg["api_base"])
    check("API Key", has_key, "已设置" if has_key else "未设置")
    check("API 地址", has_base, cfg["api_base"] if has_base else "未设置")
    check("模型", bool(cfg["model"]), cfg["model"] if cfg["model"] else "未设置")
    
    # API 连通性
    if has_key and has_base:
        try:
            r = requests.post(cfg['api_base'].rstrip('/'),
                json={"model": cfg['model'] or "test", "messages":[{"role":"user","content":"hi"}], "max_tokens":1, "stream":False},
                headers={"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"},
                timeout=8)
            ok = r.status_code in (200, 400, 422, 429)
            msg = f"{r.status_code}" if r.status_code != 200 else "正常"
            if r.status_code == 400:
                try:
                    err = r.json()
                    m = err.get('error',{}).get('message','') or err.get('message','')
                    msg = f"400 ({m[:40]})" if m else "400 (请求格式有误，但服务可达)"
                except: msg = "400 (服务可达)"
            check("API 连通", ok, msg)
        except Exception as e:
            check("API 连通", False, str(e)[:50])
    else:
        check("API 连通", False, "跳过（Key 或地址未配置）")
    
    print()
    if ok:
        print("  一切正常，可以看图了。")
    else:
        print("  有问题需要修复，见上方 ✗ 标记。")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--setup", "setup"):
        setup()
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] in ("--doctor", "doctor"):
        doctor()
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "-help", "help"):
        print("用法: openvl <命令> [参数]")
        print()
        print("  看图:")
        print("    openvl <图片路径或URL>       # 从文件或URL看图")
        print("    openvl -c                    # 从剪贴板读图")
        print("    openvl --stdin               # 从 stdin 读 data URI")
        print("    openvl --base64 iVBOR...     # 直接传 base64 数据")
        print("    openvl <图片> -t 0.3         # 温度（0~1，越低越严谨）")
        print("    openvl <图片> -T low         # 思考深度 (low|medium|high)")
        print("    openvl <图片> -s 512         # 图片最大边长（默认1024，越小越省）")
        print()
        print("  配置:")
        print("    openvl -key <密钥>           # 设置 API Key")
        print("    openvl -api <地址>           # 设置 API 地址")
        print("    openvl -model <模型>         # 设置默认模型")
        print("    openvl -cfg                  # 查看当前配置")
        print("    openvl doctor               # 环境诊断")
        print("    openvl setup                # 交互式配置")
        print()
        print("  MCP:")
        print("    openvl --mcp [http|stdio]   # 启动 MCP 服务器")
        print()
        sys.exit(0)
    
    if sys.argv[1] in ("-v", "--version"):
        print(f"OpenVL v{OPENVL_VERSION}")
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

    images = []
    strength = None
    thinking_effort = None
    max_size = 1024
    clip = False
    stdin_mode = False
    base64_mode = False
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
        elif sys.argv[i] == "--stdin":
            stdin_mode = True
        elif sys.argv[i] == "--base64":
            base64_mode = True
        elif sys.argv[i] in ("--clip", "-c"):
            clip = True
        elif sys.argv[i].startswith("-mcp"):
            pass
        else:
            images.append(sys.argv[i])
        i += 1
    
    if stdin_mode:
        images = [sys.stdin.read().strip()]
    
    # 从 images 中分离 query：最后一个参数如果不是文件/URL/data URI 当作问题
    query = None
    if images and not base64_mode and not clip:
        last = images[-1]
        if not os.path.isfile(last) and not last.startswith(("data:", "http://", "https://")):
            query = images.pop()
    
    if "--mcp" in sys.argv:
        mcp_idx = sys.argv.index("--mcp")
        mode = sys.argv[mcp_idx + 1] if mcp_idx + 1 < len(sys.argv) and sys.argv[mcp_idx + 1] in ("http", "stdio") else "stdio"
        os.environ["OPENVL_MCP_MODE"] = mode
        import mcp_server
        mcp_server.main()
        sys.exit(0)

    if clip:
        describe_image(from_clipboard=True, strength=strength, thinking_effort=thinking_effort, query=query, max_size=max_size)
    elif images:
        if base64_mode:
            uri = f"data:image/jpeg;base64,{images[-1]}"
            describe_image(image_source=uri, strength=strength, thinking_effort=thinking_effort, query=query, max_size=max_size)
        else:
            describe_image(image_list=images, strength=strength, thinking_effort=thinking_effort, query=query, max_size=max_size)
    else:
        print("请提供图片路径或使用 -c")
