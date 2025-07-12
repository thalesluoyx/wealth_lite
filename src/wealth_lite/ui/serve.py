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
import urllib.request
import urllib.error
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 确保stdout使用utf-8编码，解决emoji显示问题
if sys.stdout.encoding != 'utf-8':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

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
    
    def do_GET(self):
        """处理GET请求"""
        # 如果是API请求，转发到API服务器
        if self.path.startswith('/api/'):
            self.proxy_request('GET')
        else:
            # 否则正常处理
            super().do_GET()
    
    def do_POST(self):
        """处理POST请求"""
        # 如果是API请求，转发到API服务器
        if self.path.startswith('/api/'):
            self.proxy_request('POST')
        else:
            # 否则正常处理
            super().do_POST()
    
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        # 如果是API请求，转发到API服务器
        if self.path.startswith('/api/'):
            self.proxy_request('OPTIONS')
        else:
            # 否则正常处理
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
    
    def proxy_request(self, method):
        """将请求代理到API服务器"""
        api_url = f"http://localhost:8081{self.path}"
        
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # 创建请求
            headers = {k: v for k, v in self.headers.items() 
                      if k.lower() not in ('host', 'content-length')}
            
            # 确保设置正确的Content-Type
            if method == 'POST' and 'content-type' not in map(str.lower, headers.keys()):
                headers['Content-Type'] = 'application/json'
            
            req = urllib.request.Request(
                api_url,
                data=body,
                headers=headers,
                method=method
            )
            
            # 发送请求到API服务器
            with urllib.request.urlopen(req) as response:
                # 设置响应状态码
                self.send_response(response.status)
                
                # 读取响应体
                response_data = response.read()
                
                # 设置响应头
                for header, value in response.getheaders():
                    if header.lower() not in ('transfer-encoding', 'content-encoding', 'content-length'):
                        self.send_header(header, value)
                
                # 设置正确的Content-Length
                self.send_header('Content-Length', str(len(response_data)))
                
                # 确保设置正确的Content-Type
                if 'content-type' not in map(str.lower, dict(response.getheaders()).keys()):
                    self.send_header('Content-Type', 'application/json')
                
                # 结束头部
                self.end_headers()
                
                # 发送响应体
                self.wfile.write(response_data)
                
                # 记录成功的API请求
                print(f"API代理: {method} {self.path} -> {response.status}")
                
        except urllib.error.HTTPError as e:
            # 处理HTTP错误
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            
            # 尝试读取错误响应
            try:
                error_data = e.read()
                error_json = json.loads(error_data)
                error_message = json.dumps(error_json)
            except:
                error_message = json.dumps({
                    "success": False,
                    "error": f"API服务器错误: {str(e)}"
                })
            
            # 设置正确的Content-Length
            error_bytes = error_message.encode('utf-8')
            self.send_header('Content-Length', str(len(error_bytes)))
            self.end_headers()
            
            self.wfile.write(error_bytes)
            print(f"API代理错误: {method} {self.path} -> {e.code}")
            
        except urllib.error.URLError as e:
            # 处理连接错误
            self.send_response(503)  # Service Unavailable
            self.send_header('Content-Type', 'application/json')
            
            error_message = json.dumps({
                "success": False,
                "error": f"无法连接到API服务器: {str(e.reason)}"
            })
            
            # 设置正确的Content-Length
            error_bytes = error_message.encode('utf-8')
            self.send_header('Content-Length', str(len(error_bytes)))
            self.end_headers()
            
            self.wfile.write(error_bytes)
            print(f"API代理连接失败: {method} {self.path} -> {str(e.reason)}")
            
        except Exception as e:
            # 处理其他错误
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            
            error_message = json.dumps({
                "success": False,
                "error": f"代理请求错误: {str(e)}"
            })
            
            # 设置正确的Content-Length
            error_bytes = error_message.encode('utf-8')
            self.send_header('Content-Length', str(len(error_bytes)))
            self.end_headers()
            
            self.wfile.write(error_bytes)
            print(f"API代理错误: {method} {self.path} -> {str(e)}")
    
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
            print(f"正在打开浏览器: {url}")
        except Exception as e:
            print(f"无法自动打开浏览器: {e}")
            print(f"请手动访问: {url}")
    
    thread = threading.Thread(target=_open)
    thread.daemon = True
    thread.start()

def start_file_watcher():
    """启动文件监听器"""
    def on_file_changed(file_path):
        rel_path = os.path.relpath(file_path)
        print(f"文件已更改: {rel_path}")
        print("请刷新浏览器查看更改")
    
    event_handler = FileWatcher(on_file_changed)
    observer = Observer()
    observer.schedule(event_handler, path='app', recursive=True)
    observer.start()
    return observer

def main():
    """主函数"""
    print("启动 WealthLite UI 开发服务器...")
    
    # 自动定位app目录（以本文件为基准）
    base_dir = Path(__file__).parent
    app_dir = base_dir / 'app'
    if not app_dir.exists():
        print(f"错误: 未找到app目录: {app_dir}")
        sys.exit(1)
    
    # 加载配置
    config = load_config()
    default_port = config.get('dev_port', 8000)
    
    try:
        # 查找可用端口
        port = find_free_port(default_port)
        
        print(f"开发服务器地址: http://localhost:{port}")
        print(f"服务目录: {app_dir.absolute()}")
        print(f"开发模式: 启用CORS和热重载提示")
        print(f"API代理: 将 /api/* 请求转发到 http://localhost:8081")
        
        # 启动文件监听器
        def on_file_changed(file_path):
            rel_path = os.path.relpath(file_path, app_dir)
            print(f"文件已更改: {rel_path}")
            print("请刷新浏览器查看更改")
        event_handler = FileWatcher(on_file_changed)
        observer = Observer()
        observer.schedule(event_handler, path=str(app_dir), recursive=True)
        observer.start()
        print("文件监听器: 已启动")
        
        # 创建服务器
        server = HTTPServer(('localhost', port), lambda *args, **kwargs: WealthLiteDevHandler(*args, directory=str(app_dir), **kwargs))
        
        print("开发提示:")
        print("  - 修改文件后刷新浏览器查看更改")
        print("  - 按 Ctrl+C 停止服务器")
        print("  - 查看演示: cd demo && python start_demo.py")
        print("=" * 50)
        
        # 启动服务器
        print(f"开发服务器已启动在端口 {port}")
        
        # 自动打开浏览器（默认禁用）
        auto_open_browser = config.get('auto_open_browser', False)
        if auto_open_browser:
            dev_url = f"http://localhost:{port}"
            open_browser(dev_url)
        else:
            print(f"请手动访问: http://localhost:{port}")
        
        # 启动服务器
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        if 'observer' in locals():
            observer.stop()
            observer.join()
        print("服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 