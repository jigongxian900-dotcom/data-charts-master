"""Inline the gallery and its source data for offline viewing."""
from argparse import ArgumentParser
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def build(out):
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    parts = {
        "DATA": json.dumps(data, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c"),
        "MOTION": (HERE.parents[1] / "assets" / "chart-motion.js").read_text(encoding="utf-8"),
        "GALLERY": (HERE / "gallery.js").read_text(encoding="utf-8"),
    }
    template = (HERE / "template.html").read_text(encoding="utf-8")
    result = re.sub(r"@@([A-Z]+)@@", lambda match: parts[match.group(1)], template)
    out.write_text(result, encoding="utf-8")


if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("--out", type=Path, default=HERE / "index.html")
    build(p.parse_args().out)
