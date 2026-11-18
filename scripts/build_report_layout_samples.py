"""Generate three ordinary-size, standalone layouts from one operating case."""
from argparse import ArgumentParser
from copy import deepcopy
import json
from pathlib import Path

from build_operating_story import display, make_spec, names, percentage
from compose_html import build


ROOT = Path(__file__).resolve().parents[1]


def layouts(raw):
    full, data = make_spec(raw)
    brief = deepcopy(full)
    unit = raw["unit"]
    date = raw["period"].split("对比", 1)[0]
    first = data["gaps"][0]
    gap = data["gap"]
    growth = data["growth"]
    metric = raw.get("same_store_metric", "同店指标")
    attainment = percentage(data["actual"], data["target"])
    gap_title = ("营业额目标达成情况" if gap is None else
                 f"营业额距目标差 {display(gap)} {unit}" if gap > 0 else
                 f"营业额超目标 {display(-gap)} {unit}" if gap < 0 else "营业额达到目标")
    gap_summary = ("本期有市场尚未报齐，先核对已有目标与实际。" if gap is None else
                   f'{first["name"]}差额最大，{display(first["gap"])} {unit}。'
                   if first["gap"] is not None and first["gap"] > 0 else "各市场的实际与目标见下图。")
    origin = f'{names(data["top"])}合计贡献 {display(data["top_value"])} {unit}' if data["top"] else "各市场营业额增减"
    if data["top_share"] is not None:
        origin += f'，占净增量 {display(data["top_share"], "%")}'
    focus = [f'{row["name"]}{metric}同比 {display(row["sameStoreGrowth"], "%")}' for row in data["risk"]]
    focus_text = "，".join(focus) + "。" if focus else f"已知市场中，未见总额增长而{metric}下降。"
    source = f'经营台账 · {data["n"]} 个市场' if raw["synthetic"] else raw["source"]
    metrics = [
        {"label": "目标达成率", "value": display(attainment, "%")},
        {"label": "本期营业额", "value": display(data["actual"]), "unit": unit},
        {"label": "营业额目标", "value": display(data["target"]), "unit": unit},
    ]
    action = (f'先复核{first["name"]}的目标差额，再按门店查看同店和订单变化。'
              if first["gap"] is not None and first["gap"] > 0 else "按市场复核目标与同店表现。")
    gap_share = percentage(first["gap"], gap) if gap is not None and gap > 0 else None
    gap_annotation = gap_summary
    if gap_share is not None and first["gap"] > 0 and gap_share <= 100:
        gap_annotation = f'{display(first["gap"])} {unit}，占区域净差额 {display(gap_share, "%")}。'
    growth_chart, _, same_store_chart = full["charts"]
    if growth_chart["kind"] == "waterfall":
        growth_chart["rows"][0]["label"] = "上年同期"
        growth_chart["rows"][-1]["label"] = "本期"
    scope_title = f'{len(data["risk"])} 个市场总额增长，{metric}下降'
    if data["scatter_n"] < data["n"]:
        scope_title = f'已报市场中，{scope_title}'
    same_store_chart.update(title=scope_title, y_unit=f"{metric}同比（%）")
    story = {
        "growth-contribution": {"nav": "营业额增量", "title": "上年同期至本期营业额变化",
                                "headline": f'营业额净增 {display(data["change"])} {unit}' if data["change"] is not None and data["change"] > 0 else full["charts"][0]["title"],
                                "caption": "各市场增量按本期营业额减上年同期营业额计算。"
                                           if data["growth_n"] == data["n"] else f'两期均有记录的市场为 {data["growth_n"]}/{data["n"]}。',
                                "callout": origin + "。"},
        "target-gap": {"nav": "目标缺口", "title": "各市场目标差额", "headline": gap_title,
                       "caption": "差额＝营业额目标－本期营业额。"
                                  + (f'有成对记录的市场为 {data["gap_n"]}/{data["n"]}。' if data["gap_n"] < data["n"] else ""),
                       "callout": gap_annotation},
        "growth-same-store": {"nav": "同店表现", "title": f"全量营业额同比与{metric}同比",
                              "headline": full["charts"][2]["title"], "caption": "同店指两期均营业的相同门店。"
                                         + (f'有成对记录的市场为 {data["scatter_n"]}/{data["n"]}。' if data["scatter_n"] < data["n"] else ""),
                              "callout": focus_text},
    }
    if first["gap"] is not None and first["gap"] > 0:
        story["target-gap"].update(key_label=f'{first["name"]}目标差额',
                                  key_reading=f'{display(first["gap"])} {unit}')
    if 1 <= len(data["risk"]) <= 2:
        story["growth-same-store"].update(
            key_label=" / ".join(row["name"] for row in data["risk"]),
            key_reading=" / ".join(display(row["sameStoreGrowth"], "%") for row in data["risk"]))
    brief["title"] = gap_title
    brief["charts"] = [full["charts"][1]]
    brief["composition"] = {
        "summary": gap_summary,
        "sections": [{"title": "目标差额", "charts": ["target-gap"]}],
        "closing": action,
        "audience": {"edition": "经营简报", "date": date, "source": source, "action_label": "下次复盘",
                     "metrics": metrics, "figures": {"target-gap": story["target-gap"]}},
    }
    full["title"] = (f"营业额同比增 {display(round(growth,1), '%')}，距目标差 {display(gap)} {unit}"
                     if growth is not None and growth > 0 and gap is not None and gap > 0 else gap_title)
    full["composition"] = {
        "summary": (f'{names(data["risk"])}总额增长，{metric}仍下降。' if focus else "分市场复核增长、目标差额和同店表现。"),
        "closing": action,
        "sections": [{"title": origin, "layout": "sequence", "charts": ["growth-contribution"]},
                     {"title": f'{first["name"]}目标差额最大' if first["gap"] is not None and first["gap"] > 0 else "各市场目标差额",
                      "layout": "feature", "charts": ["target-gap"]},
                     {"title": full["charts"][2]["title"], "layout": "feature", "charts": ["growth-same-store"]}],
        "audience": {"edition": "月度经营回顾", "date": date, "source": source, "action_label": "下次复盘",
                     "metrics": metrics, "figures": story},
    }
    return {
        "brief.html": build(brief, reading="brief", theme="graphite", brand_accent="#923C38", delivery="final"),
        "report.html": build(full, reading="editorial", theme="graphite", brand_accent="#3A596D", delivery="final"),
        "slides.html": build(full, mode="slides", theme="graphite", brand_accent="#3A596D", delivery="final"),
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "examples" / "operating-story" / "input.json")
    parser.add_argument("--output", type=Path, default=ROOT / "examples" / "report-layouts")
    args = parser.parse_args()
    raw = json.loads(args.input.read_text(encoding="utf-8-sig"))
    if args.input == ROOT / "examples" / "operating-story" / "input.json":
        raw.setdefault("same_store_metric", "同店营业额")
    args.output.mkdir(parents=True, exist_ok=True)
    for name, report in layouts(raw).items():
        (args.output / name).write_text(report, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
