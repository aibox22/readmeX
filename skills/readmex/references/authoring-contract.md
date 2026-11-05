# Static diagram authoring contract

## Evidence and meaning

Author only inspected project facts. Preserve every agreed role, relationship, protocol, direction, boundary, and exception when changing abstraction. Record which surviving node or relationship carries each fact. A startup-file citation does not prove a network protocol. Speculative relationships must be removed or explicitly explained in Markdown as a concept.

The JSON schemas reject unknown properties, malformed identifiers, invalid node types, and invalid output paths. Cross-collection validation rejects duplicate relationship IDs. Architecture validates positions, node overlap, node text width, boundaries, labels, routes, port directions, arrowheads, and canvas containment. Workflow additionally validates lanes, columns, the main path, semantic checks, group/phase placement, and its compiled routing geometry. Keep `quality_profile: "showcase"` enabled.

## Layout and routing

Start with automatic routes and endpoint sides. Explicit `via`, `channelX`, `channelY`, `labelAt`, `labelSegment`, or sides preserve authored geometry; use them only when the automatic result has a measured problem. Read the diagnostic's subject, evidence, and suggested fixes before editing.

A clear gap is the space between node borders, not between node centers. Labels render on opaque masks; at 28 units allow roughly `18 × ASCII text units + 16` of width (CJK counts as two units), plus breathing room. The SVG mask and diagnostic measure the same rectangle. Increase spacing or move a label to resolve a collision. Keep action, protocol, direction, async behavior, and cross-boundary meaning.

Node text is one line. Widen a node or shorten its wording while preserving meaning; do not reduce required text below its floor. Put supporting implementation detail in Markdown. Never increase the viewBox alone to hide clipping: the output width is normalized to 1200, so an oversized canvas can fail text-size validation.

Keep supplied/agreed topology fixed. Splitting a diagram into a main path and a secondary mechanism is allowed when all necessary facts remain in the README. Changes to topology require source evidence, not aesthetic preference.

## Language and visual system

Use the README's primary language, preserve literal code names, and set `meta.locale` for accessible titles and renderer-owned labels. English and Simplified Chinese are built in. For other locales, supply the reusable `meta.translations` keys; missing keys fall back to English and are reported.

Freeze palette, type, shapes, motif, and composition before drawing. `visual_preset` selects one of the renderer's light palettes. The published SVG embeds concrete styles and a fixed light background; it carries no viewer, script, foreignObject, remote font, or SVG animation.

## Acceptance

Run the renderer with `--layout-json` when diagnosing geometry; it returns the receipt without writing an image, and exits nonzero on invalid geometry. Normal rendering verifies sources before publication, validates geometry, normalizes the canvas, checks text floors, and atomically replaces only a valid output. Invalid sources, schema, geometry, or typography must not overwrite a previously valid asset.

Preview the rendered image at 900 and 360 pixels. Essential node/step labels must remain readable at 360; if not, simplify/split the image and move the full explanation into Markdown. Always write one concise Markdown paragraph below architecture and workflow images. Run `scripts/readme_view_audit.py` after embedding; that audit supplements visual inspection.
