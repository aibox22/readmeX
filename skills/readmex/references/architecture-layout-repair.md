# Architecture layout repair

Keep all inspected topology and semantic labels during a repair. Do not repair a crowded diagram by shrinking its type or dropping a necessary edge.

1. Run `node bin/render-diagram.mjs diagram.json --repo-root /target --layout-json` and read the resolved component/boundary/label rectangles and diagnostics.
2. Fix invalid positions, node overlap, text width, and canvas containment first. Prefer a sparse 1200-unit canvas with wide nodes; split separate mechanisms into separate images when needed.
3. Fix boundary title containment and genuine ownership/isolation meaning. An oversized boundary can reduce legibility after normalization.
4. Fix wrong endpoint direction, port spacing, arrowhead collisions, and routes crossing unrelated nodes. Start by removing unnecessary manual route pins so automatic routing can retry.
5. Fix label-to-node, label-to-label, and label-to-route collisions using the suggested `labelAt`, `labelDx`, `labelDy`, or `labelSegment`. Suggested offsets replace the authored values.
6. Re-run after each dependent change. Keep action/protocol/direction/async labels. When wording is too long, shorten it truthfully and move the full detail into Markdown.
7. Render the static SVG and inspect it at 900 and 360 pixels. Confirm that essential names remain readable and that the Markdown paragraph explains the complete mechanism.

The layout receipt uses the renderer's source coordinates; the published SVG normalizes them to a 1200-unit viewBox. Geometry success alone does not guarantee GitHub legibility. Never fall back to an HTML viewer/template or hand-write unchecked SVG to bypass a failed diagram.
