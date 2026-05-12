# 玄学系统集成实施规划

本文是在 [INTEGRATION_ROADMAP.md](./INTEGRATION_ROADMAP.md) 的基础上，进一步落成的实施规划版文档。

如果说路线图回答的是“系统未来应该长成什么样”，那么本文回答的是：

- 先做什么
- 每一期改哪些文件
- 新模块如何接入统一问事
- 新模块如何进入统一 signal 与仲裁
- 前端全景图如何扩展
- 测试如何跟进

## 1. 实施目标

实施规划的目标不是简单新增几个模块页面，而是确保每个新能力都能进入统一主链。

每个新模块接入时，应同时完成以下五件事：

1. `独立计算能力`
   模块本身可以独立输入、独立计算、独立返回结果
2. `统一问事可编排`
   模块可以被统一问事路由命中并参与自动组合
3. `统一摘要可归一`
   模块结果能被映射成稳定的摘要字段
4. `统一决策可仲裁`
   模块摘要能进入 signal 层与仲裁层
5. `统一前端可回看`
   模块能进入全景图、trace 详情、结果卡片与工作台入口

## 2. 当前代码基线

当前可作为扩展落点的核心文件如下：

### 2.1 后端主干

- `backend/core/consult/engine.py`
  统一问事编排主入口
- `backend/core/consult/router.py`
  问题归类、用途归类、模块推断
- `backend/core/consult/summarizers.py`
  模块摘要生成
- `backend/core/consult/trace.py`
  全景图、步骤链、证据展示
- `backend/core/decision/kernel.py`
  signal 映射与世界模型聚合
- `backend/core/decision/arbitration.py`
  权重仲裁与推荐动作
- `backend/api/bazi.py`
  命理类现有接口
- `backend/api/divination.py`
  占事 / 择日类现有接口
- `backend/api/system.py`
  统一问事、反馈、日志、权重

### 2.2 前端主干

- `frontend/index.html`
  工作台总容器与总览页
- `frontend/workspace-shell.js`
  侧边栏模块入口
- `frontend/consult-panel.js`
  统一问事请求、模块元信息、全景图兜底
- `frontend/trace-panel.js`
  Mermaid 与步骤展开区
- `frontend/decision-panel.js`
  决策层可视化
- `frontend/common-renderers.js`
  摘要、文本、trace 基础渲染

### 2.3 现有测试基线

- `backend/tests/test_system_engine.py`
  统一问事编排与 trace 集成测试
- `backend/tests/test_api_validation.py`
  API 参数校验测试
- `backend/tests/test_core_logic.py`
  核心逻辑测试
- `backend/tests/test_runtime_store.py`
  运行时存储测试

## 3. 新模块统一接入模板

后续无论接 `紫微`、`风水`、`六壬` 还是其他模块，建议统一按照下面模板接入。

### 3.1 后端文件层

每个模块至少需要：

- `backend/core/<module>.py`
  核心算法与结果结构
- `backend/api/<module>.py` 或并入现有业务域 API
  对外 HTTP 接口
- `backend/core/consult/summarizers.py`
  新增 `summarize_<module>_result()`
- `backend/core/consult/router.py`
  扩展 `MODULE_LABELS` 与 `infer_consult_modules()`
- `backend/core/consult/engine.py`
  在统一问事中新增模块调用分支
- `backend/core/consult/trace.py`
  增加模块节点链路与全景图节点
- `backend/core/decision/kernel.py`
  新增 `signal_from_<module>()`
- `backend/core/decision/arbitration.py`
  补默认权重与决策类型权重映射

### 3.2 前端文件层

每个模块至少需要：

- `frontend/<module>.html`
  独立模块页面
- `frontend/workspace-shell.js`
  加入侧边栏入口
- `frontend/consult-panel.js`
  加入模块中文名、全景图 lane、摘要展示
- `frontend/trace-panel.js`
  无需大改，依赖统一 trace 结构即可
- `frontend/index.html`
  如果需要首页卡片，可增加入口卡片

### 3.3 测试层

每个模块接入时至少补三类测试：

1. 模块核心算法测试
2. 独立 API 参数与响应测试
3. 统一问事自动编排命中测试

## 4. 统一 signal 扩展规则

所有新模块在进入仲裁前，必须先统一映射为 signal，而不是直接拼接自然语言。

建议保留并扩展以下 signal 域：

- `baseline_strength`
- `timing_window`
- `external_support`
- `internal_resistance`
- `risk_exposure`
- `certainty`
- `actionability`
- `direction_score`

如需进一步增强，可增补：

