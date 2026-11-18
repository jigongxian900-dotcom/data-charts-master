# 图形与动效图谱

[打开原创图谱](../examples/diagram-atlas/index.html)。图谱覆盖路径与责任、组织与系统、时间与阶段、判断与关系、解释与变形、数据与数量六类阅读任务。搜索图名或业务问题，可看到选图条件、原始合成数据和浏览器动效。

## 选图规则

| 问题 | 画法 | 动效与失效条件 |
|---|---|---|
| 条件如何决定下一步，责任如何交接 | 决策流程、泳道、消息时序、服务蓝图 | 按已知方向表现交接。规则与实绩分开，缺路径 ID 时用阶段量或真实单段 |
| 系统由什么组成，改了哪些连接 | 架构、部署、数据流、架构变更、领域模型 | 先显边界后连边。稳定 ID 保留前后位置，新增、移除及重接明示 |
| 什么时候发生，先后与用时分别是什么 | 时间线、折叠时间线、甘特、路径旁注、步骤 | 日期与时长按真实尺度。定性间距声明为示意，跳过时间或缺报不得画成持续过程 |
| 关系、重叠或假设如何检查 | 维恩、因果回路、逻辑故障树、权限矩阵、追踪矩阵 | 交集用精确成员，空间面积可无量纲。回路保留边符号与证据状态，门类型由逻辑决定 |
| 是否适合用定性变形辅助讲解 | 开放螺旋、同源弧线、中心轨道、轴测、波形旁注 | 让形态服务含义。螺旋只在迭代扩大时使用，波峰需要有出处或定性说明 |
| 实测数据怎样变，多少量真的流到下游 | 条图、趋势、分布、面积树图、桑基和变体 | 固定尺度和单位。可用遮罩揭示原始几何，厚度由数量决定。缺报保留空位 |

从能回答问题的最小结构出发。示例合适时复用其布局和动效，输入不同则重新映射。只需路线追踪时可以显现一条真实边。只有能回答新的问题时，才增加筛选、聚焦和状态切换。

## 制作入口

- 阶段、岗位、条件和带稳定 ID 实绩的可复用生产入口是 [流程图制作](workflow-diagrams.md)。
- 原始数量图优先按 [图表合同](html-delivery.md) 实现，其他布局从 [自定义渲染入口](custom-renderers.md) 开始。
- 图谱每张图是经过编排的示例。可更换示例数据并继续完善布局。流程、完整树、架构和类型示例的任意 JSON 自动排版需按场景编写。
- 需要重新生成图谱时运行 `python scripts/build_diagram_atlas.py`，输出为包含代码和案例数据的离线 HTML。

## 来源对应

