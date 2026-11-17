# 零售脉搏 · 三幕交互动效展示

自包含 `index.html` 可直接离线打开。所有数据为原创合成演示，不是用户真实业绩或质量评分。

- 增长轨迹：固定 4 月基线，所选月份同对象条长与近似数字同帧过渡。
- 收入结构：三个互斥渠道在同一金额尺度内移动边界，保持段与段相接。
- 门店位次：新港 95→194→268 万元，对应第 5→第 2→第 1；复用 RetainedRows 保留 DOM 身份、焦点与行位移，内部营收数值由 ChartMotion 独立同帧更新，不从零重播。

初始不自动播放。播放/暂停、手动月份与场景、筛选/排序可随时操作。初始与运行中减少动态均即时收敛并停止自动播放。

## 重建

在技能仓库根目录执行：

```sh
python examples/motion-showcase/build_showcase.py --skill-root .
```

构建器从该技能的 `assets/chart-motion.js`、`assets/retained-motion.js`、`assets/retained-rows.js` 内联完整脚本，保留许可头。不是任意业务数据的通用制图器；本例数据、布局及尺度需一起核对。

## 录制接口

页面参数：`?scene=growth|mix|stores&period=0|1|2`。

```js
showcase.setScene('growth');
showcase.setPeriod(0);
showcase.setPeriod(1);
showcase.setPeriod(2);
showcase.setScene('mix');
showcase.setScene('stores');
showcase.setFilter('high'); // 营收≥180万元
showcase.pause();
```

也可以点击 `#sortToggle` 切换原始顺序/营收排序。API操作仍经过真实运行时；没有伪造动画中间帧的seek入口。`showcase.finish()`用于稳定截图/导出，不用于假装连续动效。

## 已验证

`verify.cjs` 完成 37 项真实无头 Edge 检查：单文件离线、业务合计、首帧无目标闪回、真实中间帧、快速反向、初始与运行reduce、堆叠无缝、行第5→第1、DOM身份、同值不重播、退出焦点、播放暂停、三幕720×1280取景及基本390px无横溢。另已实际查看1440桌面与三幕720竖向截图。

```sh
node examples/motion-showcase/verify.cjs
```

需要已安装的 `playwright`，或通过 `PLAYWRIGHT_MODULE` 指向已有安装。检查不代表跨浏览器全覆盖、完整无障碍认证或95分评分。保留实际数据与测试证据；页面发布由协调者处理。
