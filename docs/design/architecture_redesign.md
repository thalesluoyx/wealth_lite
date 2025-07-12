# WealthLite 架构重设计方案

## 背景

原系统存在双模型并存的问题：Asset模型和Transaction/Position模型各自独立，导致前端UI混乱、数据重复且不一致。本文档记录了架构重设计的完整方案。

## 问题分析

### 当前问题
1. **双模型并存**：Asset模型和Transaction/Position模型各自独立，数据重复且不一致
2. **职责混乱**：Asset类既包含静态属性又包含交易记录，违反单一职责原则
3. **类型局限**：当前Transaction模型主要针对固定收益产品，扩展性差
4. **数据流混乱**：两套模型的数据流向不明确，难以维护

## 设计原则

### 核心原则
- **交易驱动**：所有持仓都由交易产生
- **职责分离**：每个类只负责自己的核心职责
- **类型抽象**：支持多种资产类型的扩展
- **轻量化**：保持系统简洁，避免过度设计

### 业务原则
- **只有交易能产生持仓**：符合金融系统的核心原理
- **数据可追溯性**：所有计算结果都能追溯到原始交易
- **多货币支持**：支持用户自定义基础货币
- **国际化**：支持中英文双语

## 新架构设计

### 层次结构

```
配置管理层 (🔄 Phase 1.5 - 待补充)
├── AppConfig (应用配置)
├── I18nManager (国际化管理)
└── ExchangeRateManager (汇率管理)

资产定义层 (✅ Phase 1 - 已完成)
├── Asset (资产基础信息) - models/asset.py
├── AssetType (资产类型枚举) - models/enums.py
├── TransactionType (交易类型枚举) - models/enums.py
├── Currency (货币枚举) - models/enums.py
├── InterestType (利息类型枚举) - models/enums.py
├── PaymentFrequency (付息频率枚举) - models/enums.py
├── PositionStatus (持仓状态枚举) - models/enums.py
├── RiskLevel (风险等级枚举) - models/enums.py
└── LiquidityLevel (流动性等级枚举) - models/enums.py

交易事件层 (✅ Phase 1 - 已完成)
├── BaseTransaction (通用交易基类) - models/transaction.py
├── CashTransaction (现金类交易) - models/transaction.py
├── FixedIncomeTransaction (固定收益交易) - models/transaction.py
├── EquityTransaction (权益类交易) - models/transaction.py
└── RealEstateTransaction (房产交易) - models/transaction.py

持仓计算层 (✅ Phase 1 - 已完成)
├── Position (持仓状态) - models/position.py
├── Portfolio (投资组合) - models/portfolio.py
└── PortfolioSnapshot (组合快照) - models/portfolio.py

数据持久化层 (✅ Phase 1 - 已完成)
├── DatabaseManager (数据库管理器) - data/database.py
├── AssetRepository (资产数据访问) - data/repositories.py
├── TransactionRepository (交易数据访问) - data/repositories.py
├── PortfolioSnapshotRepository (快照数据访问) - data/repositories.py
└── RepositoryManager (数据访问管理器) - data/repositories.py

业务服务层 (✅ Phase 1 - 已完成)
└── WealthService (财富管理服务) - services/wealth_service.py

专业计算层 (🔄 Phase 2+ - 待实现)
├── CashCalculator (现金类计算器)
├── FixedIncomeCalculator (固定收益计算器)
├── EquityCalculator (权益类计算器)
└── RealEstateCalculator (房产计算器)

分析报告层 (🔄 Phase 5 - 待实现)
├── PerformanceAnalyzer (业绩分析器)
└── ReportGenerator (报告生成器)
```

### 核心类设计

#### Asset（资产基础信息）
```python
class Asset:
    - asset_id: str
    - asset_name: str  
    - asset_type: AssetType
    - asset_subtype: Optional[AssetSubType]
    - currency: Currency
    - 静态属性（发行方、评级等）
    # 职责：只管理资产的静态属性，不包含交易记录和计算逻辑
```

#### AssetType（资产类型枚举）
```python
class AssetType(Enum):
    # === 第一阶段开发范围 ===
    CASH = "现金及等价物"          # ✅ Phase 1: 已实现
    FIXED_INCOME = "固定收益类"    # ✅ Phase 1: 已实现
    
    # === 后续阶段 ===
    EQUITY = "权益类"              # 🔄 Phase 2: 待实现
    REAL_ESTATE = "不动产"         # 🔄 Phase 3: 待实现
    COMMODITY = "大宗商品"         # 🔄 Phase 4: 待实现
```

