# Quick creation

Read the entire project and workspace sufficiently to understand its purpose, requirements, public interfaces, and first successful use. Do not run `scan.py`, the review scorecard, or the visual optimization pipeline in this mode. Check the entrypoint's existing-README rule before writing.

Create a comprehensive, well-structured README with concise prose. Take inspiration from these four examples for structure, tone, and content; examples are not evidence for the target project:

- https://raw.githubusercontent.com/Azure-Samples/serverless-chat-langchainjs/refs/heads/main/README.md
- https://raw.githubusercontent.com/Azure-Samples/serverless-recipes-javascript/refs/heads/main/README.md
- https://raw.githubusercontent.com/sinedied/run-on-output/refs/heads/main/README.md
- https://raw.githubusercontent.com/sinedied/smoke/refs/heads/main/README.md

Use GFM and GitHub admonitions (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`) where they help. Use few emojis. Include an existing project logo in the header, with meaningful alt text; if copying it for the README, publish the referenced copy in `readme/assets/`.

Make the project identity, value, requirements, installation, and an actual usage example easy to find. Select sections that the project needs, rather than filling a template with empty content. Match prose language to the user, then the existing README, then English. Do not include author biographies or attribution sections; preserve any legally required notices. Do not add LICENSE, CONTRIBUTING, or CHANGELOG sections to the body: those have dedicated files. A required legal notice or a short license pointer is not a license chapter.

Only add one or two Mermaid diagrams when the project has multiple runtime components or a meaningful main workflow. A small, single-purpose library needs no diagram. Explain diagram meaning in Markdown so essential facts are available without rendering it. Do not generate hero images or GIFs in quick mode.

Write `<target>/README.md` directly. Check examples and links against files you actually read; do not invent flags, benchmark numbers, adoption, or project stability. In combined execution continue to review, then optimization; optimization replaces Mermaid with static images.
