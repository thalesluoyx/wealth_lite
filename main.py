#!/usr/bin/env python3
"""
WealthLite 主应用入口
整合FastAPI后端和前端UI，提供完整的桌面应用体验
"""

import os
import sys
import threading
import webbrowser
from pathlib import Path
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from src.wealth_lite.config.log_config import setup_logging, LOG_LEVEL
import glob
import time

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent / "src"))

from src.wealth_lite.data.database import DatabaseManager
from src.wealth_lite.services.wealth_service import WealthService
from src.wealth_lite.services.enum_generator import EnumGeneratorService
from src.wealth_lite.services.snapshot_service import SnapshotService, AIConfigService
from src.wealth_lite.services.ai_service import ai_analysis_service
from src.wealth_lite.models.enums import AssetType, AssetSubType, Currency, TransactionType
from src.wealth_lite.config.env_loader import load_environment, get_env
from src.wealth_lite.config.prompt_templates import get_available_prompt_types

# 加载环境变量
load_environment()

# 初始化日志
setup_logging(LOG_LEVEL)

db_manager = DatabaseManager()
wealth_service = WealthService(db_manager)
config_service = AIConfigService(db_manager)
snapshot_service = SnapshotService(db_manager, wealth_service)

class WealthLiteApp:
    """WealthLite 应用主类"""
    
    def __init__(self):
        self.app = None
        self.wealth_service = None
        self.db_manager = None
        self.host = "127.0.0.1"
        self.port = 8080
        
    def initialize_services(self):
        """初始化服务"""
        try:
            # 初始化数据库 - 根据环境变量自动选择数据库
            
            self.db_manager = DatabaseManager()
            self.wealth_service = WealthService(self.db_manager)
            
            # 生成前端枚举文件
            enum_generator = EnumGeneratorService()
            if enum_generator.generate_enums_file():
                logging.info("✅ 前端枚举文件生成成功")
            else:
                logging.warning("⚠️ 前端枚举文件生成失败，前端将使用备用数据")
            
            # 创建启动时的自动快照
            try:
                from wealth_lite.services.snapshot_service import SnapshotService
                snapshot_service = SnapshotService(self.db_manager, self.wealth_service)
                snapshot = snapshot_service.create_startup_snapshot()
                if snapshot:
                    logging.info(f"✅ 自动快照创建成功: {snapshot.snapshot_id}")
                else:
                    logging.info("ℹ️ 今日自动快照已存在，跳过创建")
            except Exception as e:
                logging.warning(f"⚠️ 自动快照创建失败: {e}")
                # 不阻断应用启动
            
            logging.info("✅ 数据库服务初始化成功")
            logging.info(f"wealth_service 初始化完成，依赖 db_manager 状态: {self.db_manager.is_connected()}")
            
        except Exception as e:
            logging.error(f"❌ 服务初始化失败: {e}", exc_info=True)
            raise
    
    def create_app(self) -> FastAPI:
        """创建FastAPI应用"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # 启动时初始化服务
            self.initialize_services()
            yield
            # 关闭时清理资源
            if self.db_manager:
                self.db_manager.close()
        
        app = FastAPI(
            title="WealthLite",
            description="个人财富管理系统",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # 添加CORS中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 注册API路由
        self.register_api_routes(app)
        
        # 静态文件服务（开发环境禁用缓存）
        ui_path = Path(__file__).parent / "src" / "wealth_lite" / "ui" / "app"
        if ui_path.exists():
            # 创建自定义静态文件类，禁用缓存
            class NoCacheStaticFiles(StaticFiles):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                
                def file_response(self, *args, **kwargs):
                    response = super().file_response(*args, **kwargs)
                    # 添加禁用缓存的响应头
                    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                    response.headers["Pragma"] = "no-cache"
                    response.headers["Expires"] = "0"
                    return response
            
            app.mount("/static", NoCacheStaticFiles(directory=str(ui_path), html=True), name="static")
        
        # 根路径重定向到主页
        @app.get("/")
        async def root():
            return RedirectResponse(url="/static/index.html")
        
        # Favicon
        @app.get("/favicon.ico")
        async def favicon():
            favicon_path = Path(__file__).parent / "src" / "wealth_lite" / "ui" / "app" / "favicon.ico"
            if favicon_path.exists():
                return FileResponse(str(favicon_path))
            else:
                raise HTTPException(status_code=404, detail="Favicon not found")
        
        return app
    
    def register_api_routes(self, app: FastAPI):
        """注册API路由"""
        
        @app.get("/api/health")
        async def health_check():
            """健康检查"""
            return {"status": "healthy", "service": "WealthLite"}

        # ==================== 快照管理 API ====================
        
        @app.get("/api/portfolio/current")
        async def get_current_portfolio():
            """获取当前投资组合状态"""
            try:
                from wealth_lite.services.snapshot_service import SnapshotService
                
                # 使用SnapshotService获取当前投资组合状态
                portfolio = self.wealth_service.get_portfolio()
                
                if not portfolio:
                    return {
                        "success": True,
                        "data": {
                            "total_value": 0,
                            "total_cost": 0,
                            "total_return": 0,
                            "total_return_rate": 0
                        }
                    }
                
                # 计算当前投资组合状态
                total_value = sum(pos.current_book_value for pos in portfolio.positions)
                total_cost = sum(pos.net_invested for pos in portfolio.positions)
                total_return = total_value - total_cost
                total_return_rate = (total_return / total_cost * 100) if total_cost > 0 else 0
                
                return {
                    "success": True,
                    "data": {
                        "total_value": float(total_value),
                        "total_cost": float(total_cost),
                        "total_return": float(total_return),
                        "total_return_rate": float(total_return_rate)
                    }
                }
                
            except Exception as e:
                logging.error(f"❌ 获取当前投资组合失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        @app.get("/api/snapshots")
        async def get_snapshots(type: str = "auto", limit: int = 50, offset: int = 0):
            """获取快照列表"""
            try:
                from wealth_lite.services.snapshot_service import SnapshotService
                from wealth_lite.models.enums import SnapshotType
                
                # 转换快照类型
                snapshot_type = SnapshotType.AUTO if type.lower() == 'auto' else SnapshotType.MANUAL
                
                # 获取快照列表
                snapshots = snapshot_service.get_snapshots_by_type(snapshot_type, limit, offset)
                
                # 转换为前端格式
                snapshots_data = []
                for snapshot in snapshots:
                    snapshots_data.append({
                        "snapshot_id": snapshot.snapshot_id,
                        "snapshot_date": snapshot.snapshot_date.isoformat(),
                        "snapshot_type": snapshot.snapshot_type.value,
                        "total_value": float(snapshot.total_value),
                        "total_return": float(snapshot.total_return),
                        "total_return_rate": float(snapshot.total_return_rate),
                        "notes": snapshot.notes,
                        "is_today": snapshot.is_today
                    })
                
                # 统计信息
                stats = {
                    "total_count": len(snapshots),
                    "type": type
                }
                
                return {
                    "success": True,
                    "data": {
                        "snapshots": snapshots_data,
                        "stats": stats
                    }
                }
                
            except Exception as e:
                logging.error(f"❌ 获取快照列表失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        @app.post("/api/snapshots")
        async def create_snapshot(snapshot_data: dict):
            """创建手动快照"""
            try:
                from wealth_lite.services.snapshot_service import SnapshotService
                
                notes = snapshot_data.get("notes", "")
                
                # 创建手动快照
                snapshot = snapshot_service.create_manual_snapshot(notes)
                
                return {
                    "success": True,
                    "data": {
                        "snapshot_id": snapshot.snapshot_id,
                        "snapshot_date": snapshot.snapshot_date.isoformat(),
                        "snapshot_type": snapshot.snapshot_type.value,
                        "total_value": float(snapshot.total_value),
                        "notes": snapshot.notes
                    },
                    "message": "快照创建成功"
                }
                
            except Exception as e:
                logging.error(f"❌ 创建快照失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        @app.get("/api/snapshots/{snapshot_id}")
        async def get_snapshot_detail(snapshot_id: str):
            """获取快照详情"""
            try:
                # 不要在这里 import 或 new SnapshotService
                snapshot = snapshot_service.get_snapshot_by_id(snapshot_id)
                if not snapshot:
                    return {
                        "success": False,
                        "message": "快照不存在"
                    }
                return {
                    "success": True,
                    "data": {
                        "snapshot": snapshot.to_dict()
                    }
                }
            except Exception as e:
                logging.error(f"❌ 获取快照详情失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        @app.delete("/api/snapshots/{snapshot_id}")
        async def delete_snapshot(snapshot_id: str):
            """删除快照"""
            try:
                from wealth_lite.services.snapshot_service import SnapshotService
                
                result = snapshot_service.delete_snapshot(snapshot_id)
                
                if result:
                    return {
                        "success": True,
                        "message": "快照删除成功"
                    }
                else:
                    return {
                        "success": False,
                        "message": "无法删除快照"
                    }
                
            except Exception as e:
                logging.error(f"❌ 删除快照失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        @app.get("/api/snapshots/today/manual")
        async def check_today_manual_snapshot():
            """检查今日是否已有手动快照"""
            try:
                from wealth_lite.services.snapshot_service import SnapshotService
                from wealth_lite.models.enums import SnapshotType
                from datetime import date
                
                snapshot = snapshot_service.get_snapshot_by_date_and_type(date.today(), SnapshotType.MANUAL)
                
                return {
                    "success": True,
                    "data": {
                        "snapshot": {
                            "snapshot_id": snapshot.snapshot_id,
                            "snapshot_date": snapshot.snapshot_date.isoformat(),
                            "total_value": float(snapshot.total_value)
                        } if snapshot else None
                    }
                }
                
            except Exception as e:
                logging.error(f"❌ 检查今日快照失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        @app.post("/api/snapshots/compare")
        async def compare_snapshots(comparison_data: dict):
            """对比两个快照"""
            try:
                from wealth_lite.services.snapshot_service import SnapshotService
                
                snapshot1_id = comparison_data.get("snapshot1_id")
                snapshot2_id = comparison_data.get("snapshot2_id")
                
                if not snapshot1_id or not snapshot2_id:
                    return {
                        "success": False,
                        "message": "需要提供两个快照ID"
                    }
                
                # 进行快照对比
                comparison = snapshot_service.compare_snapshots(snapshot1_id, snapshot2_id)
                
                return {
                    "success": True,
                    "data": comparison
                }
                
            except Exception as e:
                logging.error(f"❌ 快照对比失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        # ==================== AI分析 API ====================
        
        @app.get("/api/ai/configs")
        async def get_ai_configs():
            """获取AI配置列表"""
            try:
                configs = config_service.get_all_configs()
                default_config = config_service.get_default_config()
                
                configs_data = []
                for config in configs:
                    configs_data.append({
                        "config_id": config.config_id,
                        "config_name": config.config_name,
                        "ai_type": config.ai_type.value,
                        "is_default": config.is_default,
                        "display_name": f"{config.config_name} ({config.ai_type.value})"
                    })
                
                return {
                    "success": True,
                    "data": {
                        "configs": configs_data,
                        "default_config": {
                            "config_id": default_config.config_id,
                            "ai_type": default_config.ai_type.value
                        } if default_config else None
                    }
                }
                
            except Exception as e:
                logging.error(f"❌ 获取AI配置失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        @app.post("/api/ai/configs/switch")
        async def switch_ai_config(config_data: dict):
            """切换AI配置"""
            try:
                from src.wealth_lite.models.enums import AIType
                ai_type_str = config_data.get("ai_type")
                if not ai_type_str:
                    return {
                        "success": False,
                        "message": "需要提供AI类型"
                    }
                ai_type = AIType.LOCAL if ai_type_str == "LOCAL" else AIType.CLOUD
                config = config_service.switch_ai_type(ai_type)
                return {
                    "success": True,
                    "data": {
                        "config_id": config.config_id,
                        "ai_type": config.ai_type.value
                    },
                    "message": "AI配置已更新"
                }
            except Exception as e:
                logging.error(f"❌ 切换AI配置失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        @app.post("/api/ai/analysis/snapshots")
        async def analyze_snapshots_with_ai(analysis_data: dict):
            """使用AI分析快照对比"""
            try:
                snapshot1_id = analysis_data.get("snapshot1_id")
                snapshot2_id = analysis_data.get("snapshot2_id")
                config_id = analysis_data.get("config_id")
                user_prompt = analysis_data.get("user_prompt", "")
                conversation_id = analysis_data.get("conversation_id")
                
                # 获取prompt类型
                system_prompt_type = analysis_data.get("system_prompt_type", "default")
                user_prompt_type = analysis_data.get("user_prompt_type", "default")
                result_template_type = analysis_data.get("result_template_type", "default")
                
                # 获取快照
                snapshot1 = snapshot_service.get_snapshot_by_id(snapshot1_id)
                snapshot2 = snapshot_service.get_snapshot_by_id(snapshot2_id) if snapshot2_id else None
                
                if not snapshot1:
                    return {
                        "success": False,
                        "message": "快照1不存在"
                    }
                
                # 获取AI配置
                ai_config = config_service.get_config_by_id(config_id) if config_id else config_service.get_default_config()
                
                if not ai_config:
                    return {
                        "success": False,
                        "message": "AI配置不存在"
                    }
                
                # 执行分析
                if snapshot2:
                    # 对比分析
                    result = ai_analysis_service.compare_snapshots(
                        snapshot1, snapshot2, ai_config, user_prompt, conversation_id,
                        system_prompt_type, user_prompt_type, result_template_type
                    )
                else:
                    # 单快照分析
                    result = ai_analysis_service.analyze_snapshot(
                        snapshot1, ai_config, user_prompt, conversation_id,
                        system_prompt_type, user_prompt_type, result_template_type
                    )
                
                return {
                    "success": True,
                    "data": result.to_dict()
                }
                
            except Exception as e:
                logging.error(f"❌ AI分析失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }
        
        @app.post("/api/ai/conversation/continue")
        async def continue_ai_conversation(conversation_data: dict):
            """继续AI对话"""
            try:
                conversation_id = conversation_data.get("conversation_id")
                user_message = conversation_data.get("message", "")
                config_id = conversation_data.get("config_id")
                
                if not conversation_id:
                    return {
                        "success": False,
                        "message": "对话ID不能为空"
                    }
                
                if not user_message:
                    return {
                        "success": False,
                        "message": "消息内容不能为空"
                    }
                
                # 获取AI配置
                ai_config = config_service.get_config_by_id(config_id) if config_id else config_service.get_default_config()
                
                # 继续对话
                response = ai_analysis_service.continue_conversation(conversation_id, user_message, ai_config)
                
                return {
                    "success": True,
                    "data": {
                        "conversation_id": conversation_id,
                        "response": response
                    }
                }
                
            except Exception as e:
                logging.error(f"❌ 继续AI对话失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }
        
        @app.get("/api/ai/conversation/{conversation_id}")
        async def get_ai_conversation(conversation_id: str):
            """获取AI对话历史"""
            try:
                conversation = ai_analysis_service.get_conversation(conversation_id)
                
                if not conversation:
                    return {
                        "success": False,
                        "message": "对话不存在"
                    }
                
                return {
                    "success": True,
                    "data": {
                        "conversation_id": conversation_id,
                        "messages": conversation
                    }
                }
                
            except Exception as e:
                logging.error(f"❌ 获取AI对话历史失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }
        
        @app.delete("/api/ai/conversation/{conversation_id}")
        async def delete_ai_conversation(conversation_id: str):
            """删除AI对话历史"""
            try:
                success = ai_analysis_service.clear_conversation(conversation_id)
                
                if success:
                    return {
                        "success": True,
                        "message": "对话历史已删除"
                    }
                else:
                    return {
                        "success": False,
                        "message": "对话不存在"
                    }
                
            except Exception as e:
                logging.error(f"❌ 删除AI对话历史失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        @app.get("/api/ai/analysis/{analysis_id}")
        async def get_ai_analysis_result(analysis_id: str):
            """获取AI分析结果"""
            try:
                # 这里暂时返回模拟数据，后续需要实现数据库存储
                return {
                    "success": True,
                    "data": {
                        "analysis_id": analysis_id,
                        "analysis_status": "SUCCESS",
                        "analysis_summary": "投资组合表现良好",
                        "investment_advice": "建议继续持有",
                        "risk_assessment": "风险可控",
                        "processing_time_ms": 1500,
                        "created_date": datetime.now().isoformat()
                    }
                }
                
            except Exception as e:
                logging.error(f"❌ 获取AI分析结果失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }
        
        @app.post("/api/ai/configs")
        async def create_ai_config(config_data: dict):
            """创建AI配置"""
            try:
                from wealth_lite.models.snapshot import AIAnalysisConfig
                from wealth_lite.models.enums import AIType
                
                # 构建配置对象
                config = AIAnalysisConfig(
                    config_name=config_data.get("config_name", ""),
                    ai_type=AIType[config_data.get("ai_type", "CLOUD")],
                    cloud_provider=config_data.get("cloud_provider", ""),
                    cloud_api_key=config_data.get("cloud_api_key", ""),
                    cloud_api_url=config_data.get("cloud_api_url", ""),
                    cloud_model_name=config_data.get("cloud_model_name", ""),
                    local_model_name=config_data.get("local_model_name", ""),
                    local_api_port=config_data.get("local_api_port", 11434),
                    max_tokens=config_data.get("max_tokens", 4000),
                    temperature=config_data.get("temperature", 0.7),
                    timeout_seconds=config_data.get("timeout_seconds", 30)
                )
                
                # 保存配置
                success = config_service.save_config(config)
                
                if success:
                    return {
                        "success": True,
                        "data": config.to_dict()
                    }
                else:
                    return {
                        "success": False,
                        "message": "保存配置失败"
                    }
                    
            except Exception as e:
                logging.error(f"❌ 创建AI配置失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }
        
        @app.post("/api/ai/configs/test")
        async def test_ai_config(config_data: dict):
            """测试AI配置"""
            try:
                from wealth_lite.models.snapshot import AIAnalysisConfig
                from wealth_lite.models.enums import AIType
                
                # 构建临时配置对象进行测试
                config = AIAnalysisConfig(
                    config_name=config_data.get("config_name", "测试配置"),
                    ai_type=AIType[config_data.get("ai_type", "CLOUD")],
                    cloud_provider=config_data.get("cloud_provider", ""),
                    cloud_api_key=config_data.get("cloud_api_key", ""),
                    cloud_api_url=config_data.get("cloud_api_url", ""),
                    cloud_model_name=config_data.get("cloud_model_name", ""),
                    local_model_name=config_data.get("local_model_name", ""),
                    local_api_port=config_data.get("local_api_port", 11434),
                    max_tokens=config_data.get("max_tokens", 4000),
                    temperature=config_data.get("temperature", 0.7),
                    timeout_seconds=config_data.get("timeout_seconds", 30)
                )
                
                # 测试配置
                test_result = ai_analysis_service.test_ai_config(config)
                
                return {
                    "success": True,
                    "data": test_result
                }
                    
            except Exception as e:
                logging.error(f"❌ 测试AI配置失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }
        
        @app.post("/api/ai/configs/predefined")
        async def create_predefined_configs():
            """创建预定义的AI配置"""
            try:
                configs = config_service.create_predefined_configs()
                
                return {
                    "success": True,
                    "message": f"创建了 {len(configs)} 个预定义配置",
                    "data": [config.to_dict() for config in configs]
                }
                
            except Exception as e:
                logging.error(f"❌ 创建预定义配置失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        @app.get("/api/ai/prompt-types")
        async def get_available_ai_prompt_types():
            """获取可用的AI提示类型"""
            try:
                prompt_types = get_available_prompt_types()
                
                return {
                    "success": True,
                    "data": prompt_types
                }
                
            except Exception as e:
                logging.error(f"❌ 获取AI提示类型失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "message": str(e)
                }

        # ==================== 原有的API路由 ====================


        @app.get("/api/dashboard/summary")
        async def get_dashboard_summary():
            """获取仪表板总览数据"""
            try:
                logging.info("🔄 开始获取仪表板数据...")
                portfolio = self.wealth_service.get_portfolio()
                logging.info(f"✅ 获取到投资组合，包含 {len(portfolio.positions)} 个持仓")
                
                # 计算总资产
                total_assets = sum(pos.current_book_value for pos in portfolio.positions)
                logging.info(f"📊 总资产: {total_assets}")
                
                # 按资产类型分组
                cash_assets = sum(
                    pos.current_book_value
                    for pos in portfolio.positions
                    if pos.asset.asset_type.name == "CASH"
                )
                
                fixed_income_assets = sum(
                    pos.current_book_value
                    for pos in portfolio.positions
                    if pos.asset.asset_type.name == "FIXED_INCOME"
                )
                
                logging.info(f"💰 现金资产: {cash_assets}, 固定收益: {fixed_income_assets}")
                
                # 获取完整的持仓数据
                assets_list = []
                for pos in portfolio.positions:
                    try:
                        # 计算持有天数
                        holding_days = 0
                        if pos.first_transaction_date:
                            holding_days = (datetime.now().date() - pos.first_transaction_date).days
                        
                        # 计算当前价值
                        current_value = pos.calculate_current_value()
                        total_return = pos.calculate_total_return(current_value)
                        total_return_rate = pos.calculate_total_return_rate(current_value) / 100  # 转换为小数
                        annualized_return = pos.calculate_annualized_return(current_value) / 100  # 转换为小数
                        
                        logging.info(f"📈 处理持仓: {pos.asset_name}, 状态: {pos.status}, 收益: {total_return}")
                        
                        assets_list.append({
                            # 基本信息
                            "id": pos.asset.asset_id,
                            "name": pos.asset.asset_name,
                            "type": pos.asset.asset_type.name.lower(),
                            "asset_subtype": pos.asset.asset_subtype.value if pos.asset.asset_subtype else "未知",
                            "currency": pos.asset.currency.name,
                            
                            # 持仓价值（基础货币 - 人民币）
                            "amount": float(pos.current_book_value),
                            "current_value": float(current_value),
                            "current_book_value": float(pos.current_book_value),
                            
                            # 持仓价值（原币种）
                            "amount_original_currency": float(pos.current_book_value_original_currency),
                            "current_value_original_currency": float(pos.current_book_value_original_currency),
                            "current_book_value_original_currency": float(pos.current_book_value_original_currency),
                            
                            # 收益数据
                            "total_return": float(total_return),
                            "total_return_rate": float(total_return_rate),
                            "annualized_return": float(annualized_return),
                            "unrealized_pnl": float(pos.calculate_unrealized_pnl()),
                            "realized_pnl": float(pos.calculate_realized_pnl()),
                            
                            # 交易统计
                            "transaction_count": pos.transaction_count,
                            "first_transaction_date": pos.first_transaction_date.isoformat() if pos.first_transaction_date else None,
                            "last_transaction_date": pos.last_transaction_date.isoformat() if pos.last_transaction_date else None,
                            "holding_days": holding_days,
                            "firstTransactionDate": pos.first_transaction_date.isoformat() if pos.first_transaction_date else None,  # 兼容前端
                            
                            # 资金流水
                            "total_invested": float(pos.total_invested),
                            "total_withdrawn": float(pos.total_withdrawn),
                            "total_income": float(pos.total_income),
                            "total_fees": float(pos.total_fees),
                            "net_invested": float(pos.net_invested),
                            "principal_amount": float(pos.principal_amount),
                            
                            # 持仓状态
                            "status": pos.status.name,
                            
                            # 兼容字段
                            "symbol": pos.asset.symbol or "",
                            "quantity": float(pos.current_book_value),
                        })
                        
                    except Exception as pos_error:
                        logging.error(f"❌ 处理持仓 {pos.asset_name} 时出错: {pos_error}", exc_info=True)
                        continue
                
                logging.info(f"✅ 成功处理 {len(assets_list)} 个持仓")
                
                return {
                    "total_assets": float(total_assets),
                    "total_change": float(portfolio.calculate_total_return()),  # 使用正确的方法名
                    "total_change_percent": float(portfolio.calculate_total_return_rate()),  # 已经是百分比
                    "cash_assets": float(cash_assets),
                    "fixed_income_assets": float(fixed_income_assets),
                    "assets": assets_list,
                    "last_updated": datetime.now().isoformat()
                }
                
            except Exception as e:
                logging.error(f"❌ 获取仪表板数据失败: {e}", exc_info=True)
                # 返回模拟数据作为fallback，包含完整字段
                logging.warning("🔄 使用fallback模拟数据")
                return {
                    "total_assets": 2341270.0,
                    "total_change": 8750.0,
                    "total_change_percent": 5.85,
                    "cash_assets": 1234000.0,
                    "fixed_income_assets": 1107270.0,
                    "assets": [
                        {
                            "id": "cash_001",
                            "name": "招商银行活期存款",
                            "type": "cash",
                            "asset_subtype": "活期存款",
                            "symbol": "CNY",
                            "amount": 65000.0,
                            "quantity": 65000.0,
                            "currency": "CNY",
                            "current_value": 65000.0,
                            "current_book_value": 65000.0,
                            "total_return": 320.0,
                            "total_return_rate": 0.0049,
                            "annualized_return": 0.018,
                            "unrealized_pnl": 0.0,
                            "realized_pnl": 320.0,
                            "transaction_count": 5,
                            "first_transaction_date": "2024-01-15",
                            "last_transaction_date": "2024-06-20",
                            "firstTransactionDate": "2024-01-15",
                            "holding_days": 180,
                            "total_invested": 65000.0,
                            "total_withdrawn": 0.0,
                            "total_income": 320.0,
                            "total_fees": 0.0,
                            "net_invested": 65000.0,
                            "principal_amount": 65000.0,
                            "status": "ACTIVE"
                        },
                        {
                            "id": "deposit_001", 
                            "name": "工商银行定期存款",
                            "type": "fixed_income",
                            "asset_subtype": "定期存款",
                            "symbol": "CNY",
                            "amount": 84600.0,
                            "quantity": 84600.0,
                            "currency": "CNY",
                            "current_value": 84600.0,
                            "current_book_value": 84600.0,
                            "total_return": 4600.0,
                            "total_return_rate": 0.0575,
                            "annualized_return": 0.0575,
                            "unrealized_pnl": 0.0,
                            "realized_pnl": 4600.0,
                            "transaction_count": 2,
                            "first_transaction_date": "2023-12-01",
                            "last_transaction_date": "2024-06-01",
                            "firstTransactionDate": "2023-12-01",
                            "holding_days": 200,
                            "total_invested": 80000.0,
                            "total_withdrawn": 0.0,
                            "total_income": 4600.0,
                            "total_fees": 0.0,
                            "net_invested": 80000.0,
                            "principal_amount": 80000.0,
                            "status": "ACTIVE"
                        },
                        {
                            "id": "bond_001",
                            "name": "建设银行理财产品",
                            "type": "fixed_income",
                            "asset_subtype": "银行理财",
                            "symbol": "CNY",
                            "amount": 52500.0,
                            "quantity": 52500.0,
                            "currency": "CNY",
                            "current_value": 0.0,
                            "current_book_value": 0.0,
                            "total_return": 2500.0,
                            "total_return_rate": 0.05,
                            "annualized_return": 0.20,
                            "unrealized_pnl": 0.0,
                            "realized_pnl": 2500.0,
                            "transaction_count": 3,
                            "first_transaction_date": "2024-01-01",
                            "last_transaction_date": "2024-04-01",
                            "firstTransactionDate": "2024-01-01",
                            "holding_days": 90,
                            "total_invested": 50000.0,
                            "total_withdrawn": 52500.0,
                            "total_income": 2500.0,
                            "total_fees": 0.0,
                            "net_invested": 0.0,
                            "principal_amount": 0.0,
                            "status": "MATURED"
                        }
                    ],
                    "last_updated": datetime.now().isoformat()
                }
        
        @app.get("/api/debug/data")
        async def debug_data():
            """调试：查看数据库中的数据"""
            try:
                # 获取所有资产
                assets = self.wealth_service.get_all_assets()
                assets_info = [
                    {
                        "id": asset.asset_id,
                        "name": asset.asset_name,
                        "type": asset.asset_type.name,
                        "subtype": asset.asset_subtype.value if asset.asset_subtype else None
                    }
                    for asset in assets
                ]
                
                # 获取所有交易
                transactions = self.wealth_service.get_all_transactions()
                transactions_info = [
                    {
                        "id": tx.transaction_id,
                        "asset_id": tx.asset_id,
                        "type": tx.transaction_type.name,
                        "amount": float(tx.amount),
                        "date": tx.transaction_date.isoformat()
                    }
                    for tx in transactions
                ]
                
                # 获取所有持仓
                positions = self.wealth_service.get_all_positions()
                positions_info = [
                    {
                        "asset_name": pos.asset_name,
                        "transaction_count": pos.transaction_count,
                        "net_invested": float(pos.net_invested),
                        "current_book_value": float(pos.current_book_value)
                    }
                    for pos in positions
                ]
                
                return {
                    "assets_count": len(assets),
                    "transactions_count": len(transactions),
                    "positions_count": len(positions),
                    "assets": assets_info,
                    "transactions": transactions_info[:10],  # 只显示前10个
                    "positions": positions_info
                }
                
            except Exception as e:
                logging.error(f"❌ 调试数据获取失败: {e}", exc_info=True)
                return {"error": str(e)}

        @app.get("/api/assets")
        async def get_assets():
            """获取资产列表"""
            try:
                assets = self.wealth_service.get_all_assets()
                return [
                    {
                        "id": asset.asset_id,
                        "name": asset.asset_name,
                        "asset_type": asset.asset_type.name,
                        "asset_subtype": asset.asset_subtype.name if asset.asset_subtype else None,
                        "currency": asset.currency.name,
                        "description": asset.description,
                        "created_at": asset.created_date.isoformat()
                    }
                    for asset in assets
                ]
            except Exception as e:
                logging.error(f"❌ 获取资产列表失败: {e}", exc_info=True)
                return []
        
        @app.post("/api/assets")
        async def create_asset(asset_data: dict):
            """创建新资产"""
            try:
                
                # 验证必填字段
                required_fields = ['name', 'asset_type', 'currency']
                for field in required_fields:
                    if field not in asset_data or not asset_data[field]:
                        raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")
                
                # 转换枚举类型（支持名称和值）
                try:
                    # 首先尝试按名称查找
                    if hasattr(AssetType, asset_data['asset_type']):
                        asset_type = getattr(AssetType, asset_data['asset_type'])
                    else:
                        # 如果按名称找不到，尝试按值查找
                        asset_type = AssetType(asset_data['asset_type'])
                    
                    if hasattr(Currency, asset_data['currency']):
                        currency = getattr(Currency, asset_data['currency'])
                    else:
                        currency = Currency(asset_data['currency'])
                        
                except (ValueError, AttributeError) as e:
                    raise HTTPException(status_code=400, detail=f"无效的枚举值: {e}")
                
                # 处理资产子类型
                asset_subtype = None
                if 'asset_subtype' in asset_data and asset_data['asset_subtype']:
                    try:
                        if hasattr(AssetSubType, asset_data['asset_subtype']):
                            asset_subtype = getattr(AssetSubType, asset_data['asset_subtype'])
                        else:
                            asset_subtype = AssetSubType(asset_data['asset_subtype'])
                    except (ValueError, AttributeError) as e:
                        raise HTTPException(status_code=400, detail=f"无效的资产子类型: {asset_data['asset_subtype']}")
                else:
                    # 设置默认子类型
                    type_subtype_map = {
                        AssetType.CASH: AssetSubType.CHECKING_ACCOUNT,
                        AssetType.FIXED_INCOME: AssetSubType.GOVERNMENT_BOND,
                        AssetType.EQUITY: AssetSubType.DOMESTIC_STOCK
                    }
                    asset_subtype = type_subtype_map.get(asset_type, AssetSubType.CHECKING_ACCOUNT)
                
                # 创建资产
                asset = self.wealth_service.create_asset(
                    asset_name=asset_data['name'],
                    asset_type=asset_type,
                    asset_subtype=asset_subtype,
                    currency=currency,
                    description=asset_data.get('description', ''),
                    issuer='',
                    credit_rating=''
                )
                
                return {
                    "id": asset.asset_id,
                    "name": asset.asset_name,
                    "asset_type": asset.asset_type.name,
                    "asset_subtype": asset.asset_subtype.name if asset.asset_subtype else None,
                    "currency": asset.currency.name,
                    "description": asset.description,
                    "created_at": asset.created_date.isoformat(),
                    "message": "资产创建成功"
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"❌ 创建资产失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"创建资产失败: {str(e)}")
        
        @app.get("/api/transactions")
        async def get_transactions(limit: int = 50):
            """获取交易记录"""
            try:
                transactions = self.wealth_service.get_recent_transactions(limit)
                result = []
                
                for tx in transactions:
                    # 基础交易信息
                    tx_data = {
                        "id": tx.transaction_id,
                        "asset_id": tx.asset_id,
                        "type": tx.transaction_type.name,
                        "amount": float(tx.amount),
                        "date": tx.transaction_date.isoformat(),
                        "currency": tx.currency.name,
                        "exchange_rate": float(tx.exchange_rate) if tx.exchange_rate else 1.0,
                        "amount_base_currency": float(tx.amount_base_currency) if tx.amount_base_currency else float(tx.amount),
                        "notes": tx.notes,
                        "reference_number": tx.reference_number,
                        "created_date": tx.created_date.isoformat() if tx.created_date else None,
                        "transaction_class": tx.__class__.__name__  # 交易类型类名
                    }
                    
                    # 添加特定类型的详细信息
                    if hasattr(tx, 'quantity') and tx.quantity:
                        tx_data["quantity"] = float(tx.quantity)
                    if hasattr(tx, 'price_per_share') and tx.price_per_share:
                        tx_data["price_per_share"] = float(tx.price_per_share)
                    if hasattr(tx, 'commission') and tx.commission:
                        tx_data["commission"] = float(tx.commission)
                    
                    # 固定收益特有字段
                    if hasattr(tx, 'annual_rate') and tx.annual_rate:
                        tx_data["annual_rate"] = float(tx.annual_rate)
                    if hasattr(tx, 'start_date') and tx.start_date:
                        tx_data["start_date"] = tx.start_date.isoformat()
                    if hasattr(tx, 'maturity_date') and tx.maturity_date:
                        tx_data["maturity_date"] = tx.maturity_date.isoformat()
                    if hasattr(tx, 'interest_type'):
                        tx_data["interest_type"] = tx.interest_type.name if hasattr(tx.interest_type, 'name') else str(tx.interest_type)
                    if hasattr(tx, 'payment_frequency'):
                        tx_data["payment_frequency"] = tx.payment_frequency.name if hasattr(tx.payment_frequency, 'name') else str(tx.payment_frequency)
                    if hasattr(tx, 'face_value') and tx.face_value:
                        tx_data["face_value"] = float(tx.face_value)
                    if hasattr(tx, 'coupon_rate') and tx.coupon_rate:
                        tx_data["coupon_rate"] = float(tx.coupon_rate)
                    
                    # 现金类特有字段
                    if hasattr(tx, 'account_type'):
                        tx_data["account_type"] = tx.account_type
                    if hasattr(tx, 'interest_rate') and tx.interest_rate:
                        tx_data["interest_rate"] = float(tx.interest_rate)
                    if hasattr(tx, 'compound_frequency'):
                        tx_data["compound_frequency"] = tx.compound_frequency
                    
                    # 房产特有字段
                    if hasattr(tx, 'property_area') and tx.property_area:
                        tx_data["property_area"] = float(tx.property_area)
                    if hasattr(tx, 'price_per_unit') and tx.price_per_unit:
                        tx_data["price_per_unit"] = float(tx.price_per_unit)
                    if hasattr(tx, 'rental_income') and tx.rental_income:
                        tx_data["rental_income"] = float(tx.rental_income)
                    if hasattr(tx, 'property_type'):
                        tx_data["property_type"] = tx.property_type
                    if hasattr(tx, 'location'):
                        tx_data["location"] = tx.location
                    if hasattr(tx, 'tax_amount') and tx.tax_amount:
                        tx_data["tax_amount"] = float(tx.tax_amount)
                    
                    result.append(tx_data)
                
                return result
            except Exception as e:
                logging.error(f"❌ 获取交易记录失败: {e}", exc_info=True)
                return []
        
        @app.get("/api/transactions/{tx_id}")
        async def get_transaction_details(tx_id: str):
            """获取单个交易的详细信息（包含固定收益详情）"""
            try:
                from wealth_lite.models.transaction import FixedIncomeTransaction
                
                tx = self.wealth_service.get_transaction(tx_id)
                if not tx:
                    raise HTTPException(status_code=404, detail="交易记录不存在")
                
                # 基础交易信息
                result = {
                    "id": tx.transaction_id,
                    "asset_id": tx.asset_id,
                    "type": tx.transaction_type.name,
                    "amount": float(tx.amount),
                    "date": tx.transaction_date.isoformat(),
                    "currency": tx.currency.name,
                    "exchange_rate": float(tx.exchange_rate) if tx.exchange_rate else 1.0,
                    "notes": tx.notes
                }
                
                # 如果是固定收益交易，添加详情字段
                if isinstance(tx, FixedIncomeTransaction):
                    result.update({
                        "annual_rate": float(tx.annual_rate) if tx.annual_rate else None,
                        "start_date": tx.start_date.isoformat() if tx.start_date else None,
                        "maturity_date": tx.maturity_date.isoformat() if tx.maturity_date else None,
                        "interest_type": tx.interest_type,
                        "payment_frequency": tx.payment_frequency,
                        "face_value": float(tx.face_value) if tx.face_value else None,
                        "coupon_rate": float(tx.coupon_rate) if tx.coupon_rate else None
                    })
                
                return result
                
            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"❌ 获取交易详情失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"获取交易详情失败: {str(e)}")
        
        @app.put("/api/assets/{asset_id}")
        async def update_asset(asset_id: str, asset_data: dict):
            """更新资产"""
            try:
                # 验证资产是否存在
                existing_asset = self.wealth_service.get_asset(asset_id)
                if not existing_asset:
                    raise HTTPException(status_code=404, detail="资产不存在")
                
                # 转换枚举类型（支持名称和值）
                asset_type = None
                if 'asset_type' in asset_data:
                    type_value = asset_data.get('asset_type')
                    try:
                        if hasattr(AssetType, type_value):
                            asset_type = getattr(AssetType, type_value)
                        else:
                            asset_type = AssetType(type_value)
                    except (ValueError, AttributeError) as e:
                        raise HTTPException(status_code=400, detail=f"无效的资产类型: {type_value}")
                
                currency = None
                if 'currency' in asset_data:
                    try:
                        if hasattr(Currency, asset_data['currency']):
                            currency = getattr(Currency, asset_data['currency'])
                        else:
                            currency = Currency(asset_data['currency'])
                    except (ValueError, AttributeError) as e:
                        raise HTTPException(status_code=400, detail=f"无效的货币类型: {asset_data['currency']}")

                # 处理资产子类型
                asset_subtype = None
                if 'asset_subtype' in asset_data:
                    if asset_data['asset_subtype']:  # 非空字符串
                        try:
                            if hasattr(AssetSubType, asset_data['asset_subtype']):
                                asset_subtype = getattr(AssetSubType, asset_data['asset_subtype'])
                            else:
                                asset_subtype = AssetSubType(asset_data['asset_subtype'])
                        except (ValueError, AttributeError) as e:
                            raise HTTPException(status_code=400, detail=f"无效的资产子类型: {asset_data['asset_subtype']}")
                
                # 更新资产
                updated_asset = self.wealth_service.update_asset(
                    asset_id=asset_id,
                    asset_name=asset_data.get('name'),
                    asset_type=asset_type,
                    asset_subtype=asset_subtype,
                    currency=currency,
                    description=asset_data.get('description')
                )
                
                return {
                    "id": updated_asset.asset_id,
                    "name": updated_asset.asset_name,
                    "asset_type": updated_asset.asset_type.name,
                    "asset_subtype": updated_asset.asset_subtype.name if updated_asset.asset_subtype else None,
                    "currency": updated_asset.currency.name,
                    "description": updated_asset.description,
                    "created_at": updated_asset.created_date.isoformat(),
                    "message": "资产更新成功"
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"❌ 更新资产失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"更新资产失败: {str(e)}")

        @app.delete("/api/assets/{asset_id}")
        async def delete_asset(asset_id: str):
            """删除资产"""
            try:
                result = self.wealth_service.delete_asset(asset_id)
                if result:
                    return {"success": True, "message": "资产已删除"}
                else:
                    raise HTTPException(status_code=404, detail="资产不存在")
            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"❌ 删除资产失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"删除资产失败: {str(e)}")

        @app.post("/api/transactions")
        async def create_transaction(tx_data: dict):
            """创建交易（支持现金类和固定收益类）"""
            try:
                from decimal import Decimal
                import datetime
                
                asset_id = tx_data["asset_id"]
                
                # 兼容前端字段名
                tx_type = tx_data.get("type") or tx_data.get("transaction_type")
                if not tx_type:
                    raise HTTPException(status_code=400, detail="缺少交易类型字段: type/transaction_type")
                try:
                    tx_type = TransactionType[tx_type]  # 用名字查找
                except KeyError:
                    raise HTTPException(status_code=400, detail=f"无效的交易类型: {tx_type}")
                
                amount = Decimal(str(tx_data["amount"]))
                
                # 兼容字符串日期
                tx_date = tx_data.get("date") or tx_data.get("transaction_date")
                if not tx_date:
                    raise HTTPException(status_code=400, detail="缺少交易日期字段: date/transaction_date")
                if isinstance(tx_date, str):
                    tx_date = datetime.date.fromisoformat(tx_date)
                
                currency_str = tx_data.get("currency", "CNY")
                try:
                    currency = Currency[currency_str]  # 用名字查找
                except KeyError:
                    raise HTTPException(status_code=400, detail=f"无效的货币类型: {currency_str}")
                
                exchange_rate = Decimal(str(tx_data.get("exchange_rate", 1.0)))
                notes = tx_data.get("notes", "")
                
                # 获取资产信息以确定资产类型
                asset = self.wealth_service.get_asset(asset_id)
                if not asset:
                    raise HTTPException(status_code=400, detail=f"资产不存在: {asset_id}")
                
                
                # 根据资产类型创建不同的交易
                if asset.asset_type.name == AssetType.CASH.name:
                    tx = self.wealth_service.create_cash_transaction(
                        asset_id=asset_id,
                        transaction_type=tx_type,
                        amount=amount,
                        transaction_date=tx_date,
                        currency=currency,
                        exchange_rate=exchange_rate,
                        notes=notes
                    )
                elif asset.asset_type.name == AssetType.FIXED_INCOME.name:
                    # 解析固定收益特有字段
                    annual_rate = tx_data.get("annual_rate")
                    if annual_rate is not None:
                        annual_rate = Decimal(str(annual_rate))
                    
                    start_date = tx_data.get("start_date")
                    if start_date and isinstance(start_date, str):
                        start_date = datetime.date.fromisoformat(start_date)
                    
                    maturity_date = tx_data.get("maturity_date")
                    if maturity_date and isinstance(maturity_date, str):
                        maturity_date = datetime.date.fromisoformat(maturity_date)
                    
                    interest_type = tx_data.get("interest_type")
                    payment_frequency = tx_data.get("payment_frequency")
                    
                    face_value = tx_data.get("face_value")
                    if face_value is not None:
                        face_value = Decimal(str(face_value))
                    
                    coupon_rate = tx_data.get("coupon_rate")
                    if coupon_rate is not None:
                        coupon_rate = Decimal(str(coupon_rate))
                    
                    tx = self.wealth_service.create_fixed_income_transaction(
                        asset_id=asset_id,
                        transaction_type=tx_type,
                        amount=amount,
                        transaction_date=tx_date,
                        currency=currency,
                        exchange_rate=exchange_rate,
                        annual_rate=annual_rate,
                        start_date=start_date,
                        maturity_date=maturity_date,
                        interest_type=interest_type,
                        payment_frequency=payment_frequency,
                        face_value=face_value,
                        coupon_rate=coupon_rate,
                        notes=notes
                    )
                else:
                    raise HTTPException(status_code=400, detail=f"暂不支持的资产类型: {asset.asset_type}")
                
                return {
                    "id": tx.transaction_id, 
                    "asset_id": tx.asset_id, 
                    "type": tx.transaction_type.name,  # 使用英文名称保持一致
                    "amount": float(tx.amount), 
                    "date": str(tx.transaction_date), 
                    "currency": tx.currency.name,      # 使用英文名称保持一致
                    "notes": tx.notes
                }
            except Exception as e:
                logging.error(f"❌ 创建交易失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"创建交易失败: {str(e)}")

        @app.put("/api/transactions/{tx_id}")
        async def update_transaction(tx_id: str, tx_data: dict):
            """更新交易（仅支持现金类部分字段）"""
            try:
                tx = self.wealth_service.get_transaction(tx_id)
                if not tx:
                    raise HTTPException(status_code=404, detail="交易不存在")
                # 只允许更新amount、notes、date
                if "amount" in tx_data:
                    tx.amount = tx_data["amount"]
                if "notes" in tx_data:
                    tx.notes = tx_data["notes"]
                if "date" in tx_data:
                    tx.transaction_date = tx_data["date"]
                result = self.wealth_service.update_transaction(tx)
                if result:
                    return {"success": True, "message": "交易已更新"}
                else:
                    raise HTTPException(status_code=500, detail="交易更新失败")
            except Exception as e:
                logging.error(f"❌ 更新交易失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"更新交易失败: {str(e)}")

        @app.post("/api/positions/{asset_id}/withdraw")
        async def withdraw_from_position(asset_id: str, withdraw_data: dict):
            """从持仓中提取资产"""
            try:
                from decimal import Decimal
                import datetime
                
                # 获取持仓信息
                position = self.wealth_service.get_position(asset_id)
                if not position:
                    raise HTTPException(status_code=404, detail="持仓不存在")
                
                # 获取提取金额
                withdraw_amount = Decimal(str(withdraw_data["amount"]))
                if withdraw_amount <= 0:
                    raise HTTPException(status_code=400, detail="提取金额必须大于0")
                
                # 验证提取金额不能超过持仓价值
                # 获取资产信息以确定币种
                asset = self.wealth_service.get_asset(asset_id)
                if not asset:
                    raise HTTPException(status_code=404, detail="资产不存在")
                
                # 根据资产币种选择合适的持仓价值进行比较
                if asset.currency.name == "CNY":
                    # 人民币资产：使用人民币基础货币价值
                    current_value = position.calculate_current_value()
                    currency_name = "人民币"
                else:
                    # 外币资产：使用原币种价值
                    current_value = position.current_book_value_original_currency
                    currency_name = f"{asset.currency.name}"
                
                if withdraw_amount > current_value:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"提取金额({withdraw_amount} {asset.currency.name})不能超过持仓价值({current_value} {asset.currency.name})"
                    )
                
                # 获取其他参数
                currency_str = withdraw_data.get("currency", "CNY")
                try:
                    currency = Currency[currency_str]
                except KeyError:
                    raise HTTPException(status_code=400, detail=f"无效的货币类型: {currency_str}")
                
                exchange_rate = Decimal(str(withdraw_data.get("exchange_rate", 1.0)))
                notes = withdraw_data.get("notes", "")
                
                # 提取日期
                withdraw_date = withdraw_data.get("date") or withdraw_data.get("transaction_date")
                if not withdraw_date:
                    withdraw_date = datetime.date.today()
                elif isinstance(withdraw_date, str):
                    withdraw_date = datetime.date.fromisoformat(withdraw_date)
                
                # 创建提取交易
                if asset.asset_type.name == AssetType.CASH.name:
                    tx = self.wealth_service.create_cash_transaction(
                        asset_id=asset_id,
                        transaction_type=TransactionType.WITHDRAW,
                        amount=withdraw_amount,
                        transaction_date=withdraw_date,
                        currency=currency,
                        exchange_rate=exchange_rate,
                        notes=notes
                    )
                elif asset.asset_type.name == AssetType.FIXED_INCOME.name:
                    tx = self.wealth_service.create_fixed_income_transaction(
                        asset_id=asset_id,
                        transaction_type=TransactionType.WITHDRAW,
                        amount=withdraw_amount,
                        transaction_date=withdraw_date,
                        currency=currency,
                        exchange_rate=exchange_rate,
                        notes=notes
                    )
                else:
                    raise HTTPException(status_code=400, detail=f"暂不支持的资产类型: {asset.asset_type}")
                
                # 重新获取持仓信息以计算新的状态
                updated_position = self.wealth_service.get_position(asset_id)
                new_current_value = updated_position.calculate_current_value()
                
                # 确定新的持仓状态
                from wealth_lite.models.enums import PositionStatus
                new_status = PositionStatus.ACTIVE
                
                if new_current_value <= 0:
                    new_status = PositionStatus.WITHDRAWN
                elif new_current_value < current_value:
                    new_status = PositionStatus.PARTIALLY_WITHDRAWN
                
                return {
                    "success": True,
                    "message": "资产提取成功",
                    "transaction_id": tx.transaction_id,
                    "withdraw_amount": float(withdraw_amount),
                    "remaining_value": float(new_current_value),
                    "new_status": new_status.value,
                    "status_code": new_status.name
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"❌ 提取资产失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"提取资产失败: {str(e)}")

        @app.delete("/api/transactions/{tx_id}")
        async def delete_transaction(tx_id: str):
            """删除交易"""
            try:
                result = self.wealth_service.delete_transaction(tx_id)
                if result:
                    return {"success": True, "message": "交易已删除"}
                else:
                    raise HTTPException(status_code=404, detail="交易不存在")
            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"❌ 删除交易失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"删除交易失败: {str(e)}")
    
    def find_available_port(self, start_port: int = 8080) -> int:
        """寻找可用端口"""
        import socket
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    return port
            except OSError:
                continue
        raise RuntimeError("无法找到可用端口")
    
    def open_browser(self):
        """延迟打开浏览器"""
        import time
        time.sleep(1.5)  # 等待服务器启动
        url = f"http://{self.host}:{self.port}/static/index.html"
        print(f"🌐 正在打开浏览器: {url}")
        webbrowser.open(url)
    
    def run(self, auto_open_browser: bool = True):  # 默认改回True
        """运行应用"""
        try:
            # 寻找可用端口
            self.port = self.find_available_port(8080)
            
            # 创建FastAPI应用
            self.app = self.create_app()
            
            logging.info("🚀 启动 WealthLite 应用...")
            logging.info(f"📍 API服务器地址: http://{self.host}:{self.port}")
            logging.info(f"📍 前端页面地址: http://{self.host}:{self.port}/static/index.html")
            logging.info(f"📁 工作目录: {Path.cwd()}")
            logging.info("\n💡 提示:")
            logging.info("  - 应用将自动在浏览器中打开")
            logging.info("  - 按 Ctrl+C 停止应用")
            logging.info("  - 数据保存在 user_data/ 目录")
            logging.info("\n" + "="*50)
            
            # 在后台线程中打开浏览器
            if auto_open_browser:
                browser_thread = threading.Thread(target=self.open_browser, daemon=True)
                browser_thread.start()
            
            # 启动服务器
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info",
                access_log=False
            )
            
        except KeyboardInterrupt:
            logging.info("\n🛑 应用已停止")
        except Exception as e:
            logging.error(f"❌ 启动应用时出错: {e}", exc_info=True)
            sys.exit(1)


def main():
    """主函数"""
    app = WealthLiteApp()
    app.run()


if __name__ == "__main__":
    main() 