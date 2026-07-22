#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenVL 本地测试（默认不打真实 API）。

用法:
  python tests/test_openvl.py
  python tests/test_openvl.py --e2e          # 额外跑真实看图（需已配置 API）
  npm test
"""

from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
VISION_PY = ROOT / "scripts" / "vision.py"
MCP_JS = ROOT / "scripts" / "mcp_server.js"
BIN_OPENVL = ROOT / "bin" / "openvl"


def load_vision():
    spec = importlib.util.spec_from_file_location("openvl_vision", VISION_PY)
    mod = importlib.util.module_from_spec(spec)
    # 避免被当前进程 argv 影响
    with mock.patch.object(sys, "argv", ["vision.py"]):
        spec.loader.exec_module(mod)
    return mod


class TestDetectApiType(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = load_vision()

    def test_chat(self):
        self.assertEqual(self.v.detect_api_type("https://x.com/v1/chat/completions"), "chat")

    def test_responses(self):
        self.assertEqual(self.v.detect_api_type("https://x.com/v1/responses"), "responses")

    def test_gemini(self):
        url = "https://generativelanguage.googleapis.com/v1beta/models/m:generateContent"
        self.assertEqual(self.v.detect_api_type(url), "gemini")

    def test_claude(self):
        self.assertEqual(self.v.detect_api_type("https://api.anthropic.com/v1/messages"), "claude")


class TestLoadConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = load_vision()

    def setUp(self):
        self._env = {
            k: os.environ.get(k)
            for k in ("VISION_API_KEY", "VISION_API_BASE", "VISION_MODEL", "VISION_MAX_TOKENS")
        }

    def tearDown(self):
        for k, val in self._env.items():
            if val is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = val

    def test_env_overrides_file(self):
        os.environ["VISION_API_KEY"] = "ENV_KEY_ONLY"
        os.environ["VISION_API_BASE"] = "https://env.example/v1/chat/completions"
        os.environ["VISION_MODEL"] = "env-model"
        os.environ["VISION_MAX_TOKENS"] = "7777"
        cfg = self.v.load_config()
        self.assertEqual(cfg["api_key"], "ENV_KEY_ONLY")
        self.assertIn("env.example", cfg["api_base"])
        self.assertEqual(cfg["model"], "env-model")
        self.assertEqual(cfg["max_tokens"], 7777)

    def test_default_max_tokens(self):
        os.environ.pop("VISION_MAX_TOKENS", None)
        cfg = self.v.load_config()
        # 文件若未写 max_tokens，应落到默认
        self.assertIsInstance(cfg["max_tokens"], int)
        self.assertGreaterEqual(cfg["max_tokens"], 1024)
        self.assertEqual(self.v.DEFAULT_MAX_TOKENS, 16384)


class TestCliParsing(unittest.TestCase):
    """复刻 CLI 分离 query 的逻辑，防止 -c 带问题再回归。"""

    def _parse(self, argv):
        images = []
        clip = False
        base64_mode = False
        max_tokens = None
        i = 1
        while i < len(argv):
            if argv[i] == "-t":
                i += 1
            elif argv[i] in ("-T", "--think"):
                i += 1
            elif argv[i] in ("-s", "--size"):
                i += 1
            elif argv[i] in ("-m", "--max-tokens"):
                i += 1
                max_tokens = int(argv[i]) if i < len(argv) else None
            elif argv[i] == "--stdin":
                pass
            elif argv[i] == "--base64":
                base64_mode = True
            elif argv[i] in ("--clip", "-c"):
                clip = True
            elif argv[i] == "-P":
                pass
            elif argv[i].startswith("-mcp"):
                pass
            else:
                images.append(argv[i])
            i += 1

        query = None
        if images and not base64_mode:
            last = images[-1]
            if not os.path.isfile(last) and not last.startswith(("data:", "http://", "https://")):
                query = images.pop()
        return {"images": images, "query": query, "clip": clip, "base64_mode": base64_mode, "max_tokens": max_tokens}

    def test_clip_with_query(self):
        r = self._parse(["vision.py", "-c", "这张图是什么"])
        self.assertTrue(r["clip"])
        self.assertEqual(r["query"], "这张图是什么")
        self.assertEqual(r["images"], [])

    def test_clip_only(self):
        r = self._parse(["vision.py", "-c"])
        self.assertTrue(r["clip"])
        self.assertIsNone(r["query"])

    def test_file_with_query(self):
        r = self._parse(["vision.py", "a.png", "描述一下"])
        self.assertEqual(r["images"], ["a.png"])
        self.assertEqual(r["query"], "描述一下")

    def test_url_with_query(self):
        r = self._parse(["vision.py", "https://x.com/a.png", "OCR"])
        self.assertEqual(r["images"], ["https://x.com/a.png"])
        self.assertEqual(r["query"], "OCR")

    def test_max_tokens_flag(self):
        r = self._parse(["vision.py", "a.png", "-m", "8192", "问题"])
        self.assertEqual(r["max_tokens"], 8192)
        self.assertEqual(r["query"], "问题")
        self.assertEqual(r["images"], ["a.png"])

    def test_base64_does_not_steal_query(self):
        r = self._parse(["vision.py", "--base64", "iVBORxxx"])
        self.assertTrue(r["base64_mode"])
        self.assertIsNone(r["query"])
        self.assertEqual(r["images"], ["iVBORxxx"])


class TestSetupAndSourceGuards(unittest.TestCase):
    def test_setup_calls_doctor(self):
        src = VISION_PY.read_text(encoding="utf-8")
        setup = src[src.index("def setup()") : src.index('if __name__')]
        self.assertIn("doctor()", setup)
        self.assertNotIn("nonlocal ok", setup)

    def test_providers_are_streaming(self):
        src = VISION_PY.read_text(encoding="utf-8")
        self.assertIn("streamGenerateContent", src)
        self.assertIn("content_block_delta", src)
        self.assertIn("response.output_text.delta", src)
        self.assertNotIn('"max_tokens": 1024', src)
        self.assertNotIn('"max_output_tokens": 1024', src)

    def test_url_fail_no_silent_fallback(self):
        src = VISION_PY.read_text(encoding="utf-8")
        start = src.index('if img_path.startswith("http://")')
        end = src.index('print(f"无效的图片', start)
        branch = src[start:end]
        self.assertIn("下载图片失败", branch)
        self.assertNotIn("return img_path", branch)

    def test_resize_uses_tempdir(self):
        src = VISION_PY.read_text(encoding="utf-8")
        self.assertIn("tempfile.mkstemp", src)


class TestResizeImage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = load_vision()

    def test_large_image_goes_to_temp(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")

        d = Path(tempfile.mkdtemp())
        img_path = d / "big.png"
        Image.new("RGB", (2000, 2000), "red").save(img_path)
        resized = self.v.resize_image(str(img_path), max_size=256)
        try:
            self.assertNotEqual(resized, str(img_path))
            self.assertTrue(Path(resized).exists())
            self.assertNotEqual(Path(resized).parent.resolve(), d.resolve())
            # 图片目录不应出现临时文件
            leftovers = [p for p in d.iterdir() if p.name != "big.png"]
            self.assertEqual(leftovers, [])
        finally:
            if resized != str(img_path) and os.path.exists(resized):
                os.remove(resized)


class TestCliSmoke(unittest.TestCase):
    def _run(self, *args, timeout=30):
        return subprocess.run(
            [sys.executable, "-X", "utf8", str(VISION_PY), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT),
        )

    def test_help(self):
        r = self._run("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("用法", r.stdout)
        self.assertIn("-m", r.stdout)

    def test_version(self):
        r = self._run("-v")
        self.assertEqual(r.returncode, 0)
        self.assertIn("OpenVL", r.stdout)

    def test_cfg(self):
        r = self._run("-cfg")
        self.assertEqual(r.returncode, 0)
        self.assertIn("max_tokens", r.stdout)
        self.assertIn("API", r.stdout)

    def test_bad_url_image(self):
        r = self._run("https://example.invalid/no-such.png", timeout=30)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("下载图片失败", r.stdout + r.stderr)


class TestMcpSmoke(unittest.TestCase):
    def test_initialize(self):
        if not MCP_JS.exists():
            self.skipTest("mcp_server.js missing")
        proc = subprocess.run(
            ["node", str(MCP_JS)],
            input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n',
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "OPENVL_MCP_MODE": "stdio"},
        )
        self.assertIn("openvl", proc.stdout)
        # 不应把 key 前缀打到 stderr
        self.assertNotRegex(proc.stderr, r"API Key: .*\.\.\.")

    def test_tools_list(self):
        proc = subprocess.run(
            ["node", str(MCP_JS)],
            input=(
                '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
                '{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n'
            ),
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "OPENVL_MCP_MODE": "stdio"},
        )
        self.assertIn("describe_image", proc.stdout)
        self.assertIn("describe_clipboard", proc.stdout)


class TestBinEntry(unittest.TestCase):
    def test_help_via_node(self):
        if not BIN_OPENVL.exists():
            self.skipTest("bin/openvl missing")
        r = subprocess.run(
            ["node", str(BIN_OPENVL), "--help"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("用法", r.stdout)


class TestLiveE2E(unittest.TestCase):
    def test_describe_simple_image(self):
        if os.environ.get("OPENVL_RUN_E2E") != "1":
            self.skipTest("pass --e2e (or OPENVL_RUN_E2E=1) to run live API test")
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow not installed")

        p = Path(tempfile.gettempdir()) / "openvl_test_e2e.png"
        img = Image.new("RGB", (240, 140), (30, 90, 200))
        d = ImageDraw.Draw(img)
        d.rectangle([16, 16, 224, 124], outline=(255, 220, 0), width=4)
        d.text((40, 60), "OpenVL", fill=(255, 255, 255))
        img.save(p)

        r = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                str(VISION_PY),
                str(p),
                "-P",
                "-m",
                "256",
                "用一句话说明主色和是否有黄框",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.strip())


def main():
    e2e = os.environ.get("OPENVL_RUN_E2E") == "1"
    # 只把标准 unittest 参数交给 loader
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if e2e and result.wasSuccessful():
        print("\n(已包含 --e2e 真实 API 用例)")
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    if "--e2e" in sys.argv:
        os.environ["OPENVL_RUN_E2E"] = "1"
        sys.argv = [a for a in sys.argv if a != "--e2e"]
    main()
