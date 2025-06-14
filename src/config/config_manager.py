"""
配置管理器
负责加载和管理应用配置和用户设置
"""

import json
import os
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = config_dir
        self.app_config_file = os.path.join(config_dir, "app_config.json")
        self.user_settings_file = os.path.join(config_dir, "user_settings.json")
        
        self._app_config: Dict[str, Any] = {}
        self._user_settings: Dict[str, Any] = {}
        
        # 加载配置
        self.load_config()
    
    def load_config(self):
        """加载所有配置文件"""
        self._load_app_config()
        self._load_user_settings()
    
    def _load_app_config(self):
        """加载应用配置"""
        try:
            if os.path.exists(self.app_config_file):
                with open(self.app_config_file, 'r', encoding='utf-8') as f:
                    self._app_config = json.load(f)
                print(f"加载应用配置: {self.app_config_file}")
            else:
                print(f"应用配置文件不存在: {self.app_config_file}")
                self._app_config = self._get_default_app_config()
        except Exception as e:
            print(f"加载应用配置失败: {e}")
            self._app_config = self._get_default_app_config()
    
    def _load_user_settings(self):
        """加载用户设置"""
        try:
            if os.path.exists(self.user_settings_file):
                with open(self.user_settings_file, 'r', encoding='utf-8') as f:
                    self._user_settings = json.load(f)
                print(f"加载用户设置: {self.user_settings_file}")
            else:
                print(f"用户设置文件不存在: {self.user_settings_file}")
                self._user_settings = self._get_default_user_settings()
        except Exception as e:
            print(f"加载用户设置失败: {e}")
            self._user_settings = self._get_default_user_settings()
    
    def _get_default_app_config(self) -> Dict[str, Any]:
        """获取默认应用配置"""
        return {
            "version": "0.1.0",
            "data_format_version": "1.0",
            "data_directory": "user_data",
            "backup_settings": {
                "auto_backup": True,
                "backup_interval_days": 7,
                "max_backup_files": 10
            },
            "display_settings": {
                "currency_symbol": "¥",
                "decimal_places": 2,
                "date_format": "YYYY-MM-DD",
                "percentage_format": "0.00%"
            },
            "default_categories": [
                {
                    "primary": "固定收益类",
                    "secondary": ["定期存款", "国债", "企业债", "债券基金"]
                },
                {
                    "primary": "股票类",
                    "secondary": ["A股", "港股", "美股", "股票基金"]
                },
                {
                    "primary": "基金类",
                    "secondary": ["货币基金", "债券基金", "股票基金", "混合基金", "指数基金"]
                },
                {
                    "primary": "房地产",
                    "secondary": ["住宅", "商业地产", "REITs"]
                },
                {
                    "primary": "其他",
                    "secondary": ["贵金属", "商品", "数字货币", "其他投资"]
                }
            ]
        }
    
    def _get_default_user_settings(self) -> Dict[str, Any]:
        """获取默认用户设置"""
        return {
            "user_preferences": {
                "default_category": "",
                "auto_save": True,
                "show_tooltips": True,
                "theme": "light",
                "language": "zh_CN"
            },
            "window_settings": {
                "width": 1200,
                "height": 800,
                "maximized": False,
                "position_x": 100,
                "position_y": 100
            },
            "data_settings": {
                "auto_refresh": True,
                "refresh_interval_minutes": 30,
                "show_zero_values": False
            },
            "export_settings": {
                "default_format": "xlsx",
                "include_charts": True,
                "include_summary": True
            }
        }
    
    def get_app_config(self, key: str = None) -> Any:
        """
        获取应用配置
        
        Args:
            key: 配置键，如果为None则返回所有配置
            
        Returns:
            配置值
        """
        if key is None:
            return self._app_config
        return self._app_config.get(key)
    
    def get_user_setting(self, key: str = None) -> Any:
        """
        获取用户设置
        
        Args:
            key: 设置键，如果为None则返回所有设置
            
        Returns:
            设置值
        """
        if key is None:
            return self._user_settings
        return self._user_settings.get(key)
    
    def set_user_setting(self, key: str, value: Any) -> bool:
        """
        设置用户设置
        
        Args:
            key: 设置键
            value: 设置值
            
        Returns:
            是否设置成功
        """
        try:
            # 支持嵌套键，如 "window_settings.width"
            keys = key.split('.')
            current = self._user_settings
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = value
            return self.save_user_settings()
        except Exception as e:
            print(f"设置用户设置失败: {e}")
            return False
    
    def save_user_settings(self) -> bool:
        """
        保存用户设置到文件
        
        Returns:
            是否保存成功
        """
        try:
            # 确保配置目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            with open(self.user_settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._user_settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存用户设置失败: {e}")
            return False
    
    def get_data_directory(self) -> str:
        """获取数据目录路径"""
        return self.get_app_config("data_directory") or "user_data"
    
    def get_default_categories(self) -> list:
        """获取默认分类列表"""
        return self.get_app_config("default_categories") or []
    
    def get_window_settings(self) -> Dict[str, Any]:
        """获取窗口设置"""
        return self.get_user_setting("window_settings") or {}
    
    def get_display_settings(self) -> Dict[str, Any]:
        """获取显示设置"""
        return self.get_app_config("display_settings") or {}


# 全局配置管理器实例
config_manager = ConfigManager() 