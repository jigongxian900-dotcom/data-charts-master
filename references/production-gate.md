# 生成入口与产物门禁

这是工程检查，不是业务正确、完整交互或审美评分。默认不降低要求来制造通过。

## 有界生成

已预聚合、明确适配时：
`python scripts/bounded_build.py request.json NEW_OUTPUT_DIR --skill-dir SKILL_DIR --preflight scripts/artifact_preflight.cjs --contract contract.json`
请求为 `{"intent":"ranking-states","payload":{...}}`。intent支持ranking-states、attainment-states、metric-cards、svg-scenes，payload分别遵循motion_builder、KPI builder或scene_html原契约。svg-scenes只支持已核算的矩形/圆/线场景，不自动聚合业务数据。不处理自然语言选图、聚合或联接。未知意图返回custom_required，不是完成；继续自主设计。退出0也仅证明所选工程门禁，release_ready仍为false，必须读图与核验业务。

## 每份自定义HTML也做

`node scripts/artifact_preflight.cjs --html index.html --out preflight.json --contract contract.json`
需Node和Playwright，可用PLAYWRIGHT_MODULE指定已安装模块。独立无头Edge，不使用桌面鼠标键盘。示例contract：
```json
{"rapidSelectors":["#periodA","#periodB"],"requireControls":true,"settleMs":700}
```
选择真实可逆操作，不用无关按钮替代；没有按钮的作品或select操作，用等价专用探针留下证据，不能谎称已测。可为明确的详情对话框焦点转移设置focusTargets；不能用来掩盖焦点丢失。

默认检查：初始及按钮Enter后的pageerror/console.error、焦点连续、ARIA引用存在、快速反向、初始及运行reduce的CSS/WAAPI状态。退出1表示失败/必测未覆盖，退出2是工具不可用。先修再复跑；如受执行环境限制如实记录，不能只看截图就说通过。重绘SVG保留title/desc和稳定ID，重建可交互节点时恢复同一对象焦点。

## 不在通用门禁里的必须补

select/input/链接/动态新控件、数据答案、canvas/rAF真实几何、所有业务状态不由此自动证明。专用探针至少检查业务所需操作/复原及数值、轴、标签同源；可比对象变化取起中终帧、打断和反向，不能仅查CSS声明。首屏reduce不从零尺寸闪入；未变对象和重复当前选择不重播入场。跨单位/不可比对象用即时或分层切换，不强行插值。

主图仍需实看截图：并列对象不靠完全重叠的标记隐藏，紧邻标签可读，必要比较共同可见，结论回答每个要求的期间/对象。修复工程错误不是提高视觉分数的替代。
