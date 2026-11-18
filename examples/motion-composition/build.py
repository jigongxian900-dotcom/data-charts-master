"""Build the self-contained motion composition sample."""
from argparse import ArgumentParser
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def build(out):
    parts = {
        "MOTION": (HERE.parents[1] / "assets" / "chart-motion.js").read_text(encoding="utf-8"),
        "DEMO": (HERE / "demo.js").read_text(encoding="utf-8"),
    }
    template = (HERE / "template.html").read_text(encoding="utf-8")
    out.write_text(re.sub(r"@@([A-Z]+)@@", lambda match: parts[match.group(1)], template), encoding="utf-8")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "index.html")
    build(parser.parse_args().out)
