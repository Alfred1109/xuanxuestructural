# 架构说明

> 文档状态：当前事实来源  
> 适用场景：查看当前代码组织、模块边界、兼容层策略、请求流与维护约束。  
> 相关文档：
>
> - [README.md](./README.md)：运行入口与目录导航
> - [INTEGRATION_ROADMAP.md](./INTEGRATION_ROADMAP.md)：中长期规划版图
> - [INTEGRATION_IMPLEMENTATION_PLAN.md](./INTEGRATION_IMPLEMENTATION_PLAN.md)：阶段性实施拆解与历史参考

本文面向开发者，说明当前 `xuanxue-web/` 的真实代码结构、主要数据流、兼容层策略，以及后续扩展时应遵守的边界。

## 1. 设计目标

当前架构围绕四个目标组织：

1. 保持现有 API 路径与返回结构兼容。
2. 把“统一问事”从单文件实现拆成可维护的分层结构。
3. 把“决策内核”从零散工具函数整理成独立子包。
4. 把首页 `index.html` 从大段内联脚本整理成职责清晰的前端模块。

## 2. 顶层结构

```text
xuanxue-web/
├── backend/
│   ├── main.py
│   ├── api/
│   └── core/
├── frontend/
└── ARCHITECTURE.md
```

### 后端分工

- `backend/main.py`
  只负责创建 FastAPI app、挂中间件、注册异常处理、`include_router`
- `backend/api/`
  面向 HTTP 的路由层
- `backend/core/`
  领域计算、统一问事编排、决策内核、运行时存储

### 前端分工

- `frontend/index.html`
  统一问事中心 + 工作台容器
- 其余 `*.html`
  单模块页面
- 新增 `*.js`
  首页拆分后的职责脚本

## 3. 后端架构

### 3.1 API 层

`backend/api/` 当前按业务域拆分：

- `common.py`
  统一响应外壳、异常处理、AI 运行态、CORS 配置
- `bazi.py`
  八字、历法、干支
- `divination.py`
  六爻、梅花、奇门、择日
- `ai.py`
  AI 增强接口与 AI 状态
- `system.py`
  统一问事、反馈、日志、权重

这一层的原则是：

- 只处理 HTTP 输入输出、参数校验、错误翻译
- 不承载复杂编排逻辑
- 领域逻辑尽量下沉到 `core/`

### 3.2 统一问事层

`backend/core/consult/` 是统一问事的真实实现目录：

- `models.py`
  `UnifiedConsultRequest`、`TraceStep`、`TraceGraph`
- `router.py`
  问题类型归一化、用途归一化、模块推断
- `summarizers.py`
  各术数结果摘要与八字基础分析
- `trace.py`
  trace graph 组装
- `engine.py`
  `ConsultationEngine` 主编排器

统一问事的大致流程：

1. 接收 `UnifiedConsultRequest`
2. 识别 `matter_type / purpose`
3. 推断应启用的模块集合
4. 分别调用八字 / 六爻 / 梅花 / 奇门 / 择日
5. 生成模块摘要
6. 调用决策内核生成统一世界模型和仲裁结果
7. 生成 trace
8. 写入 decision log
9. 返回统一结果

### 3.3 决策内核层

`backend/core/decision/` 是统一信号与仲裁的真实实现目录：

- `signal_schema.py`
  统一信号结构
- `environment_modifiers.py`
  环境修正项
- `arbitration.py`
  模块权重归一化、冲突处理、推荐动作生成
- `kernel.py`
  从模块摘要构建统一世界模型
- `weight_tuning.py`
  调权能力兼容入口

这一层的角色不是替代术数模块，而是把不同术数的摘要统一成可比较的信号字段，例如：

- `baseline_strength`
- `timing_window`
- `external_support`
- `risk_exposure`
- `certainty`
- `direction_score`

然后再根据 `decision_type` 做权重仲裁。

### 3.4 运行时存储层

`backend/core/runtime/store.py` 统一封装 JSONL 读写：

- 路径解析
- append
- recent read
- 空文件容错
- 损坏行容错

当前使用者：

- `core/decision_log.py`
- `core/weight_tuning.py`

原则是：

- `store.py` 只做底层持久化帮助
- 领域文件只表达业务语义，不重复实现文件读写

## 4. 兼容层策略

为了不打断旧导入，保留了几类兼容入口。

### 4.1 system_engine 兼容

`backend/core/system_engine.py` 现在是薄兼容层。

真实实现位置：

- `core/consult/models.py`
- `core/consult/engine.py`
- `core/consult/trace.py`
- `core/consult/router.py`
- `core/consult/summarizers.py`

保留它的原因：

- 老测试仍从 `core.system_engine` 导入
- 旧外部调用不需要立即重写

### 4.2 决策内核兼容

以下旧文件仍可导入，但只是转发：

- `core/decision_kernel.py`
- `core/signal_schema.py`
- `core/environment_modifiers.py`
- `core/arbitration.py`

真实实现已迁移到 `core/decision/`

兼容层原则：

- 可以读，但不建议继续向旧文件新增真实逻辑
- 新开发应优先引用新目录

## 5. 前端架构

### 5.1 首页拆分

`frontend/index.html` 不再承载大段业务脚本，首页相关逻辑拆到：

- `common-renderers.js`
  通用渲染函数