**第一阶段开发说明**：
- **现金及等价物**：包括储蓄存款、货币基金、短期存款等
- **固定收益类**：包括政府债券、企业债券、定期存款等
- **开发重点**：完善这两种资产类型的完整功能链路

#### TransactionType（交易类型枚举）
```python
class TransactionType(Enum):
    BUY = "买入"
    SELL = "卖出"
    DEPOSIT = "存入"
    WITHDRAW = "取出"
    INTEREST = "利息收入"
    DIVIDEND = "分红收入"
    FEE = "手续费"
    TRANSFER_IN = "转入"
    TRANSFER_OUT = "转出"
```

#### BaseTransaction（通用交易基类）
```python
class BaseTransaction:
    - transaction_id: str
    - asset_id: str  # 关联到具体资产
    - transaction_date: date
    - transaction_type: TransactionType
    - amount: Decimal
    - currency: Currency
    - exchange_rate: Decimal
    - amount_base_currency: Decimal  # 基础货币金额
    # 职责：定义所有交易的共同属性
```

#### Position（持仓状态）
```python
class Position:
    - asset: Asset  # 关联资产信息
    - transactions: List[BaseTransaction]  # 关联交易记录
    - 计算属性（成本、市值、收益等）
    # 职责：基于交易记录计算持仓状态，所有数值都从交易记录计算得出
```

#### Portfolio（当前投资组合）
```python
class Portfolio:
    - positions: List[Position]  # 当前所有持仓
    - base_currency: Currency
    - total_value: Decimal  # 实时计算
    - total_cost: Decimal   # 实时计算
    - asset_allocation: Dict  # 实时计算
    - performance_metrics: Dict  # 实时计算
    # 职责：提供当前投资组合的实时状态，会受到新增交易（包括回溯交易）影响
```

#### PortfolioSnapshot（组合快照）
```python
class PortfolioSnapshot:
    - snapshot_id: str
    - snapshot_date: datetime
    - base_currency: Currency  # 快照时的基础货币
    - total_value: Decimal     # 快照时的总价值（不可变）
    - asset_allocation: Dict   # 快照时的资产配置（不可变）
    - performance_metrics: Dict # 快照时的业绩指标（不可变）
    - position_snapshots: List[Dict]  # 快照时各持仓的状态（不可变）
    # 职责：记录特定时间点的投资组合历史状态，一旦创建不可修改，不受后续交易影响
```

## 功能特性

### 1. Portfolio架构设计

#### 当前Portfolio（实时计算）
- **特性**：基于所有交易记录实时计算的投资组合状态
- **数据来源**：从所有Transaction动态计算Position，再汇总为Portfolio
- **更新机制**：任何新增交易（包括回溯交易）都会影响当前Portfolio的计算结果
- **用途**：提供最新、最准确的投资组合状态

#### Portfolio快照功能（历史存档）
- **特性**：记录特定时间点投资组合的不可变历史状态
- **数据独立性**：一旦创建，不受后续任何交易（包括回溯交易）影响
- **触发机制**：
  - 定期自动快照（每月/季度）
  - 重大交易后快照
  - 用户手动创建快照
- **存储策略**：完整记录快照时刻的组合状态，包括各持仓详情
- **用途**：历史对比、业绩评估、合规记录

### 2. 多货币支持
- **基础货币**：用户可自定义，默认人民币
- **汇率管理**：手动输入，记住最近使用的汇率
- **计算基准**：所有金额最终转换为基础货币进行分析
- **历史处理**：用户更改基础货币后，保留原始交易币种信息，重新计算所有基础货币金额

### 3. 国际化支持
- **语言支持**：中英文双语
- **实现优先级**：
  1. 核心业务逻辑的中英文支持
  2. UI界面的完整翻译
- **本地化内容**：
  - UI文本翻译
  - 数字格式本地化
  - 日期格式本地化
  - 货币显示格式

### 4. 现金及等价物分类
- **新增分类**：现金及等价物作为独立的一级分类
- **子类型**：活期存款、储蓄存款、货币基金、短期存款、国库券
- **特殊属性**：极高流动性、极低风险、简单利息计算

