# 🚀 玄学预测系统 - 快速启动指南

## 📋 系统要求

- Python 3.8 或更高版本
- 现代浏览器（Chrome、Firefox、Edge等）
- 网络连接（用于前后端通信）

## 🔧 安装步骤

### 1. 安装Python依赖

打开命令行，进入项目目录，执行：

```bash
cd backend
pip install -r requirements.txt
```

如果安装速度慢，可以使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 启动后端服务

在 `backend` 目录下执行：

```bash
python main.py
```

看到以下信息表示启动成功：

```
==================================================
玄学预测系统API服务启动中...
访问地址: http://localhost:8002
API文档: http://localhost:8002/docs
==================================================
INFO:     Uvicorn running on http://0.0.0.0:8002
```

### 3. 打开前端页面

用浏览器打开：

```
http://localhost:8003/index.html
```

推荐使用仓库根目录的 `./start.sh` 一键启动前后端与知识库。

## 🎯 使用方法

1. 在前端页面输入出生信息：
   - 出生年份（1900-2100）
   - 出生月份（1-12）
   - 出生日期（1-31）
   - 出生时辰（0-23）
   - 出生分钟（0-59）
   - 性别（男/女）

2. 点击"开始排盘"按钮

3. 系统将显示：
   - 八字四柱（年月日时）
   - 五行分布
   - 十神关系
   - 大运流程
   - 命理分析和建议

## 🔍 测试API

访问 http://localhost:8002/docs 可以看到完整的API文档，可以直接在浏览器中测试API。

### 测试示例

使用curl测试八字排盘：

```bash
curl -X POST "http://localhost:8002/api/bazi" \
  -H "Content-Type: application/json" \
  -d '{
    "year": 1990,
    "month": 1,
    "day": 1,
    "hour": 12,
    "minute": 0,
    "gender": "男"
  }'
```

## ⚠️ 常见问题

### 1. 后端启动失败

**问题**：提示 `ModuleNotFoundError: No module named 'fastapi'`

**解决**：确保已安装依赖
```bash
pip install -r requirements.txt
```

### 2. 前端无法连接后端

**问题**：前端显示"计算失败：API请求失败"

**解决**：
- 确保后端服务已启动（http://localhost:8002）
- 检查浏览器控制台是否有CORS错误
- 确认防火墙没有阻止8002端口

### 3. 端口被占用

**问题**：提示 `Address already in use`

**解决**：修改 `backend/main.py` 最后一行的端口号：
```python
uvicorn.run(app, host="0.0.0.0", port=8005)  # 改为8005或其他端口
```

同时修改 `frontend/config.js` 中的API地址：
```javascript
// 现在推荐在 frontend/config.js 中统一修改
window.APP_CONFIG = { API_BASE_URL: 'http://localhost:8005' };
```

## 📚 API接口说明

### 1. 八字排盘

**接口**：`POST /api/bazi`

**请求参数**：
```json
{
  "year": 1990,
  "month": 1,
  "day": 1,
  "hour": 12,
  "minute": 0,
  "gender": "男"
}
```

**返回数据**：
- 出生信息（阳历、农历）
- 八字四柱
- 五行统计
- 十神关系
- 大运流程
- 命理分析

### 2. 阳历转农历

**接口**：`POST /api/calendar/solar-to-lunar`

**请求参数**：
```json
{
  "year": 2024,
  "month": 2,
  "day": 10
}
```

### 3. 获取年份干支

**接口**：`GET /api/ganzhi/year/{year}`

**示例**：`GET /api/ganzhi/year/2024`

## 🎨 自定义配置

### 修改前端样式

编辑 `frontend/index.html` 中的 `<style>` 部分，可以自定义：
- 颜色主题
- 布局样式
- 字体大小

### 扩展后端功能

当前后端以 `backend/main.py` 作为路由入口、`backend/core/` 存放算法模块。

扩展建议：
- 在 `backend/core/` 增加新的算法文件（如 `fengshui.py`）
- 在 `backend/main.py` 新增对应接口路由并调用算法模块

### 配置CORS来源（可选）

后端默认只允许本地前端地址（`http://localhost:8003` 和 `http://127.0.0.1:8003`）。

如需允许其他域名，可在启动前设置环境变量：

```bash
export CORS_ALLOW_ORIGINS="https://example.com,https://app.example.com"
```

## 📊 项目结构

```
xuanxue-web/
├── backend/              # Python后端
│   ├── core/            # 核心算法
│   │   ├── ganzhi.py   # 天干地支
│   │   ├── calendar.py # 万年历
│   │   └── bazi_core.py # 八字排盘
│   ├── main.py          # FastAPI主程序
│   └── requirements.txt # 依赖列表
│
├── frontend/            # 前端界面
│   └── index.html      # 单页应用
│
├── docs/               # 理论文档
└── README.md           # 项目说明
```

## 🔮 下一步开发

当前版本是MVP（最小可行产品），包含基础的八字排盘功能。

后续可以扩展：

1. **更精确的算法**
   - 真太阳时校正
   - 精确节气计算
   - 更详细的格局判断

2. **更多功能模块**
   - 紫微斗数
   - 六爻占卜
   - 风水分析
   - 面相分析
   - 择日系统

3. **用户体验优化**
   - 用户账号系统
   - 历史记录保存
   - 报告导出（PDF）
   - 数据可视化图表

4. **AI增强**
   - 使用大语言模型生成更详细的解读
   - 智能问答系统
   - 个性化建议

## 📞 技术支持

如有问题，请检查：
1. Python版本是否正确
2. 依赖是否完整安装
3. 端口是否被占用
4. 浏览器控制台的错误信息

## ⚖️ 免责声明

本系统仅供学习、研究和娱乐使用，不应作为人生重大决策的唯一依据。命运掌握在自己手中，积极努力才是改变人生的关键。