- `space_support`
- `counterparty_pressure`
- `layout_stability`
- `trend_duration`
- `opportunity_density`

模块映射建议：

- `八字 / 紫微`
  重点贡献 `baseline_strength`
- `六爻 / 梅花 / 六壬`
  重点贡献 `event`, `certainty`, `counterparty_pressure`
- `奇门 / 择日 / 流时增强`
  重点贡献 `timing_window`, `direction_score`
- `风水 / 方位`
  重点贡献 `space_support`, `layout_stability`, `external_support`

## 5. 分期实施规划

## 5.1 Phase 1：紫微斗数接入

### 目标

- 把系统从“八字单核命理”升级为“八字 + 紫微双核命理”
- 让统一问事具备第二套命理底盘视角

### 后端实施项

- [x] 新增 `backend/core/ziwei.py`
  - 已切换为基于正式紫微斗数排盘库的核心逻辑
  - 命宫、身宫、主星、四化、宫位结果结构
- [x] 新增 `backend/api/ziwei.py`
  - `POST /api/ziwei`
  - 输入建议复用出生时间结构，并支持性别
- [x] 更新 `backend/main.py`
  - 注册 `ziwei` router
- [x] 更新 `backend/core/consult/router.py`
  - 扩展 `MODULE_LABELS["ziwei"] = "紫微"`
  - 在有完整出生信息时支持命中 `ziwei`
- [x] 更新 `backend/core/consult/engine.py`
  - 新增 `ziwei` 调用分支
  - 写入 `module_results["ziwei"]`
  - 写入 `module_summaries["ziwei"]`
- [x] 更新 `backend/core/consult/summarizers.py`
  - 新增 `summarize_ziwei_result()`
  - 已补充命宫主轴、四化摘要、当前大限、事业/关系/财务/健康向量
- [x] 更新 `backend/core/consult/trace.py`
  - 新增 `ziwei` 节点链
  - 推荐节点：
    - `ziwei_mingpan`
    - `ziwei_minggong`
    - `ziwei_sihua`
    - `ziwei_judge`
- [x] 更新 `backend/core/decision/kernel.py`
  - 新增 `signal_from_ziwei()`
- [x] 更新权重预设
  - 已在 `backend/core/weight_tuning.py` 中为 `strategic / tactical / temporal / balanced` 场景加入 `ziwei` 权重
- [ ] 更新 `backend/core/decision/arbitration.py`
  - 如后续需要更细粒度的紫微仲裁策略，再补充模块特化逻辑

### 前端实施项

- [x] 新增 `frontend/ziwei.html`
- [x] 更新 `frontend/workspace-shell.js`
  - 增加“紫微斗数”入口
- [x] 更新 `frontend/consult-panel.js`
  - 增加 `ziwei` 的中文名、摘要、全景图 lane
- [x] 更新 `frontend/index.html`
  - 已增加侧边栏与首页入口卡片

### 摘要字段建议

- `summary`
- `minggong`
- `shengong`
- `major_stars`
- `career_vector`
- `relationship_vector`
- `health_vector`
- `fortune_cycle`

### signal 映射建议

- `baseline_strength`
  命盘整体稳定度
- `external_support`
  贵人、资源、顺势程度
- `certainty`
  宫位与主星判断稳定度
- `direction_score`
  对当前问题的偏正向或偏保守建议

### 测试项

- [x] 新增 `backend/tests/test_ziwei_core.py`
- [x] 新增 `backend/tests/test_ziwei_api.py`
- [x] 更新 `backend/tests/test_system_engine.py`
  - 验证有出生信息时是否能命中 `ziwei`
  - 验证 trace 是否包含紫微节点

## 5.2 Phase 2：风水 / 空间层接入

### 目标

- 建立正式的“论地层”
- 让地点、朝向、布局、办公环境进入统一决策

### 后端实施项

- [x] 新增 `backend/core/fengshui.py`
  - 阳宅 / 方位 / 布局计算逻辑
- [x] 新增 `backend/api/fengshui.py`
  - `POST /api/fengshui`
  - 输入支持：
    - 地点
    - 朝向
    - 场景类型
    - 房间或工位描述
- [x] 更新 `backend/main.py`
  - 注册 `fengshui` router
- [ ] 更新 `backend/core/consult/models.py`
  - 当前先复用 `location` 完成统一问事轻量接入，后续再扩更细空间字段
- [x] 更新 `backend/core/consult/router.py`
  - 识别“搬家、住宅、办公室、工位、朝向、布局、选址”等问题
