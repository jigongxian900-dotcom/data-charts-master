# 有界 SVG 数值场景入口

这不是自然语言选图或自动聚合。作者提供可信、已核算的数值几何，入口复用现有 ChartMotion，避免每页重写 requestAnimationFrame。不会将工程通过写成 9.5 或自动业务正确。

## 运行

```powershell
python scene_html.py manufacturing.json output.html --runtime SKILL/assets/chart-motion.js
```

只依赖 Python 标准库；输出完全自包含 HTML。模板与脚本放在同一目录。`funding.json` 演示两期同单位资金段的边界与总长度同时变化。`manufacturing.json` 演示数量变化、范围变化、真零/未报。示例为合成验证数据，视觉是测试壳，不是面向用户的设计上限。

## Schema 边界

顶层 title/description/source/width/height，marks 与 states。每个 mark 固定 id、kind(rect/circle/line)、label、unit、六位色值。state 提供 id、label、semanticSpace、description、guides、values。values 以稳定 id 提供原值与几何；没有的ID是不在范围，显式 value:null 是未报且禁止附几何，真零有实际零几何。只能用数值属性，不解析SVG path、不接收原始HTML。

几何字段严格匹配：rect x/y/width/height/lx/ly；circle cx/cy/r/lx/ly；line x1/y1/x2/y2/lx/ly。lx/ly是标签位置。单位可在value上覆盖，但同semanticSpace不能改变单位或轴说明。改变坐标语义必须换semanticSpace；该转换立即完成，不在金额与百分比之间插值。几何映射、坐标解释、选图与布局仍由作者检查，不能用该schema证明数值几何正确。

同身份同语义场景从当前绘制帧过渡；新成员直接出现在真实几何，缺失或离开成员直接移除，不从0补造数据。过渡期间标签和原值表是目标值，并明确标“目标”。稳定ID关联，不按数组下标配对。输入上限100对象/20状态；几何绝对值<=1e6、原值绝对值<=1e15、视口100..5000；不支持曲线拓扑、Canvas或任意复杂路径。

## 核验

`test_scene.py` 四方法：两业务样例与换数、10拒绝子例、标记注入转义、极值/特殊ID。`verify-scene.cjs` 真实无头Edge：起始同步帧、实际中间几何、快速反向、全采样范围不越界、初始/中途reduce、真零与缺报、真值入场、键盘、重复状态、同单位堆叠共享边界、语义换轴即时、极值/特殊ID、无运行错误。Playwright可用PLAYWRIGHT_MODULE指定。

曾有一个测试误把共享guides对象同时改了两状态，已修夹具；另一次跨进程100ms读数在浏览器调度延迟下错过动画，已改为页面内连续RAF采样，未改动画来迎合测试。真实截图已目视检查，尚待独立复核，不称为新题评分。
