# WealthLite UI API 文档

UI层与后端服务的接口规范。

## 📡 API 架构

### 基础配置
- **基础URL**: `http://localhost:5000/api/v1`
- **数据格式**: JSON
- **认证方式**: 暂无（本地应用）
- **错误处理**: 统一错误响应格式

### 响应格式
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2025-06-22T17:49:00Z"
}
```

## 🏠 仪表板 API

### GET /dashboard/summary
获取仪表板概览数据

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_assets": 2341270,
    "cash_assets": 1234000,
    "fixed_income": 1107270,
    "annual_return": 12.5,
    "daily_change": 8750,
    "daily_change_percent": 5.85
  }
}
```

### GET /dashboard/chart-data
获取资产趋势图表数据

**参数**:
- `range`: 时间范围 (7d, 1m, 3m, 1y)

**响应示例**:
```json
{
  "success": true,
  "data": {
    "labels": ["2025-06-15", "2025-06-16", "..."],
    "datasets": [
      {
        "label": "现金",
        "data": [1200000, 1210000, "..."]
      }
    ]
  }
}
```

## 🪙 资产管理 API

### GET /assets
获取资产列表

**参数**:
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）
- `type`: 资产类型筛选
- `currency`: 币种筛选

**响应示例**:
```json
{
  "success": true,
  "data": {
    "assets": [
      {
        "id": 1,
        "name": "现金账户",
        "symbol": "CASH",
        "type": "CASH",
        "currency": "CNY",
        "current_value": 65000,
        "return_rate": 2.1
      }
    ],
    "total": 15,
    "page": 1,
    "limit": 20
  }
}
```

### POST /assets
创建新资产

**请求体**:
```json
{
  "name": "国债2024001",
  "symbol": "GB2024001",
  "type": "FIXED_INCOME",
  "currency": "CNY",
  "face_value": 100000,
  "interest_rate": 3.8
}
```

### PUT /assets/{id}
更新资产信息

### DELETE /assets/{id}
删除资产

## 📋 交易记录 API

### GET /transactions
获取交易记录列表

**参数**:
- `page`: 页码
- `limit`: 每页数量
- `start_date`: 开始日期
- `end_date`: 结束日期
- `type`: 交易类型
- `asset_id`: 资产ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": 1,
        "date": "2025-06-21",
        "asset_id": 1,
        "asset_name": "现金账户",
        "type": "DEPOSIT",
        "quantity": 10000,
        "price": 1.0,
        "amount": 10000,
        "notes": "工资收入"
      }
    ],
    "total": 1234,
    "page": 1,
    "limit": 20
  }
}
```

### POST /transactions
创建新交易

**请求体**:
```json
{
  "asset_id": 1,
  "type": "DEPOSIT",
  "quantity": 10000,
  "price": 1.0,
  "date": "2025-06-21",
  "notes": "工资收入"
}
```

### DELETE /transactions/{id}
删除交易记录

## 📊 投资组合 API

### GET /portfolio/overview
获取投资组合概览

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_assets": 2341270,
    "total_return": 234127,
    "annual_return_rate": 12.5,
    "risk_level": "MEDIUM",
    "max_drawdown": -5.2
  }
}
```

### GET /portfolio/allocation
获取资产配置分析

**响应示例**:
```json
{
  "success": true,
  "data": {
    "by_type": [
      {"type": "CASH", "value": 1234000, "percentage": 52.7},
      {"type": "FIXED_INCOME", "value": 1107270, "percentage": 47.3}
    ],
    "by_currency": [
      {"currency": "CNY", "value": 2341270, "percentage": 100}
    ]
  }
}
```

## ⚙️ 设置 API

### GET /settings
获取用户设置

**响应示例**:
```json
{
  "success": true,
  "data": {
    "default_currency": "CNY",
    "number_format": "1,234.56",
    "auto_refresh": 30,
    "data_retention": "PERMANENT"
  }
}
```

### PUT /settings
更新用户设置

## 📤 导入导出 API

### POST /export/data
导出数据

**参数**:
- `format`: 导出格式 (json, excel, csv)
- `include`: 包含的数据类型

**响应**: 文件下载

### POST /import/data
导入数据

**请求**: 文件上传

## 🚨 错误处理

### 错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "details": {
      "field": "amount",
      "reason": "必须为正数"
    }
  },
  "timestamp": "2025-06-22T17:49:00Z"
}
```

### 常见错误码
- `VALIDATION_ERROR`: 数据验证错误
- `NOT_FOUND`: 资源不存在
- `DUPLICATE_ENTRY`: 重复数据
- `INSUFFICIENT_BALANCE`: 余额不足
- `INVALID_OPERATION`: 无效操作

## 🔄 实时数据

### WebSocket 连接
- **URL**: `ws://localhost:5000/ws`
- **用途**: 实时数据推送

### 消息格式
```json
{
  "type": "ASSET_UPDATE",
  "data": {
    "asset_id": 1,
    "new_value": 65500,
    "change": 500
  },
  "timestamp": "2025-06-22T17:49:00Z"
}
```

---

## 📝 开发说明

- 所有API都是异步的，使用Promise/async-await
- 错误处理统一通过try-catch块
- 数据缓存策略：本地存储 + 定时刷新
- 离线支持：关键数据本地缓存 