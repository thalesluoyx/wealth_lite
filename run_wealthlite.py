#!/usr/bin/env python3
"""
WealthLite 启动脚本
简化的应用程序启动入口
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# 启动应用程序
if __name__ == "__main__":
    from main import main
    main() 