# 投资组合快照功能设计文档

**版本**: v1.0  
**创建日期**: 2025-07-10  
**最后更新**: 2025-07-10  
**作者**: WealthLite开发团队

## 1. 功能概述

### 1.1 功能描述
投资组合快照功能允许用户保存特定时间点的投资组合状态，用于历史对比、业绩分析和投资决策支持。系统支持自动快照和手动快照两种模式。

### 1.2 核心价值
- **历史追踪**: 记录投资组合在不同时间点的状态
- **业绩分析**: 提供时间序列数据支持投资业绩评估
- **决策支持**: 通过历史数据分析辅助投资决策
- **合规记录**: 满足投资记录保存的合规要求

### 1.3 功能边界
- **包含**: 快照创建、存储、查询、分析、UI展示、AI分析对比
- **不包含**: 快照数据的外部导出、第三方系统集成
- **限制**: 每日最多保留一个自动快照和一个手动快照

## 2. 需求分析

### 2.1 自动快照需求
- **触发时机**: 每次服务启动时自动生成
- **存储策略**: 每天只保留一个快照，新快照覆盖当天的旧快照
- **数据范围**: 包含完整的投资组合状态和计算指标
- **生命周期**: 系统自动管理，用户无法手动删除

### 2.2 手动快照需求
- **触发方式**: 用户在投资组合页面手动触发
- **存储策略**: 每天只保留一个快照，新快照覆盖当天的旧快照
- **数据范围**: 与自动快照相同，但独立存储
- **生命周期**: 用户可以手动删除（除当天快照外）

### 2.3 UI交互需求
- **快照创建**: 提供"创建快照"按钮
- **快照浏览**: 提供快照列表，支持自动/手动快照切换
- **快照详情**: 显示快照的完整数据和分析
- **快照对比**: 支持不同快照之间的对比分析
- **AI分析对比**: 支持AI驱动的快照对比分析和投资建议

### 2.4 AI分析需求
- **AI服务选择**: 支持云端AI和本地AI两种模式
- **默认配置**: 默认使用本地AI，用户可切换到云端AI
- **分析功能**: 提供快照对比的深度分析和投资建议
- **配置管理**: 提供AI服务配置和切换界面

## 3. 数据模型设计

### 3.1 数据库表结构

#### 3.1.1 PORTFOLIO_SNAPSHOTS表
```sql
CREATE TABLE portfolio_snapshots (
    snapshot_id VARCHAR(36) PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    snapshot_time TIMESTAMP NOT NULL,
    snapshot_type VARCHAR(20) NOT NULL,  -- 'AUTO' 或 'MANUAL'
    base_currency VARCHAR(3) NOT NULL,
    
    -- 组合概览数据
    total_value DECIMAL(20,2) NOT NULL,
    total_cost DECIMAL(20,2) NOT NULL,
    total_return DECIMAL(20,2) NOT NULL,
    total_return_rate DECIMAL(10,4) NOT NULL,
    
    -- 分类统计
    cash_value DECIMAL(20,2) DEFAULT 0,
    fixed_income_value DECIMAL(20,2) DEFAULT 0,
    equity_value DECIMAL(20,2) DEFAULT 0,
    real_estate_value DECIMAL(20,2) DEFAULT 0,
    commodity_value DECIMAL(20,2) DEFAULT 0,
    
    -- 业绩指标
    annualized_return DECIMAL(10,4) DEFAULT 0,
    volatility DECIMAL(10,4) DEFAULT 0,
    sharpe_ratio DECIMAL(10,4) DEFAULT 0,
    max_drawdown DECIMAL(10,4) DEFAULT 0,
    
    -- 详细数据（JSON格式）
    position_snapshots TEXT NOT NULL,  -- JSON: 完整的持仓详情
    asset_allocation TEXT NOT NULL,    -- JSON: 资产配置分析
    performance_metrics TEXT NOT NULL, -- JSON: 业绩指标详情
    
    -- 元数据
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    
    -- 唯一约束：每天每种类型只能有一个快照
    UNIQUE(snapshot_date, snapshot_type)
);
```

