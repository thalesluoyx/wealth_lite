#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WealthLite UI 演示服务器启动脚本
"""

import os
import sys
import webbrowser
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

class WealthLiteHandler(SimpleHTTPRequestHandler):
    """自定义HTTP处理器"""
    
    def __init__(self, *args, **kwargs):
        # 设置服务目录为ui文件夹
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def end_headers(self):
        # 添加CORS头部支持
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def log_message(self, format, *args):
        # 简化日志输出
        return

def find_free_port(start_port=8000):
    """查找可用端口"""
    import socket
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError("无法找到可用端口")

def open_browser(url, delay=1.5):
    """延迟打开浏览器"""
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            print(f"🌐 正在打开浏览器: {url}")
        except Exception as e:
            print(f"⚠️ 无法自动打开浏览器: {e}")
            print(f"请手动访问: {url}")
    
    thread = threading.Thread(target=_open)
    thread.daemon = True
    thread.start()

def main():
    """主函数"""
    print("🚀 启动 WealthLite UI 演示服务器...")

    # 允许在demo目录下直接运行
    demo_dir = Path(__file__).parent
    if not demo_dir.name == 'demo':
        print("❌ 错误: 请在demo目录下运行此脚本")
        sys.exit(1)

    # 检查必要文件（只检查实际存在的demo页面）
    demo_files = ['demo.html', 'demo_modules.html', 'stagewise_demo.html', 'test_stagewise.html']
    missing_files = [f for f in demo_files if not (demo_dir / f).exists()]
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        sys.exit(1)

    try:
        # 查找可用端口
        port = find_free_port()
        print(f"📍 服务器地址: http://localhost:{port}")
        print(f"📁 服务目录: {demo_dir.absolute()}")

        # 创建服务器
        server = HTTPServer(('localhost', port), WealthLiteHandler)

        # 显示可用页面
        print(f"🌐 可用页面:")
        print(f"  - 完整模块演示: http://localhost:{port}/demo_modules.html")
        print(f"  - 基础演示: http://localhost:{port}/demo.html")
        print(f"  - 交互演示: http://localhost:{port}/stagewise_demo.html")
        print(f"  - 测试演示: http://localhost:{port}/test_stagewise.html")

        print("💡 提示:")
        print("  - 打开浏览器访问上述地址查看演示")
        print("  - 按 Ctrl+C 停止服务器")
        print("  - 演示界面包含完整的模块划分和交互功能")
        print("=" * 50)

        # 启动服务器
        print(f"✅ 服务器已启动在端口 {port}")

        # 自动打开完整模块演示页面
        demo_url = f"http://localhost:{port}/demo_modules.html"
        open_browser(demo_url)

        # 启动服务器
        server.serve_forever()

    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 