## 数据存储方案

### SQLite + JSON 混合方案

#### 选择理由
1. **轻量化**：SQLite单文件数据库，无需安装服务
2. **关系支持**：完美支持Asset-Transaction-Position关系
3. **事务安全**：保证数据完整性
4. **查询能力**：支持复杂的统计和分析查询
5. **跨平台**：Python内置支持，打包无额外依赖

#### 文件结构
```
user_data/
├── wealth_lite.db          # SQLite主数据库
├── config/
│   ├── app_config.json     # 应用配置
│   ├── i18n/              # 多语言文件
│   └── exchange_rates.json # 汇率缓存
├── exports/               # CSV/XLSX导出
└── backups/              # 数据库备份
```

#### 数据库表结构（软外键关联）- ✅ 已实现

**核心表结构**：
1. **ASSETS**：资产基础信息表（12个字段）
   - asset_id, asset_name, asset_type, asset_subtype
   - currency, description, issuer, credit_rating, extended_attributes
   - created_date, updated_date

2. **TRANSACTIONS**：交易记录主表（10个字段）
   - transaction_id, asset_id, transaction_date, transaction_type
   - amount, currency, exchange_rate, amount_base_currency
   - notes, created_date

3. **CASH_TRANSACTIONS**：现金交易详情表（4个字段）
   - transaction_id, account_type, interest_rate, compound_frequency

4. **FIXED_INCOME_TRANSACTIONS**：固定收益交易详情表（8个字段）
   - transaction_id, annual_rate, start_date, maturity_date
   - interest_type, payment_frequency, face_value, coupon_rate

5. **EQUITY_TRANSACTIONS**：权益交易详情表（5个字段，Phase 2准备）
   - transaction_id, quantity, price_per_share, dividend_amount, split_ratio

6. **REAL_ESTATE_TRANSACTIONS**：不动产交易详情表（5个字段，Phase 3准备）
   - transaction_id, property_area, price_per_unit, rental_income, property_type

7. **PORTFOLIO_SNAPSHOTS**：投资组合快照表（13个字段）
   - snapshot_id, snapshot_date, base_currency, description
   - total_value, total_cost, total_return, return_rate
   - asset_allocation, performance_metrics, position_snapshots
   - created_date, is_immutable

**索引设计**：
- 资产表：按类型、分类、货币建立索引
- 交易表：按资产ID、日期、类型、货币建立索引
- 详情表：按交易ID建立索引
- 快照表：按日期、货币建立索引
- **EQUITY_TRANSACTIONS**：权益类交易详情（软关联）
- **CASH_TRANSACTIONS**：现金类交易详情（软关联）
- **REAL_ESTATE_TRANSACTIONS**：房产交易详情（软关联）
- **PORTFOLIO_SNAPSHOTS**：投资组合快照（JSON存储）
- **EXCHANGE_RATES**：汇率信息
- **APP_CONFIG**：应用配置

#### Portfolio数据架构澄清
**当前Portfolio（实时计算）**：
- 不需要独立的数据表存储
- 基于TRANSACTIONS表实时计算所有Position
- 通过Service层聚合生成Portfolio对象
- 数据流：TRANSACTIONS → Position计算 → Portfolio聚合

**Portfolio快照（历史存档）**：
- 使用PORTFOLIO_SNAPSHOTS表存储
- position_snapshots字段以JSON格式存储完整的持仓详情
- 一旦创建，数据不可变，不受后续交易影响
- 用于历史对比和业绩分析

#### 软外键关联设计
**设计原则**：
- 采用软外键关联，避免数据库级强约束
- 所有表间关联通过ID字段建立逻辑关系
- 数据完整性由软件层Repository和Service保证
- 通过索引优化查询性能

**优势**：
- **灵活性**：无外键约束限制，支持复杂业务逻辑
- **扩展性**：易于添加新的交易类型和关联关系
- **性能**：避免外键检查开销，提升操作效率
- **维护性**：软件层控制数据一致性，便于调试和维护

**实现策略**：
- Repository层负责数据持久化和基础验证
- Service层负责业务逻辑验证和事务管理
- 使用LEFT JOIN查询获取完整的关联数据
- 通过软件事务保证数据操作的原子性

