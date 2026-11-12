# Data Charts Master · 见数

**让图表回答问题，也让人愿意看。** 面向 Codex、Claude Code 和兼容 `SKILL.md` 的 Agent：业务选图、视觉设计、HTML 交互与 SVG 输出。

[在线图谱 ↗](https://jigongxian900-dotcom.github.io/data-charts-master/) · [交互动效 ↗](https://jigongxian900-dotcom.github.io/data-charts-master/#motion) · [安装使用](#安装与第一次使用) · [English](README.en.md) · [MIT](LICENSE)

[![见数：从数字到判断，54例图表与七套配色](docs/assets/readme-hero.png)](https://jigongxian900-dotcom.github.io/data-charts-master/)

**54** 个图表与组合实例 · **7** 套原创语义配色 · **3** 个交互叙事实例。示例可离线打开，附原始值、业务问题、适用条件与阅读边界。

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
git clone https://github.com/jigongxian900-dotcom/data-charts-master.git .agents/skills/data-charts-master
```

**Claude Code：**

```sh
git clone https://github.com/jigongxian900-dotcom/data-charts-master.git .claude/skills/data-charts-master
```

然后在该项目中打开 Agent 会话。Codex 输入 `$data-charts-master`，Claude Code 输入 `/data-charts-master`，再描述任务。没有自动发现时，让 Agent 直接读取安装目录中的 `SKILL.md`。

复制这个示例，再附上你的数据：

```text
使用 data-charts-master。我要判断哪些区域没有达到目标。
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

## 范围与许可

54例是按固定合成数据编写的完整实例；Python 助手另支持横条、折线、堆叠、瀑布、箱线和散点六类通用图。迁移时要重算标题、标注、尺度与派生值。

PPTX 提供制作与验证方法，需要另配制作工具；本仓库没有打包全原生数据可编辑的54页演示文稿。图谱以中文为主，英文 README 不代表图表已全部英文化。

代码、文档、配色和合成数据采用 **MIT**，允许商用和修改。所有数值均为演示数据，不代表任何公司的实际经营。

[验证范围](docs/validation.md) · [能力边界](references/capability-evidence.md) · [贡献方式](CONTRIBUTING.md)

视觉与仓库呈现参考 [Lieflat Charts](https://github.com/larashero3-dotcom/lieflat-charts)、[Diagram Design](https://github.com/cathrynlavery/diagram-design)、[Vivid Figures](https://github.com/yjz211/vivid-illustration-skill) 和 [Tableau](https://www.tableau.com/data-insights/dashboard-showcase)。独立实现，未打包上述项目的源码、模板或图像。[第三方说明](THIRD_PARTY_NOTICES.md)