- `consult-panel.js`
  统一问事提交、fallback、总装配
- `decision-panel.js`
  决策内核卡片和指标条
- `trace-panel.js`
  Mermaid 与步骤展开区
- `auth-client.js`
  登录态、账号中心、问事历史与账号资料维护；发布登录状态变更事件
- `consult-session.js`
  账号范围的标签页草稿存储、结果 ID 和统一导航地址
- `consult-form-state.js`
  表单草稿恢复、条件编辑、清空撤销；自动恢复不能覆盖用户刚编辑的内容
- `consult-workspace.js`
  按历史 ID 读取完整结果、鉴权状态切换与本次结果追问

### 5.2 前端职责边界

推荐按下面边界继续维护：

- `index.html`
  只保留结构、样式、脚本引用、初始化入口
- `consult-panel.js`
  管理统一问事 view-model，不直接渲染决策卡片细节
- `decision-panel.js`
  只关心决策面板
- `trace-panel.js`
  只关心流程图与步骤证据展示
- `common-renderers.js`
  存放可复用的基础渲染积木

## 6. 关键请求流

### 6.1 统一问事

```text
frontend/index.html
  -> consult-panel.js
  -> POST /api/system/consult
  -> api/system.py
  -> core.system_engine / core.consult.engine
  -> core.decision.kernel
  -> decision_log + trace
  -> 返回统一结果
  -> decision-panel.js + trace-panel.js 渲染
```

### 6.2 结果恢复与持续追问

统一问事成功后，通过 `account_history.history_id` 打开 `consult-result.html?id=...`。
工作台始终从 `GET /api/auth/history/{id}` 读取归属于当前账号的完整结果，
浏览器的 latest-result 存储只帮助定位最近一份记录，不作为鉴权或结果数据来源。
新历史同时保存完整 `consultation` 和 `request_payload`；旧历史保留原结论及摘要，
不补造当时未保存的计算流程。历史列表也打开这一工作台，不维护第二套详情渲染。

`index.html?edit={id}` 读取原始请求到可编辑草稿，随后移除 edit 参数，
防止刷新时覆盖刚编辑的条件。`index.html?new=1` 开始新草稿。
草稿保存在当前标签页的 sessionStorage 中，按账号区分；访客登录时保留本页输入。
场景模板仅提供问题，不改动出生资料。实际提交时锁定表单，显示真实等待耗时，
客户端超时不表示服务端已取消计算，因此不自动重试。

`POST /api/system/consult/{id}/followups` 接收 `{question, request_id?}`；
`GET` 同一路径读取此前追问。服务端校验归属，再由 `core/consult/followups.py`
从首轮问事及此前追问构造上下文并调用 AI；AI 不可用时返回 503，保留用户输入，
不保存伪答。追问记录独立保存到 `CONSULT_FOLLOWUPS_PATH` 对应 JSONL。
首轮计算和追问 AI 调用在线程池执行，避免阻塞鉴权、历史读取等请求。

## 7. 测试策略

当前后端测试主要覆盖：

- 核心算法正确性
- API 参数校验与响应包裹
- `system_engine` 兼容导出
- runtime JSONL 容错
- 调权生效链路
- `core.decision.*` 与旧路径兼容

建议继续保持：

1. 新能力优先补后端单元测试
2. 有兼容层时必须补兼容测试
3. 改 API 包裹格式时必须跑 `test_api_validation.py`

## 8. 扩展约定

### 后端新增能力时

- 新 HTTP 接口先考虑加到 `api/` 现有域中
- 如果出现新的稳定领域，再建新子模块
- 不要把复杂编排重新塞回 `main.py`
- 不要把统一问事逻辑重新塞回 `system_engine.py`

### 统一问事新增模块时

至少需要补这些点：

1. 模块路由条件
2. 模块执行逻辑
3. 摘要函数
4. 决策信号映射
5. trace 展示
6. 兼容测试

### 前端首页新增面板时

- 优先新增独立脚本，不回到内联脚本模式
- 通用展示能力先看能否放进 `common-renderers.js`
- 不引入框架的前提下，继续保持“按职责拆文件”的组织方式

## 9. 当前已知技术债

虽然这轮已经完成主拆分，但仍有一些后续可以继续优化的点：

- 首页仍包含一块较大的内嵌八字面板逻辑，未来还能继续细拆
- 前端目前缺少自动化测试
- `weight_tuning.py` 仍保留在 `core/` 顶层，同时在 `core/decision/` 提供兼容入口
- 文档站与应用工程的开发者文档还未完全打通

## 10. 维护建议

如果你接下来要继续演进这个项目，推荐优先顺序：

1. 先看 `api/` 和 `core/consult/`
2. 再看 `core/decision/`
3. 最后看兼容层文件

判断一个文件是不是“真实实现”的快速方法：

- 文件里如果主要是 `from ... import *`
  说明它更可能是兼容入口
- 如果文件位于 `consult/` 或 `decision/`
  通常就是当前主实现

问事和追问的可选 `request_id` 由账号范围的前端会话生成，等待超时后相同条件重用。服务层在线程池中对同用户、同请求 ID 加跨进程锁，完整覆盖计算和持久化；相同内容重放原结果，内容不同返回 409。图片识别成功后在当前账号会话按图片草稿签名缓存解析结果，使重试的实际条件保持一致。
