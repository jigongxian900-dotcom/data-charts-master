# Public-release validation

Checked 2026-11-12 against the 5.1.0 release candidate. These are reproducible engineering checks and scoped browser observations, not external certification or user aesthetic acceptance.

| Check | Result | Scope |
|---|---|---|
| Python helper | 26 behavioral tests passed | Six kinds, missing/zero/tiny values, targets, decimal subtraction, compact geometry, readable ticks and offset-scale values |
| Report / presentation | Nine tests passed | Composition completeness, raw download equivalence, safe strings, standalone SVG and print/navigation structure |
| Coherent operating case | 16 tests passed | Derived arithmetic, risk labels and caveats, tiny nonzero display, unfamiliar metadata, partial coverage, null/zero, unchanged source, injection and output-path guard |
| Gallery / standalone SVG | 54 original cases, 54 SVGs, seven palettes passed | Finite geometry, self-contained structure, valid references and editable text; not a complete statistical audit |
| Responsive gallery | 324 combinations passed | 54 cases at widths 320, 375, 390, 430, 768 and 1440; nonempty chart and no page overflow |
| Interactive labs | 18 control-driven checks passed | Three actual SVG state changes at each of those six widths, with reduced motion |
| Theme, search and scope | Passed | Seven themes, empty search/reset, regional scope plus table/export synchronization |
| Compact report / presentation | Six default kinds checked at 320 and 390 | Dedicated compact geometry; 320 slide minimum actual SVG glyph size 12.799px; no detected text collision, SVG clipping or page overflow in these samples |
| Compact stress examples | Long Chinese labels, large numbers and target states checked | 320/390 report layouts; unbreakable numbers use labeled local panning rather than page overflow |
| Projection | Eight supplied pages at 1440×810 and 1280×720 | Figures, sources and caveats fit; arbitrary long inputs can require reading mode |
| Coherent operating report | Headless Edge at 320/390/1440 | Three chapters from eight raw rows; minimum actual SVG glyph 13.90px at 320; exact source download; no detected text collision or clipping |
| Empty-target state | Lab1 at 320/390/1440 | All targets missing produces a true compact state, not zero gaps; SVG export retains coverage and metadata |
| Screen / print restoration | Operating story from fresh pages at 320/390/1440 | Phone-start print keeps risk names and markers; actual PDFs retain eight circles, two diamonds and the full eight-row source table; screen view restores afterward |
| Package hygiene | Passed | Local paths, previews, source/host mirrors, synthetic-data declaration, neutral names and host-path/credential-pattern scan |

Gallery checks observed no remote runtime requests or page errors. Browser work used headless Microsoft Edge through a development-only Playwright setup; it did not take over the user's browser. Viewing and rebuilding do not need Playwright. README captures and GIFs show actual rendered examples and control-driven transitions.

Reproduce from the repository root with Python 3.10+ and Node.js 20+:

```sh
python scripts/test_chart_html.py
python scripts/test_compose_html.py
python scripts/test_operating_story.py
python scripts/compose_html.py examples/composed/source.json --mode report --theme ruby --out examples/composed/report.html
python scripts/compose_html.py examples/composed/source.json --mode slides --theme ruby --out examples/composed/slides.html
python scripts/build_operating_story.py
node scripts/build_gallery.js
python scripts/verify_release.py
```

The GitHub workflow repeats tests, regeneration, reproducibility and package checks. Online Pages delivery is checked after deployment; local observations alone do not prove remote publication. Agent installation routes follow the official documentation linked in the usage guide. Folder placement does not prove automatic discovery in every agent client.

No all-browser, all-device, full WCAG or every-input statistical guarantee is made. The public package contains HTML presentations and SVGs; it does not bundle a native-editable PPTX. Independent AI review is separate from human acceptance. Private scores are not external endorsements. Comparative observations do not prove universal superiority to another project.