- [x] 更新 `backend/core/consult/engine.py`
  - 新增 `fengshui` 调用分支
- [x] 更新 `backend/core/consult/summarizers.py`
  - 新增 `summarize_fengshui_result()`
- [x] 更新 `backend/core/consult/trace.py`
  - 新增风水节点链
  - 推荐节点：
    - `fengshui_orientation`
    - `fengshui_layout`
    - `fengshui_judge`
- [x] 更新 `backend/core/decision/kernel.py`
  - 新增 `signal_from_fengshui()`
- [ ] 更新 `backend/core/decision/environment_modifiers.py`
  - 当前先保留原环境修正层，后续再与正式风水层进一步解耦

### 前端实施项

- [x] 新增 `frontend/fengshui.html`
- [x] 更新 `frontend/workspace-shell.js`
  - 增加“风水 / 阳宅”入口
- [x] 更新 `frontend/consult-panel.js`
  - 加入 `fengshui` 模块 lane
- [x] 更新 `frontend/index.html`
  - 已增加空间类入口卡片与工作台入口

### 摘要字段建议

- `summary`
- `orientation_fit`
- `layout_risk`
- `space_support`
- `recommended_direction`
- `avoid_direction`
- `adjustment_advice`

### signal 映射建议

- `external_support`
  环境与空间支持度
- `risk_exposure`
  空间隐患程度
- `direction_score`
  朝向与动作方向建议
- `space_support`
  作为新增辅助字段写入 raw / aggregate 扩展

### 测试项

- [x] 新增 `backend/tests/test_fengshui_core.py`
- [x] 新增 `backend/tests/test_fengshui_api.py`
- [x] 更新 `backend/tests/test_system_engine.py`
  - 验证空间类问题是否能命中风水模块

## 5.3 Phase 3：六壬神课接入

### 目标

- 增强复杂事件、博弈局势、对手意图与动态变化判断

### 后端实施项

- 新增 `backend/core/liuren.py`
- 新增 `backend/api/liuren.py`
  - `POST /api/divination/liuren` 或 `POST /api/liuren`
- 更新 `backend/main.py`
  - 注册 router
- 更新 `backend/core/consult/router.py`
  - 识别谈判、竞争、诉讼、对手、合作破裂、隐情类问题
- 更新 `backend/core/consult/engine.py`
  - 新增 `liuren` 调用分支
- 更新 `backend/core/consult/summarizers.py`
  - 新增 `summarize_liuren_result()`
- 更新 `backend/core/consult/trace.py`
  - 新增六壬节点链
  - 推荐节点：
    - `liuren_ke`
    - `liuren_sanchuan`
    - `liuren_judge`
- 更新 `backend/core/decision/kernel.py`
  - 新增 `signal_from_liuren()`
- 更新 `backend/core/decision/arbitration.py`
  - 在 `tactical` 场景增强 `liuren` 权重

### 前端实施项

- 新增 `frontend/liuren.html`
- 更新 `frontend/workspace-shell.js`
  - 增加“六壬神课”入口
- 更新 `frontend/consult-panel.js`
  - 加入 `liuren` lane 与摘要

### 摘要字段建议

- `summary`
- `sanchuan`
- `sike`
- `counterparty_intent`
- `hidden_obstacle`
- `timing_trigger`
- `advice`

### signal 映射建议

- `certainty`
  复杂事件判断稳定度
- `risk_exposure`
  暗阻与隐患
- `internal_resistance`
  事件推进难度
- `direction_score`
  当前策略倾向

### 测试项

- 新增 `backend/tests/test_liuren_core.py`
- 新增 `backend/tests/test_liuren_api.py`
- 更新 `backend/tests/test_system_engine.py`
  - 验证竞争、诉讼、谈判类问题的自动命中

## 5.4 Phase 4：统一时间增强层

### 目标

- 把时间能力从“单独择日页”升级为跨模块增强能力

### 后端实施项

- 新增 `backend/core/time_enhancer.py`
  - 流年 / 流月 / 流日 / 流时统一增强逻辑
- 更新 `backend/core/consult/engine.py`
  - 在命理或事件模块完成后，按需要附加时间增强结果
- 更新 `backend/core/consult/summarizers.py`
  - 为各主模块增加时间增强摘要拼接
- 更新 `backend/core/consult/trace.py`
  - 新增时间增强节点
  - 推荐节点：
    - `time_year_cycle`
    - `time_month_window`
    - `time_day_window`
    - `time_hour_window`
- 更新 `backend/core/decision/kernel.py`
  - 强化 `timing_window` 来源
