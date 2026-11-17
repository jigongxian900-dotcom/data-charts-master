# 数据过渡：最短接线

适合**对象 ID 相同、度量有限、单位一致、尺度可比**的状态切换。一个操作有对象追踪价值时，先接通一次完整状态切换：同帧绘制图形和文字，允许快速反向；无追踪收益或数据无法安全插值时即时切换。示例是合成数据与接线机制，不限定图型、样式或引擎。每次单独读取本文件，避免与大数据合并导致截断。

成员增减时，若对象 ID、轴与单位可比，另读 [散点连续追踪](motion-retained-example.md)：保留对象按当前帧追踪，进入、退出分开处理；该实现仅验证散点。若不可安全插值，另读 [范围分层切换](motion-membership-example.md)，按范围标示真实观测与独立尺度，或选择即时切换。缺失不得填成 0；两种路径均需实测当前业务数据。

单文件 HTML：本页固定成员示例将 `assets/chart-motion.js` 和 `assets/chart-state-motion.js` **按此顺序**各自的完整源代码内联到 HTML 的两个 `<script>` 中，再放以下片段。不要只引用本地文件，否则交付文件不可独立运行；已有引擎能满足相同语义则不必使用本组件。处理不同单位、缺失及非线性路径时，先设计明确的分阶段或静态切换；摘要只能聚合业务上可加的数据。

以下示例的数字、长度、总计都来自同一个量化帧；过渡值明确标注不是新增观测，目标数据在结束后恢复原始精度。保留按钮 DOM，快速反向从可见帧续接，支持用户初始及运行时启用减少动态。

```html
<section id="demo" aria-label="合成示例">
  <div><button id="before" aria-pressed="true">上期</button> <button id="after" aria-pressed="false">本期</button></div>
  <p id="status" role="status"></p>
  <svg viewBox="0 0 440 100" role="img" aria-label="两组数量对比">
    <text x="0" y="27">甲</text><rect id="bar-a" x="40" y="10" width="0" height="20" fill="#137a70"/><text id="val-a" x="365" y="27"></text>
    <text x="0" y="67">乙</text><rect id="bar-b" x="40" y="50" width="0" height="20" fill="#5968a8"/><text id="val-b" x="365" y="67"></text>
  </svg>
  <p>合计：<span id="total"></span> 件</p>
</section>
<script>
const states = {before:{A:12,B:21}, after:{A:29,B:16}}; // 合成数据，单位：件
const labels = {before:'上期', after:'本期'};
const $ = id => document.getElementById(id);
const motion = ChartStateMotion.create({
  initial:states.before, initialLabel:labels.before, statusElement:$('status'), duration:800,
  presentValue:v => Math.round(v*10)/10,
  aggregate:v => v.A+v.B, // 本例数量可加，实际先核对口径
  render:f => {
    $('bar-a').setAttribute('width', f.values.A/40*320); // 两期统一 0–40 尺度
    $('bar-b').setAttribute('width', f.values.B/40*320);
    $('val-a').textContent = f.values.A.toFixed(1);
    $('val-b').textContent = f.values.B.toFixed(1);
    $('total').textContent = f.summary.toFixed(1);
  }
});
for (const key of ['before','after']) $(key).addEventListener('click', () => {
  for (const k of ['before','after']) $(k).setAttribute('aria-pressed', String(k===key));
  motion.set(states[key],labels[key]);
});
// 导出时：motion.withStableFrame(() => { 从最新目标状态读取图表、数值并执行导出; });
// 不再使用该图时：motion.destroy()，解除监听。
</script>
```

`presentValue` 仅对中间帧统一精度；稳定帧保留原始值。案例为减少视觉跳动格式化为一位小数，换数据应保留能够正确判断阈值的精度；中间值不能宣称是实测。当前组件仅处理固定成员的有限数值；拒绝 null 与成员变化，不会为你推导分母、单位、坐标轴、焦点或业务分类。它自带运行中减少动态及打印前收敛，导出在 `withStableFrame` 的同步回调内读取稳定图、表与数值；用户交互仍由作者验证。CSS 或 Web Animations 自行实现时，运行中偏好改变需处理该图表所属的活动动画；不能只依赖初始媒体查询。

**交付前检查**：独立无头浏览器或录屏检查真实页面起点、中点、终点、快速反向、初始和运行中减少动态、键盘焦点；在浏览器派发偏好 change 事件后及下一帧取样，别把事件前瞬时状态当成失效。看图形和数值是否同帧、插值是否误认成事实、筛选摘要是否与目标口径一致、导出与打印是否稳定。可按 [动效探针](production-gate.md) 的配置运行 `node <skill目录>/scripts/motion_probe.cjs <配置.json> <证据目录>`，或进行等效实测；工具记录不能替代业务判断。
