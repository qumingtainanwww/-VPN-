#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller 打包脚本 - NodeCollector 网页版
双击运行或命令行执行: python build_exe.py
"""

import os
import sys
import shutil
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent
MAIN_SCRIPT = BASE_DIR / "网页版NodeCollector.py"
OUTPUT_DIR = BASE_DIR / "dist_exe"

# 检查主脚本是否存在
if not MAIN_SCRIPT.exists():
    print(f"错误: 找不到主程序 {MAIN_SCRIPT}")
    sys.exit(1)

# 清理旧的构建
if OUTPUT_DIR.exists():
    print("清理旧的构建文件...")
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

# PyInstaller 命令参数
cmd = [
    "pyinstaller",
    "--onefile",                      # 打包成单个 EXE
    "--noconsole",                    # 无控制台窗口（GUI模式）
    f"--name=NodeCollector",         # EXE 名称
    f"--distpath={OUTPUT_DIR}",      # 输出目录
    "--add-data", f"templates{os.pathsep}templates",   # 添加模板目录
    "--add-data", f"static{os.pathsep}static",         # 添加静态文件目录
    "--hidden-import", "flask",
    "--hidden-import", "requests",
    "--hidden-import", "concurrent.futures",
    "--hidden-import", "pyperclip",
    "--hidden-import", "urllib.parse",
    "--hidden-import", "json",
    "--hidden-import", "base64",
    "--hidden-import", "hashlib",
    "--hidden-import", "webbrowser",
    str(MAIN_SCRIPT)
]

print("=" * 60)
print("NodeCollector EXE 打包工具")
print("=" * 60)
print(f"\n主程序: {MAIN_SCRIPT}")
print(f"输出目录: {OUTPUT_DIR}")
print("\n开始打包...\n")

# 执行打包
import subprocess
result = subprocess.run(cmd, cwd=str(BASE_DIR))

if result.returncode == 0:
    print("\n" + "=" * 60)
    print("✓ 打包成功!")
    print("=" * 60)
    exe_path = OUTPUT_DIR / "NodeCollector.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n生成文件: {exe_path}")
        print(f"文件大小: {size_mb:.2f} MB")
        print("\n使用说明:")
        print("1. 双击 NodeCollector.exe 启动")
        print("2. 浏览器会自动打开 http://127.0.0.1:5000")
        print("3. nodes 目录会在 EXE 同目录自动创建\n")
    else:
        print("\n警告: 未找到生成的 EXE 文件")
else:
    print("\n" + "=" * 60)
    print("✗ 打包失败，请检查错误信息")
    print("=" * 60)
    sys.exit(1)
