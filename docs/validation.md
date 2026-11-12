# Public-release validation

Checked 2026-11-12 against public version 5.0.1. This update also checks the generic palette identifiers, README previews, installation paths and narrow-screen interactions.

| Check | Result | Scope |
|---|---|---|
| Python helper | 14 behavioral tests passed | Missing values, tiny nonzero values, numeric contracts, scale/label/color behavior |
| Gallery build | 54 cases / seven palettes | Node generator; HTML, source JSON and SVG |
| SVG structure | 54 passed | Self-contained structure, valid references, finite geometry and editable text; not a complete visual or data audit |
| Responsive gallery | 324 combinations passed | 54 cases at widths 320, 375, 390, 430, 768 and 1440; nonempty chart and no page overflow |
| Interactive labs | 18 checks passed | Three actual control-driven SVG changes at each of those six widths, with reduced motion |
| Theme switching | Seven passed | Chart remains available in each palette |
| Regional filter | Passed | Operating overview scope and rows update together |
| SVG / JSON exports | Passed | Current regional selection preserved; downloaded JSON row count matches active case |
| Target-ring states | Passed | Above target, below target, unknown target and zero target; undefined ratios are not shown as zero |
| Search | Passed | No-result state and reset to all 54 examples |
| Controls / keyboard / print | Basic checks passed | Previous/next and data-table controls at six widths. Earlier focused checks covered keyboard focus and print visibility |
| Offline runtime | Passed | No external requests or page errors observed while checking the gallery |
| Publication package | Passed | Local links and preview paths, synthetic-data declaration, generic names and host-path/credential-pattern scan |

Reproduce the deterministic checks from the repository root:

```sh
python scripts/test_chart_html.py
node scripts/build_gallery.js
python scripts/verify_release.py
```

The GitHub workflow repeats behavioral, rebuild/reproducibility and package checks. Browser captures used a development-only Playwright/Edge setup. Viewing and rebuilding do not need that setup. Preview assets show actual rendered examples.

The README now groups examples by analytical use, shows two actual geometric interactions, and uses responsive picture sources for KPI/mobile previews. The GitHub page itself is checked after deployment. Agent installation locations follow the official documentation linked in the usage guide. Folder placement and sample generation checks do not prove automatic discovery in every agent client.

This does not establish all-browser compatibility, full WCAG conformance, performance on every device, full keyboard coverage of every lab, or universal statistical correctness. The public release does not bundle a native-editable PPTX. Internal review scores are not presented as external certification.
