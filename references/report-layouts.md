# HTML 报告与演示排版

从使用场景选普通网页宽度、A4 或 16:9。先确定首屏读者要做的一个判断，再安排支持该判断的数据，最后放可追溯的口径和明细。留白用来分隔不同层级，关联紧密的标题、图和读数放在一起。色板决定焦点和类别，幅面决定内容密度。

| 交付 | 适用读法 | 构图与尺寸 | 实例 |
|---|---|---|---|
| 一页简报 | 快速确认结果和下一步 | 常规桌面网页，A4 纵向打印。首屏给结论、核心量和一张主要证据图，口径随图，源表在末尾 | [目标差额简报](../examples/report-layouts/brief.html) |
| 多章节报告 | 顺序阅读或回查章节 | 内容最大宽度约 1180px。每个章节按主图与旁注、同屏并排对照或纵向序列重新编排 | [经营复盘](../examples/report-layouts/report.html) |
| 16:9 演示 | 汇报时逐屏推进 | 桌面聚焦投影保持 16:9；每页聚焦一个判断。图太密时拆成两页，口径和可下载明细留在资料区 | [可翻页演示](../examples/report-layouts/slides.html) |

## 从数据到版面

同一份数据交付三种形式时，先分别写三份提纲。三份可采用不同的图和证据深度。

- 简报开头给本次优先级，并列总量、对象份额和下一步。需要保留明细时把完整数据放到资料区。纸面按 A4 的阅读顺序重排。
- 长报告先建立按同一对象合并的证据表，把实绩、目标差额、同比和同店对齐，再用章节回答增量从哪里来、哪里需要核查。稳定 ID 支持比较对象时可加聚焦。聚焦必须更新对应的原值和指标。
- 演示从优先级切入，逐页用不同的证据回答疑问。末页写明本次会议要确认什么、谁带回什么，以及拿什么判断下一步。角色可写成建议分工，待确认的估算列出期间与依据。

以 [经营缺口案例的三份成品](#html-报告与演示排版) 为例，同一组原始数据分别编排成缺口简报、经营复盘和会议演示。复盘将既有缺口与下期改善估算分开，完整数据可在三份成品中下载。

1. 写下读者需要做的判断。简报首屏放判断、读数和行动。长报告用章节导航定位证据，首章让图及核心读数进入首屏。演示每页用一个结论标题和足够大的主图，边栏确有解释时才保留。
2. 同口径并排比较共用轴和单位。短标签用贴近图形的读数，长标签可增高行距或换图，确保业务词和带单位的数值整体换行。标题、导语和图注各承担一个作用。通过同屏、断页和投影截图检查不必要的白区。
3. 交付成稿时清理模板提示、生成说明、验收结论、内部状态、调试编号和哈希。将影响判断的期间、单位、口径、缺口、来源写在相关图旁。详细定义、下载与校验留在资料区或交付说明。合成样例在来源处标「示例数据」。
4. 桌面首屏检查标题、图、关键值和下一步。按真实报告尺寸打印并实看。投影逐页看字号、对比、剪裁与导航，普通 1280×720 屏幕上的关键图中文字宜至少约 16px。空间不足时调整构图或拆页。

## 制作

在 [原始图表合同](html-delivery.md) 上设置 `composition.sections`。每个图只在一个章节出现。`layout` 选择 `feature`（图与说明）、`comparison`（两图对照）或 `sequence`（顺序阅读）。已有报告可以加入自定义 SVG 或 HTML 图表，保留原始图和标注。

```bash
python scripts/compose_html.py spec.json --delivery final --mode report --reading brief --out brief.html
python scripts/compose_html.py spec.json --delivery final --mode report --reading editorial --out report.html
python scripts/compose_html.py spec.json --delivery final --mode slides --out slides.html
python scripts/build_report_layout_samples.py
```

用 `composition.summary` 写首屏导语，`composition.closing` 写具体下一步。`composition.audience` 可提供 `edition`、`date`、`source`、`action_label`、三项以内 `metrics`（`label`、`value`、可选 `unit`）。`audience.figures` 按图 ID 写图名 `title`、章节名 `nav`、投影结论 `headline`、图注 `caption` 和事实旁注 `callout`。这些文字使用已核实的事实。没有口径变化时用一条短图注。报告可使用完整 `source_data`。其他自定义版面沿用图表与资料出口。

主题用 `--theme`，指定焦点色用 `--brand-accent`。在比较 [三种图形表现](chart-shapes.md) 后，用 `shape` 将选定表现应用到成稿。

研究来源为 [Lieflat Charts 的 Report Templates](https://github.com/larashero3-dotcom/lieflat-charts#templates) 和 [Frontend Slides 的固定舞台与密度规则](https://github.com/zarazhangrui/frontend-slides)。另参考花叔 Design 的媒介与观众距离判断。示例、模板和运行逻辑由 Jee Charts Master 实现。
