# One source, two original reading outputs

Open `report.html` for the editorial report or `slides.html` for the HTML presentation. Both run offline and use `source.json`: 6 charts, 61 synthetic observations, including explicit missing values, zero, negative values, reconciled increments and an outlying observation. They are demonstrations, not real business records.

The report uses a wide trend with side notes, a direct scale/composition pair, a full-width arithmetic bridge, and a distribution/association pair. Each section's explanation is supplied in `source.json`. The paired examples have different measures; their section text explicitly separates their questions rather than implying one explains the other.

```sh
python scripts/compose_html.py examples/composed/source.json --mode report --theme ruby --out examples/composed/report.html
python scripts/compose_html.py examples/composed/source.json --mode slides --theme ruby --out examples/composed/slides.html
python scripts/test_compose_html.py
```

Run these commands from the repository root. Python standard library only. Changing a row and rebuilding changes the plotted geometry, data table, inline source and downloadable source. If the row participates in a validated numeric claim, update that author-declared claim too; incorrect claims fail validation.

Slides offer buttons, keyboard navigation, cover links, touch swipe, overview and printing of all pages. Trends/waterfalls use a full-width chart, comparisons use a side note, and distributions/associations put evidence beneath the main chart. Wide screens use a 16:9 minimum canvas; long content expands and phone screens stack. The expandable “资料与导出” control contains full JSON, each static SVG and the same-source tables. Print-to-PDF uses your browser. This is not a native editable PowerPoint deck.

On desktop, “聚焦投影” removes the outside interface and fits the chart, provenance and notes into the available viewport. “返回阅读” restores full vertical reading. The supplied deck was checked at 1440×810 and 1280×720. Longer input can require reading mode; a projection warning appears if content overflows or chart text would shrink below 12 pixels.

See `references/composed-outputs.md` for the optional composition schema, data-transfer contract and limits.
