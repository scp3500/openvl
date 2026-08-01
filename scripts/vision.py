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
import re
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

DEFAULT_MAX_TOKENS = 32768
API_TIMEOUT = 180

# 配置模板占位符特征：load_config 读取时遇到这些内容视为“未配置”，跳过
# （postinstall 不再生成模板，但历史安装/用户手抄模板仍可能残留）
PLACEHOLDER_MARKS = ("你的", "模型ID", "your", "YOUR_API", "replace", "xxx")


def _is_placeholder(text):
    return any(mark in text for mark in PLACEHOLDER_MARKS)


CONFIG_FLAG_TO_KEY = {
    "-key": "key", "--set-key": "key",
    "-api": "base", "--set-base": "base",
    "-model": "model", "--set-model": "model",
    "-max-tokens": "max_tokens", "--set-max-tokens": "max_tokens",
    "-api-type": "api_type", "--set-api-type": "api_type",
}


def _parse_config_args(argv):
    """解析配置命令行参数，支持连写。

    例：["-key", "sk-x", "-api", "https://...", "-model", "m"]
    返回：{"key": "sk-x", "base": "https://...", "model": "m"}
    遇到缺失值或未知参数时抛 ValueError。
    """
    updates = {}
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag not in CONFIG_FLAG_TO_KEY:
            raise ValueError(f"未知配置参数: {flag}")
        if i + 1 >= len(argv):
            raise ValueError(f"请提供 {flag} 的值")
        updates[CONFIG_FLAG_TO_KEY[flag]] = argv[i + 1]
        i += 2
    return updates


def set_config(key, value):
    """写入配置项到 config.env"""
    config = load_config()
    if key == "key":
        config["api_key"] = value
    elif key == "base":
        config["api_base"] = value
    elif key == "model":
        config["model"] = value
    elif key == "api_type":
        config["api_type"] = value.strip().lower()
    elif key == "max_tokens":
        try:
            config["max_tokens"] = int(value)
        except (TypeError, ValueError):
            print(f"无效的 max_tokens: {value}")
            sys.exit(1)
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
                elif line_stripped.startswith("VISION_API_TYPE="):
                    lines.append(f"VISION_API_TYPE={config['api_type']}\n")
                    written.add("api_type")
                elif line_stripped.startswith("VISION_MAX_TOKENS="):
                    lines.append(f"VISION_MAX_TOKENS={config['max_tokens']}\n")
                    written.add("max_tokens")
                else:
                    lines.append(line)
    if "key" not in written:
        lines.append(f"VISION_API_KEY={config['api_key']}\n")
    if "base" not in written:
        lines.append(f"VISION_API_BASE={config['api_base']}\n")
    if "model" not in written:
        lines.append(f"VISION_MODEL={config['model']}\n")
    if "api_type" not in written and key == "api_type":
        lines.append(f"VISION_API_TYPE={config['api_type']}\n")
    if "max_tokens" not in written and key == "max_tokens":
        lines.append(f"VISION_MAX_TOKENS={config['max_tokens']}\n")
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"已设置: {key}={value}")