- 更新 `backend/core/decision/arbitration.py`
  - 在 `temporal` 类型下强化时间增强权重

### 前端实施项

- 不建议先做独立页面
- 优先在统一问事 trace 与结果说明中体现
- 后续如有需要，可增加“时间增强视图”

### 摘要字段建议

- `year_cycle`
- `month_window`
- `day_window`
- `hour_window`
- `best_time_slot`
- `avoid_time_slot`

### signal 映射建议

- `timing_window`
  主字段
- `certainty`
  时间判断稳定度
- `actionability`
  当前时点是否适合动作

### 测试项

- 新增 `backend/tests/test_time_enhancer.py`
- 更新 `backend/tests/test_system_engine.py`
  - 验证时间类问题时 `timing_window` 有增强

## 5.5 Phase 5：高阶补充层

### 目标

- 丰富解释维度
- 提升高阶用户使用深度

### 建议模块

- `太乙神数`
- `神煞 / 纳音 / 十二长生 / 空亡`
- `相学`
- `姓名学`

### 实施策略

- 神煞、纳音、空亡建议先做“特征增强层”，不急着做独立页面
- 太乙可作为高阶独立模块
- 相学涉及图像输入，建议单列产品课题，不与前三期混做

## 6. API 规划建议

为了避免后续接口散乱，建议逐步把 API 规划为四域：

- `api/bazi.py`
  八字、紫微等命理域
- `api/divination.py`
  六爻、梅花、奇门、六壬、太乙等占事域
- `api/fengshui.py`
  风水 / 阳宅 / 空间域
- `api/system.py`
  统一问事 / 日志 / 权重 / 反馈

如继续拆分，也建议遵守一条原则：

> 接口如何拆分可以灵活，但统一问事入口必须始终只有一个。

## 7. 前端全景图扩展规划

当前全景图已具备：

- 总控层
- 术数模块层
- 集成决策层
- 灰态全景 + 激活节点

后续扩展建议如下。

### Phase 1 后

新增：

- 紫微命理线

### Phase 2 后

新增：

- 风水空间线
- 空间输入区块

### Phase 3 后

新增：

- 六壬事件线

### Phase 4 后

新增：

- 统一时间增强线

### 展示原则

- 全部能力灰态常驻
- 本次命中模块高亮
- 本次真实路径高亮
- trace 步骤区按模块分组展开

## 8. 数据与日志规划

每接入一个新模块，建议同时保证以下日志可回看：

- 原始输入
- 模块摘要
- 统一 signal
- 仲裁权重
- 最终建议
- 用户反馈

建议新增或保留以下数据断点：

- `module_summaries["<module>"]`
- `decision_kernel["world_model"]["signals"]`
- `decision_kernel["arbitration"]["weights"]`
- `trace["steps"]`

这样后续才能做：

- 模块效果复盘
- 调权分析
- AI 综合质量评估
- 用户采纳结果回溯

## 9. 测试与验收标准

每一期建议按以下标准验收。

### 9.1 算法层验收

- 能独立计算
- 返回结构稳定
- 关键字段不缺失

### 9.2 API 层验收

- 参数校验完整
- 错误提示清晰
- 成功返回结构兼容统一格式

### 9.3 编排层验收

- 能被统一问事自动命中
- 能生成摘要
- 能进入 world model
- 能进入 arbitration
- 能进入 trace

### 9.4 前端层验收

- 有独立入口
- 有全景图节点
- 有结果展示
- 有 trace 详情

### 9.5 回归层验收

- 现有模块不回退
- 旧 API 不破坏
- `test_system_engine.py` 持续通过
- `test_api_validation.py` 持续通过

## 10. 推荐实施顺序总结

从投入产出比、系统完整度和集成收益来看，推荐顺序如下：

1. `紫微斗数`
2. `风水 / 阳宅 / 方位`
3. `六壬神课`
4. `统一时间增强层`
5. `太乙 / 神煞增强 / 相学等高阶能力`

推荐原因：

- `紫微` 解决命理单核问题
- `风水` 补齐空间层
- `六壬` 强化复杂事件预测
- `时间增强层` 让全系统时机判断联动
- `高阶补充层` 最后做，不抢主干

## 11. 一句话执行原则

后续每增加一个模块，都不要只做“独立页面 + 独立接口”，而要按以下链路一次性接通：

`核心算法 -> API -> 统一问事路由 -> 摘要 -> signal -> 仲裁 -> trace -> 前端全景图 -> 测试`

只有这样，系统才会持续朝“综合玄学决策平台”进化，而不是重新退回成“模块拼盘”。
