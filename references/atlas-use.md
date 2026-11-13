# Using the 54-example atlas

Open [the atlas](../examples/dashboard-atlas/atlas.html), or the hosted gallery linked in README.
Each case discloses its question, encoding, units, period, scope, data and limitations.
All public examples use original synthetic data or mechanism-only diagrams.
Reusing a case means recalculating its story, annotations, axes and geometry as well as changing the input.
`node examples/dashboard-atlas/build_atlas.js` rebuilds the HTML, JSON and 54 SVG files.
The Python helper separately supports six generic chart types; it does not generate all 54 examples from arbitrary JSON.

The helper is an optional tool, and the atlas is a craft reference; neither limits what an Agent can design. For a new compound encoding or coordinate/hierarchy transformation, use [composition reasoning](composition-reasoning.md) and, when useful, the [custom renderer interface](custom-renderers.md). A new design must still prove its data alignment, geometry, mobile layout and complete export. An unseen chart name is not an inability, and one successful example does not validate arbitrary inputs.
