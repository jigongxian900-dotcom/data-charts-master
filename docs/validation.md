# Public-release validation

## v5.3.0 / 2026-11-17

本轮9题的主评和交叉复评逐题通过预先冻结的95分门槛。六道已知问题回归与三道陌生题首次交付分开记录。This is a scoped AI review of synthetic cases, not a universal score or independent human certification.

每格为主评 / 复评。两组结果各自须总分至少95，且业务、审美各至少19，数据至少14，交互至少24，动效至少19。任何硬失败、必修项或必测缺项都不能靠均分抵消。

| 场景 | 类别 | 业务 /20 | 审美 /20 | 数据 /15 | 交互 /25 | 动效 /20 | 总分 /100 |
|---|---|---:|---:|---:|---:|---:|---:|
| [配送排班](regression/intercity-delivery-scheduling.html) | 回归修订 | 20 / 20 | 19.5 / 19.5 | 15 / 15 | 25 / 25 | 20 / 20 | 99.5 / 99.5 |
| [双因素投放](regression/factorial-outreach-experiment.html) | 回归 | 20 / 20 | 19.5 / 19 | 15 / 15 | 25 / 25 | 20 / 20 | 99.5 / 99 |
| [易腐库存](regression/perishable-inventory-expiry.html) | 回归修订 | 20 / 20 | 19.5 / 19.5 | 15 / 15 | 25 / 25 | 20 / 20 | 99.5 / 99.5 |
| [招聘等待与负荷](regression/recruitment-waiting-load.html) | 回归修订 | 20 / 20 | 19.5 / 19.5 | 15 / 15 | 25 / 25 | 20 / 20 | 99.5 / 99.5 |
| [错误预算与时延](regression/service-error-budget-latency.html) | 回归修订 | 20 / 20 | 19.5 / 19.5 | 15 / 15 | 25 / 25 | 20 / 20 | 99.5 / 99.5 |
| [预约容量](regression/venue-booking-capacity.html) | 回归 | 20 / 20 | 19 / 19.5 | 15 / 15 | 25 / 24.5 | 20 / 20 | 99 / 99 |
| [应收核对](desktop/receivables-reconciliation.html) | 陌生题首次交付 | 20 / 19.5 | 19.5 / 19.5 | 15 / 15 | 25 / 25 | 20 / 20 | 99.5 / 99 |
| [租户与房源分配](desktop/tenant-unit-allocation.html) | 陌生题首次交付 | 20 / 20 | 19.5 / 19.5 | 15 / 15 | 25 / 25 | 20 / 20 | 99.5 / 99.5 |
| [市政请求与工作量](desktop/civic-request-overlap.html) | 陌生题首次交付 | 20 / 20 | 19 / 19.5 | 15 / 15 | 25 / 25 | 20 / 20 | 99 / 99.5 |

[完整逐题数值和指纹](benchmarks/em2-20261117.json) · [冻结量表](review-rubric.md) · [C3交付协议](review-protocol.md)

### 一次交付与保留的失败

三道陌生题只给执行者原始问题、数据、冻结技能和合同。一次用户请求可包含自主规划、制作、交付前独立实看及自修；不是只调用一次生成工具。首次正式提交前不接触外部评分或私有真值。六道回归允许同题修复，不能改称陌生题首次成功。

此前一组三道新输入的审美只有16.5–17/20，且有二维范围遗漏。本轮回归首评仍发现留白、注释密度与键盘恢复缺口。旧分、未验收记录和修订分别保留。最终按预先指定的版本合并，不挑历史最高分，不申请普适9.9分。

三名非作者评委分别主评业务与数据、审美、交互与动效。每个维度再由另一名非作者独立复核。真实桌面操作、中间几何、三轮中断、运行时减少动态及稳定出口有原始证据。有效的相同输入、代码、状态证据可复用，复评不等于重复执行每一条旧测试。

### 验证边界与过程记录

- 文件访问和独立上下文属于流程隔离，不是操作系统沙箱或真人外部认证。
- 旧四份业务报告未写未验收字段。11月17日另一位非作者核对原证据并补必要路径后，新增覆盖确认；旧成绩与日期未回填。
- 两题先做了原始数据复算，再把交互主评分写入冻结文件。另有一次评委在自身冻结后意外看到另一角色的同题摘要。相关记录保留，未据此改分，不声称全程完全盲法。
- 本轮以桌面为主。手机只基本可用，不认证全部移动交互、实际菜单缩放、全部浏览器或实体打印。
- 本轮验证HTML与SVG。历史Office证据不替代新PPTX编辑、保存及重开验证。
- 发布的是C3的5.3.0公开派生版。运行时只有许可注释变化；公开文案、路径和示例范围有整理。本地后续5.3.1地图等补丁保留，不继承本表评分。
- 九份公开HTML与评分原件的差异仅为明确的自有许可首行及换行。原始输入保留；派生数据相同。各例provenance同时给出评分原件和公开文件指纹。

### 可复跑的工程检查

发布包通过76项Python合同测试、32项动效行为测试、54例图谱校验。三道陌生题的制作器隔离重建通过；六道回归直接运行公开HTML源码并核对输入及派生值。九页公开派生默认冒烟无页面错误或远端运行请求。测试数量不计入审美评分。

```sh
python -m unittest discover -s scripts -p 'test_*.py'
node scripts/test_chart_motion.cjs
python scripts/rebuild_desktop_examples.py
python scripts/sync_regression_examples.py
node scripts/build_gallery.js
python scripts/verify_release.py
```

