"""
JSON文件存储管理器

提供配置文件和设置的JSON格式存储功能。
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class JSONStorage:
    """JSON文件存储管理器"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化JSON存储管理器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.config_file = self.data_dir / "config.json"
        self.settings_file = self.data_dir / "settings.json"
        
        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self.default_config = {
            "version": "0.1.0",
            "created_date": datetime.now().isoformat(),
            "data_format_version": "1.0",
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
            }
        }
        
        # 默认用户设置
        self.default_settings = {
            "user_preferences": {
                "default_category": "",
                "auto_save": True,
                "show_tooltips": True,
                "theme": "default"
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
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        if not self.config_file.exists():
            # 如果配置文件不存在，创建默认配置
            self.save_config(self.default_config)
            return self.default_config.copy()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 合并默认配置（处理新增的配置项）
            merged_config = self._merge_config(self.default_config, config)
            
            # 如果配置有更新，保存回文件
            if merged_config != config:
                self.save_config(merged_config)
            
            return merged_config
            
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        保存配置文件
        
        Args:
            config: 配置字典
            
        Returns:
            是否保存成功
        """
        try:
            # 添加更新时间
            config["updated_date"] = datetime.now().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def load_settings(self) -> Dict[str, Any]:
        """
        加载用户设置
        
        Returns:
            设置字典
        """
        if not self.settings_file.exists():
            # 如果设置文件不存在，创建默认设置
            self.save_settings(self.default_settings)
            return self.default_settings.copy()
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 合并默认设置
            merged_settings = self._merge_config(self.default_settings, settings)
            
            # 如果设置有更新，保存回文件
            if merged_settings != settings:
                self.save_settings(merged_settings)
            
            return merged_settings
            
        except Exception as e:
            print(f"加载设置文件失败: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        保存用户设置
        
        Args:
            settings: 设置字典
            
        Returns:
            是否保存成功
        """
        try:
            # 添加更新时间
            settings["updated_date"] = datetime.now().isoformat()
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"保存设置文件失败: {e}")
            return False
    
    def get_setting(self, key_path: str, default_value: Any = None) -> Any:
        """
        获取指定路径的设置值
        
        Args:
            key_path: 设置键路径，用点分隔，如 "user_preferences.theme"
            default_value: 默认值
            
        Returns:
            设置值
        """
        settings = self.load_settings()
        
        # 按路径获取值
        keys = key_path.split('.')
        value = settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default_value
    
    def set_setting(self, key_path: str, value: Any) -> bool:
        """
        设置指定路径的设置值
        
        Args:
            key_path: 设置键路径
            value: 设置值
            
        Returns:
            是否设置成功
        """
        settings = self.load_settings()
        
        # 按路径设置值
        keys = key_path.split('.')
        current = settings
        
        try:
            # 导航到父级字典
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 设置最终值
            current[keys[-1]] = value
            
            return self.save_settings(settings)
            
        except Exception as e:
            print(f"设置配置值失败: {e}")
            return False
    
    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并配置字典，用用户配置覆盖默认配置
        
        Args:
            default: 默认配置
            user: 用户配置
            
        Returns:
            合并后的配置
        """
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # 递归合并嵌套字典
                merged[key] = self._merge_config(merged[key], value)
            else:
                # 直接覆盖
                merged[key] = value
        
        return merged
    
    def export_data(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        导出数据到JSON文件
        
        Args:
            file_path: 文件路径
            data: 要导出的数据
            
        Returns:
            是否导出成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"导出数据失败: {e}")
            return False
    
    def import_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        从JSON文件导入数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            导入的数据，失败时返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"导入数据失败: {e}")
            return None
    
    def reset_to_defaults(self) -> bool:
        """
        重置所有配置为默认值
        
        Returns:
            是否重置成功
        """
        try:
            # 创建新的默认配置（更新时间戳）
            fresh_default_config = {
                "version": "0.1.0",
                "created_date": datetime.now().isoformat(),
                "data_format_version": "1.0",
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
                }
            }
            
            fresh_default_settings = {
                "user_preferences": {
                    "default_category": "",
                    "auto_save": True,
                    "show_tooltips": True,
                    "theme": "default"
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
                }
            }
            
            # 重置配置文件
            config_success = self.save_config(fresh_default_config)
            
            # 重置设置文件
            settings_success = self.save_settings(fresh_default_settings)
            
            return config_success and settings_success
            
        except Exception as e:
            print(f"重置配置失败: {e}")
            return False
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        获取JSON文件信息
        
        Returns:
            文件信息字典
        """
        info = {
            "config_file": {
                "path": str(self.config_file),
                "exists": self.config_file.exists(),
                "size": self.config_file.stat().st_size if self.config_file.exists() else 0,
                "modified": datetime.fromtimestamp(
                    self.config_file.stat().st_mtime
                ).isoformat() if self.config_file.exists() else None
            },
            "settings_file": {
                "path": str(self.settings_file),
                "exists": self.settings_file.exists(),
                "size": self.settings_file.stat().st_size if self.settings_file.exists() else 0,
                "modified": datetime.fromtimestamp(
                    self.settings_file.stat().st_mtime
                ).isoformat() if self.settings_file.exists() else None
            }
        }
        
        return info 