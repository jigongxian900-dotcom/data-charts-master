# ChartMotion 1.0.1

可选、无依赖的图表几何动效运行时。浏览器中将 `assets/chart-motion.js` 原文内联在 `<script>` 中，得到 `window.ChartMotion`；Node 中 `require('./chart-motion.js')`。文件本身不请求网络。不修改已有六类 helper 的默认行为，也不包含图型枚举或图表引擎。

## 最小接入

```js
const motion = ChartMotion.create({
  scene: { 'store-a': { x: 10, width: 120 }, 'store-b': { x: 10, width: 90 } },
  duration: 320,
  paint(scene, info) {
    // Map 的键是业务对象稳定 ID，不按数组下标匹配。
    for (const [id, g] of scene) {
      const element = marks.get(id); // 作者负责建立、删除标记。
      element.setAttribute('x', g.x);
      element.setAttribute('width', g.width);
    }
    // 作者同时更新坐标、定量读数；若不可同步，过渡中隐藏读数。
    quantitativeLabels.hidden = ['transition', 'cancelled'].includes(info.phase);
  },
  onStart(visibleScene, targetScene, info) { /* 作者处理单位/轴/度量语义 */ },
  onSettled(scene, info) { /* 作者更新最终标签、同源表、摘要等 */ }
});
motion.to(nextScene, { meta: { metric: 'author-defined', unit: 'author-defined' } });
const svg = motion.withStableFrame(() => document.querySelector('svg').outerHTML);
motion.destroy();
```

`create()` 同步绘制一次初始场景。`paint` 为必须项。回调拿到的场景均为副本，内部几何不会因作者修改回调参数而变化。`meta` 是作者对象，运行时不解析、不改写，也不保证深复制。

## 输入与插值合同

- 场景输入为 `Map<string, geometry>` 或普通对象。ID 是非空稳定字符串，顺序变化不影响对象对应。输出快照统一为 `Map`。
- geometry 支持有限数值、静态字符串/布尔值/null，以及由这些值组成的密集数组和普通对象；对象副本使用无原型对象。不能传 DOM 节点、Date、函数、undefined、稀疏数组或循环引用；NaN/Infinity 拒绝。
- 默认只插相同结构内的数值。对象属性顺序可变化；属性集合、数组长度和静态值须兼容。插值为线性数值插值，可传 `ease(t)`，返回值必须有限并限制在 0–1。
- SVG `d` 字符串仅在两端相同时保留原样。变化的路径、字符串或结构默认抛错，**不会解析数字后盲 morph**。作者可提供显式 `interpolate(from, to, easedT, id, context)`，或先完成淡出等阶段再创建另一结构。自定义插值结果仍须是有效几何。
- `interpolate` 收到独立几何副本；`context` 含原始 `progress`、`meta`、该 ID 的 `entering`、`exiting`。自定义几何的拓扑和业务有效性由作者负责，运行时只查支持的值及有限数。
- 默认增删 ID 在过渡起点立即切换，新增值立即处于目标几何，删除值立即退出；不把第 N 项对应到另一对象。连续进入可传 `enter(id, targetGeometry)` 返回起始几何；连续退出可传 `exit(id, currentGeometry)` 返回退出目标。退出 ID 在完成时移除。钩子不得依赖数组下标，宜保持纯计算。
- 新请求先验证目标与兼容性，再取消旧动画。无效目标不会中断已有动画。duration 必须为非负有限数；0、相同场景或 reduced motion 均同步稳定，不排帧。

## API

