# Original composed outputs

`scripts/compose_html.py` turns the same validated chart input into an offline reading report or HTML presentation. It uses the six original renderers in `chart_html.py`: bar, line, stacked, waterfall, box, scatter. It does not add a renderer for every chart in the visual atlas.

```sh
python scripts/compose_html.py examples/representative.json --mode report --out report.html --theme ruby
python scripts/compose_html.py examples/composed/source.json --mode slides --out slides.html --theme ruby
python scripts/test_compose_html.py
```

No installation, network, remote fonts, assets, or third-party libraries are needed. Open the generated HTML directly in a modern browser. Both modes contain their full source JSON and per-chart data tables. The download link works without JavaScript. The original `source.json`, report and slides in `examples/composed/` share the same parsed source object and SHA-256. JSON download uses canonical formatting; `--source-out delivered-source.json` additionally copies the original input bytes exactly.

## Narrative contract

The base chart contract is unchanged. Optional `composition` supplies author-written report hierarchy:

```json
{
  "composition": {
    "subtitle": "Author-supplied subtitle",
    "summary": "Author-supplied executive summary",
    "sections": [
      {
        "title": "Author-supplied question or conclusion",
        "intro": "Author-supplied context and evidence boundaries",
        "layout": "feature",
        "charts": ["trend"]
      }
    ],
    "closing": "Author-supplied closing note"
  }
}
```

Every source chart must appear exactly once across sections. `feature` uses a side note and a wide chart. `comparison` requires two charts and places them directly alongside each other; it does not claim their units, denominators or scales are comparable. `sequence` gives charts the full reading width. On narrow screens, all arrangements stack. Without composition metadata, each chart becomes a question-led section. No numerical headline, business claim, causal explanation or recommendation is invented. Numeric `claims` retain the base renderer's validation.

Slides contain a cover with a jump index, then one chart per reading page in input order. Trends and waterfalls use full-width chart reading, comparisons use a side note, and distributions/associations use a main chart with a bottom evidence strip. Source titles, questions, notes and provenance remain visible. The wide-screen page uses a 16:9 minimum reading canvas. Long content increases page height instead of being clipped; it is not a fixed-size slide-authoring engine. Narrow screens stack text and chart in reading order. Screen provenance and unit text are at least 12 CSS pixels.

## Controls and data transfer

- Previous / next buttons; left/right arrows, PageUp/PageDown, Home/End; Escape toggles overview. Navigation does not intercept focused links, buttons, summaries or form fields.
- Touch swipe changes page only for a predominantly horizontal gesture. Vertical scrolling remains available. Tables and controls do not initiate swipe navigation.
- Overview shows all pages. The cover index jumps to a specific question. Without JavaScript, all pages remain visible.
- Presentation data tables, static SVG downloads and full JSON download are collected in one expandable “资料与导出” control above the stage. Page content contains reading material and provenance. No export tools are repeated inside chart pages.
- “聚焦投影” switches wide screens to the actual available viewport: outside headers, resource tools and footer disappear, while the main chart, source, units and missing-data notes remain. “返回阅读” restores the full reading layout. Phones automatically use vertical reading. If long content overflows or actual SVG glyph size falls below 12 pixels, a visible message asks the reader to use reading mode. Arbitrary input is not promised to fit one projected screen.
- Print uses every page, including pages hidden by current navigation, and restores navigation afterward. Browser print can save PDF; this is not an independent PDF authoring engine. Print omits expanded raw tables; the attached/downloadable JSON and screen tables preserve them.
- Every chart has a static standalone SVG download with resolved theme colors, labels and system fonts. Full provenance remains next to the chart in HTML. SVG carries an accessible provenance description and the exact chart object, including null rows, in XML metadata; it does not reproduce the visible HTML source footer.
- Null remains missing, not zero. Line gaps, negative values, stack denominators, waterfall reconciliation and box observations use the base renderer unchanged.
- Source and ledger JSON escape `<`, `>` and `&` before embedding. Visible strings are HTML-escaped. A title containing `</script>` remains inert and survives source download.
- There is no motion dependency. Reduced-motion explicitly removes animation and transitions. Reopening offline restores the complete artifact; no service or account is required.

## Boundaries

Phones use a separate compact SVG layout rather than shrinking the desktop canvas. The compact waterfall shows changes on a shared contribution scale and states the start, end and net change as text; it is explicitly labeled as a contribution view rather than a cumulative bridge. Long unbreakable labels can use clearly indicated local panning. The original input and desktop SVG download remain intact. Inspect actual on-screen type size, not only SVG font declarations.

HTML presentation is the delivered format. This composer does not produce native editable PPTX, promise exact print pagination for arbitrary long text, or support all 54 atlas chart types. Renderer density limits still apply. Long figure labels can require a different chart, fewer categories, or the included data table. Authors still review factual claims, cross-chart comparability and the final reading/projected layout. The supplied six-chart deck was checked page by page in projection at 1440×810 and 1280×720; that result is not a guarantee for a different input.

The focused tests verify parsed JSON download equivalence, standalone SVG XML, changed-value geometry, missing-data semantics, unsafe text roundtrip, composition completeness and generic-contract operation. Independent browser checks should verify actual desktop/mobile geometry, navigation, offline behavior and printing; a Python test passing is not visual acceptance.