def load_config():
    config = {"api_key": "", "api_base": "", "model": "", "max_tokens": None, "api_type": ""}

    # 优先级：环境变量 > 配置文件（文件只填空，不覆盖 env）
    env_key = os.environ.get("VISION_API_KEY", "")
    if env_key and not _is_placeholder(env_key):
        config["api_key"] = env_key
    env_base = os.environ.get("VISION_API_BASE", "")
    if env_base and not _is_placeholder(env_base):
        config["api_base"] = env_base.rstrip("/")
    env_model = os.environ.get("VISION_MODEL", "")
    if env_model and not _is_placeholder(env_model):
        config["model"] = env_model
    env_type = os.environ.get("VISION_API_TYPE", "")
    if env_type and not _is_placeholder(env_type):
        config["api_type"] = env_type.strip().lower()
    env_max = os.environ.get("VISION_MAX_TOKENS", "")
    if env_max:
        try:
            config["max_tokens"] = int(env_max)
        except ValueError:
            pass

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
                if line.startswith("VISION_API_KEY=") and not _is_placeholder(line):
                    if not config["api_key"]:
                        config["api_key"] = line.split("=", 1)[1].strip()
                elif line.startswith("VISION_API_BASE=") and not _is_placeholder(line):
                    if not config["api_base"]:
                        config["api_base"] = line.split("=", 1)[1].strip().rstrip("/")
                elif line.startswith("VISION_MODEL=") and not _is_placeholder(line):
                    if not config["model"]:
                        config["model"] = line.split("=", 1)[1].strip()
                elif line.startswith("VISION_API_TYPE=") and not _is_placeholder(line):
                    if not config["api_type"]:
                        config["api_type"] = line.split("=", 1)[1].strip().lower()
                elif line.startswith("VISION_MAX_TOKENS="):
                    if config["max_tokens"] is None:
                        try:
                            config["max_tokens"] = int(line.split("=", 1)[1].strip())
                        except ValueError:
                            pass
    if config["max_tokens"] is None:
        config["max_tokens"] = DEFAULT_MAX_TOKENS
    config["api_base"] = normalize_api_base(config["api_base"], config["api_type"])
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
        import tempfile
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
            suffix = ".jpg" if fmt == "JPEG" else ".png"
            fd, tmp = tempfile.mkstemp(prefix="openvl_", suffix=suffix)
            os.close(fd)
            img.save(tmp, fmt, quality=85)
            return tmp
    except ImportError:
        pass
    except Exception:
        pass
    return image_path

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

FULL_ENDPOINT_RE = re.compile(r"/(chat/completions|responses|messages|:?generateContent|:?streamGenerateContent)$", re.I)
NATIVE_HOST_RE = re.compile(r"generativelanguage|googleapis\.com|anthropic\.com", re.I)


def normalize_api_base(raw, api_type=""):
    """自动补全 API 地址为完整 endpoint。

    用户可填任意形态，自动规范化：
      https://host/v1/chat/completions  → 不动（已是完整 endpoint）
      https://host/v1                  → https://host/v1/chat/completions
      https://host                      → https://host/v1/chat/completions
      gemini/anthropic 原生地址         → 不动（不强行补 OpenAI 路径）

    若显式指定 api_type（如 "responses"），按该类型补全路径。
    """
    url = (raw or "").strip().strip('"').rstrip("/")
    if not url or not url.startswith(("http://", "https://")):
        return url
    if FULL_ENDPOINT_RE.search(url):
        return url
    if NATIVE_HOST_RE.search(url):
        return url
    t = (api_type or "").strip().lower()
    if t == "responses":
        return (url + "/responses") if url.endswith("/v1") else (url + "/v1/responses")
    if url.endswith("/v1"):
        return url + "/chat/completions"
    return url + "/v1/chat/completions"


def detect_api_type(url):
    """根据 URL 自动识别 API 类型"""
    url = (url or "").lower()
    if "googleapis.com" in url or "generativelanguage" in url or "streamgeneratecontent" in url or "generatecontent" in url:
        return "gemini"
    if "api.anthropic.com" in url or url.rstrip("/").endswith("/messages") or "/v1/messages" in url:
        # 仅当明确 anthropic 或 messages 路径时；中转站 /messages 也可能是 chat，优先 anthropic 域名
        if "anthropic" in url or "/v1/messages" in url:
            return "claude"
    if "/responses" in url:
        return "responses"
    return "chat"


def _fail_http(resp):
    print(f"API 请求失败 ({resp.status_code}): {resp.text[:500]}")
    sys.exit(1)


def _iter_sse_lines(resp):
    for line in resp.iter_lines():
        if not line:
            continue
        yield line.decode("utf-8", errors="replace")


def call_gemini(api_url, api_key, payload):
    """调用 Google Gemini API（SSE 流式）"""
    model = payload.get("model", "")
    token = payload.get("max_tokens", DEFAULT_MAX_TOKENS)
    temp = payload.get("temperature", None)

    url = api_url.rstrip("/")
    if "generateContent" not in url and "streamGenerateContent" not in url:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"
    else:
        url = url.replace(":generateContent", ":streamGenerateContent")
    if "key=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}key={api_key}"
    if "alt=sse" not in url:
        url += "&alt=sse" if "?" in url else "?alt=sse"

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

    resp = requests.post(url, json=body, stream=True, timeout=API_TIMEOUT)
    if resp.status_code != 200:
        _fail_http(resp)

    for line in _iter_sse_lines(resp):
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            chunk = json.loads(data)
            cands = chunk.get("candidates") or []
            if not cands:
                continue
            parts = (cands[0].get("content") or {}).get("parts") or []
            for p in parts:
                text = p.get("text")
                if text:
                    print(text, end="", flush=True)
        except json.JSONDecodeError:
            pass
    print()


