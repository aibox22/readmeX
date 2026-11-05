# README diagram defaults

Use the architecture and workflow JSON renderers only. Start from the matching example, then replace every sample role and relationship using the inspected project. Keep the README diagram at the reader's abstraction level: usually two to five named parts or steps per image. Split a dense mechanism into separate images and explain the complete behavior in Markdown.

Set `meta.output` to `readme/assets/architecture.svg` or `readme/assets/workflow.svg`. JSON sources stay under `.readmex/optimize/diagrams/`. Run `node bin/render-diagram.mjs diagram.json --repo-root /absolute/target`; the process resolves output inside that target. The output is a standalone SVG with a 1200-unit-wide viewBox and a fixed light background. The renderers require Node.js 18 or newer and no npm installation.

Use one primary language: user choice, existing README, then English. Keep API, protocol, product, and command names literal. Set `meta.locale` to `en` or `zh-CN` for built-in renderer labels; other locales can supply `meta.translations`. Readable prose goes below the image in Markdown.

Choose `meta.visual_preset` from `classic`, `signal-flow`, `blueprint`, or `editorial` to match the frozen visual direction. Set `quality_profile: "showcase"` so topology and route-quality errors are hard failures. SVG animation is never a delivery format: approved motion is a separate GIF derived from a static hero or workflow SVG.

Main node labels start at 40 units, supporting labels at 28. Author short labels and wide nodes (typically 280–320 × 130). The final 1200-unit normalization must keep primary labels at least 20 and supporting labels at least 18. These desktop floors do not imply mobile legibility: preview at 900 and 360 pixels, keep required node names legible, and split/reduce density when they fail. Do not shrink text to fit a crowded diagram.

For architecture, use a two or three column grid or explicit `pos`/`size`, then automatic routes. Grid defaults are `origin: [40,80]`, `cols: 3`, `cellW: 320`, `cellH: 130`, `gapX: 80`, `gapY: 90`. A boundary needs a real isolation/ownership fact and enough room for its label. A boundary around one node must not repeat the node name.

For workflow, use schema version 2 with lanes, nodes at integer columns, a truthful `mainPath`, and edges. The compiler derives column spacing from occupied columns and node geometry. Keep phases/groups only when they explain distinct stages. Start without absolute pins; add a side, route, channel, or label position only for a measured defect.

Keep node responsibilities, edge direction, protocols, synchronous/asynchronous behavior, and exceptions truthful. Start an edge unlabeled only when its endpoints already imply its entire meaning. Move a label or route to fix collisions; do not delete semantic relationships for a cleaner picture.

Add `sources: [{"path":"src/example.py","line":12,"end_line":20}]` to a node when a inspected file proves it. The default verifier checks the current working tree and records file SHA-256 hashes, including non-Git/new projects. Only explicitly supplying `meta.repository.revision` selects commit verification; that branch requires a matching origin and a locally available full commit SHA. See [Repository evidence](repository-authoring.md).
