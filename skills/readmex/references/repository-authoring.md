# Repository source evidence

Scan the actual target working tree and read the source before authoring diagram JSON. Keep the machine-readable JSON under `.readmex/optimize/diagrams/`; publish only the referenced SVG in `readme/assets/`.

Attach one to three source references to architecture `components[]` or workflow `nodes[]`:

```json
"sources": [{"path": "src/main.py", "line": 12, "end_line": 20, "label": "entry"}]
```

Paths are relative POSIX paths inside the target. Absolute paths, `..`, `.git`, backslashes, non-files, symlinks escaping the target, unavailable files, and nonexistent/reversed line ranges fail verification. Line numbers are optional; `end_line` requires `line`.

## Current working tree (default)

Omit `meta.repository` or omit its `revision`. The renderer verifies the actual files and line ranges under `--repo-root` and records each referenced file's SHA-256 in the SVG's `readmex-source-evidence` metadata. This supports new projects without Git, projects without an origin, and uncommitted files. Evidence carries no fake commit and no web permalink. It proves that the cited file/range exists; the agent must still inspect whether it supports the node's claim.

## Explicit commit

Use this branch only when the requested diagram intentionally describes a fixed committed revision:

```json
"repository": {
  "url": "https://github.com/owner/project",
  "revision": "0123456789012345678901234567890123456789",
  "link_mode": "web"
}
```

Replace the placeholder with an actual full 40-character SHA. The target must be the Git top-level directory, have a matching `origin`, and contain that commit locally. File and line references are checked against the commit blobs. A missing origin/commit or mismatched repository fails; never invent or create a commit to make a diagram pass. `link_mode: "local-only"` preserves strict commit verification while omitting web links. Web source links support canonical GitHub and Gitee repositories.

## Commands

```bash
node bin/render-diagram.mjs /target/.readmex/optimize/diagrams/architecture.json --repo-root /target
node bin/render-diagram.mjs /target/.readmex/optimize/diagrams/workflow.json --repo-root /target --layout-json
```

Source verification happens before any output write. A failure stops that diagram and must not replace a valid SVG. Fix a genuine citation mistake using inspected source; if the source cannot support the claim, remove/downgrade the claim and record that change in the scorecard. Do not silently remove evidence solely to bypass verification.