#### 3.1.2 AI_ANALYSIS_CONFIGS表
```sql
CREATE TABLE ai_analysis_configs (
    config_id VARCHAR(36) PRIMARY KEY,
    config_name VARCHAR(100) NOT NULL,
    ai_type VARCHAR(20) NOT NULL,  -- 'LOCAL' 或 'CLOUD'
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 本地AI配置
    local_model_path VARCHAR(500),
    local_model_name VARCHAR(100),
    local_api_port INTEGER,
    
    -- 云端AI配置
    cloud_provider VARCHAR(50),  -- 'OPENAI', 'CLAUDE', 'GEMINI' 等
    cloud_api_key VARCHAR(500),
    cloud_api_url VARCHAR(500),
    cloud_model_name VARCHAR(100),
    
    -- 通用配置
    max_tokens INTEGER DEFAULT 4000,
    temperature DECIMAL(3,2) DEFAULT 0.7,
    timeout_seconds INTEGER DEFAULT 30,
    
    -- 元数据
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 确保只有一个默认配置
    UNIQUE(is_default) WHERE is_default = TRUE
);
```

#### 3.1.3 AI_ANALYSIS_RESULTS表
```sql
CREATE TABLE ai_analysis_results (
    analysis_id VARCHAR(36) PRIMARY KEY,
    snapshot1_id VARCHAR(36) NOT NULL,
    snapshot2_id VARCHAR(36) NOT NULL,
    config_id VARCHAR(36) NOT NULL,
    
    -- 分析结果
    analysis_content TEXT NOT NULL,
    analysis_summary TEXT,
    investment_advice TEXT,
    risk_assessment TEXT,
    
    -- 分析元数据
    analysis_type VARCHAR(50) NOT NULL,  -- 'COMPARISON', 'TREND', 'RISK' 等
    analysis_status VARCHAR(20) NOT NULL, -- 'SUCCESS', 'FAILED', 'PENDING'
    error_message TEXT,
    processing_time_ms INTEGER,
    
    -- 时间戳
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (snapshot1_id) REFERENCES portfolio_snapshots(snapshot_id),
    FOREIGN KEY (snapshot2_id) REFERENCES portfolio_snapshots(snapshot_id),
    FOREIGN KEY (config_id) REFERENCES ai_analysis_configs(config_id)
);
```

#### 3.1.4 索引设计
```sql
-- 主要查询索引
CREATE INDEX idx_snapshots_date_type ON portfolio_snapshots(snapshot_date DESC, snapshot_type);
CREATE INDEX idx_snapshots_type_date ON portfolio_snapshots(snapshot_type, snapshot_date DESC);
CREATE INDEX idx_snapshots_currency ON portfolio_snapshots(base_currency);

-- AI配置索引
CREATE INDEX idx_ai_configs_type ON ai_analysis_configs(ai_type);
CREATE INDEX idx_ai_configs_default ON ai_analysis_configs(is_default, is_active);

-- AI分析结果索引
CREATE INDEX idx_ai_results_snapshots ON ai_analysis_results(snapshot1_id, snapshot2_id);
CREATE INDEX idx_ai_results_status ON ai_analysis_results(analysis_status, created_date DESC);
CREATE INDEX idx_ai_results_type ON ai_analysis_results(analysis_type, created_date DESC);
```

### 3.2 数据模型类

#### 3.2.1 PortfolioSnapshot类
```python
@dataclass
class PortfolioSnapshot:
    """投资组合快照"""
    
    # 基础信息
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snapshot_date: date = field(default_factory=date.today)
    snapshot_time: datetime = field(default_factory=datetime.now)
    snapshot_type: SnapshotType = SnapshotType.MANUAL
    base_currency: Currency = Currency.CNY
    
    # 组合概览
    total_value: Decimal = Decimal('0')
    total_cost: Decimal = Decimal('0')
    total_return: Decimal = Decimal('0')
    total_return_rate: Decimal = Decimal('0')
    
    # 分类统计
    cash_value: Decimal = Decimal('0')
    fixed_income_value: Decimal = Decimal('0')
    equity_value: Decimal = Decimal('0')
    real_estate_value: Decimal = Decimal('0')
    commodity_value: Decimal = Decimal('0')
    
    # 业绩指标
    annualized_return: Decimal = Decimal('0')
    volatility: Decimal = Decimal('0')
    sharpe_ratio: Decimal = Decimal('0')
    max_drawdown: Decimal = Decimal('0')
    
    # 详细数据
    position_snapshots: List[Dict[str, Any]] = field(default_factory=list)
    asset_allocation: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    created_date: datetime = field(default_factory=datetime.now)
    notes: str = ""
    
    @property
    def is_today(self) -> bool:
        """判断是否为今天的快照"""
        return self.snapshot_date == date.today()
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        type_name = "自动" if self.snapshot_type == SnapshotType.AUTO else "手动"
        return f"{self.snapshot_date.strftime('%Y-%m-%d')} {type_name}快照"
```

