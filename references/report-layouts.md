# HTML 报告与演示排版

从使用场景选普通网页宽度、A4 或 16:9。先确定首屏读者要做的一个判断，再安排支持该判断的数据，最后放可追溯的口径和明细。留白用来分隔不同层级，关联紧密的标题、图和读数放在一起。色板决定焦点和类别，幅面决定内容密度。

| 交付 | 适用读法 | 构图与尺寸 | 实例 |
|---|---|---|---|
| 一页简报 | 快速确认结果和下一步 | 常规桌面网页，A4 纵向打印。首屏给结论、核心量和一张主要证据图，口径随图，源表在末尾 | [目标差额简报](../examples/report-layouts/brief.html) |
| 多章节报告 | 顺序阅读或回查章节 | 内容最大宽度约 1180px。每个章节按主图与旁注、同屏并排对照或纵向序列重新编排 | [经营复盘](../examples/report-layouts/report.html) |
| 16:9 演示 | 汇报时逐屏推进 | 桌面聚焦投影保持 16:9；每页聚焦一个判断。图太密时拆成两页，口径和可下载明细留在资料区 | [可翻页演示](../examples/report-layouts/slides.html) |

## 从数据到版面

1. 写下决策、证据、比较和条件。简报保留影响当前决策的主图。长篇报告可逐节补充来源与反例。演示把互相依赖的图保留在同一页，证据过多则分屏。
2. 同口径并排比较共用轴和单位。同一条证据被两个小标题重复使用时，合成一处并把两个问题写成旁注。来源、缺口和对应关系紧跟相关图。
3. 单份图表永远保留同源数据、关键定义与静态读数。用章节链接、展开明细或翻页解决阅读量。必要结论首屏可读，呈现动效可关闭。
4. 浏览器检查第一屏、长标签和标题换行。打印前查看页数和断页。投影时逐屏确认 16:9、字号和高度，核对键盘翻页、总览和静态资料出口。

## 制作

在 [原始图表合同](html-delivery.md) 上设置 `composition.sections`。每个图只在一个章节出现。`layout` 选择 `feature`（图与说明）、`comparison`（两图对照）或 `sequence`（顺序阅读）。已有报告可以加入自定义 SVG 或 HTML 图表，保留原始图和标注。

```bash
python scripts/compose_html.py spec.json --mode report --reading brief --out brief.html
python scripts/compose_html.py spec.json --mode report --reading editorial --out report.html
python scripts/compose_html.py spec.json --mode slides --out slides.html
python scripts/build_report_layout_samples.py
```

可按内容使用备选 `story`（叙事推进）或 `evidence`（证据密集），主题用 `--theme`，指定焦点色用 `--brand-accent`。颜色不改变数据含义。简报只需把对应的图纳入待生成合同，完整原始观测可保留在 `source_data`。内容超过一页时按章节拆分或使用长报告。示例按同一组合器制作，合成数据可下载。

研究来源为 [Lieflat Charts 的 Report Templates](https://github.com/larashero3-dotcom/lieflat-charts#templates) 和 [Frontend Slides 的固定舞台与密度规则](https://github.com/zarazhangrui/frontend-slides)。另参考花叔 Design 的媒介与观众距离判断。示例、模板和运行逻辑由 Jee Charts Master 实现。
