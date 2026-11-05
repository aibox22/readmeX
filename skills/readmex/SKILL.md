---
name: readmex
description: Create, review, or beautify a project README. Use for requests to write README.md, audit README claims or structure, score a README, or add README hero images and diagrams; supports quick creation, review, visual optimization, and the combined flow.
license: MIT
metadata:
  requirements: Python 3 and Node.js 18+; GIFs optionally use Pillow, ffmpeg, and rsvg-convert or macOS sips.
---

# readmex

Help project authors write a clear, concise, attractive README. Select only the requested pipeline; load its instructions when needed. The combined flow is **quick creation → review → optimization**. Do not produce the old interactive project overview or insert its blocks into the README.

## Route

| User request | Pipeline |
| --- | --- |
| “Write a README” / “写个 README”, with no scope | Ask “要快速简洁的，还是完整清晰并且有配图的？” in the single opening question batch; quick selects quick creation, complete selects the combined flow |
| Quick / “快速写一份” | [quick-create.md](pipelines/quick-create.md) |
| Review, check, score, “为什么没人用” **about a README** | [review.md](pipelines/review.md) |
| Beautify, hero image, architecture or workflow image | [optimize.md](pipelines/optimize.md) |
| Complete, full process, “一条龙” | All three, in order |

Use the target repository given by the user, otherwise the workspace root. If quick creation encounters `README.md`, route to review instead of replacing it. An explicit request to **rewrite** authorizes replacement. In the combined flow an existing README similarly skips creation and enters review → optimization. Do not back up a README before changing it.

## Ask once, at the beginning

For a known review or optimization route, scan and inspect relevant code before asking. Quick creation reads the project directly and **does not run the scanner**. For an ambiguous “write a README”, inspect necessary files first, then include route selection and questions conditional on choosing the complete flow in **one message**; scan only after the selected route needs it.

Infer repository, project type, existing brand, and publication targets from files. Combine only applicable questions into that one message:

- Route selection only for an ambiguous “write a README”.
- Review facts, at most six questions: always ask whether adoption is personal or company procurement, which alternatives readers already know, and what legal or policy content must appear. Ask who the readers are and the project's actual status only when repository evidence is inconclusive.
- Standalone optimization: ask whether to refresh the whole page or produce assets only. The combined flow defaults to a whole-page refresh.
- When planning a hero: “是否可以调用生图工具生成素材？”
- When planning a hero or workflow image: “是否可以把头图和流程图做成 GIF 动图？”

Reader identity and adoption are separate facts: “individual developer” alone does not establish whether adoption is personal or requires company procurement. Use an explicit adoption answer rather than inferring it from the reader's job.

Image generation and GIFs each require an explicit affirmative answer; no answer or refusal means static SVG only. Existing explicit choices count as answers. Do not ask further design or factual questions during execution. During review or optimization, downgrade or delete newly discovered unsupported claims and record them in the scorecard. The one later approval gate is **standalone review**: deliver the diagnosis and wait for agreement before rewriting `README.md`. Combined execution already authorizes the rewrite. Linux GIF installation may require the user to enter a sudo password in their own terminal; this is an installation interaction, never a request to disclose the password.

## Files and shared preparation

Resolve helper paths from the installed skill directory, not the target's working directory. Before producing intermediates, append the exact line `.readmex/` to the target `.gitignore` if absent; create `.gitignore` when needed and preserve its other contents.

For review or optimization, run once per invocation and reuse the facts across pipelines:

```bash
python3 <skill>/scripts/scan.py <target> --output <target>/.readmex/scan.json
```

Read entrypoints and code as well; the scan is an inventory, not evidence of behavior. The scanner also prints JSON to stdout. Language follows the user's instruction, then an existing README, then English.

| Location in the target | Contract |
| --- | --- |
| `README.md` | Final project page at the repository root |
| `readme/assets/` | Only files referenced by the README; commit these assets |
| `.readmex/scan.json` | Shared repository inventory |
| `.readmex/review/audit.txt`, `scorecard.md` | Mechanical findings and evidence-based diagnosis |
| `.readmex/optimize/story.md` | Five-line project story and frozen visual specification |
| `.readmex/optimize/diagrams/architecture.json`, `workflow.json` | Authored renderer input |
| `.readmex/optimize/imagegen/` | `hero-layout.svg`, `hero-subject.png`, `hero-prompt.txt` |
| `.readmex/optimize/motion/` | Motion specification JSON; delete rendered frames after production |
| `.readmex/optimize/preview/` | Previews at 900 and 360 pixels wide |

Published assets may include `hero.svg` or a composited `hero.png`, `hero.gif` alongside `hero.svg`, `architecture.svg`, `workflow.svg` and optional `workflow.gif`, and referenced `section-*.svg`. Keep unpublished sources and previews in `.readmex/`. Clean up only assets owned by this run that are no longer referenced; preserve unrelated files.
