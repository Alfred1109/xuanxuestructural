# AI增强功能配置指南

## 📖 概述

玄学预测系统支持AI增强功能，可以提供更深入、更个性化的分析和建议。AI功能基于火山引擎的豆包大模型（DeepSeek-V3）。

## 🔑 获取API密钥

### 1. 注册火山引擎账号

访问：https://console.volcengine.com/

### 2. 开通豆包大模型服务

1. 登录控制台
2. 搜索"豆包大模型"或"ARK"
3. 开通服务（可能需要实名认证）
4. 创建API密钥

### 3. 获取API Key

在豆包大模型控制台中：
1. 进入"API管理"
2. 创建新的API密钥
3. 复制保存API Key（只显示一次）

## ⚙️ 配置方法

### 方法一：环境变量（推荐）

#### 临时配置（当前终端会话有效）

```bash
export ARK_API_KEY="your_api_key_here"
```

然后启动系统：
```bash
./start.sh
```

#### 永久配置（推荐）

添加到 `~/.bashrc` 或 `~/.zshrc`：

```bash
echo 'export ARK_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

或者编辑文件：
```bash
nano ~/.bashrc
```

添加这一行：
```bash
export ARK_API_KEY="your_api_key_here"
```

保存后重新加载：
```bash
source ~/.bashrc
```

### 方法二：启动脚本中配置

编辑 `start.sh`，在启动后端之前添加：

```bash
# 在 "启动后端服务器" 之前添加
export ARK_API_KEY="your_api_key_here"
```

### 方法三：创建配置文件

创建 `.env` 文件（不推荐，因为可能泄露密钥）：

```bash
cd xuanxue-web/backend
echo 'ARK_API_KEY=your_api_key_here' > .env
```

## ✅ 验证配置

### 1. 检查环境变量

```bash
echo $ARK_API_KEY
```

应该显示你的API密钥。

### 2. 检查API状态

启动系统后，访问：
```bash
curl http://localhost:8002/api/ai/status
```

返回示例：
```json
{
  "success": true,
  "data": {
    "available": true,
    "model": "deepseek-v3-2-251201",
    "message": "AI服务正常"
  }
}
```

### 3. 测试AI对话

```bash
curl -X POST "http://localhost:8002/api/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是八字命理？"}'
```

## 🎯 AI增强功能

配置成功后，以下功能将启用AI增强：

### 1. AI增强八字分析

**接口**: `POST /api/ai/enhance-bazi`

提供更深入的性格分析、事业建议、财运预测等。

**前端使用**: 在八字排盘页面，点击"AI深度分析"按钮

### 2. AI增强六爻解读

**接口**: `POST /api/ai/enhance-liuyao`

根据卦象和问题，提供更详细的解读和建议。

**前端使用**: 在六爻占卜页面，点击"AI增强解读"按钮

### 3. AI增强奇门遁甲

**接口**: `POST /api/ai/enhance-qimen`

结合奇门遁甲盘和事项类型，提供专业的预测分析。

**前端使用**: 在奇门遁甲页面，点击"AI深度分析"按钮

### 4. AI增强择日建议

**接口**: `GET /api/ai/enhance-zeri/{year}/{month}/{day}`

根据日期和用途，提供更个性化的择日建议。

**前端使用**: 在择日页面，点击"AI增强建议"按钮

### 5. AI智能对话

**接口**: `POST /api/ai/chat`

可以询问任何玄学相关的问题，AI会给出专业解答。

**前端使用**: 在任意页面，点击"AI助手"按钮

## 💰 费用说明

- 火山引擎豆包大模型采用按量计费
- 新用户通常有免费额度
- 具体价格请查看火山引擎官网
- 建议设置费用预警

## 🔒 安全建议

1. **不要将API密钥提交到Git仓库**
   ```bash
   # 添加到 .gitignore
   echo '.env' >> .gitignore
   echo '*.key' >> .gitignore
   ```

2. **定期更换API密钥**

3. **设置API调用限制**
   - 在火山引擎控制台设置每日调用上限
   - 避免意外产生高额费用

4. **监控API使用情况**
   - 定期检查控制台的使用统计
   - 关注异常调用

## ⚠️ 常见问题

### 1. 提示"AI服务未配置"

**原因**: 未设置 `ARK_API_KEY` 环境变量

**解决**: 按照上述方法配置API密钥，然后重启服务

### 2. 提示"AI服务暂时不可用"

**可能原因**:
- API密钥错误
- 网络连接问题
- API配额用完
- 服务端问题

**解决**:
```bash
# 检查环境变量
echo $ARK_API_KEY

# 查看后端日志
tail -f /tmp/xuanxue-backend.log

# 测试API连接
curl -X POST "http://localhost:8002/api/ai/status"
```

### 3. API调用失败

**检查步骤**:
1. 确认API密钥正确
2. 检查网络连接
3. 查看后端日志中的错误信息
4. 访问火山引擎控制台检查服务状态

### 4. 响应速度慢

**原因**: AI模型推理需要时间

**优化**:
- 这是正常现象，通常需要3-10秒
- 可以在前端添加加载动画提示用户等待

## 📊 使用示例

### 示例1：AI增强八字分析

```bash
curl -X POST "http://localhost:8002/api/ai/enhance-bazi" \
  -H "Content-Type: application/json" \
  -d '{
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 14,
    "minute": 30,
    "gender": "男"
  }'
```

### 示例2：AI智能对话

```bash
curl -X POST "http://localhost:8002/api/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "我的八字是甲子年、丙寅月、戊辰日、庚申时，请分析一下我的命理特点",
    "context": ""
  }'
```

### 示例3：检查AI状态

```bash
curl http://localhost:8002/api/ai/status
```

## 🎓 模型说明

当前使用的模型：**DeepSeek-V3-2-251201**

特点：
- 强大的中文理解能力
- 专业的知识推理
- 适合玄学领域的分析

如需更换模型，编辑 `xuanxue-web/backend/core/llm_helper.py`：
```python
self.model = "deepseek-v3-2-251201"  # 改为其他模型
```

## 📞 技术支持

如有问题，请：
1. 查看后端日志：`tail -f /tmp/xuanxue-backend.log`
2. 检查API文档：http://localhost:8002/docs
3. 访问火山引擎文档：https://www.volcengine.com/docs/

## ⚖️ 免责声明

AI生成的内容仅供参考，不应作为人生重大决策的唯一依据。请理性看待AI分析结果。
