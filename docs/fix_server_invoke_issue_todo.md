I'll analyze the files and explain the relationships between them to help understand the server startup issues.

## 问题分析

### 1) API调用失败的原因

查看代码后，我发现存在几个关键问题：

1. **服务器架构冲突**：
   - `main.py` 中有一个完整的FastAPI应用，包含了所有API路由
   - 新增的 `api_server.py` 创建了另一个FastAPI应用，使用了 `api_routes.py` 中定义的路由
   - 两个服务器定义了相同的API路径但实现不同，导致冲突

2. **实例化问题**：
   - `api_routes.py` 中重新实例化了服务类（`wealth_service`、`ai_config_service`等）
   - `main.py` 中也实例化了这些服务类
   - 两套实例使用不同的数据库连接，导致数据不一致

3. **端口冲突**：
   - `main.py` 默认使用8080端口
   - `api_server.py` 默认也使用8080端口
   - `serve.py` 使用8000端口，并将API请求代理到8081端口

### 2) API接口废弃的原因

新的架构设计中，想要将API服务器和UI服务器分离：
- `api_server.py` 负责提供API服务
- `serve.py` 负责提供静态文件服务并代理API请求

但是实现上存在问题：
- `api_routes.py` 中定义的路由与 `main.py` 中的路由不一致
- 许多在 `main.py` 中实现的API（如`get_snapshot_detail`）在 `api_routes.py` 中没有对应实现
- 开发了新架构但没有完全迁移旧API，导致功能缺失

### 3) 日志问题

日志为空的可能原因：
- 日志配置问题：新的服务器可能没有正确配置日志
- 服务器启动失败：如果服务器启动失败，可能没有生成日志
- 权限问题：可能无法写入日志文件

### 4) 测试用例与实际运行的差异

测试用例通过但实际运行有问题的原因：
- 测试环境与运行环境不同：测试可能使用了隔离的环境
- 测试范围有限：测试可能只验证了单个组件的功能，而非整个系统的集成
- 服务器配置问题：测试可能没有验证服务器启动和API路由的正确性

## 架构设计评估

`api_routes.py` 和 `api_server.py` 的设计存在以下问题：

1. **重复定义**：与 `main.py` 中的API重复
2. **不完整实现**：没有实现所有必要的API
3. **资源冲突**：创建了重复的服务实例和数据库连接
4. **架构混乱**：没有明确的职责分离，导致混乱

## 解决方案

### 步骤1：确定架构方向

我们需要决定使用哪种架构模式：
1. 单一服务器模式：只使用 `main.py` 中的FastAPI应用
2. 分离模式：使用 `api_server.py` 提供API，`serve.py` 提供UI

**建议**：使用单一服务器模式，因为它更简单，已经实现了所有必要的API。
Search files...
Read file: test_api_server.py
### 步骤2：检查服务器启动流程

通过分析代码，我发现项目有多个服务器启动脚本：

1. `main.py` - 主应用入口，包含完整的FastAPI应用
2. `run_servers.py` - 同时启动API服务器和UI服务器的脚本
3. `scripts/start_dev.py` - 开发环境启动脚本
4. `src/wealth_lite/ui/serve.py` - UI开发服务器
5. `src/wealth_lite/ui/api_server.py` - API服务器
6. `test_api_server.py` - 测试用API服务器

这些脚本之间存在冲突，特别是端口使用和API路由定义上。
Read file: src/wealth_lite/config/env_loader.py
Read file: .env.development


## 解决方案（Step by Step）

### 步骤1：确定服务器启动方式

明确采用单一服务器模式：只使用 `main.py` 中的FastAPI应用，删除不需要的启动脚本。

根据分析，我们有以下几种启动方式：
1. `python main.py` - 启动单一服务器（包含API和UI）
2. `python run_servers.py` - 启动分离的API和UI服务器
3. `python scripts/start_dev.py` - 开发环境启动脚本

**建议**：
- 使用`python main.py` 作为主要启动方式，因为它已经实现了所有API功能。
- 使用`python scripts/start_dev.py` 作为开发环境启动脚本。
- 使用`python scripts/start_prod.py` 作为生产环境启动脚本。


**验证方法**：
```
python main.py
python scripts/start_dev.py
python scripts/start_prod.py
```

确认服务器能否正常启动，并在浏览器中访问 `http://localhost:8080/static/index.html`。


### 步骤2：修复前端API调用

前端API调用失败可能是因为路径或格式不匹配。

**解决方案**：
1. 检查前端API调用路径
2. 确保API响应格式一致

修改 `main.py` 中的API路由，确保返回格式与前端期望一致：

```python
# 在main.py中添加一个中间件，确保API响应格式一致
@app.middleware("http")
async def add_response_format(request, call_next):
    response = await call_next(request)
    
    # 只处理API请求
    if request.url.path.startswith("/api/"):
        # 尝试读取响应内容
        body = await response.body()
        
        try:
            # 解析JSON
            data = json.loads(body)
            
            # 如果没有success字段，添加一个
            if isinstance(data, dict) and "success" not in data:
                data = {"success": True, "data": data}
                
            # 创建新的响应
            return JSONResponse(
                content=data,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except:
            # 如果不是JSON或解析失败，返回原始响应
            pass
    
    return response
```

**验证方法**：
重启应用，使用浏览器开发者工具检查API响应格式。

## 总结与经验教训

### 问题总结

1. **架构混乱**：多个服务器实现和启动脚本导致冲突
2. **API实现不一致**：新旧API实现不同步，导致功能缺失
3. **日志配置问题**：日志未正确配置，导致无法追踪错误
4. **测试与生产环境差异**：测试环境与实际运行环境不同

### 经验教训

1. **统一架构设计**：
   - 在引入新功能前，明确架构设计
   - 避免重复实现相同功能
   - 确保新旧代码的兼容性

2. **API设计规范**：
   - 定义清晰的API响应格式
   - 确保所有API遵循相同的格式约定
   - 使用API版本控制管理变更

3. **日志与调试**：
   - 配置全面的日志记录
   - 在关键位置添加调试日志
   - 定期检查日志文件

4. **测试策略改进**：
   - 增加集成测试和端到端测试
   - 模拟真实环境进行测试
   - 测试API响应格式和前端兼容性

5. **代码重构最佳实践**：
   - 渐进式重构，避免大规模修改
   - 保持向后兼容性
   - 在重构前编写测试用例

### 后续改进建议

1. **统一API实现**：合并 `api_routes.py` 和 `main.py` 中的API实现
2. **简化服务器架构**：决定使用单一服务器还是分离服务器，并统一实现
3. **增强日志系统**：添加结构化日志和日志分析工具
4. **改进测试覆盖率**：添加更多集成测试和端到端测试
5. **文档更新**：更新架构文档，明确服务器启动流程和API规范

通过这些改进，可以避免类似问题再次发生，并提高代码的可维护性和稳定性。