The 3 unfamiliar works and 6 regression works remain different evidence classes. These results do not predict arbitrary future inputs, market leadership, stars or paid conversions.

<details>
<summary>Retained historical 5.2 / 5.1 observations</summary>

## 5.2 composition candidate

Checked locally on 2026-11-13: all 76 behavioral tests passed, including 25 new custom-renderer and geometry tests. Default report, presentation and operating-story output was byte-identical to the 5.1.0 baseline. The 54-case release hygiene check also passed. These results verify contracts and compatibility; they do not score autonomous analysis or aesthetics.

The mechanism library records nine works: eight original static previews inspected, one curator-only case, no original interactions exercised. No third-party artwork, workbook or template is bundled.

Fresh-task production and independent review are separate acceptance gates. Historical scores are not inherited. Three fresh contexts completed two genuine compound/transformed encodings and one valid rejection of unsupported flow. Initial review failed the expanded layout and print-data retention checks. Two same-task technical repairs were independently retested at 320/390/1440; inputs, calculations, original planning and decisions remained byte-identical, with the first failures retained. Repairs are not new unfamiliar tasks.

Portable worked examples are in `examples/autonomy/`, mirrored under `docs/autonomy/`. Only file locations and provenance guards were adapted; all three rebuilt HTML and computed outputs match the reviewed artifacts byte for byte. [Reproduction hashes](autonomy/reproduction.json) bind these examples. These observations cover those task domains and mechanisms, not arbitrary chart mastery. New tests can be reproduced with `python scripts/test_custom_chart.py` and `python scripts/test_chart_geometry.py`; the existing continuous-check configuration remains unchanged.

## Retained 5.1 observations

Checked 2026-11-12 against the 5.1.0 release candidate. These are reproducible engineering checks and scoped browser observations, not external certification or user aesthetic acceptance.

| Check | Result | Scope |
|---|---|---|
| Python helper | 26 behavioral tests passed | Six kinds, missing/zero/tiny values, targets, decimal subtraction, compact geometry, readable ticks and offset-scale values |
| Report / presentation | Nine tests passed | Composition completeness, raw download equivalence, safe strings, standalone SVG and print/navigation structure |
| Coherent operating case | 16 tests passed | Derived arithmetic, risk labels and caveats, tiny nonzero display, unfamiliar metadata, partial coverage, null/zero, unchanged source, injection and output-path guard |
| Gallery / standalone SVG | 54 original cases, 54 SVGs, seven palettes passed | Finite geometry, self-contained structure, valid references and editable text; not a complete statistical audit |
| Responsive gallery | 324 combinations passed | 54 cases at widths 320, 375, 390, 430, 768 and 1440; nonempty chart and no page overflow |
| Interactive labs | 18 control-driven checks passed | Three actual SVG state changes at each of those six widths, with reduced motion |
| Theme, search and scope | Passed | Seven themes, empty search/reset, regional scope plus table/export synchronization |
| Compact report / presentation | Six default kinds checked at 320 and 390 | Dedicated compact geometry; 320 slide minimum actual SVG glyph size 12.799px; no detected text collision, SVG clipping or page overflow in these samples |
| Compact stress examples | Long Chinese labels, large numbers and target states checked | 320/390 report layouts; unbreakable numbers use labeled local panning rather than page overflow |
| Projection | Eight supplied pages at 1440×810 and 1280×720 | Figures, sources and caveats fit; arbitrary long inputs can require reading mode |
| Coherent operating report | Headless Edge at 320/390/1440 | Three chapters from eight raw rows; minimum actual SVG glyph 13.90px at 320; exact source download; no detected text collision or clipping |
| Empty-target state | Lab1 at 320/390/1440 | All targets missing produces a true compact state, not zero gaps; SVG export retains coverage and metadata |
| Screen / print restoration | Operating story from fresh pages at 320/390/1440 | Phone-start print keeps risk names and markers; actual PDFs retain eight circles, two diamonds and the full eight-row source table; screen view restores afterward |
| Package hygiene | Passed | Local paths, previews, source/host mirrors, synthetic-data declaration, neutral names and host-path/credential-pattern scan |

Gallery checks observed no remote runtime requests or page errors. Browser work used headless Microsoft Edge through a development-only Playwright setup; it did not take over the user's browser. Viewing and rebuilding do not need Playwright. README captures and GIFs show actual rendered examples and control-driven transitions.

Reproduce from the repository root with Python 3.10+ and Node.js 20+:

```sh
python scripts/test_chart_html.py
python scripts/test_compose_html.py
python scripts/test_operating_story.py
python scripts/compose_html.py examples/composed/source.json --mode report --theme ruby --out examples/composed/report.html
python scripts/compose_html.py examples/composed/source.json --mode slides --theme ruby --out examples/composed/slides.html
python scripts/build_operating_story.py
node scripts/build_gallery.js
python scripts/verify_release.py
```

The GitHub workflow repeats tests, regeneration, reproducibility and package checks. Online Pages delivery is checked after deployment; local observations alone do not prove remote publication. Agent installation routes follow the official documentation linked in the usage guide. Folder placement does not prove automatic discovery in every agent client.

No all-browser, all-device, full WCAG or every-input statistical guarantee is made. The public package contains HTML presentations and SVGs; it does not bundle a native-editable PPTX. Independent AI review is separate from human acceptance. Private scores are not external endorsements. Comparative observations do not prove universal superiority to another project.


</details>