| API | 行为 |
|---|---|
| `create({scene, paint, duration=320, ease, interpolate, enter, exit, meta, onStart, onSettled, environment})` | 创建独立控制器并绘制初始场景 |
| `to(scene, settings={})` / `transition(...)` | 设置新目标，返回控制器。settings 可覆盖 duration/ease/interpolate/enter/exit/meta |
| `snapshot()` | 返回最近实际传给 paint 的几何副本；包含尚在退出的 ID |
| `target()` | 返回最近合法 to 的目标副本；cancel 保留该目标，不含最终会删除的 ID |
| `isRunning()` | 当前是否有动画任务 |
| `cancel()` | 冻结已画帧、取消排帧，保留最近合法目标；活动任务存在时同步 paint cancelled，不发 onSettled |
| `finish(reason='finish')` | 同步画到最近合法目标并发 onSettled，包括此前 cancel 暂停的目标；没有待完成目标时只返回快照。回调可重入创建新动画 |
| `withStableFrame(callback)` | 先同步完成目标，再同步执行导出 callback(snapshot)，返回其结果；范围内重入的 to 也同步稳定。若作者回调再次取消并留下待完成目标，抛错并拒绝导出；只包同步读出，异步操作须先在 callback 内取出 SVG/数据 |
| `destroy()` | 取消排帧、失效旧回调、移除媒体及 print 监听；可重复调用。之后 to/finish/cancel/withStableFrame 抛错，snapshot/target 仍可读取 |

`info` 含 `phase`（start/transition/settled/cancelled）、0–1 `progress`、`reason`、`meta`、`entering`/`exiting` ID 数组。`onStart` 在动画/即时稳定前触发；`paint` 可同步重入 to/cancel/finish/destroy，旧帧不会覆盖新任务，旧 settled 回调会跳过。作者回调异常会向调用方抛出，当前任务停止，合法目标仍保留供 finish 恢复；已经由重入创建的替代任务保留。不得在每次 onSettled 无条件递归 to，否则作者代码自身会无限递归。

cancelled 表示冻结的可见几何，可能是半帧，不代表原目标业务值已达成。作者须按当前几何重算读数或继续隐藏，不能在 cancelled 时恢复目标值标签。snapshot 保持半帧，target 保留最近合法目标。随后 finish、withStableFrame、beforeprint 或运行时 reduced motion 都会同步落到该目标并恢复 settled 状态。新的 to 仍从可见半帧接续，并替换待完成目标。isRunning=false 只表示没有排帧任务，不表示取消前目标已达成。

## 连续、可访问性与导出

- 每个中间几何实际 paint 后都保存为 current。快速反向从该帧接续；同时取消 RAF 并使用 generation 失效旧回调，防 RAF 取消竞态。
- 自动读取 `prefers-reduced-motion: reduce`，监听运行时变化。变为 reduce 时立即完成目标；变回 no-preference 后新请求可继续动画。
- 自动监听 beforeprint，使用稳定帧包装同步完成动画；afterprint 重新绘制当前屏幕场景。不改筛选、视角、业务数据，不恢复到打印前的半帧。
- SVG 导出使用 `withStableFrame`；只调用 finish 时，onSettled 作者回调仍可能合法开启另一动画，因此包装导出更稳妥。
- 确定性测试可注入 environment `{ now, requestFrame, cancelFrame, mediaQuery, eventTarget }`。生产浏览器默认使用原生时钟、RAF、媒体查询与 window。

## 焦点辅助

```js
ChartMotion.preserveFocus(controlsRoot, () => renderControls());
// 或拆开：
const saved = ChartMotion.captureFocus(controlsRoot);
renderControls();
ChartMotion.restoreFocus(controlsRoot, saved);
```

给控件设置唯一 `data-focus-key`，用同一业务 ID 保持语义；重绘前后次序可以变化。捕获/恢复包括文本选择位置，focus 使用 preventScroll。找不到、禁用或出现重复键时返回 false，不按索引猜。可给 captureFocus(root, attribute) 指定另一属性。辅助函数不处理异步重绘、影子 DOM 内部焦点或控件消失后的业务替代焦点。

## 已验证与边界

行为单测 32/32 通过；真实无头 Edge 验证中间帧、反转、焦点与文本选区、重复 focus-key、动态 reduced motion、取消后稳定导出/打印、print 事件、SVG 稳定读出、零远程请求和零页面错误。浏览器截图已实际查看。PDF 用真实浏览器 printToPDF 导出，未声称系统实体打印机验收。

这是一套可复用动效机制。tooltip、刷选、筛选、表格、单位、轴、语义标签、标记增删 DOM 与数据完整性仍由作者定义；不保证任意图型或路径可直接变形，也不以本夹具代替新业务产物验收。
