"""
资产类型选择对话框

让用户选择要创建的资产类型。
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class AssetTypeSelector:
    """资产类型选择对话框"""
    
    def __init__(self, parent):
        self.parent = parent
        self.selected_type = None
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("选择资产类型")
        self.dialog.geometry("450x420")  # 增加宽度和高度
        self.dialog.resizable(True, True)  # 允许调整大小
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_dialog()
        
        # 创建界面
        self._create_widgets()
    
    def _center_dialog(self):
        """对话框居中显示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="请选择要创建的资产类型", font=("TkDefaultFont", 12, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 资产类型列表
        asset_types = [
            ("固定收益类", "定期存款、国债、企业债、债券基金等"),
            ("股票类", "股票投资、股票基金等"),
            ("基金类", "货币基金、混合基金、指数基金等"),
            ("房地产", "房产投资、REITs等"),
            ("其他", "其他类型的投资")
        ]
        
        # 创建单选按钮
        self.asset_type_var = tk.StringVar(value="固定收益类")
        
        for asset_type, description in asset_types:
            frame = ttk.Frame(main_frame)
            frame.pack(fill=tk.X, pady=5)
            
            # 单选按钮
            radio = ttk.Radiobutton(
                frame,
                text=asset_type,
                variable=self.asset_type_var,
                value=asset_type,
                command=self._on_type_change
            )
            radio.pack(anchor=tk.W)
            
            # 描述
            desc_label = ttk.Label(frame, text=f"  {description}", foreground="gray")
            desc_label.pack(anchor=tk.W, padx=(20, 0))
        
        # 特殊表单提示
        self.special_form_label = ttk.Label(
            main_frame, 
            text="✓ 此类型有专门的表单界面", 
            foreground="green",
            font=("TkDefaultFont", 9)
        )
        self.special_form_label.pack(pady=(10, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
      
        # 取消按钮
        ttk.Button(button_frame, text="取消", command=self._cancel).pack(side=tk.RIGHT)
          # 确定按钮
        ttk.Button(button_frame, text="确定", command=self._confirm).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 初始化提示
        self._on_type_change()
    
    def _on_type_change(self):
        """资产类型变化时的处理"""
        asset_type = self.asset_type_var.get()
        
        # 检查是否有专门的表单
        specialized_types = {"固定收益类"}
        
        if asset_type in specialized_types:
            self.special_form_label.config(
                text="✓ 此类型有专门的表单界面",
                foreground="green"
            )
            self.special_form_label.pack(pady=(10, 0))
        else:
            self.special_form_label.config(
                text="○ 此类型使用通用表单界面",
                foreground="gray"
            )
            self.special_form_label.pack(pady=(10, 0))
    
    def _confirm(self):
        """确定选择"""
        self.selected_type = self.asset_type_var.get()
        self.dialog.destroy()
    
    def _cancel(self):
        """取消选择"""
        self.selected_type = None
        self.dialog.destroy()
    
    def show(self) -> Optional[str]:
        """显示对话框并返回选择的资产类型"""
        self.dialog.wait_window()
        return self.selected_type 