#### 3.2.2 SnapshotType枚举
```python
class SnapshotType(Enum):
    AUTO = "AUTO"     # 自动快照
    MANUAL = "MANUAL" # 手动快照
    
    @property
    def display_name(self) -> str:
        return {"AUTO": "自动快照", "MANUAL": "手动快照"}[self.value]
```

#### 3.2.3 AIAnalysisConfig类
```python
@dataclass
class AIAnalysisConfig:
    """AI分析配置"""
    
    # 基础信息
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config_name: str = ""
    ai_type: AIType = AIType.LOCAL
    is_default: bool = False
    is_active: bool = True
    
    # 本地AI配置
    local_model_path: str = ""
    local_model_name: str = ""
    local_api_port: int = 11434  # Ollama默认端口
    
    # 云端AI配置
    cloud_provider: str = ""
    cloud_api_key: str = ""
    cloud_api_url: str = ""
    cloud_model_name: str = ""
    
    # 通用配置
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout_seconds: int = 30
    
    # 元数据
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        return f"{self.config_name} ({self.ai_type.display_name})"
```

#### 3.2.4 AIType枚举
```python
class AIType(Enum):
    LOCAL = "LOCAL"   # 本地AI
    CLOUD = "CLOUD"   # 云端AI
    
    @property
    def display_name(self) -> str:
        return {"LOCAL": "本地AI", "CLOUD": "云端AI"}[self.value]
```

#### 3.2.5 AIAnalysisResult类
```python
@dataclass
class AIAnalysisResult:
    """AI分析结果"""
    
    # 基础信息
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snapshot1_id: str = ""
    snapshot2_id: str = ""
    config_id: str = ""
    
    # 分析结果
    analysis_content: str = ""
    analysis_summary: str = ""
    investment_advice: str = ""
    risk_assessment: str = ""
    
    # 分析元数据
    analysis_type: str = "COMPARISON"
    analysis_status: str = "PENDING"
    error_message: str = ""
    processing_time_ms: int = 0
    
    # 时间戳
    created_date: datetime = field(default_factory=datetime.now)
    
    @property
    def is_success(self) -> bool:
        """判断分析是否成功"""
        return self.analysis_status == "SUCCESS"
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        return f"AI分析 - {self.created_date.strftime('%Y-%m-%d %H:%M')}"
```

## 4. 业务逻辑设计

### 4.1 快照创建流程

#### 4.1.1 自动快照创建
```python
class AutoSnapshotService:
    def create_startup_snapshot(self):
        """服务启动时创建自动快照"""
        try:
            # 1. 检查今天是否已有自动快照
            today = date.today()
            existing_snapshot = self.snapshot_repository.get_by_date_and_type(
                today, SnapshotType.AUTO
            )
            
            # 2. 如果存在，删除旧快照
            if existing_snapshot:
                self.snapshot_repository.delete(existing_snapshot.snapshot_id)
                logger.info(f"删除旧的自动快照: {existing_snapshot.snapshot_id}")
            
            # 3. 计算当前投资组合状态
            current_portfolio = self.portfolio_service.get_current_portfolio()
            
            # 4. 创建新快照
            snapshot = self.create_snapshot_from_portfolio(
                current_portfolio, 
                SnapshotType.AUTO
            )
            
            # 5. 保存快照
            self.snapshot_repository.save(snapshot)
            logger.info(f"创建自动快照成功: {snapshot.snapshot_id}")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"创建自动快照失败: {e}")
            raise
```

