#!/usr/bin/env python3
"""
调试资产类型选择器

测试资产类型选择器是否能正常工作。
"""

import sys
import os

# 添加src目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_dir)

import tkinter as tk
from tkinter import messagebox
from data.asset_manager import AssetManager
from models.category import CategoryManager
from gui.asset_form_factory import AssetFormFactory
from gui.asset_type_selector import AssetTypeSelector


def test_asset_selector():
    """测试资产类型选择器"""
    root = tk.Tk()
    root.title("调试资产类型选择器")
    root.geometry("300x200")
    
    def on_new_asset():
        """新建资产测试"""
        print("开始新建资产流程...")
        
        # 显示资产类型选择对话框
        selector = AssetTypeSelector(root)
        selected_type = selector.show()
        
        print(f"用户选择的资产类型: {selected_type}")
        
        if not selected_type:
            messagebox.showinfo("信息", "用户取消了选择")
            return
        
        # 初始化管理器
        asset_manager = AssetManager("test_data")
        category_manager = CategoryManager()
        
        # 根据选择的类型创建对应的表单
        try:
            form = AssetFormFactory.create_form(
                root, 
                asset_manager, 
                category_manager, 
                asset_type=selected_type
            )
            print(f"创建的表单类型: {type(form).__name__}")
            
            # 显示表单
            result = form.show()
            print(f"表单返回结果: {result}")
            
            if result:
                messagebox.showinfo("成功", f"成功创建{selected_type}资产！")
            else:
                messagebox.showinfo("信息", "用户取消了表单")
                
        except Exception as e:
            print(f"创建表单时出错: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"创建表单失败: {e}")
    
    # 创建测试按钮
    btn = tk.Button(root, text="测试新建资产", command=on_new_asset, font=("TkDefaultFont", 12))
    btn.pack(expand=True)
    
    # 添加说明
    label = tk.Label(root, text="点击按钮测试资产类型选择器", wraplength=250)
    label.pack(pady=10)
    
    root.mainloop()


if __name__ == "__main__":
    test_asset_selector() 