def call_claude(api_url, api_key, payload):
    """调用 Claude API（SSE 流式）"""
    model = payload.get("model", "")
    token = payload.get("max_tokens", DEFAULT_MAX_TOKENS)
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

    body = {"model": model, "max_tokens": token, "messages": content, "stream": True}
    if temp is not None:
        body["temperature"] = temp

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    url = api_url.rstrip("/")
    if "/messages" not in url:
        url = "https://api.anthropic.com/v1/messages"

    resp = requests.post(url, headers=headers, json=body, stream=True, timeout=API_TIMEOUT)
    if resp.status_code != 200:
        _fail_http(resp)

    for line in _iter_sse_lines(resp):
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            chunk = json.loads(data)
            if chunk.get("type") == "content_block_delta":
                delta = chunk.get("delta") or {}
                text = delta.get("text", "")
                if text:
                    print(text, end="", flush=True)
            elif chunk.get("type") == "error":
                err = chunk.get("error") or chunk
                print(f"\nAPI 流式错误: {err}")
                sys.exit(1)
        except json.JSONDecodeError:
            pass
    print()


def call_responses(api_url, api_key, payload):
    """调用 OpenAI Responses API（流式）"""
    input_items = []
    for msg in payload.get("messages", []):
        content_blocks = []
        for item in msg.get("content", []):
            if item.get("type") == "image_url":
                content_blocks.append({"type": "input_image", "image_url": item["image_url"]["url"]})
            elif item.get("type") == "text":
                content_blocks.append({"type": "input_text", "text": item["text"]})
        input_items.append({"role": msg.get("role", "user"), "content": content_blocks})

    max_tokens = payload.get("max_tokens", DEFAULT_MAX_TOKENS)
    body = {
        "model": payload["model"],
        "input": input_items,
        "max_output_tokens": max_tokens,
        "stream": True,
    }
    if payload.get("temperature") is not None:
        body["temperature"] = payload["temperature"]
    if payload.get("reasoning_effort") is not None:
        body["reasoning"] = {"effort": payload["reasoning_effort"]}

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(api_url, headers=headers, json=body, stream=True, timeout=API_TIMEOUT)
    if resp.status_code != 200:
        _fail_http(resp)
    for line in _iter_sse_lines(resp):
        if line.startswith("data: "):
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                ctype = chunk.get("type")
                if ctype == "response.output_text.delta":
                    print(chunk.get("delta", ""), end="", flush=True)
                elif ctype == "response.failed":
                    print(f"\nAPI 失败: {chunk}")
                    sys.exit(1)
            except json.JSONDecodeError:
                pass
    print()


def call_chat(api_url, api_key, payload):
    """调用 OpenAI Chat Completions API（流式）"""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=API_TIMEOUT)
    if resp.status_code != 200:
        _fail_http(resp)
    for line in _iter_sse_lines(resp):
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