#### 4.1.2 手动快照创建
```python
class ManualSnapshotService:
    def create_manual_snapshot(self, notes: str = "") -> PortfolioSnapshot:
        """用户手动创建快照"""
        try:
            # 1. 检查今天是否已有手动快照
            today = date.today()
            existing_snapshot = self.snapshot_repository.get_by_date_and_type(
                today, SnapshotType.MANUAL
            )
            
            # 2. 如果存在，询问用户是否覆盖
            if existing_snapshot:
                # 前端会处理确认逻辑
                self.snapshot_repository.delete(existing_snapshot.snapshot_id)
                logger.info(f"删除旧的手动快照: {existing_snapshot.snapshot_id}")
            
            # 3. 计算当前投资组合状态
            current_portfolio = self.portfolio_service.get_current_portfolio()
            
            # 4. 创建新快照
            snapshot = self.create_snapshot_from_portfolio(
                current_portfolio, 
                SnapshotType.MANUAL,
                notes
            )
            
            # 5. 保存快照
            self.snapshot_repository.save(snapshot)
            logger.info(f"创建手动快照成功: {snapshot.snapshot_id}")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"创建手动快照失败: {e}")
            raise
```

### 4.2 快照数据计算

#### 4.2.1 核心计算逻辑
```python
class SnapshotCalculator:
    def create_snapshot_from_portfolio(
        self, 
        portfolio: Portfolio, 
        snapshot_type: SnapshotType,
        notes: str = ""
    ) -> PortfolioSnapshot:
        """从投资组合创建快照"""
        
        # 1. 计算基础数据
        total_value = sum(pos.current_value for pos in portfolio.positions)
        total_cost = sum(pos.total_cost for pos in portfolio.positions)
        total_return = total_value - total_cost
        total_return_rate = total_return / total_cost if total_cost > 0 else 0
        
        # 2. 计算分类统计
        type_values = self.calculate_asset_type_values(portfolio.positions)
        
        # 3. 计算业绩指标
        performance_metrics = self.calculate_performance_metrics(portfolio)
        
        # 4. 生成持仓快照
        position_snapshots = self.create_position_snapshots(portfolio.positions)
        
        # 5. 计算资产配置
        asset_allocation = self.calculate_asset_allocation(portfolio.positions)
        
        # 6. 创建快照对象
        snapshot = PortfolioSnapshot(
            snapshot_type=snapshot_type,
            total_value=total_value,
            total_cost=total_cost,
            total_return=total_return,
            total_return_rate=total_return_rate,
            cash_value=type_values.get('CASH', 0),
            fixed_income_value=type_values.get('FIXED_INCOME', 0),
            equity_value=type_values.get('EQUITY', 0),
            real_estate_value=type_values.get('REAL_ESTATE', 0),
            commodity_value=type_values.get('COMMODITY', 0),
            annualized_return=performance_metrics.get('annualized_return', 0),
            volatility=performance_metrics.get('volatility', 0),
            sharpe_ratio=performance_metrics.get('sharpe_ratio', 0),
            max_drawdown=performance_metrics.get('max_drawdown', 0),
            position_snapshots=position_snapshots,
            asset_allocation=asset_allocation,
            performance_metrics=performance_metrics,
            notes=notes
        )
        
        return snapshot
```

### 4.3 快照查询和分析

#### 4.3.1 快照列表查询
```python
class SnapshotQueryService:
    def get_snapshots_by_type(
        self, 
        snapshot_type: SnapshotType,
        limit: int = 30,
        offset: int = 0
    ) -> List[PortfolioSnapshot]:
        """按类型查询快照列表"""
        return self.snapshot_repository.get_by_type(
            snapshot_type, limit, offset
        )
    
    def get_recent_snapshots(
        self, 
        days: int = 30
    ) -> Dict[str, List[PortfolioSnapshot]]:
        """获取最近的快照（按类型分组）"""
        start_date = date.today() - timedelta(days=days)
        snapshots = self.snapshot_repository.get_by_date_range(
            start_date, date.today()
        )
        
        return {
            'auto': [s for s in snapshots if s.snapshot_type == SnapshotType.AUTO],
            'manual': [s for s in snapshots if s.snapshot_type == SnapshotType.MANUAL]
        }
```

