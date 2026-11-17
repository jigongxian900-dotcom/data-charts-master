# Capability boundaries / 能力边界

This public snapshot includes independently implemented HTML/SVG examples and synthetic data.

| Output | Included | Boundary |
|---|---|---|
| HTML atlas | 54 examples, seven palettes, local filtering and export | Curated examples; not a universal arbitrary-JSON chart engine |
| SVG | 54 standalone files | Text uses system fonts; rendering can vary by platform |
| Interaction labs | Three complete HTML files | Fixed synthetic scenarios; recompute all derived values when reusing |
| Report / presentation | Two runnable outputs from one validated source | Six generic chart kinds; supplied narrative; wide projection and narrow reading are separate |
| Python helper | Six generic chart types, explicit bar targets and 26 behavioral tests | Validate the schema before building; use declared performance direction for target status |
| Coherent operating case | One eight-market source, three linked views, 16 focused tests | Synthetic data; target gap is not resource priority; same-store denominator is unspecified |
| PPTX | Production guidance | Requires a separate authoring tool and real save/reopen verification; no claim that every chart datum is native-editable |
| Statistical figures | Distribution / interval examples | Synthetic samples and supplied intervals are not empirical evidence |

See [public validation](../docs/validation.md) for checks of this exact release. Internal review scores and private Office evidence are not included as public certification.

## 5.2.0自主组合的实证边界

- 新入口以作者生成函数扩展图内表达，不逐图扩展六类枚举。公共层检查三尺寸、完整原始字段、逐源行覆盖、源绑定与静态SVG；业务校验与几何编码仍由作者实现并通过实物检验。
- 线性/分类尺度、极坐标/扇区与层级分区是可复用数学部件。它们不自动选择图型，不推断业务分母，不把所有变形视为已掌握。
- 实现层保留旧51项测试并增加25项合同/数学测试，76项通过；旧report、slides和operating-story的默认重建与5.1.0基线逐字节相同。测试数量不计入审美或自主判断的得分。
- 灵感库含9件具体作品的原创机制分析，8件查看原作静态预览，1件仅策展正文/截图；原作交互均未实测。图型误称、量纲及超额表现等缺陷照实登记，不把优秀作品当无缺陷模板。第三方代码、模板、工作簿和图像不随库分发。
- 自主组合能力按冻结新题，由不同执行者只拿技能与输入制作，再交独立评审。熟悉样例、开放接口存在、旧评分均不能代替新题表现；同题修复后成绩与首轮陌生迁移证据分开。
- 以上不解除既有PPTX原生数据编辑限制，也不把HTML/SVG新图自动算作原生Office图表。需要该能力时仍须另作实际编辑、保存和重开验证。

## 5.3.0交互与动效的实证边界

增加可选的稳定ID几何运行时与分析交互设计路径。运行时提供可见帧接续、取消旧帧与回调、动态减少动态、同步目标导出和焦点辅助；不自动决定业务状态、单位、坐标和路径兼容性。

初始机制检查为32项Node行为测试与8组无头Edge夹具验证，覆盖真实中间帧、反转、取消后导出打印、运行时媒体偏好和焦点。取消后读数通知及半帧出口缺陷在冻结前修正，旧夹具记录保留。夹具和测试数量不证明新业务体验。

此前三题99/100仅保留为当时量表下的局部记录。扩大到六个不同业务问题时，另冻交互/动效重点量表与新输入，由独立执行者制作后匿名评审；报告逐题分数、最低值、必修、首次失败及修复，不把新旧权重的分数作优劣比较。新题尚未评审时，不预先宣称稳定或普适9.9分。

2026-11-17完成C3的六题回归与三题陌生输入评审。三角色主评及另一非作者交叉复核，逐题通过预先冻结的95分与各维门槛，必需缺项清零；保留首败和修订。陌生题允许交付前内部实看自修，已知题外部反馈后的修复只记回归。具体分数、限定公开差异和过程边界见[本版验证](../docs/validation.md)。本结论仅绑定5.3.0 C3公开派生版，不覆盖之后的本地5.3.1增量或任意未来输入。
