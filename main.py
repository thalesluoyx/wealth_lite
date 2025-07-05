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

from wealth_lite.services.wealth_service import WealthService
from wealth_lite.data.database import DatabaseManager
from wealth_lite.models.enums import AssetType, Currency, TransactionType

# 初始化日志
setup_logging(LOG_LEVEL)

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
            self.wealth_service = WealthService()
            
            logging.info("✅ 数据库服务初始化成功")
            
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
        
        @app.get("/api/dashboard/summary")
        async def get_dashboard_summary():
            """获取仪表板总览数据"""
            try:
                portfolio = self.wealth_service.get_portfolio()
                
                # 计算总资产
                total_assets = sum(pos.current_book_value for pos in portfolio.positions)
                
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
                
                # 资产明细
                assets_list = []
                for pos in portfolio.positions[:10]:  # 只返回前10个
                    assets_list.append({
                        "id": pos.asset.asset_id,
                        "name": pos.asset.asset_name,
                        "type": pos.asset.asset_type.name.lower(),
                        "symbol": pos.asset.symbol or "",
                        "amount": float(pos.current_book_value),
                        "quantity": float(pos.current_book_value),  # 对于现金类资产，数量等于金额
                        "currency": pos.asset.currency.name
                    })
                
                return {
                    "total_assets": float(total_assets),
                    "total_change": 8750.0,  # TODO: 计算实际变化
                    "total_change_percent": 5.85,  # TODO: 计算实际变化百分比
                    "cash_assets": float(cash_assets),
                    "fixed_income_assets": float(fixed_income_assets),
                    "assets": assets_list,
                    "last_updated": datetime.now().isoformat()  # 使用当前时间
                }
                
            except Exception as e:
                logging.error(f"❌ 获取仪表板数据失败: {e}", exc_info=True)
                # 返回模拟数据作为fallback
                return {
                    "total_assets": 2341270.0,
                    "total_change": 8750.0,
                    "total_change_percent": 5.85,
                    "cash_assets": 1234000.0,
                    "fixed_income_assets": 1107270.0,
                    "assets": [
                        {
                            "id": "cash_001",
                            "name": "现金",
                            "type": "cash",
                            "symbol": "CNY",
                            "amount": 65000.0,
                            "quantity": 65000.0,
                            "currency": "CNY"
                        },
                        {
                            "id": "deposit_001", 
                            "name": "定期存款",
                            "type": "cash",
                            "symbol": "CNY",
                            "amount": 84600.0,
                            "quantity": 84600.0,
                            "currency": "CNY"
                        },
                        {
                            "id": "bond_001",
                            "name": "理财产品",
                            "type": "fixed_income",
                            "symbol": "CNY",
                            "amount": 52500.0,
                            "quantity": 52500.0,
                            "currency": "CNY"
                        }
                    ],
                    "last_updated": datetime.now().isoformat()
                }
        
        @app.get("/api/assets")
        async def get_assets():
            """获取资产列表"""
            try:
                assets = self.wealth_service.get_all_assets()
                return [
                    {
                        "id": asset.asset_id,
                        "name": asset.asset_name,
                        "type": asset.asset_type.name,
                        "currency": asset.currency.name,
                        "description": asset.description,
                        "primary_category": asset.primary_category,
                        "secondary_category": asset.secondary_category,
                        "created_date": asset.created_date.isoformat()
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
                required_fields = ['name', 'type', 'currency']
                for field in required_fields:
                    if field not in asset_data or not asset_data[field]:
                        raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")
                
                # 转换枚举类型（支持名称和值）
                try:
                    # 首先尝试按名称查找
                    if hasattr(AssetType, asset_data['type']):
                        asset_type = getattr(AssetType, asset_data['type'])
                    else:
                        # 如果按名称找不到，尝试按值查找
                        asset_type = AssetType(asset_data['type'])
                    
                    if hasattr(Currency, asset_data['currency']):
                        currency = getattr(Currency, asset_data['currency'])
                    else:
                        currency = Currency(asset_data['currency'])
                        
                except (ValueError, AttributeError) as e:
                    raise HTTPException(status_code=400, detail=f"无效的枚举值: {e}")
                
                # 设置默认分类
                type_category_map = {
                    AssetType.CASH: ("现金及等价物", "储蓄存款"),
                    AssetType.FIXED_INCOME: ("固定收益类", "政府债券"),
                    AssetType.EQUITY: ("权益类", "股票")
                }
                default_primary, default_secondary = type_category_map.get(asset_type, ("其他", "未分类"))
                
                # 创建资产
                asset = self.wealth_service.create_asset(
                    asset_name=asset_data['name'],
                    asset_type=asset_type,
                    primary_category=asset_data.get('primary_category', default_primary),
                    secondary_category=asset_data.get('secondary_category', default_secondary),
                    currency=currency,
                    description=asset_data.get('description', ''),
                    issuer=asset_data.get('issuer', ''),
                    credit_rating=asset_data.get('credit_rating', '')
                )
                
                return {
                    "id": asset.asset_id,
                    "name": asset.asset_name,
                    "type": asset.asset_type.name,
                    "currency": asset.currency.name,
                    "description": asset.description,
                    "primary_category": asset.primary_category,
                    "secondary_category": asset.secondary_category,
                    "created_date": asset.created_date.isoformat(),
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
                return [
                    {
                        "id": tx.transaction_id,
                        "asset_id": tx.asset_id,
                        "type": tx.transaction_type.name,
                        "amount": float(tx.amount),
                        "price": float(getattr(tx, "price", 0)) if getattr(tx, "price", None) is not None else None,
                        "quantity": float(getattr(tx, "quantity", 0)) if getattr(tx, "quantity", None) is not None else None,
                        "date": tx.transaction_date.isoformat(),
                        "currency": tx.currency.name,
                        "description": tx.notes
                    }
                    for tx in transactions
                ]
            except Exception as e:
                logging.error(f"❌ 获取交易记录失败: {e}", exc_info=True)
                return []
        
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

        @app.post("/api/transactions/{tx_id}/withdraw")
        async def withdraw_transaction(tx_id: str):
            """取回交易（创建反向交易）"""
            try:
                # 获取原交易
                original_tx = self.wealth_service.get_transaction(tx_id)
                if not original_tx:
                    raise HTTPException(status_code=404, detail="交易不存在")
                
                # 创建反向交易
                from wealth_lite.models.enums import TransactionType
                from decimal import Decimal
                import datetime
                
                # 确定反向交易类型
                reverse_type_map = {
                    TransactionType.DEPOSIT: TransactionType.WITHDRAW,
                    TransactionType.INTEREST: TransactionType.WITHDRAW,
                }
                
                reverse_type = reverse_type_map.get(original_tx.transaction_type)
                if not reverse_type:
                    raise HTTPException(status_code=400, detail="该交易类型不支持取回操作")
                
                # 创建反向交易
                reverse_tx = self.wealth_service.create_cash_transaction(
                    asset_id=original_tx.asset_id,
                    transaction_type=reverse_type,
                    amount=original_tx.amount,
                    transaction_date=datetime.date.today(),
                    currency=original_tx.currency,
                    exchange_rate=original_tx.exchange_rate,
                    notes=f"取回交易: {original_tx.notes or ''}"
                )
                
                # 更新原交易状态（如果有状态字段的话）
                # 这里可以添加状态更新逻辑
                
                return {
                    "success": True,
                    "message": "交易已成功取回",
                    "original_transaction_id": tx_id,
                    "reverse_transaction_id": reverse_tx.transaction_id,
                    "reverse_amount": float(reverse_tx.amount)
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"❌ 取回交易失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"取回交易失败: {str(e)}")

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