def describe_image(image_source=None, strength=None, thinking_effort=None, from_clipboard=False, query=None, max_size=1024, image_list=None, use_default_prompt=True, max_tokens=None):
    config = load_config()
    if not config["api_key"]:
        print("错误: 未配置 API Key")
        print(f"请编辑 {ENV_FILE} 文件")
        sys.exit(1)
    if not config["api_base"]:
        print("错误: 未配置 API 地址")
        sys.exit(1)
    if max_tokens is None:
        max_tokens = config.get("max_tokens") or DEFAULT_MAX_TOKENS

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
            try:
                b = encode_image(resized)
                mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                            ".webp": "image/webp", ".gif": "image/gif", ".bmp": "image/bmp"}
                m = mime_map.get(Path(resized).suffix.lower(), "image/jpeg")
                return f"data:{m};base64,{b}"
            finally:
                if resized != img_path:
                    try:
                        os.remove(resized)
                    except OSError:
                        pass
        if img_path.startswith("data:"):
            return img_path
        if img_path.startswith("http://") or img_path.startswith("https://"):
            # 部分图站需要代理或 Referer
            dl_url = img_path
            headers = {}
            if "pximg.net" in img_path:
                headers["Referer"] = "https://www.pixiv.net/"
                dl_url = img_path.replace("i.pximg.net", "i.pixiv.cat")
            try:
                r = requests.get(dl_url, headers=headers, timeout=15)
            except requests.exceptions.RequestException as e:
                print(f"下载图片失败: {e}")
                sys.exit(1)
            if not r.ok:
                print(f"下载图片失败 ({r.status_code}): {img_path}")
                sys.exit(1)
            ct = r.headers.get("content-type", "image/jpeg").split(";")[0].strip() or "image/jpeg"
            b64 = base64.b64encode(r.content).decode()
            return f"data:{ct};base64,{b64}"
        print(f"无效的图片: {img_path}")
        sys.exit(1)

    prompt = load_prompt() if use_default_prompt else ""
    if query:
        if use_default_prompt:
            prompt += "\n\n用户问题：" + query
        else:
            prompt = query
    api_type = detect_api_type(config["api_base"])
    forced = config.get("api_type") or ""
    # URL 已带完整 endpoint 时 URL 优先（用户明确信号）；仅 URL 含糊（需补全）时用强制类型
    if forced and not FULL_ENDPOINT_RE.search(config["api_base"]):
        api_type = forced

    content = [{"type": "text", "text": prompt}]
    for s in sources:
        content.append({"type": "image_url", "image_url": {"url": load_image(s)}})

    payload = {
        "model": config["model"],
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "stream": True,
    }
    if strength is not None:
        payload["temperature"] = strength
    if thinking_effort is not None:
        payload["reasoning_effort"] = thinking_effort

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

