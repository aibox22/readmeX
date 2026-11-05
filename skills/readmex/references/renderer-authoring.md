# JSON → GitHub-safe static SVG

Use only architecture and workflow. The CLI selects the renderer from `diagram_type`:

```bash
node bin/render-diagram.mjs /target/.readmex/optimize/diagrams/architecture.json --repo-root /target
node bin/render-diagram.mjs /target/.readmex/optimize/diagrams/workflow.json --repo-root /target --layout-json
```

A normal run writes `meta.output`, normally `readme/assets/architecture.svg` or `readme/assets/workflow.svg`, relative to the target. `--layout-json` returns diagnostic geometry without publishing an image. Both paths validate schema, current-tree/explicit-commit source references, and renderer geometry; failed validation exits nonzero and preserves the prior output.

Start with `examples/web-app.architecture.json` and `examples/agent-tool-call.workflow.json`. Replace the entire sample story with inspected project facts. Read [defaults](authoring-defaults.md), [contract](authoring-contract.md), and [source evidence](repository-authoring.md) before authoring.

The SVG embeds the renderer's concrete light-theme styles, a fixed background, accessible title/description, and any source-evidence receipt. The output viewBox is 1200 units wide. Styles are independent of an HTML viewer. No script, foreignObject, remote font, or animated SVG is published.

The writer enforces final primary/supporting text floors of 20/18 units. Default main node names are 40 and supporting text 28 so a small three-step diagram remains useful on mobile. Preview at 900 and 360 pixels: when necessary labels are unreadable, split the mechanism, reduce density, and put detail in Markdown. The numeric floor is a desktop guard, not a substitute for a mobile preview.

Add one Markdown paragraph under each diagram. Architecture is always static. Approved GIF work derives only hero/workflow from stable SVG element IDs and keeps the matching static SVG in `readme/assets/`. Animation specs and previews stay under `.readmex/optimize/`; no overview JSON/HTML or viewer block is produced.