### 性能优化
- **索引优化**：在查询频繁的字段上建立索引
- **连接池**：复用数据库连接
- **批量操作**：交易数据批量插入
- **延迟加载**：大量数据分页加载

## 数据流设计

### 标准流程
1. **资产定义** → 创建Asset（静态信息）
2. **交易发生** → 创建具体Transaction
3. **持仓计算** → 基于Transaction生成Position
4. **组合分析** → 基于多个Position生成Portfolio
5. **快照记录** → 定期或手动创建PortfolioSnapshot

### 计算逻辑
- 所有持仓状态都从交易记录实时计算
- 基础货币转换在交易记录时完成
- 快照仅存储计算结果，不存储中间数据

## 前后端分离架构设计

随着系统功能的扩展，特别是AI分析功能的引入，WealthLite采用了前后端分离的架构设计。这种设计模式使前端界面和后端业务逻辑可以独立开发和部署，提高了系统的可维护性和扩展性。

### 服务器架构

```
WealthLite服务器架构
├── UI服务器 (serve.py)
│   ├── 提供静态文件服务
│   ├── 开发环境热重载功能
│   └── API请求代理转发
└── API服务器 (api_server.py)
    ├── 处理业务逻辑请求
    ├── 数据处理和持久化
    ├── AI功能集成
    └── 安全认证和授权
```

#### UI服务器 (serve.py)
- **主要职责**：提供静态文件服务，托管前端HTML、CSS和JavaScript文件
- **开发功能**：提供热重载功能，方便前端开发
- **代理功能**：将API请求转发到API服务器，解决跨域问题

#### API服务器 (api_server.py)
- **主要职责**：处理所有业务逻辑和数据处理
- **路由管理**：通过api_routes.py定义API端点和路由
- **数据安全**：处理敏感信息，如API密钥等
- **复杂计算**：执行需要服务器端处理的复杂计算

### 为什么需要API服务器

在引入AI分析功能之前，WealthLite主要依赖前端代码和本地数据处理。随着AI功能的引入，出现了以下需求：

1. **服务器端处理**：
   - AI分析需要调用外部API（如OpenRouter），这需要在服务器端进行
   - 需要安全存储API密钥，不能暴露在前端代码中
   - 处理大量数据和复杂计算，超出了浏览器的能力范围

2. **数据安全**：
   - 保护用户的财务数据和分析结果
   - 安全管理API密钥和认证信息

3. **扩展性**：
   - 支持更多后端服务和第三方集成
   - 为未来功能（如多用户支持、云同步等）奠定基础

### API设计原则

1. **RESTful设计**：
   - 使用标准HTTP方法（GET、POST、PUT、DELETE）
   - 资源导向的URL设计
   - 使用适当的状态码

2. **响应格式统一**：
   - 所有API响应使用统一格式：`{"success": true, "data": {...}}`
   - 错误响应：`{"success": false, "error": "错误信息"}`

3. **版本控制**：
   - API路径包含版本信息，方便未来升级

4. **文档完善**：
   - 使用FastAPI自动生成API文档
   - 详细的参数说明和示例

### 前后端通信

1. **请求代理**：
   - 前端发送请求到`/api/*`路径
   - UI服务器将请求代理转发到API服务器
   - 这种方式避免了跨域问题，简化了前端开发

2. **数据流向**：
   - 前端UI → UI服务器 → API服务器 → 业务逻辑处理 → 数据库
   - 数据库 → 业务逻辑处理 → API服务器 → UI服务器 → 前端UI

3. **错误处理**：
   - API服务器提供统一的错误处理机制
   - 前端根据错误类型显示适当的用户提示

## 部署方案

### 打包策略
- **PyInstaller**：打包成单文件可执行程序
- **数据库嵌入**：SQLite文件与程序一起打包
- **配置外置**：用户配置和数据文件在用户目录

### 文件结构
```
WealthLite.exe              # 主程序
user_data/                  # 用户数据目录（自动创建）
├── wealth_lite.db         # 主数据库
├── config/                # 配置文件
└── backups/               # 自动备份
```

## 优势总结

### 架构优势
- **数据一致性**：单一数据源，避免不一致
- **可扩展性**：容易添加新的资产类型和交易类型
- **职责清晰**：每个类职责单一，易于测试和维护
- **业务逻辑清晰**：符合金融业务的自然流程