#### 4.3.2 快照对比分析
```python
class SnapshotComparisonService:
    def compare_snapshots(
        self, 
        snapshot1: PortfolioSnapshot, 
        snapshot2: PortfolioSnapshot
    ) -> Dict[str, Any]:
        """对比两个快照"""
        
        # 1. 基础数据对比
        value_change = snapshot2.total_value - snapshot1.total_value
        value_change_rate = value_change / snapshot1.total_value if snapshot1.total_value > 0 else 0
        
        # 2. 分类数据对比
        type_changes = {}
        for asset_type in ['cash', 'fixed_income', 'equity', 'real_estate', 'commodity']:
            old_value = getattr(snapshot1, f'{asset_type}_value')
            new_value = getattr(snapshot2, f'{asset_type}_value')
            type_changes[asset_type] = {
                'old_value': old_value,
                'new_value': new_value,
                'change': new_value - old_value,
                'change_rate': (new_value - old_value) / old_value if old_value > 0 else 0
            }
        
        # 3. 业绩指标对比
        performance_changes = {
            'annualized_return': {
                'old': snapshot1.annualized_return,
                'new': snapshot2.annualized_return,
                'change': snapshot2.annualized_return - snapshot1.annualized_return
            },
            'volatility': {
                'old': snapshot1.volatility,
                'new': snapshot2.volatility,
                'change': snapshot2.volatility - snapshot1.volatility
            }
        }
        
        return {
            'period': {
                'start_date': snapshot1.snapshot_date,
                'end_date': snapshot2.snapshot_date,
                'days': (snapshot2.snapshot_date - snapshot1.snapshot_date).days
            },
            'value_change': {
                'absolute': value_change,
                'rate': value_change_rate
            },
            'type_changes': type_changes,
            'performance_changes': performance_changes
        }
```

### 4.4 AI分析服务设计

#### 4.4.1 AI配置管理服务
```python
class AIConfigService:
    def get_default_config(self) -> AIAnalysisConfig:
        """获取默认AI配置"""
        config = self.config_repository.get_default_config()
        if not config:
            # 创建默认本地AI配置
            config = AIAnalysisConfig(
                config_name="默认本地AI",
                ai_type=AIType.LOCAL,
                is_default=True,
                local_model_name="llama3.1:8b",
                local_api_port=11434
            )
            self.config_repository.save(config)
        return config
    
    def switch_ai_type(self, ai_type: AIType) -> AIAnalysisConfig:
        """切换AI类型"""
        configs = self.config_repository.get_by_type(ai_type)
        if not configs:
            raise ValueError(f"未找到{ai_type.display_name}配置")
        
        # 设置为默认配置
        config = configs[0]
        self.config_repository.set_default(config.config_id)
        return config
```

