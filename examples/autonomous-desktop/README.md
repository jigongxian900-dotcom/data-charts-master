# 三个桌面分析作品

全部采用原创合成数据。它们展示独立业务问题的完整处理过程，不是三个图型模板或通用 JSON 引擎。

| 作品 | 要完成的判断 |
|---|---|
| [应收与跨主体收款核对](receivables-reconciliation/README.md) | 区分未收、未核销、争议与汇兑，追查多对多核销 |
| [商业街铺位的整体安排](tenant-unit-allocation/README.md) | 比较完整安排的预估贡献与最差志愿 |
| [复合诉求与联合办理](civic-request-overlap/README.md) | 按独立请求与完整标签集合核对交集和办理负荷 |

在仓库根目录运行 `python scripts/rebuild_desktop_examples.py`。每例也可进入其目录运行 `python producer.py`。页面离线可读，制作器只依赖 Python 标准库。每例的 `provenance.json` 区分冻结原件和许可/换行调整后的公开派生，不声称整文件原字节相同。
