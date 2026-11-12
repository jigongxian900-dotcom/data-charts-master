# Use and adapt

Clone this repository and ask your agent to read the root `SKILL.md`. For reusable discovery, place this single folder in the custom-skill directory supported by your agent. Do not install duplicate copies.

Example prompt:

> Use data-charts-master. We need to compare actual performance with target and prior year. First check periods, units and denominators. Select the most useful chart for that decision. Build a self-contained HTML with the source table, a readable mobile layout and SVG export. Treat missing targets as unknown.

Use `docs/catalog.md` to find a curated example by business question. Copy its design only after recalculating derived values, title, labels, axes and notes.

The Python helper is separate and supports bar, line, stacked, waterfall, box and scatter. Its schema is in `references/html-delivery.md`. It uses only Python's standard library.

```sh
python scripts/chart_html.py validate examples/representative.json
python scripts/chart_html.py build examples/representative.json --out sample.html --theme mixue-ruby
```

This writes HTML and a sibling data JSON. Open the HTML locally. The atlas can export its current JSON/SVG or print one/all examples. Seven palettes preserve semantic roles. The dark palette uses a light print fallback.

The included gallery is Chinese-first. README and key usage notes are bilingual/English; this is not a fully translated English chart gallery.
