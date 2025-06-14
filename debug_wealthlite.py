#!/usr/bin/env python3
"""
WealthLite 调试脚本
逐步测试各个模块的导入和功能
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def test_step(step_name, test_func):
    """测试步骤"""
    print(f"\n{step_name}...")
    try:
        test_func()
        print(f"✓ {step_name} 成功")
        return True
    except Exception as e:
        print(f"✗ {step_name} 失败: {e}")
        return False

def test_basic_imports():
    """测试基础模块导入"""
    from models.asset import Asset
    from models.category import CategoryManager
    from data.asset_manager import AssetManager

def test_gui_imports():
    """测试GUI模块导入"""
    from gui.asset_list import AssetList
    from gui.asset_form import AssetForm
    from gui.main_window import MainWindow

def test_create_managers():
    """测试创建管理器对象"""
    from data.asset_manager import AssetManager
    from models.category import CategoryManager
    
    asset_manager = AssetManager("data")
    category_manager = CategoryManager()
    print(f"  - AssetManager创建成功")
    print(f"  - CategoryManager创建成功")

def test_create_gui():
    """测试创建GUI对象"""
    import tkinter as tk
    from gui.main_window import MainWindow
    
    # 创建主窗口但不运行mainloop
    app = MainWindow()
    print(f"  - MainWindow创建成功")
    
    # 销毁窗口
    app.root.destroy()

def main():
    """主函数"""
    print("=" * 60)
    print("WealthLite 调试测试")
    print("=" * 60)
    
    # 测试步骤
    steps = [
        ("测试基础模块导入", test_basic_imports),
        ("测试GUI模块导入", test_gui_imports),
        ("测试创建管理器对象", test_create_managers),
        ("测试创建GUI对象", test_create_gui),
    ]
    
    success_count = 0
    for step_name, test_func in steps:
        if test_step(step_name, test_func):
            success_count += 1
        else:
            break
    
    print(f"\n" + "=" * 60)
    print(f"测试结果: {success_count}/{len(steps)} 步骤成功")
    
    if success_count == len(steps):
        print("✓ 所有测试通过！现在尝试启动完整的GUI...")
        try:
            from gui.main_window import MainWindow
            app = MainWindow()
            print("✓ WealthLite GUI启动成功！")
            app.run()
        except Exception as e:
            print(f"✗ GUI启动失败: {e}")
    else:
        print("✗ 存在问题，请检查上述错误信息")

if __name__ == "__main__":
    main() 