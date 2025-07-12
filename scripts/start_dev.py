#!/usr/bin/env python3
"""
开发环境启动脚本
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
import argparse

# 设置开发环境
os.environ['WEALTH_LITE_ENV'] = 'development'

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def open_browser_with_delay(url, delay=2):
    """延迟打开浏览器"""
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            print(f"🌐 正在打开浏览器: {url}")
        except Exception as e:
            print(f"❌ 无法自动打开浏览器: {e}")
            print(f"🔗 请手动访问: {url}")
    
    thread = threading.Thread(target=_open)
    thread.daemon = True
    thread.start()
    return thread

def run_main_app():
    """运行主应用"""
    from main import main as main_app
    main_app()

# 启动应用
if __name__ == "__main__":
    print("🚀 启动 WealthLite 开发环境...")
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='WealthLite 开发环境启动脚本')
    parser.add_argument('--no-browser', action='store_true', help='禁止自动打开浏览器')
    args = parser.parse_args()
    
    try:
        # 启动主应用
        print("🖥️ 启动WealthLite应用服务器")
        
        # 运行主应用
        run_main_app()
    
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务器...")
        print("✅ 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)