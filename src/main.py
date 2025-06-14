#!/usr/bin/env python3
"""
WealthLite 主程序入口
启动GUI应用程序
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

try:
    from gui.main_window import MainWindow
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有依赖模块都已正确安装")
    sys.exit(1)


def main():
    """主函数"""
    try:
        # 创建并运行主窗口
        app = MainWindow()
        app.run()
    except Exception as e:
        # 显示错误信息
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showerror("启动错误", f"应用程序启动失败:\n{e}")
        root.destroy()
        sys.exit(1)


if __name__ == "__main__":
    main() 