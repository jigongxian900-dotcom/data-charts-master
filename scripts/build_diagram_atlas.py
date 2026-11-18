"""Build the fully offline diagram atlas from original source examples."""
from argparse import ArgumentParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SCRIPTS = {
    "__CHART_MOTION__": "chart-motion.js",
    "__ATLAS_DATA__": "diagram-atlas-data.js",
    "__ATLAS_RENDER__": "diagram-atlas-render.js",
}


def build(output):
    html = (ASSETS / "diagram-atlas.html").read_text(encoding="utf-8")
    for token, name in SCRIPTS.items():
        source = (ASSETS / name).read_text(encoding="utf-8")
        html = html.replace(token, source.replace("</script", "<\\/script"), 1)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8", newline="\n")

if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "examples" / "diagram-atlas" / "index.html")
    build(parser.parse_args().output)
