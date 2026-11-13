# 接入新组合，沿用同源交付

此入口解决基础助手只接六类合同的工具限制。作者先推导图形，再用普通Python函数实现当次任务需要的标记与变换；不要求为每个图型永久增加模板。已有项目适合用其它可视化库时可以沿用，保持同等数据与交付合同。

## 作者侧入口

在producer中将技能`scripts`加入模块路径，定义本题的业务校验函数和绘制函数后调用：

```python
from compose_html import build
from custom_chart import CustomRenderer, RenderedChart

registry = {'joint-view': CustomRenderer(
    label='本题的联合比较',
    validate=validate_task,
    render=render_task,
)}
html = build(spec, mode='report', theme='ruby', renderers=registry)
```

这是接入片段。`validate_task`和`render_task`由producer根据业务问题定义；交付时保留完整producer、spec及原始数据。CLI与无registry调用仍只校验原有六类，不从JSON读取或执行代码。注册键可自行命名，但不能覆盖已有六类；未注册的新kind会明确报错。

`spec`保留标题和`charts`，每个自定义chart含`id/kind/title/question/unit/period/scope/source/rows`。`kind`匹配registry键；`rows`可以是区间、层级、分项、配对数据等普通对象，不要求存在`value`字段。元数据写当前图的真实口径，而非沿用示例文本。原始观测与派生视图行的区别由producer声明，不把派生行数当新增样本量。

## 返回完整的尺寸与来源合同

每次`render_task(chart, variant, theme_css)`返回一个`RenderedChart`：

| 字段 | 内容 |
|---|---|
| `svg` | 当前尺寸的完整静态SVG；自带正的有限viewBox |
| `ledger` | 每个已绘制源行一条，含`row_index`、完整原始`source`及作者定义的几何/计算记录 |
| `coverage` | 每条原始行恰好一条，标记`rendered/missing/excluded`；后两者说明`reason` |
| `table_fields` | 原始行字段并集，各一次；作者指定顺序，公共表完整保留 |
| `export_svg` | 同次构建形成的完整静态对应图，不只提供未加主标记的底图 |

`variant`为`desktop/mobile/compact`。三者可以重排、改变密度或重新表达，但保持相同源行覆盖与字段。手机重排不等于删去例外。聚合图仍逐源行记账，可在多条ledger中引用同一聚合标记；一条原始行也可在自己的记录中列多个视觉标记。

coverage、表与源绑定用于查漏，不是业务正确性的自动证明。作者validator检查当次行结构、数值关系、分母、单位、尺度及几何不变量；回调不得修改输入。自定义图不使用内置`claims`的六类语义，需自行校验并呈现其声明。

公共包装层统一源JSON/哈希、数据表、来源说明、三尺寸、报告或演示控制，以及静态SVG下载。源行缺键会显示“未提供字段”，`null`显示缺失；不会把没有`value`的自定义数据都算缺失。

## 自由组合可用的工具

`chart_geometry.py`仅提供数学部件。作者可以组合它们、直接写SVG或使用其它算法，不必把表达压成这些函数：

- `linear_scale(value, domain, output, clamp=False)`：共享或反向线性尺度。null保持null；不默认截断。
- `band_scale(categories, output, padding=0)`：保持顺序的分类带。返回start/end/center/width，重复类别拒绝。
- `polar_point(cx, cy, radius, angle)`：弧度；SVG坐标中正角为顺时针。
- `area_radius(value, max_value, outer_radius, inner_radius=0)`：平方半径差与非负值成正比；同角宽时可比面积。零保留为内半径，null返回None，负值不被转成绝对值。
- `annular_sector(cx, cy, inner_radius, outer_radius, start_angle, angle_span)`：完整圆、半圆、折扇、旋转和反向是参数；返回path、面积与端点。不会为每种外观注册新kind。
- `hierarchy_partition(rows, layout='rect'|'angular', ...)`：普通id/parent/value树。检查单根、无环、父项存在与加总；叶子未知拒绝，内部null表示从完整子项求和。矩形为分层条带，角分区为等面积径向带；这是布局部件，不是万能树图设计器。

函数签名与边界以实际脚本和测试为准。需要有未知叶子的业务层级时，作者应选择明确的部分覆盖表达或其它布局，不能为调用分区器先补零。指针仪表、甘特或气泡饼也仍需各自数据前提，几何函数不会自动推断业务含义。

## SVG与导出检查

自定义SVG只用静态元素/属性，允许局部defs、渐变、裁剪与引用；包装层检查白名单、本地引用及数值有限性，并隔离各图各尺寸的ID。SVG内不使用脚本、foreignObject、外链、动画、style元素或style属性。颜色可引用当前主题token，独立出口会解析为静态色。

需要复杂状态交互时，在HTML层维护同一数据和标记身份，并为导出提供明确的稳定状态。公共层不能自动知道页面后来追加的标注是否已进入`export_svg`。如果静态出口只代表某个状态，应在图旁说明；承诺同视觉时，实际核对主要标记、标签、颜色、来源与数值。

独立SVG结构通过不等于几何或选图正确。浏览器要看桌面、窄屏和打印；凡媒体切换会换图面，确认新图面完整形成且读屏状态可恢复。PPTX仍按所需编辑层另走制作与真实保存重开验收；开放SVG入口不使其自动成为原生Office图表。
