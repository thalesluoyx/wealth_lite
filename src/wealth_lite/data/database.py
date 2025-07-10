"""
WealthLite 数据库管理器

负责SQLite数据库的连接、初始化、迁移和基础操作。
采用软外键关联设计，避免数据库级强约束。
"""

import os
import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from contextlib import contextmanager
from datetime import datetime

from ..models.enums import Currency
from ..config.database_config import DatabaseConfig


class DatabaseManager:
    """
    数据库管理器
    
    职责：
    - 管理SQLite数据库连接
    - 执行数据库初始化和迁移
    - 提供基础的CRUD操作
    - 处理事务管理
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，如果不指定则根据环境变量自动选择
                    - 测试环境：使用内存数据库 ":memory:"
                    - 开发环境：使用 user_data/wealth_lite_dev.db
                    - 生产环境：使用 user_data/wealth_lite.db
        """
        if db_path is None:
            # 使用配置类根据环境自动选择数据库路径
            self.db_path = DatabaseConfig.get_db_path()
        else:
            self.db_path = db_path
        
        # 只有非内存数据库才需要创建目录
        if self.db_path != ":memory:":
            db_path_obj = Path(self.db_path)
            db_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self._connection: Optional[sqlite3.Connection] = None
        
        # 初始化数据库
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """初始化数据库，创建必要的表"""
        with self.get_connection() as conn:
            # 启用外键支持（虽然我们使用软关联）
            conn.execute("PRAGMA foreign_keys = ON")
            
            # 创建所有表
            self._create_tables(conn)
            
            # 创建索引
            self._create_indexes(conn)
            self._connection = conn
            self.logger.info(f"数据库初始化完成: {self.db_path}")
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """创建所有数据表"""
        
        # 1. 资产表 - 存储所有资产的基础信息
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,              -- 资产唯一标识符（UUID格式）
                asset_name TEXT NOT NULL,               -- 资产名称（如：招商银行储蓄、国债2024001）
                asset_type TEXT NOT NULL,               -- 资产类型（CASH/FIXED_INCOME/EQUITY）
                asset_subtype TEXT,                     -- 资产子类型（新的两层分类结构）
                currency TEXT NOT NULL DEFAULT 'CNY',  -- 资产计价币种（CNY/USD/EUR等）
                description TEXT,                       -- 资产详细描述
                issuer TEXT,                           -- 发行方或机构名称
                credit_rating TEXT,                    -- 信用评级（AAA/AA+等，可选）
                extended_attributes TEXT,              -- JSON格式存储扩展属性（风险等级、流动性等）
                created_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 记录创建时间
                updated_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP   -- 记录最后更新时间
            )
        """)
        
        # 2. 交易表 - 存储所有交易记录的核心信息
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,                          -- 交易唯一标识符（UUID格式）
                asset_id TEXT NOT NULL,                                   -- 关联的资产ID（软关联到assets表）
                transaction_date DATE NOT NULL,                           -- 交易发生日期（YYYY-MM-DD格式）
                transaction_type TEXT NOT NULL,                           -- 交易类型（BUY/SELL/DEPOSIT/WITHDRAW/INTEREST/DIVIDEND等）
                amount DECIMAL(15,4) NOT NULL,                           -- 交易金额（原币种，最多15位数字，4位小数）
                currency TEXT NOT NULL,                                   -- 交易币种（CNY/USD/EUR等）
                exchange_rate DECIMAL(10,6) NOT NULL DEFAULT 1.0,        -- 对基础货币的汇率（默认1.0表示同币种）
                amount_base_currency DECIMAL(15,4) NOT NULL,             -- 基础货币金额（用于统一计算）
                notes TEXT,                                              -- 交易备注信息
                created_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP -- 记录创建时间
            )
        """)
        
        # 3. 现金交易详情表 - 存储现金类交易的特有属性
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cash_transactions (
                transaction_id TEXT PRIMARY KEY,        -- 交易ID（软关联到transactions表）
                account_type TEXT,                      -- 账户类型（CHECKING/SAVINGS/MONEY_MARKET等）
                interest_rate DECIMAL(8,4),            -- 利率（年化百分比，如2.5表示2.5%）
                compound_frequency TEXT                 -- 复利频率（DAILY/MONTHLY/QUARTERLY/ANNUALLY）
            )
        """)
        
        # 4. 固定收益交易详情表 - 存储债券等固定收益产品的特有属性
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fixed_income_transactions (
                transaction_id TEXT PRIMARY KEY,        -- 交易ID（软关联到transactions表）
                annual_rate DECIMAL(8,4),              -- 年化收益率（百分比，如3.5表示3.5%）
                start_date DATE,                        -- 起息日期（YYYY-MM-DD格式）
                maturity_date DATE,                     -- 到期日期（YYYY-MM-DD格式）
                interest_type TEXT,                     -- 利息类型（SIMPLE/COMPOUND/FLOATING）
                payment_frequency TEXT,                 -- 付息频率（MATURITY/MONTHLY/QUARTERLY/ANNUALLY）
                face_value DECIMAL(15,4),              -- 面值金额
                coupon_rate DECIMAL(8,4)               -- 票面利率（百分比）
            )
        """)
        
        # 5. 权益交易详情表 - 存储股票等权益类投资的特有属性（为Phase 2准备）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS equity_transactions (
                transaction_id TEXT PRIMARY KEY,        -- 交易ID（软关联到transactions表）
                quantity DECIMAL(15,6),                -- 交易数量（股数或份额，支持小数股）
                price_per_share DECIMAL(15,4),         -- 每股价格或单位净值
                dividend_amount DECIMAL(15,4),         -- 分红金额（每股分红）
                split_ratio DECIMAL(8,4)               -- 拆股比例（如2.0表示1拆2）
            )
        """)
        
        # 6. 不动产交易详情表 - 存储房产等不动产投资的特有属性（为Phase 3准备）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS real_estate_transactions (
                transaction_id TEXT PRIMARY KEY,        -- 交易ID（软关联到transactions表）
                property_area DECIMAL(10,2),           -- 房产面积（平方米，保留2位小数）
                price_per_unit DECIMAL(15,4),          -- 单价（每平方米价格）
                rental_income DECIMAL(15,4),           -- 租金收入（月租金或年租金）
                property_type TEXT                      -- 房产类型（RESIDENTIAL/COMMERCIAL/INDUSTRIAL等）
            )
        """)
        
        # 7. 投资组合快照表 - 存储特定时间点的投资组合历史状态
        conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                snapshot_id TEXT PRIMARY KEY,                                -- 快照唯一标识符（UUID格式）
                snapshot_date DATE NOT NULL,                                -- 快照日期（YYYY-MM-DD格式）
                snapshot_time DATETIME NOT NULL,                            -- 快照时间戳
                snapshot_type TEXT NOT NULL,                                -- 快照类型（'AUTO' 或 'MANUAL'）
                base_currency TEXT NOT NULL,                                -- 基础货币（CNY/USD等）
                
                -- 组合概览数据
                total_value DECIMAL(20,2) NOT NULL,                        -- 总价值（基础货币）
                total_cost DECIMAL(20,2) NOT NULL,                         -- 总成本（基础货币）
                total_return DECIMAL(20,2) NOT NULL,                       -- 总收益（基础货币）
                total_return_rate DECIMAL(10,4) NOT NULL,                  -- 总收益率（小数形式）
                
                -- 分类统计
                cash_value DECIMAL(20,2) DEFAULT 0,                        -- 现金价值
                fixed_income_value DECIMAL(20,2) DEFAULT 0,                -- 固收价值
                equity_value DECIMAL(20,2) DEFAULT 0,                      -- 权益价值
                real_estate_value DECIMAL(20,2) DEFAULT 0,                 -- 房产价值
                commodity_value DECIMAL(20,2) DEFAULT 0,                   -- 商品价值
                
                -- 业绩指标
                annualized_return DECIMAL(10,4) DEFAULT 0,                 -- 年化收益率
                volatility DECIMAL(10,4) DEFAULT 0,                        -- 波动率
                sharpe_ratio DECIMAL(10,4) DEFAULT 0,                      -- 夏普比率
                max_drawdown DECIMAL(10,4) DEFAULT 0,                      -- 最大回撤
                
                -- 详细数据（JSON格式）
                position_snapshots TEXT NOT NULL,                          -- 完整的持仓详情
                asset_allocation TEXT NOT NULL,                            -- 资产配置分析
                performance_metrics TEXT NOT NULL,                         -- 业绩指标详情
                
                -- 元数据
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 记录创建时间
                notes TEXT,                                                -- 备注信息
                
                -- 唯一约束：每天每种类型只能有一个快照
                UNIQUE(snapshot_date, snapshot_type)
            )
        """)
        
        # 8. AI分析配置表 - 存储AI分析服务的配置信息
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_analysis_configs (
                config_id TEXT PRIMARY KEY,                                -- 配置唯一标识符（UUID格式）
                config_name TEXT NOT NULL,                                 -- 配置名称
                ai_type TEXT NOT NULL,                                     -- AI类型（'LOCAL' 或 'CLOUD'）
                is_default BOOLEAN DEFAULT 0,                             -- 是否为默认配置
                is_active BOOLEAN DEFAULT 1,                              -- 是否激活
                
                -- 本地AI配置
                local_model_path TEXT,                                     -- 本地模型路径
                local_model_name TEXT,                                     -- 本地模型名称
                local_api_port INTEGER,                                    -- 本地API端口
                
                -- 云端AI配置
                cloud_provider TEXT,                                       -- 云端提供商（'OPENAI', 'CLAUDE', 'GEMINI'等）
                cloud_api_key TEXT,                                        -- 云端API密钥
                cloud_api_url TEXT,                                        -- 云端API地址
                cloud_model_name TEXT,                                     -- 云端模型名称
                
                -- 通用配置
                max_tokens INTEGER DEFAULT 4000,                          -- 最大令牌数
                temperature DECIMAL(3,2) DEFAULT 0.7,                     -- 温度参数
                timeout_seconds INTEGER DEFAULT 30,                       -- 超时时间（秒）
                
                -- 元数据
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,          -- 记录创建时间
                updated_date DATETIME DEFAULT CURRENT_TIMESTAMP           -- 记录更新时间
            )
        """)
        
        # 9. AI分析结果表 - 存储AI分析的结果
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_analysis_results (
                analysis_id TEXT PRIMARY KEY,                             -- 分析唯一标识符（UUID格式）
                snapshot1_id TEXT NOT NULL,                               -- 第一个快照ID
                snapshot2_id TEXT NOT NULL,                               -- 第二个快照ID
                config_id TEXT NOT NULL,                                  -- 使用的配置ID
                
                -- 分析结果
                analysis_content TEXT NOT NULL,                           -- 分析内容
                analysis_summary TEXT,                                    -- 分析摘要
                investment_advice TEXT,                                   -- 投资建议
                risk_assessment TEXT,                                     -- 风险评估
                
                -- 分析元数据
                analysis_type TEXT NOT NULL,                              -- 分析类型（'COMPARISON', 'TREND', 'RISK'等）
                analysis_status TEXT NOT NULL,                            -- 分析状态（'SUCCESS', 'FAILED', 'PENDING'）
                error_message TEXT,                                       -- 错误信息
                processing_time_ms INTEGER,                               -- 处理时间（毫秒）
                
                -- 时间戳
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,          -- 记录创建时间
                
                -- 外键约束（软关联）
                FOREIGN KEY (snapshot1_id) REFERENCES portfolio_snapshots(snapshot_id),
                FOREIGN KEY (snapshot2_id) REFERENCES portfolio_snapshots(snapshot_id),
                FOREIGN KEY (config_id) REFERENCES ai_analysis_configs(config_id)
            )
        """)
        
        self.logger.info("数据表创建完成")
    
    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """创建索引以提高查询性能"""
        
        # 资产表索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_subtype ON assets(asset_subtype)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_currency ON assets(currency)")
        
        # 交易表索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_asset ON transactions(asset_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_currency ON transactions(currency)")
        
        # 详情表索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cash_transaction_id ON cash_transactions(transaction_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fixed_income_transaction_id ON fixed_income_transactions(transaction_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fixed_income_maturity ON fixed_income_transactions(maturity_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_equity_transaction_id ON equity_transactions(transaction_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_real_estate_transaction_id ON real_estate_transactions(transaction_id)")
        
        # 快照表索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_date_type ON portfolio_snapshots(snapshot_date DESC, snapshot_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_type_date ON portfolio_snapshots(snapshot_type, snapshot_date DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_currency ON portfolio_snapshots(base_currency)")
        
        # AI配置索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_configs_type ON ai_analysis_configs(ai_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_configs_default ON ai_analysis_configs(is_default, is_active)")
        
        # AI分析结果索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_results_snapshots ON ai_analysis_results(snapshot1_id, snapshot2_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_results_status ON ai_analysis_results(analysis_status, created_date DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_results_type ON ai_analysis_results(analysis_type, created_date DESC)")
        
        self.logger.info("索引创建完成")
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        if self.db_path == ":memory:":
            # 内存数据库需要保持持久连接
            if self._connection is None:
                self._connection = sqlite3.connect(self.db_path)
                self._connection.row_factory = sqlite3.Row
            yield self._connection
        else:
            # 文件数据库使用临时连接
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
    
    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """执行查询并返回结果"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """执行更新操作并返回影响的行数"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: Tuple = ()) -> str:
        """执行插入操作并返回最后插入的行ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def get_table_info(self, table_name: str) -> List[sqlite3.Row]:
        """获取表结构信息"""
        return self.execute_query(f"PRAGMA table_info({table_name})")
    
    def get_database_size(self) -> int:
        """获取数据库文件大小（字节）"""
        return os.path.getsize(self.db_path) if self.db_path.exists() else 0
    
    def vacuum_database(self) -> None:
        """清理数据库，回收空间"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        self.logger.info("数据库清理完成")
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径，默认为原文件名加时间戳
            
        Returns:
            备份文件路径
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = str(self.db_path.parent / f"wealth_lite_backup_{timestamp}.db")
        
        # 使用SQLite的备份API
        with self.get_connection() as source:
            backup_conn = sqlite3.connect(backup_path)
            source.backup(backup_conn)
            backup_conn.close()
        
        self.logger.info(f"数据库备份完成: {backup_path}")
        return backup_path
    
    def restore_database(self, backup_path: str) -> None:
        """
        从备份恢复数据库
        
        Args:
            backup_path: 备份文件路径
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"备份文件不存在: {backup_path}")
        
        # 关闭当前连接
        if self._connection:
            self._connection.close()
            self._connection = None
        
        # 替换数据库文件
        import shutil
        shutil.copy2(backup_path, self.db_path)
        
        self.logger.info(f"数据库恢复完成: {backup_path}")
    
    def get_version_info(self) -> Dict[str, Any]:
        """获取数据库版本信息"""
        try:
            # 尝试从配置文件读取版本信息
            config_path = self.db_path.parent / "config" / "db_version.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        
        # 默认版本信息
        return {
            "version": "1.0.0",
            "created_date": datetime.now().isoformat(),
            "last_migration": None
        }
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def is_connected(self):
        return self._connection is not None