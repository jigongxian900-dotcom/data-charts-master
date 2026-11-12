# 54 charts · seven palettes

Open [atlas.html](atlas.html). Default: ruby red KPI cards with sparklines and year/month comparisons.

All values are original synthetic demonstration data. Every case includes its business question, units, period, scope and limitations. View the table or export the current JSON/SVG. Regional filtering in the operating overview updates the same-source chart, table and downloads.

Rebuild from repository root:

```sh
node examples/dashboard-atlas/build_atlas.js
```

The generator reads `assets/color-system.json` and `extension-charts.js`. This is a curated atlas, not an arbitrary-data charting library. Replace all derived labels and scales when adapting a case.
