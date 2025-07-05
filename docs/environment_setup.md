# 环境设置说明

## 环境变量配置

WealthLite 使用 `WEALTH_LITE_ENV` 环境变量来区分不同的运行环境：

- `test` - 测试环境（使用内存数据库）
- `development` - 开发环境（使用开发数据库）
- `production` - 生产环境（使用生产数据库）

## 各环境设置方法

### 🧪 测试环境

**方法1：pytest 自动设置（推荐）**
```bash
# 运行测试，自动使用测试环境
python -m pytest
```

**方法2：手动设置**
```bash
export WEALTH_LITE_ENV=test
python -m pytest
```

### 🛠️ 开发环境

**方法1：使用启动脚本（推荐）**
```bash
python scripts/start_dev.py
```

**方法2：手动设置环境变量**
```bash
# Linux/Mac
export WEALTH_LITE_ENV=development
python main.py

# Windows PowerShell
$env:WEALTH_LITE_ENV="development"
python main.py

# Windows CMD
set WEALTH_LITE_ENV=development
python main.py
```

**方法3：使用 .env 文件**
```bash
# 复制环境配置文件
cp .env.development .env
python main.py
```

### 🚀 生产环境

**方法1：使用启动脚本（推荐）**
```bash
python scripts/start_prod.py
```

**方法2：系统环境变量**
```bash
# 在系统启动脚本或服务配置中设置
export WEALTH_LITE_ENV=production
python main.py
```

**方法3：Docker 环境变量**
```dockerfile
ENV WEALTH_LITE_ENV=production
```

## 数据库文件位置

不同环境使用不同的数据库文件：

- **测试环境**：`:memory:` (内存数据库，测试结束后自动清理)
- **开发环境**：`user_data/wealth_lite_dev.db`
- **生产环境**：`user_data/wealth_lite.db`

## 验证当前环境

可以通过以下代码验证当前环境配置：

```python
from wealth_lite.config.database_config import DatabaseConfig

print(f"当前环境: {DatabaseConfig.get_environment()}")
print(f"数据库路径: {DatabaseConfig.get_db_path()}")
print(f"是否内存数据库: {DatabaseConfig.is_memory_db()}")
```

## 注意事项

1. **测试环境**：数据存储在内存中，测试结束后自动清理
2. **开发环境**：数据持久化，但与生产环境隔离
3. **生产环境**：使用正式的数据库文件，请定期备份
4. **环境切换**：更改环境变量后需要重启应用