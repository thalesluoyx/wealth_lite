# 服务器架构更新文档

## 背景

在添加AI分析功能后，项目出现了多个服务器启动脚本和API实现，导致了API调用失败和功能不一致的问题。主要表现为：

1. `main.py` 中实现了完整的API功能
2. `src/wealth_lite/ui/api_routes.py` 和 `src/wealth_lite/ui/api_server.py` 实现了部分API功能
3. 多个启动脚本：`main.py`、`run_servers.py`、`scripts/start_dev.py`、`scripts/start_prod.py`
4. 前端API调用失败，特别是在添加AI分析功能后

## 解决方案

我们采取了"统一服务器架构"的解决方案，具体包括：

1. **统一使用`main.py`作为唯一服务器入口**
   - `main.py`已经实现了所有必要的API功能
   - 所有API路由都在`main.py`中定义和实现

2. **修改启动脚本**
   - 修改`scripts/start_dev.py`，使其直接调用`main.py`中的应用
   - 删除冗余的`run_servers.py`启动脚本
   - 废弃分离的API和UI服务器架构

3. **删除不再使用的文件**
   - 删除`src/wealth_lite/ui/api_routes.py`
   - 删除`src/wealth_lite/ui/api_server.py`
   - 删除`run_servers.py`

4. **保持API路径一致性**
   - 确保所有API路径与前端期望一致
   - 统一API响应格式

## 好处

1. **简化架构**
   - 单一服务器入口，减少配置和维护复杂度
   - 消除多个服务器之间的协调问题
   - 减少冗余文件，使项目结构更清晰

2. **提高可靠性**
   - 消除API路由不一致的问题
   - 减少端口冲突的可能性

3. **便于调试**
   - 所有日志集中在一个进程中
   - 更容易追踪API调用和错误

4. **提高开发效率**
   - 减少在不同服务器之间切换的需要
   - 简化新功能的添加过程
   - 启动命令更加统一和简单

## 启动方式

现在，项目有两种主要的启动方式：

1. **开发环境**：`python scripts/start_dev.py`
   - 设置开发环境变量
   - 提供开发相关的命令行参数（如`--no-browser`）

2. **生产环境**：`python scripts/start_prod.py`
   - 设置生产环境变量
   - 可能有额外的生产环境配置

两种启动方式都最终调用`main.py`中的应用，确保了行为一致性。

## 后续建议

1. **测试覆盖**
   - 确保所有API端点都有适当的测试覆盖
   - 添加集成测试，确保前端和后端正确交互

2. **监控和日志**
   - 增强日志记录，确保能够捕获和诊断问题
   - 考虑添加API调用监控和性能指标

3. **文档更新**
   - 更新开发文档，明确推荐使用`scripts/start_dev.py`或`scripts/start_prod.py`作为启动方式
   - 添加API文档，描述可用的端点和参数 