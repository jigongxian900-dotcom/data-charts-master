# HTML交付与SVG助手

## 数据合同

`scripts/chart_html.py` 使用Python标准库，无联网。输入JSON顶层为 `title`、可选 `intro`、`synthetic` 和 `charts`。合成样例设置 `synthetic:true`；真实业务数据写 `data_note`，不冒充已核验。

每张图必填 `id,title,question,kind,unit,period,scope,source,rows`。字段中数值使用JSON数字，缺失使用显式null；拒绝数值字符串、布尔和非有限值。

| kind | rows字段 | 额外字段 / 条件 |
|---|---|---|
| bar | label,value,highlight可选 | 唯一类目，零基线，支持负值 |
| line | x（ISO日期）,value,group可选 | frequency为day/month/year；每组期间连续，缺测补显式null记录，不插值；按真实日期间距 |
| stacked | label,parts（名称→非负数字） | percent可选，零分母拒绝；缺失段不补零 |
| waterfall | label,value,role | 首项start，中间change，末项total；起点+贡献=终点，否则拒绝 |
| box | label,value | 原始观测，可重复组名；线性分位数、1.5IQR须、原始点全部显示 |
| scatter | label,x,y,highlight可选 | x_unit,y_unit必填；任一值缺失则不绘点，保留原记录 |

可选 `claims:[{"method":"sum","expected":120}]`，支持sum/mean/median/count，仅适用于bar/line/box的全部非缺失value。它不核验任意自然语言标题，也不解析单组过滤后的主张。

```json
{"title":"演示","synthetic":true,"charts":[{"id":"regions","title":"区域差异","question":"哪些区域更高？","kind":"bar","unit":"件","period":"合成期间","scope":"全部3组","source":"确定性合成数据","rows":[{"label":"甲","value":24},{"label":"乙","value":null},{"label":"丙","value":0}]}]}
```

`validate`先核合同；`build ... --out output.html --layout editorial|analytical|focus` 输出HTML及相邻 `.data.json`。三种布局分别为文字与主图联排、双列对照、单问题定位；均可显示全量，不自动成为用户默认风格。

配色可用输入的 `theme` 或命令参数 `--theme tidal|cobalt|grove|iris|nocturne|graphite|mixue-ruby`。见 [配色体系](color-system.md)。图例用颜色标记与正文色文字，分类色不直接承担小字号文字；深色屏幕版打印自动切到浅色语义色。输入值与图形几何不因主题改变。需要保留品牌色的PDF/PPTX按选定浅底主题另行输出与实看，不能把屏幕换色当作打印也已同步。

可复跑输入：[representative.json](../examples/representative.json)。它只是合成数据的实现样例，不是业务选图的固定模板；先按业务问题选图，再决定是否使用该助手。

## 检查真实文件

1. 打开交付文件，核对图数、数据表、数值标签和SVG几何。`chart-spec`和`chart-ledger`脚本块保存完整输入与图形记录，SHA-256绑定规范化输入。
2. 切换问题定位、重置、键盘操作源数据表与下载。此助手的定位控件筛选图表，不筛选数据；不能宣称联动经营筛选。
3. 桌面与窄屏分别布局，手机使用独立尺寸SVG；长标签换行，不等比缩成不可读小字。检查图例、长中文、负值、极端值、缺失与空图。
4. 离线/阻断请求打开，确保零外部依赖和零运行错误。外链参考不是渲染依赖，内部数据不得外发。
5. 打印模式保留全部图和数据表，不把屏幕隐藏状态带到纸上。实际打印/PDF仍须目检，不能只因有print CSS就称通过。

此助手不自动选择业务图型，不做统计显著性检验，不支持地图/密集大数据或任意仪表盘，也不是已有ECharts项目的迁移要求。复杂任务沿用现有引擎，以同等数据与运行合同验收。

### 数值精度与长标签

原始数据表、数值标签与提示保留输入的小数精度，不能把非零小量显示成零。极小或极大值可用明确的科学计数法。轴刻度可消除浮点运算噪声，但不能改变数据表与下载值。每次更换量纲，检查最小非零值、真零与负数。

长中文需要按实际字体检查viewBox边界。基础助手为桌面标签列保留字体回退余量，换行后同步增加行高。长度和单位变化后重新截图，不能只验证没有页面横向滚动。

## 现有ECharts的要点

基础瀑布默认只用两种重点色区分增减，不判绩效。已确认方向时可给图声明 `performance_direction: "higher"`（越高越有利）或 `"lower"`（越低越有利），才将正负贡献映射到有利/不利色。未声明为 `"neutral"`，节省成本不能因负号就自动被判作不利。

容器须有非零尺寸；隐藏面板显示后resize；每容器一个实例，移除前dispose；结构变更时清理旧系列。共享dataset与格式化函数。按实际版本核对API；历史“left只能6–10”等局部修复不能升级为所有图的常数。文字空间按实际标签测量。