按原目录核对 [Lieflat Diagrams](https://github.com/larashero3-dotcom/lieflat-diagrams/blob/main/skill/catalog.md) 的 35 项和 [Diagram Design](https://github.com/cathrynlavery/diagram-design#what-it-makes) 的 50 项，以及后者单列的 9 个变体。同义条目复用一个原创实例。保留定性与定量、定性重叠与精确集合、层级金字塔与同批次漏斗的不同入口。下表列出每项对应的图形和样例链接。

| 目录 | 上游标识 | Jee Charts Master |
|---|---|---|
| Lieflat 主类 | `decision` | [决策流程](../examples/diagram-atlas/index.html#decision) |
| Lieflat 主类 | `mind-map` | [思维导图](../examples/diagram-atlas/index.html#mind-map) |
| Lieflat 主类 | `folded-timeline` | [折叠时间线](../examples/diagram-atlas/index.html#folded-timeline) |
| Lieflat 主类 | `venn-sets` | [集合维恩图](../examples/diagram-atlas/index.html#venn-sets) |
| Lieflat 主类 | `journey` | [用户旅程](../examples/diagram-atlas/index.html#journey) |
| Lieflat 主类 | `gantt` | [甘特图](../examples/diagram-atlas/index.html#gantt) |
| Lieflat 主类 | `qualitative-quadrant` | [定性四象限](../examples/diagram-atlas/index.html#qualitative-quadrant) |
| Lieflat 主类 | `decision-matrix` | [决策矩阵](../examples/diagram-atlas/index.html#decision-matrix) |
| Lieflat 主类 | `organization` | [组织图](../examples/diagram-atlas/index.html#organization) |
| Lieflat 主类 | `swimlane` | [跨职能泳道](../examples/diagram-atlas/index.html#swimlane) |
| Lieflat 主类 | `blueprint` | [服务蓝图](../examples/diagram-atlas/index.html#blueprint) |
| Lieflat 主类 | `feedback` | [反馈周期](../examples/diagram-atlas/index.html#feedback) |
| Lieflat 主类 | `annotated-cycle` | [注释周期](../examples/diagram-atlas/index.html#annotated-cycle) |
| Lieflat 主类 | `dependencies` | [依赖图](../examples/diagram-atlas/index.html#dependencies) |
| Lieflat 主类 | `causal-loop` | [因果回路](../examples/diagram-atlas/index.html#causal-loop) |
| Lieflat 主类 | `concept-map` | [概念图](../examples/diagram-atlas/index.html#concept-map) |
| Lieflat 主类 | `fishbone` | [鱼骨图](../examples/diagram-atlas/index.html#fishbone) |
| Lieflat 主类 | `architecture` | [系统架构](../examples/diagram-atlas/index.html#architecture) |
| Lieflat 主类 | `sequence` | [消息时序](../examples/diagram-atlas/index.html#sequence) |
| Lieflat 主类 | `state-machine` | [状态机](../examples/diagram-atlas/index.html#state-machine) |
| Lieflat 主类 | `entity-relations` | [实体关系图](../examples/diagram-atlas/index.html#entity-relations) |
| Lieflat 主类 | `use-cases` | [用例图](../examples/diagram-atlas/index.html#use-cases) |
| Lieflat 主类 | `class-diagram` | [UML 类图](../examples/diagram-atlas/index.html#class-diagram) |
| Lieflat 主类 | `deployment-diagram` | [部署图](../examples/diagram-atlas/index.html#deployment) |
| Lieflat 主类 | `fault-tree` | [故障树](../examples/diagram-atlas/index.html#fault-tree) |
| Lieflat 主类 | `curved-classification` | [曲线分类](../examples/diagram-atlas/index.html#curved-classification) |
| Lieflat 主类 | `overlapping-circles` | [定性主题重叠](../examples/diagram-atlas/index.html#overlapping-circles) |
| Lieflat 主类 | `central-orbit` | [中心轨道](../examples/diagram-atlas/index.html#central-orbit) |
| Lieflat 主类 | `common-origin-arcs` | [同源弧线](../examples/diagram-atlas/index.html#common-origin-arcs) |
| Lieflat 主类 | `tangent-circles` | [相切嵌套圆](../examples/diagram-atlas/index.html#tangent-circles) |
| Lieflat 主类 | `segmented-day` | [分段日程](../examples/diagram-atlas/index.html#segmented-day) |
| Lieflat 主类 | `open-spiral` | [开放螺旋](../examples/diagram-atlas/index.html#open-spiral) |
| Lieflat 主类 | `wave-annotations` | [波形旁注](../examples/diagram-atlas/index.html#wave-annotations) |
| Lieflat 主类 | `wave-checkpoints` | [波形检查点](../examples/diagram-atlas/index.html#wave-checkpoints) |
| Lieflat 主类 | `free-meander` | [折返阅读路径](../examples/diagram-atlas/index.html#free-meander) |
| Diagram Design 主类 | `architecture` | [系统架构](../examples/diagram-atlas/index.html#architecture) |
| Diagram Design 主类 | `it-state` | [IT 现状图](../examples/diagram-atlas/index.html#it-state) |
| Diagram Design 主类 | `flowchart` | [决策流程](../examples/diagram-atlas/index.html#decision) |
| Diagram Design 主类 | `sequence` | [消息时序](../examples/diagram-atlas/index.html#sequence) |
| Diagram Design 主类 | `state` | [状态机](../examples/diagram-atlas/index.html#state-machine) |
| Diagram Design 主类 | `er` | [实体关系图](../examples/diagram-atlas/index.html#entity-relations) |
| Diagram Design 主类 | `timeline` | [时间线](../examples/diagram-atlas/index.html#timeline) |
| Diagram Design 主类 | `swimlane` | [跨职能泳道](../examples/diagram-atlas/index.html#swimlane) |
| Diagram Design 主类 | `quadrant` | [定量四象限](../examples/diagram-atlas/index.html#quadrant) |
| Diagram Design 主类 | `radar` | [雷达图](../examples/diagram-atlas/index.html#radar) |
| Diagram Design 主类 | `loop` | [飞轮](../examples/diagram-atlas/index.html#flywheel) |
| Diagram Design 主类 | `nested` | [嵌套边界](../examples/diagram-atlas/index.html#nested) |
| Diagram Design 主类 | `tree` | [层级树](../examples/diagram-atlas/index.html#tree) |
| Diagram Design 主类 | `org-chart` | [组织图](../examples/diagram-atlas/index.html#organization) |
| Diagram Design 主类 | `layers` | [层叠架构](../examples/diagram-atlas/index.html#layers) |
| Diagram Design 主类 | `venn` | [集合维恩图](../examples/diagram-atlas/index.html#venn-sets) |
| Diagram Design 主类 | `pyramid` | [层级金字塔](../examples/diagram-atlas/index.html#pyramid) |
| Diagram Design 主类 | `bar` | [条形比较](../examples/diagram-atlas/index.html#bar) |
| Diagram Design 主类 | `treemap` | [比例矩形树图](../examples/diagram-atlas/index.html#treemap) |
| Diagram Design 主类 | `line` | [趋势折线](../examples/diagram-atlas/index.html#line) |
| Diagram Design 主类 | `gantt` | [甘特图](../examples/diagram-atlas/index.html#gantt) |
| Diagram Design 主类 | `scatter` | [散点图](../examples/diagram-atlas/index.html#scatter) |
| Diagram Design 主类 | `high-level` | [端到端系统鸟瞰](../examples/diagram-atlas/index.html#high-level) |
| Diagram Design 主类 | `process` | [多角色作业过程](../examples/diagram-atlas/index.html#process) |
| Diagram Design 主类 | `medallion` | [勋章式数据分层](../examples/diagram-atlas/index.html#medallion) |
| Diagram Design 主类 | `data-flow` | [数据流图](../examples/diagram-atlas/index.html#data-flow) |
| Diagram Design 主类 | `dp-integration` | [平台集成图](../examples/diagram-atlas/index.html#dp-integration) |
| Diagram Design 主类 | `dp-security-matrix` | [角色权限矩阵](../examples/diagram-atlas/index.html#dp-security-matrix) |
| Diagram Design 主类 | `sankey` | [桑基图](../examples/diagram-atlas/index.html#sankey) |
| Diagram Design 主类 | `fishbone` | [鱼骨图](../examples/diagram-atlas/index.html#fishbone) |
| Diagram Design 主类 | `wardley` | [Wardley 地图](../examples/diagram-atlas/index.html#wardley) |
| Diagram Design 主类 | `kanban` | [看板](../examples/diagram-atlas/index.html#kanban) |
| Diagram Design 主类 | `journey` | [用户旅程](../examples/diagram-atlas/index.html#journey) |
| Diagram Design 主类 | `deployment` | [部署图](../examples/diagram-atlas/index.html#deployment) |
| Diagram Design 主类 | `dependency` | [依赖图](../examples/diagram-atlas/index.html#dependencies) |
| Diagram Design 主类 | `uml-class` | [UML 类图](../examples/diagram-atlas/index.html#class-diagram) |
| Diagram Design 主类 | `story-map` | [故事地图](../examples/diagram-atlas/index.html#story-map) |
| Diagram Design 主类 | `db-schema` | [物理数据库结构](../examples/diagram-atlas/index.html#db-schema) |
| Diagram Design 主类 | `polar` | [极坐标径向图](../examples/diagram-atlas/index.html#polar) |
| Diagram Design 主类 | `waterfall` | [增减瀑布图](../examples/diagram-atlas/index.html#waterfall) |
| Diagram Design 主类 | `architecture-delta` | [架构变更图](../examples/diagram-atlas/index.html#architecture-delta) |
| Diagram Design 主类 | `exploded` | [爆炸轴测图](../examples/diagram-atlas/index.html#exploded) |
| Diagram Design 主类 | `axonometric-plan` | [轴测平面图](../examples/diagram-atlas/index.html#axonometric-plan) |
| Diagram Design 主类 | `heatmap` | [热力图](../examples/diagram-atlas/index.html#heatmap) |
| Diagram Design 主类 | `service-blueprint` | [服务蓝图](../examples/diagram-atlas/index.html#blueprint) |
| Diagram Design 主类 | `sbgn` | [生物过程描述图（SBGN）](../examples/diagram-atlas/index.html#sbgn) |
| Diagram Design 主类 | `requirement-traceability` | [需求追踪矩阵](../examples/diagram-atlas/index.html#requirement-traceability) |
| Diagram Design 主类 | `event-modeling` | [事件建模](../examples/diagram-atlas/index.html#event-modeling) |
| Diagram Design 主类 | `steps` | [有序步骤](../examples/diagram-atlas/index.html#steps) |
| Diagram Design 主类 | `unit-grid` | [单位网格](../examples/diagram-atlas/index.html#unit-grid) |
| Diagram Design 变体 | `slopegraph` | [斜率图](../examples/diagram-atlas/index.html#slopegraph) |
| Diagram Design 变体 | `ridgeline` | [山脊分布图](../examples/diagram-atlas/index.html#ridgeline) |
| Diagram Design 变体 | `streamgraph` | [河流图](../examples/diagram-atlas/index.html#streamgraph) |
| Diagram Design 变体 | `bump` | [排名变动图](../examples/diagram-atlas/index.html#bump) |
| Diagram Design 变体 | `bubble` | [气泡散点图](../examples/diagram-atlas/index.html#bubble) |
| Diagram Design 变体 | `beeswarm` | [蜂群图](../examples/diagram-atlas/index.html#beeswarm) |
| Diagram Design 变体 | `box-plot` | [箱线分布图](../examples/diagram-atlas/index.html#box-plot) |
| Diagram Design 变体 | `marimekko` | [马赛克矩形图](../examples/diagram-atlas/index.html#marimekko) |
| Diagram Design 变体 | `arc-diagram` | [依赖弧图](../examples/diagram-atlas/index.html#arc-diagram) |
