# One operating question, three views

This original composition follows one eight-market source through three linked business questions. It is a synthetic editorial specimen, not an actual operating report or proof that this layout suits every analysis. It does not replace the separate six-kind teaching report.

Open `report.html` directly. It is a single offline file with inline SVG, CSS, JavaScript, embedded original source and derived chart contracts. It does not load fonts, art, scripts or other remote assets. The design, layout and annotations are original; it reuses this repository's own `compose_html.py` and `chart_html.py`.

## Read the business question first

1. **Who contributed to growth?** A reconciled contribution bridge runs from prior revenue to current revenue. The hero uses the same two totals and one shared zero baseline. If any market lacks either revenue period, the bridge becomes an explicitly partial contribution bar; a complete growth total is not fabricated.
2. **How much remains to target?** A horizontal ranking shows `target − revenue` in the source currency unit. Positive values are shortfalls; negative values are excess. This ranks catch-up amounts, not investment priority. Resources, recoverability and remaining time are unavailable.
3. **Where should same-store performance be checked?** A scatter compares market-wide revenue growth with the supplied `sameStoreGrowth` percentage. Calculated growth-positive/same-store-negative points receive diamond outlines and adjacent names; other known points retain their positions and circles. The key definition and causation limits precede the plot on mobile and sit beside it on desktop. This prompts a definition and sample check; it does not establish new-store contribution, traffic changes or causation.

The three chapters use a full-width reconciliation, a side-by-side amount ranking and a plot with a separate evidence note. The typography and hierarchy remain consistent while the layout follows each task.

The same-store chapter's SVG download is explicitly labeled as the **base SVG without the page's emphasis annotations**. Its original points, values and scales are retained; the page adds the diamond outlines, leader lines and adjacent names after rendering. The downloadable base SVG and annotated page are not claimed to be visually identical.

The page also synchronizes these risk annotations when print media becomes active, including a phone-to-print transition. Returning to screen media keeps the original screen view. Printing the page and downloading its base SVG remain separate outputs.

## Source and arithmetic

`input.json` is an unchanged copy of the original eight synthetic market records in `examples/interaction-lab/spec.json`. Its exact period, source, currency unit and scope are retained in the report. The source labels the unit `百万元` and the period `2026年10月对比2025年10月，同币种示意`; it does not identify a real currency or provide individual-store or monthly records.

The default file yields:

- Prior revenue `1080`; current revenue `1271`; net change `191`; growth `17.685185…%`.
- Target `1385`; target shortfall `114`.
- The three largest positive contributions are `80`, `40`, `32`: total `152`, or `79.581151…%` of the net increase.
- Indonesia and Singapore have positive market-wide growth and negative supplied same-store percentages. Laos has negative values on both measures.

These values, names, rankings, headings and coverage counts are calculated from input. The script has no country-ID rules. The raw source remains embedded under `source_data`; only its rows count as original observations. Bridge endpoints, contribution rows, gaps and scatter coordinates are derived views, not additional independent observations. The report downloads both the unchanged source object and the derived chart contract, and displays the original source table.

`null` remains unknown; `0` remains an observed zero. Totals require complete fields. A market growth rate requires known current and prior revenue with a positive prior value. Missing or zero prior revenue produces an unknown rate. A zero target still produces a valid absolute gap; no target ratio is needed. Each chapter reports paired coverage. Source revenue, prior revenue and targets must be nonnegative amounts; signed differences are derived. Strings, booleans, non-finite numbers and invalid source shapes are rejected instead of coerced.

The source does not define the exact numerator or denominator of `sameStoreGrowth`. The report therefore calls it `同店指标同比` and does not relabel it as `同店日店均`. It cannot explain causes, estimate ROI, construct a monthly trend or infer store-level observations from these records.

## Reproduce

From the repository root, with Python 3:

```powershell
python scripts/build_operating_story.py
python -m unittest discover -s scripts -p test_operating_story.py -v
```

To render another valid source without changing the example input:

```powershell
python scripts/build_operating_story.py --input path/to/source.json --output path/to/report.html
```

The build prints canonical source and derived-contract SHA-256 values. It does not write back to input. The canonical source SHA-256 for the default file is `eb39073514117ac2a4bdd584c928b1a7372f737e1edcea9b78616862d6c72a76`.

The dedicated tests cover the arithmetic, changed markets and metadata, target-null versus zero, missing and zero growth bases, partial actual coverage, invalid types, source immutability and script injection escaping. Browser evidence is maintained separately from the public sample.
