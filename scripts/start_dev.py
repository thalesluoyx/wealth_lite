#!/usr/bin/env python3
"""
开发环境启动脚本
"""

import os
import sys
from pathlib import Path

# 设置开发环境
os.environ['WEALTH_LITE_ENV'] = 'development'

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 启动应用
if __name__ == "__main__":
    from main import main
    main()