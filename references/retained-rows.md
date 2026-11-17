# RetainedRows: fixed-value filtering and row reordering

A small DOM adapter over the existing `RetainedMotion` + `ChartMotion` runtime. It does not replace either runtime or calculate business metrics.

Load (or fully inline) `chart-motion.js`, `retained-motion.js`, then `retained-rows.js`.

```js
const rows = RetainedRows.create({
  container: document.getElementById('rows'), // empty HTML element
  records: [{id:'A', name:'Alpha', value:42}, {id:'B', name:'Beta', value:19}],
  scopes: {all:['A','B'], reverse:['B','A'], filtered:['B']},
  initial: 'all', rowHeight: 80, duration: 420,
  createRow(record) { // once per record; return a distinct detached Element
    const content = document.createElement('div');
    content.textContent = `${record.name}: ${record.value}`;
    return content;
  },
  fallbackFocus: document.getElementById('allButton'),
  statusElement: document.getElementById('status') // optional
});
rows.set('filtered');
```

`set(scope)` returns false for a no-op. `finish()` and `withStableFrame(callback)` settle the current target for reading/export. `getNode(id)` returns the stable generated wrapper. `destroy()` cancels animation, removes generated nodes, restores the container's original style/role/tabindex and rejects further set calls. Destroy is idempotent. The caller owns listeners inside its custom content.

## Behavior and boundaries

- Immutable records; known named scopes; stable unique string IDs. This adapter does **not** interpolate changing values, redefine scales, aggregate data, accept arbitrary dynamic scopes, or measure variable-height rows.
- One fixed positive rowHeight for all rows. Each height and total scope extent must be at most 1,000,000 CSS pixels; enormous finite values and sparse scopes are rejected before DOM changes. The caller must size content to fit. The container is position:relative; wrappers use absolute y positions. Reading order follows the target order; retained descendants regain their existing focus after DOM moves.
- Retained wrappers and contents are reused. Their numerical bars never get rebuilt by filtering. Entering members render their true fixed value and fade in, not zero-to-value growth. Missing data remains the caller's explicit missing label, never an invented zero.
- Exiting wrappers immediately become inert and aria-hidden; focus in an exiting item moves to fallbackFocus (or the container if unavailable). No pointer-only hiding.
- Wrapper CSS transition/animation is disabled to avoid double interpolation. **Do not give immutable inner bars entrance keyframes or redraw them on filter.** Arbitrary client CSS or JS can otherwise invalidate this adapter's guarantees.
- Current-frame continuation, interruption, reduced motion, stable print/export and lifecycle cancellation come from the shared runtime. No new animation clock was added. Reduced motion is checked against the actual browser MediaQuery change event, not a premature controller-command return.
- This is a rendering helper, not an aesthetic score, data audit, general layout engine or fully verified screen-reader experience.

## Reproduce

`python examples/retained-rows/build_demos.py --skill-root .` generates two offline single-file demos: `harvest.html` and `fulfilment.html`. They use different fixed-value row layouts and include true zero and missing values.

`node examples/retained-rows/verify.cjs` uses installed Playwright. Set PLAYWRIGHT_MODULE to a nonstandard module installation if required; BROWSER_CHANNEL optionally chooses a browser. Windows defaults to Edge, other platforms use Playwright Chromium. Tests write test-results.json and screenshots in this directory.

54 actual browser checks cover initial/middle/target geometry, synchronous no-flash first frame, unchanged inner widths, reversal from visible geometry, retained/removed focus, inert exits, true-value entry, no-op, empty/returned scopes, stable DOM identity, initial and runtime reduced motion, stable export/print, invalid inputs, destroy, and page errors. The two default screenshots were also visually inspected. This count is engineering evidence only, not independent 9.5 scoring.

Independent review found that a finite but enormous height could collapse CSS layout; the candidate now rejects it before DOM changes. Self-review also found a generic data-scope attribute collision, now fixed using data-retained-scope/phase with a real detail-click regression. Initial test failures were harness assumptions: border-inclusive outer height versus CSS content height; and a separate controller/evaluate roundtrip sampling after a legitimate rAF advance. These were corrected with explicit content height and same-browser-task first-frame samples. The runtime reduce test now records the real change event cycle. No failed artifact was silently rescored.