#### 4.4.2 AI分析服务
```python
class AIAnalysisService:
    def analyze_snapshots(
        self, 
        snapshot1: PortfolioSnapshot, 
        snapshot2: PortfolioSnapshot,
        config: AIAnalysisConfig = None
    ) -> AIAnalysisResult:
        """AI分析两个快照的对比"""
        
        if not config:
            config = self.config_service.get_default_config()
        
        # 创建分析结果记录
        result = AIAnalysisResult(
            snapshot1_id=snapshot1.snapshot_id,
            snapshot2_id=snapshot2.snapshot_id,
            config_id=config.config_id,
            analysis_type="COMPARISON",
            analysis_status="PENDING"
        )
        
        try:
            start_time = time.time()
            
            # 准备分析数据
            analysis_data = self.prepare_analysis_data(snapshot1, snapshot2)
            
            # 调用AI分析
            if config.ai_type == AIType.LOCAL:
                analysis_content = self.call_local_ai(analysis_data, config)
            else:
                analysis_content = self.call_cloud_ai(analysis_data, config)
            
            # 解析AI响应
            parsed_result = self.parse_ai_response(analysis_content)
            
            # 更新结果
            result.analysis_content = analysis_content
            result.analysis_summary = parsed_result.get('summary', '')
            result.investment_advice = parsed_result.get('advice', '')
            result.risk_assessment = parsed_result.get('risk', '')
            result.analysis_status = "SUCCESS"
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            
        except Exception as e:
            result.analysis_status = "FAILED"
            result.error_message = str(e)
            logger.error(f"AI分析失败: {e}")
        
        # 保存结果
        self.analysis_repository.save(result)
        return result
    
    def call_local_ai(self, data: dict, config: AIAnalysisConfig) -> str:
        """调用本地AI"""
        import requests
        
        url = f"http://localhost:{config.local_api_port}/api/generate"
        prompt = self.build_analysis_prompt(data)
        
        payload = {
            "model": config.local_model_name,
            "prompt": prompt,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens
            }
        }
        
        response = requests.post(
            url, 
            json=payload, 
            timeout=config.timeout_seconds
        )
        response.raise_for_status()
        
        return response.json().get('response', '')
    
    def call_cloud_ai(self, data: dict, config: AIAnalysisConfig) -> str:
        """调用云端AI"""
        # 根据不同的云端提供商实现
        if config.cloud_provider == "OPENAI":
            return self.call_openai(data, config)
        elif config.cloud_provider == "CLAUDE":
            return self.call_claude(data, config)
        else:
            raise ValueError(f"不支持的云端AI提供商: {config.cloud_provider}")
    
    def build_analysis_prompt(self, data: dict) -> str:
        """构建分析提示词"""
        return f"""
        作为专业的投资顾问，请分析以下两个投资组合快照的变化：

        快照1 ({data['snapshot1']['date']}):
        - 总价值: {data['snapshot1']['total_value']}
        - 总收益: {data['snapshot1']['total_return']}
        - 资产配置: {data['snapshot1']['allocation']}

        快照2 ({data['snapshot2']['date']}):
        - 总价值: {data['snapshot2']['total_value']}
        - 总收益: {data['snapshot2']['total_return']}
        - 资产配置: {data['snapshot2']['allocation']}

        请从以下角度进行分析：
        1. 投资业绩变化分析
        2. 资产配置变化分析
        3. 风险评估
        4. 投资建议

        请用JSON格式返回分析结果：
        {{
            "summary": "整体分析摘要",
            "advice": "投资建议",
            "risk": "风险评估"
        }}
        """
```

## 5. API接口设计

### 5.1 快照创建API

#### 5.1.1 创建手动快照
```http
POST /api/portfolio/snapshots
Content-Type: application/json

{
    "notes": "月度投资组合快照"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "snapshot_id": "snapshot_001",
        "snapshot_date": "2025-07-10",
        "snapshot_type": "MANUAL",
        "total_value": 1234567.89,
        "total_return": 123456.78,
        "total_return_rate": 0.1112,
        "message": "快照创建成功"
    }
}
```

### 5.2 快照查询API

#### 5.2.1 获取快照列表
```http
GET /api/portfolio/snapshots?type=AUTO&limit=20&offset=0
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "snapshots": [
            {
                "snapshot_id": "snapshot_001",
                "snapshot_date": "2025-07-10",
                "snapshot_type": "AUTO",
                "total_value": 1234567.89,
                "total_return": 123456.78,
                "display_name": "2025-07-10 自动快照"
            }
        ],
        "total": 45,
        "page": 1,
        "limit": 20
    }
}
```

#### 5.2.2 获取快照详情
```http
GET /api/portfolio/snapshots/{snapshot_id}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "snapshot_id": "snapshot_001",
        "snapshot_date": "2025-07-10",
        "snapshot_type": "AUTO",
        "total_value": 1234567.89,
        "position_snapshots": [...],
        "asset_allocation": {...},
        "performance_metrics": {...}
    }
}
```

### 5.3 快照分析API

#### 5.3.1 快照对比
```http
POST /api/portfolio/snapshots/compare
Content-Type: application/json

{
    "snapshot1_id": "snapshot_001",
    "snapshot2_id": "snapshot_002"
}
```

### 5.4 AI分析API

#### 5.4.1 获取AI配置
```http
GET /api/ai/configs
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "configs": [
            {
                "config_id": "config_001",
                "config_name": "默认本地AI",
                "ai_type": "LOCAL",
                "is_default": true,
                "display_name": "默认本地AI (本地AI)"
            }
        ],
        "default_config": {
            "config_id": "config_001",
            "ai_type": "LOCAL"
        }
    }
}
```

