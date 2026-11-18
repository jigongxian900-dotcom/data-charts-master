"""Generate three ordinary-size, standalone layouts from one operating case."""
from argparse import ArgumentParser
from copy import deepcopy
import json
from pathlib import Path

from build_operating_story import display, make_spec
from compose_html import build


ROOT = Path(__file__).resolve().parents[1]


def layouts(raw):
    full, data = make_spec(raw)
    brief = deepcopy(full)
    gap = data["gaps"][0]
    brief["title"] = full["charts"][1]["title"]
    brief_summary = (
        f'{gap["name"]}差额最大，待核 {display(gap["gap"])} {raw["unit"]}。'
        if gap["gap"] is not None and gap["gap"] > 0 else
        "按市场核对实际与目标，保留缺报项。"
    )
    brief["charts"] = [full["charts"][1]]
    brief["composition"] = {
        "subtitle": raw["period"],
        "summary": brief_summary,
        "sections": [dict(full["composition"]["sections"][1], title="按市场核对差额")],
        "closing": "先复核差额最大的市场及其剩余可追回金额，口径以表内实际与目标为准。",
    }
    return {
        "brief.html": build(brief, reading="brief", theme="graphite", brand_accent="#923C38"),
        "report.html": build(full, reading="editorial", theme="graphite", brand_accent="#3A596D"),
        "slides.html": build(full, mode="slides", theme="graphite", brand_accent="#6B4B70"),
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "examples" / "operating-story" / "input.json")
    parser.add_argument("--output", type=Path, default=ROOT / "examples" / "report-layouts")
    args = parser.parse_args()
    raw = json.loads(args.input.read_text(encoding="utf-8-sig"))
    args.output.mkdir(parents=True, exist_ok=True)
    for name, report in layouts(raw).items():
        (args.output / name).write_text(report, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
