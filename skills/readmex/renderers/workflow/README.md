# Workflow renderer

The schema version 2 compiler derives spacing from lanes, occupied node columns, node sizes, groups, phases, and relationship labels. Prefer a sparse main path with automatic routing. Explicit pins are for measured geometry defects.

Run through `bin/render-diagram.mjs` with `--repo-root`; normal output is a self-contained light-background static SVG. `--layout-json` emits the compiler receipt without writing the image. Source references are checked before compilation. All hard schema, semantic, geometry, and typography failures exit nonzero.

See [renderer authoring](../../references/renderer-authoring.md) and the [workflow example](../../examples/agent-tool-call.workflow.json). Keep required names readable at 360 pixels, split dense flows, and explain full behavior in Markdown. GitHub motion is an optional separate GIF; this renderer publishes static SVG only.