#### 5.4.2 切换AI类型
```http
POST /api/ai/configs/switch
Content-Type: application/json

{
    "ai_type": "CLOUD"
}
```

#### 5.4.3 AI分析快照对比
```http
POST /api/ai/analysis/snapshots
Content-Type: application/json

{
    "snapshot1_id": "snapshot_001",
    "snapshot2_id": "snapshot_002",
    "config_id": "config_001"
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "analysis_id": "analysis_001",
        "analysis_status": "SUCCESS",
        "analysis_summary": "投资组合在过去30天内表现良好...",
        "investment_advice": "建议增加权益资产配置...",
        "risk_assessment": "当前风险水平适中...",
        "processing_time_ms": 2500
    }
}
```

#### 5.4.4 获取AI分析结果
```http
GET /api/ai/analysis/{analysis_id}
```

## 6. 前端UI设计

### 6.1 页面布局

#### 6.1.1 投资组合页面布局
```
┌─────────────────────────────────────────────────────────┐
│ 📊 投资组合                                             │
├─────────────────────────────────────────────────────────┤
│ 🔄 当前组合概览                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 总价值: ¥1,234,567  总收益: ¥123,456 (+11.12%)     │ │
│ │ [📸 创建快照]                                       │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 📈 快照浏览                                             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [🤖 自动快照] [👤 手动快照]                         │ │
│ │ ┌─────────────────────────────────────────────────┐ │ │
│ │ │ 2025-07-10 自动快照  ¥1,234,567  [查看详情]    │ │ │
│ │ │ 2025-07-09 自动快照  ¥1,220,000  [查看详情]    │ │ │
│ │ │ 2025-07-08 手动快照  ¥1,215,000  [查看详情]    │ │ │
│ │ └─────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 🤖 AI分析对比                                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ AI类型: [🏠 本地AI] [☁️ 云端AI]                     │ │
│ │ 选择快照: [选择快照1] [选择快照2] [🔍 AI分析]       │ │
│ │ 分析结果: [显示AI分析结果和建议]                    │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### 6.1.2 快照详情页面
```
┌─────────────────────────────────────────────────────────┐
│ 📊 快照详情 - 2025-07-10 自动快照                      │
├─────────────────────────────────────────────────────────┤
│ 📈 概览数据                                             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 总价值: ¥1,234,567  总成本: ¥1,111,111             │ │
│ │ 总收益: ¥123,456    收益率: 11.12%                 │ │
│ │ 年化收益: 15.5%     夏普比率: 1.25                 │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 🥧 资产配置                                             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [饼图显示资产配置]                                  │ │
│ │ 现金: 30%  固收: 50%  权益: 20%                    │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ 📋 持仓详情                                             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [持仓列表表格]                                      │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 6.2 交互设计

#### 6.2.1 快照创建流程
1. 用户点击"创建快照"按钮
2. 如果当天已有手动快照，显示确认对话框
3. 用户输入快照备注（可选）
4. 系统创建快照并显示成功消息
5. 刷新快照列表

#### 6.2.2 快照浏览流程
1. 默认显示自动快照列表
2. 用户可切换到手动快照标签
3. 点击"查看详情"进入快照详情页
4. 支持快照对比功能（选择两个快照）

#### 6.2.3 AI分析流程
1. 用户选择AI类型（本地AI/云端AI）
2. 系统显示当前AI配置状态
3. 用户选择两个快照进行对比
4. 点击"AI分析"按钮开始分析
5. 显示分析进度和结果
6. 用户可查看详细的AI分析报告

#### 6.2.4 AI配置管理流程
1. 用户进入AI配置页面
2. 查看当前配置状态
3. 切换AI类型（本地/云端）
4. 配置相关参数（API密钥、模型名称等）
5. 保存配置并测试连接

## 7. 实现计划

### 7.1 开发阶段

#### 阶段1: 数据模型和后端API (3天)
- [ ] 创建数据库表结构
- [ ] 实现PortfolioSnapshot模型类
- [ ] 实现SnapshotRepository
- [ ] 实现SnapshotService
- [ ] 实现自动快照创建逻辑
- [ ] 实现手动快照API接口

