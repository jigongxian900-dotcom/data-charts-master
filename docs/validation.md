# Public-release validation

Checked 2026-11-12 against this public snapshot, after replacing the three development comparison datasets with original synthetic values.

| Check | Result | Scope |
|---|---|---|
| Python helper | 14 behavioral tests passed | Missing values, tiny nonzero values, numeric contracts, scale/label/color behavior |
| Gallery build | 54 cases / seven palettes | Node generator; HTML, source JSON and SVG |
| SVG structure | 54 passed | Self-contained structure, valid references, finite geometry and editable text; not a complete visual or data audit |
| Desktop browser | 54 passed | Microsoft Edge headless, 1440×1100; nonempty chart and no page overflow |
| Phone browser | 54 passed | 390×844 touch context, reduced motion; no page overflow |
| Theme switching | Seven passed | Chart remains available in each palette |
| Regional filter | Passed | Operating overview scope and rows update together |
| SVG / JSON exports | Passed | Current regional selection preserved; downloaded JSON row count matches active case |
| Target-ring states | Passed | Above target, below target, unknown target and zero target; undefined ratios are not shown as zero |
| Search | Passed | No-result state and reset to all 54 examples |
| Keyboard / print | Basic checks passed | Focus can move to controls; chart remains visible in print media |
| Offline runtime | Passed | No external requests or page errors observed while checking the gallery |
| Publication package | Passed | Local Markdown links, synthetic-data declaration, host-path/credential-pattern scan |

Reproduce the deterministic checks from the repository root:

```sh
python scripts/test_chart_html.py
node examples/dashboard-atlas/build_atlas.js
python scripts/verify_release.py
```

The GitHub workflow repeats behavioral, rebuild/reproducibility and package checks. Browser captures used a development-only Playwright/Edge setup; it is not required to view or rebuild the gallery. Preview assets show actual rendered examples.

This does not establish all-browser compatibility, full WCAG conformance, performance on every device, full keyboard coverage of every lab, or universal statistical correctness. The public release does not bundle a native-editable PPTX. Internal review scores are not presented as external certification.
