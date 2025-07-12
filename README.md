# WealthLite 启动脚本说明

WealthLite项目提供了多种启动脚本，用于不同的开发和部署场景。以下是对各个启动脚本的说明和使用方法。

## 启动脚本对比

| 脚本 | 位置 | 用途 | 环境 | 实现方式 |
|------|------|------|------|----------|
| `run_servers.py` | 根目录 | 快速启动测试环境 | 开发测试 | 子进程方式启动模拟API和UI服务器 |
| `scripts/start_dev.py` | scripts目录 | 启动完整开发环境 | 开发 | 线程方式启动真实API和UI服务器 |
| `scripts/start_prod.py` | scripts目录 | 启动生产环境 | 生产 | 直接导入main模块启动集成应用 |

## 启动脚本功能对比

### 1. `run_servers.py`

快速测试脚本，使用模拟数据，适合前端开发和UI测试。

**特点：**
- 使用子进程方式启动两个独立服务器
- 启动`test_api_server.py`提供模拟API数据
- 启动`src/wealth_lite/ui/serve.py`提供UI服务
- 提供进程监控、日志合并显示和错误处理功能

**使用方法：**
```bash
python run_servers.py [--no-browser]
```

**参数：**
- `--no-browser`: 禁止自动打开浏览器

### 2. `scripts/start_dev.py`

正式的开发环境启动脚本，使用真实API但是开发模式配置。

**特点：**
- 使用线程方式启动服务器
- 直接导入并调用模块中的`main`函数
- 使用真实的API服务器(`src/wealth_lite/ui/api_server.py`)
- 支持只启动UI或API服务器

**使用方法：**
```bash
python scripts/start_dev.py [--ui-only] [--api-only] [--no-browser]
```

**参数：**
- `--ui-only`: 只启动UI服务器
- `--api-only`: 只启动API服务器
- `--no-browser`: 禁止自动打开浏览器

### 3. `scripts/start_prod.py`

生产环境启动脚本，使用生产配置和优化。

**特点：**
- 设置`WEALTH_LITE_ENV=production`环境变量
- 不分离UI和API服务器，作为一个整体应用启动
- 直接导入主模块的`main`函数

**使用方法：**
```bash
python scripts/start_prod.py
```

## 推荐使用场景

1. **前端开发和UI测试**：使用`run_servers.py`
   - 快速启动，使用模拟数据，无需数据库
   - 适合UI开发和基本功能测试

2. **完整开发环境**：使用`scripts/start_dev.py`
   - 提供完整的开发环境和真实API
   - 适合后端开发和集成测试

3. **生产部署**：使用`scripts/start_prod.py`
   - 生产环境配置和优化
   - 适合实际部署和运行

## 服务器端口

- UI服务器：`http://localhost:8000`
- API服务器：`http://localhost:8081`
- API文档：`http://localhost:8081/docs` 