### 技术优势
- **轻量化**：保持系统简洁，适合本地安装使用
- **高性能**：SQLite提供高效的查询和事务处理
- **易维护**：清晰的层次结构，便于后续开发和维护
- **国际化**：完整的多语言支持框架

## 实施计划与当前状态

### 开发阶段进度
1. **Phase 1: 核心基础 + 现金与固定收益** - ✅ **已完成**
   - ✅ 数据模型层：Asset, Transaction, Position, Portfolio
   - ✅ 枚举定义：8个核心枚举类型完整实现
   - ✅ 数据持久化层：DatabaseManager + Repository模式 + 完整CRUD操作
   - ✅ 业务服务层：WealthService统一业务接口
   - ✅ 测试框架：22个单元测试 + 8个集成测试，完整测试覆盖
   - ✅ 数据完整性：软外键关联，事务管理，错误处理
   - ✅ 性能验证：大数据集测试通过，投资组合计算<1秒

2. **Phase 1.5: 配置管理层** - 🔄 **进行中**
   - 🔄 AppConfig (应用配置)
   - 🔄 ExchangeRateManager (汇率管理)
   - 🔄 I18nManager (国际化管理)

3. **Phase 2: 基于现金与固定收益的UI开发** - 🔄 **待实现**
   - 🔄 用户界面
   - 🔄 数据导出功能

3. **Phase 3: 权益类资产** - 🔄 **待实现**
   - 🔄 股票、基金等权益类投资
   - 🔄 专业计算层：EquityCalculator

4. **Phase 4: 不动产投资** - 🔄 **待实现**
   - 🔄 房产投资管理
   - 🔄 专业计算层：RealEstateCalculator

5. **Phase 5: 大宗商品** - 🔄 **待实现**
   - 🔄 贵金属、能源等大宗商品
   - 🔄 专业计算层：CommodityCalculator

6. **Phase 6: 高级功能与UI** - 🔄 **待实现**
   - 🔄 分析报告层：PerformanceAnalyzer, ReportGenerator
   - 🔄 用户界面重构
   - 🔄 数据导入导出功能

### 当前技术架构特点
- **交易驱动架构**：严格遵循"只有交易能产生持仓"原则
- **软外键设计**：避免数据库强约束，提供更好的灵活性
- **Repository模式**：清晰的数据访问层，支持事务管理
- **服务层封装**：WealthService提供统一的业务接口
- **多货币支持**：完整的货币体系和汇率转换机制

### 质量保证现状
- ✅ **单元测试**：22个测试用例，覆盖核心业务逻辑
- ✅ **集成测试**：8个完整集成测试，验证数据持久化流程
- ✅ **测试工厂**：完整的测试数据构建系统
- ✅ **数据一致性**：严格的数据验证和关联检查
- ✅ **性能测试**：大数据集性能验证通过
- ✅ **错误处理**：完整的异常处理和边界条件测试
- 🔄 **用户体验测试**：待实现

### 架构实现对比

**✅ 完全符合设计**：
- 资产定义层：Asset + 8个枚举类型
- 交易事件层：BaseTransaction + 4个具体交易类型  
- 持仓计算层：Position + Portfolio + PortfolioSnapshot

**✅ 超出原设计（架构增强）**：
- 数据持久化层：DatabaseManager + Repository模式
- 业务服务层：WealthService统一接口
- 测试框架：完整的单元测试和测试工厂

**🔄 待补充**：
- 配置管理层：AppConfig, I18nManager, ExchangeRateManager
- 专业计算层：各类计算器（Phase 2+实现）
- 分析报告层：PerformanceAnalyzer, ReportGenerator（Phase 5实现）

**架构符合度：85%**
- 核心业务层100%符合设计
- 基础设施层超出设计预期
- 高级功能层按计划分阶段实现

### 下一步开发重点
1. **优先级1**：补充配置管理层（AppConfig, ExchangeRateManager, I18nManager）
2. **优先级2**：Phase 2权益类资产开发准备
3. **优先级3**：基础UI界面开发（基于现金和固定收益功能）



*文档版本：v2.0*  
*创建日期：2025年6月21日*  
*最后更新：2025年6月21日 16:51:40*  
*更新说明：数据持久化层完善完成，8个集成测试全部通过* 