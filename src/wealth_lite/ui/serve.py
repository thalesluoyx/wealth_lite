#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WealthLite UI 开发服务器
提供开发环境的HTTP服务和热重载功能
"""

import os
import sys
import json
import webbrowser
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WealthLiteDevHandler(SimpleHTTPRequestHandler):
    """开发环境HTTP处理器"""
    
    def __init__(self, *args, **kwargs):
        # 不再传递directory参数，避免重复
        super().__init__(*args, **kwargs)
    
    def end_headers(self):
        # 添加CORS头部和开发环境头部
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def log_message(self, format, *args):
        # 简化日志输出
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] {format % args}")

class FileWatcher(FileSystemEventHandler):
    """文件变更监听器"""
    
    def __init__(self, callback):
        self.callback = callback
        self.last_modified = {}
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # 只监听特定文件类型
        if not event.src_path.endswith(('.html', '.css', '.js')):
            return
        
        # 防止重复触发
        current_time = time.time()
        if event.src_path in self.last_modified:
            if current_time - self.last_modified[event.src_path] < 1:
                return
        
        self.last_modified[event.src_path] = current_time
        self.callback(event.src_path)

def load_config():
    """加载配置文件"""
    try:
        with open('package.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('config', {})
    except FileNotFoundError:
        return {}

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

def open_browser(url, delay=2):
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

def start_file_watcher():
    """启动文件监听器"""
    def on_file_changed(file_path):
        rel_path = os.path.relpath(file_path)
        print(f"📝 文件已更改: {rel_path}")
        print("🔄 请刷新浏览器查看更改")
    
    event_handler = FileWatcher(on_file_changed)
    observer = Observer()
    observer.schedule(event_handler, path='app', recursive=True)
    observer.start()
    return observer

def main():
    """主函数"""
    print("🚀 启动 WealthLite UI 开发服务器...")
    
    # 自动定位app目录（以本文件为基准）
    base_dir = Path(__file__).parent
    app_dir = base_dir / 'app'
    if not app_dir.exists():
        print(f"❌ 错误: 未找到app目录: {app_dir}")
        sys.exit(1)
    
    # 加载配置
    config = load_config()
    default_port = config.get('dev_port', 8000)
    
    try:
        # 查找可用端口
        port = find_free_port(default_port)
        
        print(f"📍 开发服务器地址: http://localhost:{port}")
        print(f"📁 服务目录: {app_dir.absolute()}")
        print(f"🔧 开发模式: 启用CORS和热重载提示")
        
        # 启动文件监听器
        def on_file_changed(file_path):
            rel_path = os.path.relpath(file_path, app_dir)
            print(f"📝 文件已更改: {rel_path}")
            print("🔄 请刷新浏览器查看更改")
        event_handler = FileWatcher(on_file_changed)
        observer = Observer()
        observer.schedule(event_handler, path=str(app_dir), recursive=True)
        observer.start()
        print("👀 文件监听器: 已启动")
        
        # 创建服务器
        server = HTTPServer(('localhost', port), lambda *args, **kwargs: WealthLiteDevHandler(*args, directory=str(app_dir), **kwargs))
        
        print("💡 开发提示:")
        print("  - 修改文件后刷新浏览器查看更改")
        print("  - 按 Ctrl+C 停止服务器")
        print("  - 查看演示: cd demo && python start_demo.py")
        print("=" * 50)
        
        # 启动服务器
        print(f"✅ 开发服务器已启动在端口 {port}")
        
        # 自动打开浏览器
        dev_url = f"http://localhost:{port}"
        open_browser(dev_url)
        
        # 启动服务器
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务器...")
        if 'observer' in locals():
            observer.stop()
            observer.join()
        print("✅ 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 