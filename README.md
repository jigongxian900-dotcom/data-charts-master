# Jee Charts Master · 见数

**让 Agent 按业务问题选图，自主设计复杂组合，交付可操作的 HTML 与 SVG。** 面向 Codex、Claude Code 和兼容 `SKILL.md` 的 Agent：从比较关系出发，设计构图、联动与能追踪对象的数据动效。


## 图形动效与 HTML 报告

[![实拍消息时序，含成功与回滚方向](docs/assets/diagram-atlas-preview.png)](https://jigongxian900-dotcom.github.io/data-charts-master/diagram-atlas.html#sequence)

- [80 张图形的动效图谱](https://jigongxian900-dotcom.github.io/data-charts-master/diagram-atlas.html) · 流程、架构、时间、关系、定性变形与数量。按图义选择路径描绘、消息时序、区间铺开和定量流带等动效，可搜索并核对原始示例数据。
- [流程图与真实路径](https://jigongxian900-dotcom.github.io/data-charts-master/workflow-diagrams.html) · 同一模型切换决策、泳道与实绩，支持三套版式和 SVG 下载。
- [A4 单页简报](https://jigongxian900-dotcom.github.io/data-charts-master/report-layouts/brief.html) · [多章节报告](https://jigongxian900-dotcom.github.io/data-charts-master/report-layouts/report.html) · [16:9 演示](https://jigongxian900-dotcom.github.io/data-charts-master/report-layouts/slides.html) · 同一经营案例按优先级、跨图分析和会议决定组织成三份成品。
- [十二图动效展厅](https://jigongxian900-dotcom.github.io/data-charts-master/motion-gallery.html) · [跨图动效组合](https://jigongxian900-dotcom.github.io/data-charts-master/motion-composition.html) · 看不同动效如何帮助读者追踪数据。

- [同数据三款图形](https://jigongxian900-dotcom.github.io/data-charts-master/chart-shapes.html) · 七组二十一款，柱形、端点、线条和区间的真实变化，支持分别下载 SVG。

[选图与参考对应表](references/diagram-atlas.md) · [报告排版与制作命令](references/report-layouts.md) · [从旧技能名迁移](docs/usage.md#从旧技能名迁移)

[在线图谱 ↗](https://jigongxian900-dotcom.github.io/data-charts-master/) · [自主复杂案例](#autonomous-examples) · [交互动效 ↗](https://jigongxian900-dotcom.github.io/data-charts-master/#motion) · [安装使用](#安装与第一次使用) · [English](README.en.md) · [免费与商用许可](COMMERCIAL.md)

[![真实操作：切换匹配目标，持续追踪对象、参照与取舍](docs/desktop/assets/tenant-unit-motion.gif)](https://jigongxian900-dotcom.github.io/data-charts-master/desktop/tenant-unit-allocation.html)

**54** 个图表与组合实例 · **7** 套原创语义配色 · **3** 个交互叙事实例。示例可离线打开，附原始值、业务问题、适用条件与阅读边界。

## 5.4 动效试用

[![三幕真实交互：增长、结构和门店位次](docs/motion-showcase.png)](https://jigongxian900-dotcom.github.io/data-charts-master/motion-showcase.html)

[打开三幕动效展示 ↗](https://jigongxian900-dotcom.github.io/data-charts-master/motion-showcase.html) · [离线成品与重建源](examples/motion-showcase/README.md)

本轮把动效接入做成可执行入口：已核算的 SVG 矩形/圆/线场景可一条命令生成独立 HTML，保留行适配器负责筛选与重排时的对象追踪。当前帧续接、快速反向、减少动态、焦点保留有实际浏览器回归。展示使用原创合成数据，初始不自动播放。

- [有限 SVG 场景构建器](scripts/scene-builder/SCENE-README.md)：不再逐页重写 RAF；不替作者聚合业务数据或保证几何映射正确。
- [保留对象行](references/retained-rows.md)：同 ID 节点和真实数值保留，筛选不把不变条形重新从零播放。
- [指标卡](scripts/kpi-builder/README.md)与[统一入口/产物门禁](references/production-gate.md)：明确支持边界，缺测不算通过。

这是先用一段、继续收集实际反馈的动效更新，不是95分或任意业务任务均已验证的保证。既有图谱、案例和许可边界保留。[本轮验证范围](docs/motion-5.4-validation.md)

## 先体验，再安装

1. [打开在线图谱](https://jigongxian900-dotcom.github.io/data-charts-master/)，直接操作筛选、聚焦、表格和导出。
2. [体验对象连续变换](https://jigongxian900-dotcom.github.io/data-charts-master/labs/dir-3.html)，看同一对象如何随分析问题重排。
3. 再看[安装与第一张图](#安装与第一次使用)。需要已有Agent环境；浏览在线样例无需安装。

新增动效机制用于稳定ID追踪、从可见帧反向切换、运行时减少动态和稳定出口。复杂路径、坐标、单位与业务含义仍由作者核对；不承诺任意图一键正确。

**许可从v5.3分界：**新增原创内容与修改采用非商用许可，商用另行授权；标准条款允许的机构范围、历史MIT权利和生成HTML的内嵌代码范围，见[授权说明](COMMERCIAL.md)。旧版MIT授权不追回。当前没有自助付款页或已售数量声明。

<a id="autonomous-examples"></a>

## 不查同名模板，解决新业务问题

下面三例只提供原始问题与合成数据。Agent 自主选择表达、实现分析操作，并在首次交付前完成独立实看与修正。它们展示自主制作过程，不是把任意 JSON 送进同一套模板。

| 业务问题 | 联合表达与操作 | 在线体验 / 可复现源 |
|---|---|---|
| 应收核对 | 多对多关系、带符号核对、双端追踪与计量基准切换 | [体验](https://jigongxian900-dotcom.github.io/data-charts-master/desktop/receivables-reconciliation.html) · [问题、数据与制作器](examples/autonomous-desktop/receivables-reconciliation/README.md) |
| 租户与房源分配 | 硬约束下的全局匹配，比较偏好、公平与经济取舍 | [体验](https://jigongxian900-dotcom.github.io/data-charts-master/desktop/tenant-unit-allocation.html) · [问题、数据与制作器](examples/autonomous-desktop/tenant-unit-allocation/README.md) |
| 市政请求与工作量 | 重叠集合的精确划分、选择语义与负荷联动 | [体验](https://jigongxian900-dotcom.github.io/data-charts-master/desktop/civic-request-overlap.html) · [问题、数据与制作器](examples/autonomous-desktop/civic-request-overlap/README.md) |

[直接交付成品的使用指令](docs/usage.md#第一次任务) · [自主质量流程](references/autonomous-quality-loop.md)

另有六个含同题修正的回归实录：[配送排班](https://jigongxian900-dotcom.github.io/data-charts-master/regression/intercity-delivery-scheduling.html)、[双因素投放](https://jigongxian900-dotcom.github.io/data-charts-master/regression/factorial-outreach-experiment.html)、[易腐库存](https://jigongxian900-dotcom.github.io/data-charts-master/regression/perishable-inventory-expiry.html)、[招聘等待与负荷](https://jigongxian900-dotcom.github.io/data-charts-master/regression/recruitment-waiting-load.html)、[错误预算与时延](https://jigongxian900-dotcom.github.io/data-charts-master/regression/service-error-budget-latency.html)、[预约容量](https://jigongxian900-dotcom.github.io/data-charts-master/regression/venue-booking-capacity.html)。[原始问题与完整HTML源](examples/regression/README.md) · [逐题验证与范围](docs/validation.md)。回归结果与陌生题首次交付分开记录。

<details>
<summary>查看三份真实桌面作品</summary>

[![应收核对：多对多、带符号核对与双端追踪](docs/desktop/assets/receivables-reconciliation.png)](https://jigongxian900-dotcom.github.io/data-charts-master/desktop/receivables-reconciliation.html)

[![租户与房源分配：匹配、公平与经济取舍](docs/desktop/assets/tenant-unit-allocation.png)](https://jigongxian900-dotcom.github.io/data-charts-master/desktop/tenant-unit-allocation.html)

[![市政请求：重叠集合与工作量联动](docs/desktop/assets/civic-request-overlap.png)](https://jigongxian900-dotcom.github.io/data-charts-master/desktop/civic-request-overlap.html)

</details>

## 动效用于解释变化

下面是实际 HTML 交互的录屏。点击链接即可操作；GIF 是预览，不替代交互。

### 同一组对象，三种判断

规模 → 增量 → 同店。对象身份保持连续，位置和编码随问题变化，避免重新寻找同一市场。

[![从规模到增量再到同店的真实几何动效](docs/assets/narrative-motion.gif)](https://jigongxian900-dotcom.github.io/data-charts-master/labs/dir-3.html)

[打开叙事实例 ↗](https://jigongxian900-dotcom.github.io/data-charts-master/labs/dir-3.html)

### 从增长贡献，切到目标差额

流带展示增量关系；差额视角改用共零基线，清楚区分超额和缺口。聚焦对象与原始表同步。

[![增长贡献与目标缺口切换，保留市场身份](docs/assets/flow-motion.gif)](https://jigongxian900-dotcom.github.io/data-charts-master/labs/dir-1.html)

[打开流带与差额实例 ↗](https://jigongxian900-dotcom.github.io/data-charts-master/labs/dir-1.html) · [气泡位置与市场联动 ↗](https://jigongxian900-dotcom.github.io/data-charts-master/labs/dir-2.html)

## 先看效果

### 01 / 快速判断：数字、趋势、基准一起看

KPI 卡片同时交代当前值、迷你趋势、同比和环比。利润率用百分点，成本下降按“低为优”解释。

<picture>
  <source media="(max-width: 600px)" srcset="docs/assets/kpi-mobile.png">
  <img src="docs/assets/kpi-desktop.png" alt="KPI与趋势：营业额、订单、利润率及履约成本，含同环比" width="100%">
</picture>

[体验 KPI](https://jigongxian900-dotcom.github.io/data-charts-master/#kpi-compare) · [目标子弹图](https://jigongxian900-dotcom.github.io/data-charts-master/#multi-bullet) · [四种达成状态](https://jigongxian900-dotcom.github.io/data-charts-master/#attainment-ring) · [经营组合页](https://jigongxian900-dotcom.github.io/data-charts-master/#operating-overview)

### 02 / 精确比较：把差距放回同一把尺

排序、前后变化、目标差额和蝴蝶对照，各自回答不同问题。重点色承担比较，数量编码保留共同基准。

![差额、目标与前后变化的精选图表](docs/assets/comparison-selection.png)

[排序条形](https://jigongxian900-dotcom.github.io/data-charts-master/#rankedbar) · [哑铃](https://jigongxian900-dotcom.github.io/data-charts-master/#dumbbell) · [蝴蝶](https://jigongxian900-dotcom.github.io/data-charts-master/#butterfly) · [瀑布](https://jigongxian900-dotcom.github.io/data-charts-master/#waterfall)

### 03 / 深入分析：关系、分布与时间放在一起

从留存矩阵到多维关系，先判断比较条件，再用共享尺度、直接标注和必要的解释控制复杂度。

![留存、关系与多维分析的精选图表](docs/assets/analysis-selection.png)

[Cohort 留存](https://jigongxian900-dotcom.github.io/data-charts-master/#cohort-triangle) · [时间路径散点](https://jigongxian900-dotcom.github.io/data-charts-master/#connected-scatter) · [平行坐标](https://jigongxian900-dotcom.github.io/data-charts-master/#parallel-coordinates) · [全部54例](docs/catalog.md)

<details>
<summary>展开54例总览</summary>

![54例图表与组合总览](docs/assets/atlas54.png)

</details>

## 设计图谱里还没有的图

54例提供工艺参考。新任务先推导必须共同看见的关系，再选择标记、共享尺度、分面、叠加、坐标或层级变换。没有同名样例也可以设计；数据条件不成立时，应改用有效的简单表达。

5.2新增可选的作者侧绘图接口：自写SVG可以接入同一报告，保留逐源行覆盖、精确读数、手机重排与完整静态导出。通用数学部件提供尺度、面积正确的扇区和层级分区；业务判断仍由Agent完成。

[组合与变形推理](references/composition-reasoning.md) · [9件作品的机制灵感库](references/inspiration-library.json) · [如何使用灵感](references/inspiration-use.md) · [接入自定义绘图](references/custom-renderers.md)

灵感来自DKMECO与Tableau具体作品，记录原作、机制、适用条件和反例。8件核看原作静态预览，1件仅有策展证据；原作交互未实测。库中只分发链接和原创分析。

```text
使用 jee-charts-master。先判断这道业务问题需要共同看到哪些关系。
图谱没有合适样例时，请自主组合标记与尺度，或变换坐标、层级。
说明组合多揭示了什么、最简单的有效备选，以及不能误读的条件。
输出离线HTML、原始表、派生值、手机布局和包含全部图层的SVG。
```

### 三道新题的制作实录

三个独立上下文只拿技能与各自输入制作。两题推导出真实图内组合或坐标/层级变换，一题拒绝数据不支持的复杂流向。首轮评审发现展开布局及打印缺陷，保留失败后完成同题技术复验；修复没有增加陌生题数量。

[![24小时周期、层级归属和精确比较的联合表达](docs/assets/autonomy-cycle.png)](https://jigongxian900-dotcom.github.io/data-charts-master/autonomy/energy-cycle.html)

[体验周期与层级视图](https://jigongxian900-dotcom.github.io/data-charts-master/autonomy/energy-cycle.html) · [源数据与制作器](examples/autonomy/energy-cycle/README.md)

[![同天数前后变化、观察覆盖、规模和日均差额联合判断](docs/assets/autonomy-quality.png)](https://jigongxian900-dotcom.github.io/data-charts-master/autonomy/quality-support.html)

[体验质量与工时联合判断](https://jigongxian900-dotcom.github.io/data-charts-master/autonomy/quality-support.html) · [源数据与制作器](examples/autonomy/quality-support/README.md) · [为什么这题拒绝复杂流向](https://jigongxian900-dotcom.github.io/data-charts-master/autonomy/renewal-evidence.html)

这些是固定原创合成数据的推理实录。公开制作器仅适配路径与来源验证，重建HTML及计算与评审实物逐字节一致；换数据仍需重新规划与验证。独立AI评审不等于外部认证或全部图型的能力保证。

## 七套配色，一套语义

石榴红、潮汐青、钴蓝、林地绿、鸢尾紫、夜航与石墨。每套区分焦点、类别、顺序、发散和绩效状态；换主题保持数据与比例。

![七套原创配色，按场景选择](docs/assets/palette-strips.png)

主题标识：`ruby` · `tidal` · `cobalt` · `grove` · `iris` · `nocturne` · `graphite`。

## 手机也能读

窄屏使用重新排布的 KPI、迷你趋势与完整读数，复杂图可查看原图细节。核心说明不依赖悬停。

<picture>
  <source media="(max-width: 600px)" srcset="docs/assets/mobile-demo.gif">
  <img src="docs/assets/mobile-showcase.png" alt="手机端KPI、目标子弹与蝴蝶图：重排布局和完整读数" width="100%">
</picture>

[直接在手机打开](https://jigongxian900-dotcom.github.io/data-charts-master/) · [实际检查范围](docs/validation.md)

## 安装与第一次使用

### 只想看图？不用安装

打开[在线图谱](https://jigongxian900-dotcom.github.io/data-charts-master/)。要离线查看，可下载[最新版本](https://github.com/jigongxian900-dotcom/data-charts-master/releases/latest)，解压后打开 `docs/index.html`。浏览图谱不需要 Node.js、Python 或 API Key。

### 让 Agent 使用

在**你的项目根目录**执行下面对应的一条命令（需要 Git）。Windows PowerShell、macOS 和 Linux 均可使用。

**Codex：**

```sh
git clone https://github.com/jigongxian900-dotcom/data-charts-master.git .agents/skills/jee-charts-master
```

**Claude Code：**

```sh
git clone https://github.com/jigongxian900-dotcom/data-charts-master.git .claude/skills/jee-charts-master
```

然后在该项目中打开 Agent 会话。Codex 输入 `$jee-charts-master`，Claude Code 输入 `/jee-charts-master`，再描述任务。没有自动发现时，让 Agent 直接读取安装目录中的 `SKILL.md`。

复制这个示例，再附上你的数据：

```text
使用 jee-charts-master。我要判断哪些区域没有达到目标。
请先核对期间、单位、分母和缺失值，再选择合适图表。
生成可离线打开的单文件 HTML，带来源、原始表、手机布局和 SVG 下载。
采用石榴红，目标缺失时显示未知，不补零。
```

[详细安装、更新、卸载与排错](docs/usage.md) · [Agent 能力入口](SKILL.md)

### 先跑一个完整样例

克隆或下载后，进入技能文件夹。下面只需要 **Python 3.10+**，不需要安装第三方包：

```sh
python scripts/chart_html.py validate examples/representative.json
python scripts/chart_html.py build examples/representative.json --out sample.html --theme ruby
```

Windows 的 Python 命令若为 `py`，将上面的 `python` 改为 `py`。生成 `sample.html` 和 `sample.data.json`；用浏览器打开前者即可。

**想修改54例图谱？** 用 Node.js 20+ 运行 `node scripts/build_gallery.js`。它会同步生成示例 HTML、54份 SVG 与公开展示页。[生成文件与目录说明](docs/usage.md#开发与重建)

## 同一份数据，报告与演示两种表达

[先读一份完整经营案例 ↗](https://jigongxian900-dotcom.github.io/data-charts-master/operating-story.html)：同一组八市场合成数据，连续回答增长由谁贡献、目标还差多少、哪些市场需要复核同店表现。三张图按问题换布局，标题和金额随输入计算；不把贡献恒等式写成因果。

[![完整经营案例的增长贡献章节，原值、金额桥与阅读边界同页](docs/assets/operating-story.png)](https://jigongxian900-dotcom.github.io/data-charts-master/operating-story.html)

[打开报告示例](https://jigongxian900-dotcom.github.io/data-charts-master/report.html) · [打开可翻页演示](https://jigongxian900-dotcom.github.io/data-charts-master/slides.html)

报告按问题安排通栏趋势、旁注、比较与分布；演示按比较关系编排，宽屏可切换“聚焦投影”，手机使用重新编排的紧凑图形。同源原值与静态SVG保存在统一资料区。六图教学样例含不同业务，不能连成同一因果故事；上面的经营案例提供同源连续叙事。

```sh
python scripts/compose_html.py examples/composed/source.json --mode report --theme ruby --out report.html
python scripts/compose_html.py examples/composed/source.json --mode slides --theme ruby --out slides.html
```

这两种模式可读取六类基础合同，也可通过作者侧注册函数接入新表达；叙事由输入明确提供。改变数据必须重新核对标题与业务解释。HTML演示不冒充原生可编辑PowerPoint。[输入与模式说明](references/composed-outputs.md)

## 范围与许可

54例是按固定合成数据编写的完整实例；Python 基础助手另支持横条、折线、堆叠、瀑布、箱线和散点六类通用图，可选自定义绘图接口用于新的组合与变形。迁移时要重算标题、标注、尺度与派生值。

PPTX 提供制作与验证方法，需要另配制作工具；本仓库没有打包全原生数据可编辑的54页演示文稿。图谱以中文为主，英文 README 不代表图表已全部英文化。

v5.3起的新增原创内容与修改按 [PolyForm Noncommercial](LICENSE) 提供，商业用途需另行取得授权。旧MIT版本及其已有部分继续保留原授权，详见[逐文件范围](LICENSE-SCOPE.md)。这是源码公开与商业授权模式，不称为无限制免费商用开源。本仓库生成的经营示例为合成数据，不代表公司的实际经营；第三方作品仍按其权利与许可。

[验证范围](docs/validation.md) · [能力边界](references/capability-evidence.md) · [贡献方式](CONTRIBUTING.md)

视觉与仓库呈现参考 [Lieflat Charts](https://github.com/larashero3-dotcom/lieflat-charts)、[Diagram Design](https://github.com/cathrynlavery/diagram-design)、[Vivid Figures](https://github.com/yjz211/vivid-illustration-skill) 和 [Tableau](https://www.tableau.com/data-insights/dashboard-showcase)。独立实现，未打包上述项目的源码、模板或图像。[第三方说明](THIRD_PARTY_NOTICES.md)

## 一起把好图做出来

如果它帮你完成了一张有用的图，欢迎Star留存、提交问题或分享原创合成案例。试用、下载和授权咨询均不以Star为条件。反馈请说明业务问题、期望读法、实际结果与最小复现数据；不必提供内部明细。
