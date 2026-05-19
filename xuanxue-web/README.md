# 玄学预测系统

> 阅读顺序建议：
>
> - 本文：项目运行与目录导航
> - [ARCHITECTURE.md](./ARCHITECTURE.md)：真实代码结构与职责边界
> - [INTEGRATION_ROADMAP.md](./INTEGRATION_ROADMAP.md)：阶段性规划
> - [INTEGRATION_IMPLEMENTATION_PLAN.md](./INTEGRATION_IMPLEMENTATION_PLAN.md)：细化实施记录
>
> 说明：
>
> - `backend/venv/` 是本机 Python 虚拟环境，不属于源码结构的一部分
> - `backend/runtime/` 是运行期 JSON / JSONL 数据目录，属于本机状态，不应视为核心代码

一个综合性的玄学预测平台，包含六大分支的完整功能。

开发者可先阅读：

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [INTEGRATION_ROADMAP.md](./INTEGRATION_ROADMAP.md)
- [INTEGRATION_IMPLEMENTATION_PLAN.md](./INTEGRATION_IMPLEMENTATION_PLAN.md)

## 项目架构

```
xuanxue-web/
├── backend/                   # Python 后端（FastAPI）
│   ├── main.py                # API 入口（创建 app / middleware / include_router）
│   ├── api/                   # 路由分层
│   │   ├── common.py          # 统一响应、异常处理、AI状态
│   │   ├── bazi.py            # 八字 / 历法 / 干支接口
│   │   ├── divination.py      # 六爻 / 梅花 / 奇门 / 择日接口
│   │   ├── ai.py              # AI增强与 AI状态接口
│   │   └── system.py          # 统一问事 / 反馈 / 日志 / 权重接口
│   ├── requirements.txt       # Python 依赖
│   └── core/                  # 核心算法模块
│       ├── bazi_core.py       # 八字核心算法
│       ├── bazi_advanced.py   # 八字高级分析
│       ├── liuyao.py          # 六爻占卜
│       ├── meihua.py          # 梅花易数
│       ├── qimen.py           # 奇门遁甲
│       ├── zeri.py            # 择日学
│       ├── calendar.py        # 阴阳历转换
│       ├── ganzhi.py          # 干支计算
│       ├── llm_helper.py      # AI增强能力封装
│       ├── consult/           # 统一问事编排
│       │   ├── models.py
│       │   ├── router.py
│       │   ├── summarizers.py
│       │   ├── trace.py
│       │   └── engine.py
│       ├── decision/          # 决策内核
│       │   ├── signal_schema.py
│       │   ├── environment_modifiers.py
│       │   ├── arbitration.py
│       │   ├── kernel.py
│       │   └── weight_tuning.py
│       └── runtime/           # 运行时 JSONL 存储助手
│           └── store.py
│
├── frontend/                  # 多页静态前端（原生 HTML/CSS/JS）
│   ├── index.html             # 统一问事中心 + 工作台总览
│   ├── liuyao.html            # 六爻占卜
│   ├── meihua.html            # 梅花易数
│   ├── qimen.html             # 奇门遁甲
│   ├── zeri.html              # 择日学
│   ├── ai-chat.html           # AI助手
│   ├── consult-panel.js       # 首页统一问事主流程
│   ├── decision-panel.js      # 决策内核面板渲染
│   ├── trace-panel.js         # Trace 图与步骤渲染
│   ├── auth-client.js         # 登录、账号中心与历史记录
│   ├── common-renderers.js    # 公共渲染函数
│   ├── common-header.css      # 公共顶部导航样式
│   └── config.js              # 前端统一配置（API_BASE_URL）
│
└── ../AI配置指南.md          # AI 配置说明
```

兼容说明：

- `backend/core/system_engine.py` 现在是统一问事的兼容导出层，真实实现位于 `core/consult/`
- `backend/core/decision_kernel.py`、`signal_schema.py`、`environment_modifiers.py`、`arbitration.py` 仍可继续导入，但真实实现已归档到 `core/decision/`
- API 分层入口可从 `backend/api/common.py`、`backend/api/bazi.py`、`backend/api/divination.py`、`backend/api/ai.py`、`backend/api/system.py` 直接定位

## 当前状态

当前仓库已经具备可运行的 Web 版本，包含：

- 统一问事中心（自动编排八字、六爻、梅花、奇门、择日）
- 八字排盘与基础/高级分析
- 六爻占卜与 AI 增强解读
- 梅花易数快速起卦与推演链展示
- 奇门遁甲排盘与 AI 增强解读
- 择日学查询、吉日检索与 AI 增强建议
- AI 对话助手与运行状态检查

推荐从仓库根目录使用：

```bash
./start.sh
```

启动脚本会自动检查端口占用、虚拟环境和依赖，并启动：

- 后端 API：`http://localhost:8002`
- 前端统一入口：`http://localhost/`

当前默认部署模式：

- `Nginx` 直接托管 `frontend/` 静态目录
- `Nginx` 反向代理 `/api/`、`/docs`、`/openapi.json` 到 `8002`
- 默认不再依赖本地 `8003` 静态服务

## 接口约定

- `POST` 接口优先使用 JSON body
- 前端统一通过 `frontend/config.js` 中的 `API_BASE_URL` 访问后端
- AI 配置说明链接也通过 `frontend/config.js` 统一配置
- AI 择日页面默认调用 `GET /api/ai/enhance-zeri/today`，以服务端日期为准

## 技术栈

### 后端
- **框架**: FastAPI (高性能、现代化)
- **语言**: Python 3.10+
- **形态**: 无状态计算型 API，当前版本未引入数据库或缓存

### 前端
- **形态**: 多页静态页面（原生 HTML/CSS/JS）
- **样式**: 页面内样式 + 公共头部样式 (`common-header.css`)
- **配置**: `config.js` 统一管理 `API_BASE_URL` 和 AI 配置指南地址

### 部署
- **本地/单机运行**: `./start.sh` 启动 FastAPI，并接入当前机器上的 Nginx 统一入口
- **Nginx 模板**: 参考 `../deploy/nginx/xuanxue.conf`
- **生产部署**: Docker / 云平台编排尚未在本仓库内提供现成配置

## 核心特性

### 1. 精准计算
- 阴阳历转换
- 天干地支推算
- 节气边界的年份差异修正
- 多模块统一返回结构
- 决策内核统一信号建模与权重仲裁

### 2. 智能分析
- 自动格局识别
- 用神喜忌判断
- 五行平衡分析
- 大运流年吉凶
- 统一问事 trace 流程可回看

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
- AI 状态感知与基础结果回退
- 首页账号中心与统一问事联动

## 当前未包含

- 用户账号系统
- 历史记录持久化
- 报告导出（PDF）
- Docker / Nginx / 数据库 / Redis 的仓库内实现

## 开发原则

1. **准确性优先**: 算法必须经过验证，确保计算准确
2. **模块化设计**: 每个功能独立，便于维护和扩展
3. **可解释性**: 所有预测都要给出依据和解释
4. **科学态度**: 提供多种解读，避免绝对化
5. **用户隐私**: 保护用户数据，不滥用个人信息

## 免责声明

本系统仅供参考和娱乐，不应作为人生重大决策的唯一依据。命运掌握在自己手中，积极努力才是改变人生的关键。
