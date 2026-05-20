#!/usr/bin/env python3
"""从剪贴板读图并调用 OpenVL 描述"""
import os, sys, subprocess
script = os.path.join(os.path.dirname(__file__), "vision.py")
subprocess.run([sys.executable, script, "--clip"] + sys.argv[1:])
