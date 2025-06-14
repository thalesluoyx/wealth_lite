#!/usr/bin/env python3
"""
WealthLite 主启动脚本
在根目录运行的启动入口
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# 启动应用程序
if __name__ == "__main__":
    try:
        from main import main
        main()
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有依赖模块都已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"启动错误: {e}")
        sys.exit(1) 