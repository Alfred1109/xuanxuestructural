# 玄学预测系统

一个综合性的玄学预测平台，包含六大分支的完整功能。

## 项目架构

```
xuanxue-web/
├── backend/                   # Python 后端（FastAPI）
│   ├── main.py                # API 入口（路由 + 服务编排）
│   ├── requirements.txt       # Python 依赖
│   └── core/                  # 核心算法模块
│       ├── bazi_core.py       # 八字核心算法
│       ├── bazi_advanced.py   # 八字高级分析
│       ├── liuyao.py          # 六爻占卜
│       ├── qimen.py           # 奇门遁甲
│       ├── zeri.py            # 择日学
│       ├── calendar.py        # 阴阳历转换
│       ├── ganzhi.py          # 干支计算
│       └── llm_helper.py      # AI增强能力封装
│
├── frontend/                  # 多页静态前端（原生 HTML/CSS/JS）
│   ├── index.html             # 八字排盘
│   ├── liuyao.html            # 六爻占卜
│   ├── qimen.html             # 奇门遁甲
│   ├── zeri.html              # 择日学
│   ├── ai-chat.html           # AI助手
│   ├── common-header.css      # 公共顶部导航样式
│   └── config.js              # 前端统一配置（API_BASE_URL）
│
└── ../docs + ../mkdocs.yml    # 知识库文档与站点配置
```

## 当前状态

当前仓库已经具备可运行的 Web 版本，包含：

- 八字排盘与基础/高级分析
- 六爻占卜与 AI 增强解读
- 奇门遁甲排盘与 AI 增强解读
- 择日学查询、吉日检索与 AI 增强建议
- AI 对话助手与运行状态检查
- MkDocs 知识库站点

推荐从仓库根目录使用：

```bash
./start.sh
```

启动脚本会自动检查端口占用、虚拟环境和依赖，并启动：

- 后端 API：`http://localhost:8002`
- 前端页面：`http://localhost:8003/index.html`
- 知识库：`http://localhost:8004`（已安装 MkDocs 时）

## 接口约定

- `POST` 接口优先使用 JSON body
- 前端统一通过 `frontend/config.js` 中的 `API_BASE_URL` 访问后端
- AI 择日页面默认调用 `GET /api/ai/enhance-zeri/today`，以服务端日期为准

## 技术栈

### 后端
- **框架**: FastAPI (高性能、现代化)
- **语言**: Python 3.10+
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis (可选)

### 前端
- **形态**: 多页静态页面（原生 HTML/CSS/JS）
- **样式**: 页面内样式 + 公共头部样式 (`common-header.css`)
- **配置**: `config.js` 统一管理 `API_BASE_URL`

### 部署
- **容器化**: Docker
- **Web服务器**: Nginx
- **云平台**: 阿里云 / 腾讯云

## 核心特性

### 1. 精准计算
- 阴阳历转换
- 天干地支推算
- 节气边界的年份差异修正
- 多模块统一返回结构

### 2. 智能分析
- 自动格局识别
- 用神喜忌判断
- 五行平衡分析
- 大运流年吉凶

### 3. 实用建议
- 职业方向建议
- 健康养生指导
- 人际关系分析
- 风水调整方案
- 择日选时建议

### 4. 用户体验
- 简洁直观的界面
- 详细的解释说明
- 可视化图表展示
- 报告导出功能

## 开发原则

1. **准确性优先**: 算法必须经过验证，确保计算准确
2. **模块化设计**: 每个功能独立，便于维护和扩展
3. **可解释性**: 所有预测都要给出依据和解释
4. **科学态度**: 提供多种解读，避免绝对化
5. **用户隐私**: 保护用户数据，不滥用个人信息

## 免责声明

本系统仅供参考和娱乐，不应作为人生重大决策的唯一依据。命运掌握在自己手中，积极努力才是改变人生的关键。