def _probe_api(config):
    """按 api_type 发最小探测请求，返回 (ok, detail)"""
    api_base = (config.get("api_base") or "").rstrip("/")
    api_key = config.get("api_key") or ""
    model = config.get("model") or "test"
    api_type = detect_api_type(api_base)
    forced = config.get("api_type") or ""
    if forced and not FULL_ENDPOINT_RE.search(api_base):
        api_type = forced
    try:
        if api_type == "gemini":
            url = api_base
            if "generateContent" not in url and "streamGenerateContent" not in url:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            else:
                url = url.replace(":streamGenerateContent", ":generateContent")
            if "key=" not in url:
                sep = "&" if "?" in url else "?"
                url = f"{url}{sep}key={api_key}"
            body = {
                "contents": [{"role": "user", "parts": [{"text": "hi"}]}],
                "generationConfig": {"maxOutputTokens": 1},
            }
            r = requests.post(url, json=body, timeout=8)
        elif api_type == "claude":
            url = api_base if "/messages" in api_base else "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            body = {
                "model": model,
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            }
            r = requests.post(url, headers=headers, json=body, timeout=8)
        elif api_type == "responses":
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            body = {
                "model": model,
                "input": [{"role": "user", "content": [{"type": "input_text", "text": "hi"}]}],
                "max_output_tokens": 16,
                # 部分中转的 /v1/responses 只接受流式；探测与真实请求保持一致
                "stream": True,
            }
            r = requests.post(api_base, headers=headers, json=body, timeout=8)
        else:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            body = {
                "model": model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
                "stream": False,
            }
            r = requests.post(api_base, headers=headers, json=body, timeout=8)

        ok_api = r.status_code in (200, 400, 401, 403, 404, 422, 429)
        if r.status_code == 200:
            msg = f"正常 ({api_type})"
        elif r.status_code in (401, 403):
            msg = f"{r.status_code} 鉴权失败 ({api_type})"
            ok_api = False
        else:
            detail = ""
            try:
                j = r.json()
                detail = (
                    (j.get("error") or {}).get("message")
                    if isinstance(j.get("error"), dict)
                    else j.get("error") or j.get("message") or ""
                )
                if isinstance(detail, dict):
                    detail = detail.get("message") or str(detail)
                detail = str(detail)[:60]
            except Exception:
                detail = (r.text or "")[:60]
            msg = f"{r.status_code} ({api_type}" + (f", {detail}" if detail else "") + ")"
            # 400/422 常表示服务可达但探测 payload 不完全匹配，仍算连通
            if r.status_code in (400, 422, 429):
                ok_api = True
        return ok_api, msg
    except Exception as e:
        return False, f"{api_type}: {str(e)[:50]}"


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
    chk("max_tokens", True, str(c.get("max_tokens") or DEFAULT_MAX_TOKENS))
    if c["api_base"]:
        chk("API \u7c7b\u578b", True, (c.get("api_type") or detect_api_type(c["api_base"])) + (f" (\u5f3a\u5236: {c['api_type']})" if c.get("api_type") else " (\u81ea\u52a8\u8bc6\u522b)"))
    if c["api_key"] and c["api_base"]:
        ok_api, msg = _probe_api(c)
        chk("API \u8fde\u901a", ok_api, msg)
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
    print("配置完成。")
    print()
    doctor()

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
        print("    openvl <图片> -m 8192       # 最大输出 token（默认32768）")
        print()
        print("  配置:")
        print("    openvl -key <密钥>           # 设置 API Key")
        print("    openvl -api <地址>           # 设置 API 地址")
        print("    openvl -model <模型>         # 设置默认模型")
        print("    openvl -max-tokens <N>      # 设置默认 max_tokens")
        print("    openvl -api-type <chat|responses|gemini|claude>  # 强制 API 格式（默认自动识别）")
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

    # 配置管理命令（支持连写：openvl -key X -api Y -model Z -max-tokens N -api-type T）
    if sys.argv[1] in (
        "-key", "--set-key",
        "-api", "--set-base",
        "-model", "--set-model",
        "-max-tokens", "--set-max-tokens",
        "-api-type", "--set-api-type",
    ):
        config_updates = _parse_config_args(sys.argv[1:])
        # api_type 先写：base 的路径补全需要看到强制类型（否则裸地址会被补成 chat/completions）
        for key in ("api_type", "base", "key", "model", "max_tokens"):
            if key in config_updates:
                set_config(key, config_updates[key])
        sys.exit(0)
    if sys.argv[1] in ("--show-config", "-cfg"):
        c = load_config()
        print(f"API 地址: {c['api_base']}")
        print(f"默认模型: {c['model']}")
        print(f"max_tokens: {c.get('max_tokens') or DEFAULT_MAX_TOKENS}")
        print(f"API 类型: {c.get('api_type') or detect_api_type(c.get('api_base') or '')}" + (f" (强制: {c['api_type']})" if c.get('api_type') else " (自动识别)"))
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
    max_tokens = None
    clip = False
    stdin_mode = False
    base64_mode = False
    no_default_prompt = False
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
        elif sys.argv[i] in ("-m", "--max-tokens"):
            i += 1
            try:
                max_tokens = int(sys.argv[i]) if i < len(sys.argv) else None
            except ValueError:
                print(f"无效的 max_tokens: {sys.argv[i]}")
                sys.exit(1)
        elif sys.argv[i] == "--stdin":
            stdin_mode = True
        elif sys.argv[i] == "--base64":
            base64_mode = True
        elif sys.argv[i] in ("--clip", "-c"):
            clip = True
        elif sys.argv[i] == "-P":
            no_default_prompt = True
        elif sys.argv[i].startswith("-mcp"):
            pass
        else:
            images.append(sys.argv[i])
        i += 1
    
    if stdin_mode:
        images = [sys.stdin.read().strip()]
    
    # 从 images 中分离 query：最后一个参数如果不是文件/URL/data URI 当作问题
    # clip 模式也要支持：openvl -c "这张图是什么"
    query = None
    if images and not base64_mode:
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
        describe_image(from_clipboard=True, strength=strength, thinking_effort=thinking_effort, query=query, max_size=max_size, use_default_prompt=not no_default_prompt, max_tokens=max_tokens)
    elif images:
        if base64_mode:
            uri = f"data:image/jpeg;base64,{images[-1]}"
            describe_image(image_source=uri, strength=strength, thinking_effort=thinking_effort, query=query, max_size=max_size, use_default_prompt=not no_default_prompt, max_tokens=max_tokens)
        else:
            describe_image(image_list=images, strength=strength, thinking_effort=thinking_effort, query=query, max_size=max_size, use_default_prompt=not no_default_prompt, max_tokens=max_tokens)
    else:
        print("请提供图片路径或使用 -c")
