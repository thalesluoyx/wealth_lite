"""
枚举生成器服务

在服务器启动时生成前端需要的枚举JSON文件，实现前后端枚举数据的统一管理。
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any

from ..models.enums import AssetType, AssetSubType, Currency, TransactionType, RiskLevel, LiquidityLevel


class EnumGeneratorService:
    """枚举生成器服务"""
    
    def __init__(self, output_dir: str = "src/wealth_lite/ui/app/data"):
        self.output_dir = Path(output_dir)
        self.output_file = self.output_dir / "enums.json"
        
    def generate_enums_file(self) -> bool:
        """生成枚举JSON文件"""
        try:
            # 确保输出目录存在
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成枚举数据
            enums_data = self._generate_enums_data()
            
            # 写入JSON文件
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(enums_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"✅ 枚举文件生成成功: {self.output_file}")
            return True
            
        except Exception as e:
            logging.error(f"❌ 生成枚举文件失败: {e}", exc_info=True)
            return False
    
    def _generate_enums_data(self) -> Dict[str, Any]:
        """生成完整的枚举数据"""
        return {
            # 元数据
            "meta": {
                "version": "1.0.0",
                "generated_at": "2025-01-21T00:00:00Z",
                "description": "WealthLite系统枚举定义，由后端自动生成"
            },
            
            # 资产类型
            "asset_types": {
                item.name: {
                    "display_name": item.display_name,
                    "value": item.value
                } for item in AssetType
            },
            
            # 资产子类型
            "asset_subtypes": {
                item.name: {
                    "display_name": item.display_name,
                    "value": item.value,
                    "parent_type": item.get_asset_type().name
                } for item in AssetSubType
            },
            
            # 资产子类型映射（按主类型分组）
            "asset_subtype_mapping": {
                asset_type.name: [
                    {
                        "value": subtype.name,
                        "text": subtype.display_name,
                        "description": subtype.value
                    }
                    for subtype in AssetSubType.get_subtypes_by_asset_type(asset_type)
                ]
                for asset_type in AssetType
            },
            
            # 货币类型
            "currencies": {
                item.name: {
                    "display_name": item.display_name,
                    "symbol": item.symbol,
                    "value": item.value
                } for item in Currency
            },
            
            # 交易类型
            "transaction_types": {
                item.name: {
                    "display_name": item.display_name,
                    "value": item.value,
                    "is_income": item.is_income,
                    "is_expense": item.is_expense
                } for item in TransactionType
            },
            
            # 风险等级
            "risk_levels": {
                item.name: {
                    "display_name": item.display_name,
                    "value": item.value,
                    "risk_score": item.risk_score
                } for item in RiskLevel
            },
            
            # 流动性等级
            "liquidity_levels": {
                item.name: {
                    "display_name": item.display_name,
                    "value": item.value,
                    "liquidity_score": item.liquidity_score
                } for item in LiquidityLevel
            }
        }
    
    def get_output_file_path(self) -> str:
        """获取输出文件路径"""
        return str(self.output_file)
    
    def file_exists(self) -> bool:
        """检查枚举文件是否存在"""
        return self.output_file.exists()
    
    def get_file_age_seconds(self) -> float:
        """获取文件年龄（秒）"""
        if not self.file_exists():
            return float('inf')
        
        import time
        return time.time() - self.output_file.stat().st_mtime 