#### 阶段2: 前端UI实现 (3天)
- [ ] 设计快照相关UI组件
- [ ] 实现快照列表页面
- [ ] 实现快照详情页面
- [ ] 实现快照创建功能
- [ ] 实现快照类型切换

#### 阶段3: 高级功能 (2天)
- [ ] 实现快照对比功能
- [ ] 实现快照分析图表
- [ ] 优化性能和用户体验
- [ ] 编写单元测试

#### 阶段4: 集成和测试 (2天)
- [ ] 集成测试
- [ ] 用户体验测试
- [ ] 性能测试
- [ ] 文档完善

#### 阶段5: AI分析功能 (3天) - 最低优先级
- [ ] 实现AI配置管理
- [ ] 实现本地AI调用接口
- [ ] 实现云端AI调用接口
- [ ] 实现AI分析服务
- [ ] 实现AI分析UI界面
- [ ] AI功能测试和优化

### 7.2 技术风险

#### 7.2.1 数据量风险
- **问题**: 快照数据可能占用大量存储空间
- **解决方案**: 实现数据压缩和过期清理机制

#### 7.2.2 计算性能风险
- **问题**: 复杂投资组合的快照计算可能耗时较长
- **解决方案**: 异步计算和缓存优化

#### 7.2.3 数据一致性风险
- **问题**: 快照创建过程中数据可能发生变化
- **解决方案**: 使用事务和锁机制保证数据一致性

#### 7.2.4 AI服务可用性风险
- **问题**: 本地AI服务可能不可用，云端AI可能网络异常
- **解决方案**: 实现AI服务健康检查和降级机制

#### 7.2.5 AI分析质量风险
- **问题**: AI分析结果可能不准确或不符合预期
- **解决方案**: 实现分析结果验证和用户反馈机制

## 8. 测试计划

### 8.1 单元测试
- PortfolioSnapshot模型测试
- SnapshotService业务逻辑测试
- SnapshotRepository数据访问测试
- 快照计算算法测试

### 8.2 集成测试
- 自动快照创建流程测试
- 手动快照创建流程测试
- API接口集成测试
- 前后端数据交互测试

### 8.3 性能测试
- 大量快照数据查询性能测试
- 复杂投资组合快照计算性能测试
- 并发快照创建测试

### 8.4 用户体验测试
- 快照创建流程用户体验测试
- 快照浏览和详情查看测试
- 快照对比功能测试

### 8.5 AI功能测试
- AI配置管理测试
- 本地AI调用测试
- 云端AI调用测试
- AI分析结果准确性测试
- AI服务异常处理测试

## 9. 部署和维护

### 9.1 部署要求
- 数据库迁移脚本
- 配置文件更新
- 服务重启流程
- 数据备份策略

### 9.2 监控和日志
- 快照创建成功率监控
- 快照查询性能监控
- AI分析服务可用性监控
- AI分析成功率和响应时间监控
- 异常情况告警
- 详细操作日志记录

### 9.3 维护计划
- 定期清理过期快照数据
- 数据库性能优化
- 快照数据完整性检查
- AI分析结果质量评估
- AI模型更新和优化
- 用户反馈收集和改进

---

**审核清单**:
- [ ] 需求理解是否准确
- [ ] 数据模型设计是否合理
- [ ] API接口设计是否完整
- [ ] UI设计是否符合用户体验
- [ ] 实现计划是否可行
- [ ] 技术风险是否充分考虑
- [ ] 测试计划是否全面
- [ ] AI功能设计是否合理
- [ ] AI服务集成是否可行
- [ ] 优先级安排是否合适

**重要说明**:
1. **AI功能优先级**: AI分析功能被放置在最低优先级（阶段5），确保核心快照功能优先完成
2. **AI服务支持**: 支持本地AI（默认）和云端AI两种模式，用户可自由切换
3. **技术栈**: 本地AI使用Ollama，云端AI支持OpenAI、Claude等主流服务
4. **降级机制**: 当AI服务不可用时，仍可正常使用基础快照功能

**请审核以上设计文档，确认无误后我们开始实施开发。** 