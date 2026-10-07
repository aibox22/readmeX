---
name: readmex
description: >-
  Writes a repository README, an SVG logo, and an MkDocs documentation site
  from a local scan of the target repository. Use when the user asks to
  generate or rewrite a README, create a project logo, or build a docs site,
  including requests that mention readmex, README, Logo, or 文档站.
license: MIT
compatibility: Requires Python 3 and git.
---

# readmex

Scan the target repository, choose one branch, and write that branch's files into the target. The scanner reports facts. The branch files in this skill are the templates. Write the documents yourself.

## Scan

1. Use the repository path the user gave. When they gave none, use the current workspace root.
2. Run this skill's scanner:

```bash
python scripts/scan.py <target>
```

3. The scan is complete when stdout is one JSON object containing `git`, `primary_language`, `languages`, `structure`, and `dependency_files`.

Use `git.github_username` and `git.repo_name` for badges and links. Omit GitHub badges and GitHub links when either value is empty. Leave the remote URL in prose when it is present and is not a GitHub remote.

## Choose a branch

Pick the single branch that matches the request.

- **readme-and-logo** — the user wants a README, or does not narrow the request. Write `README.md` and `images/logo.svg`. Read [readme-template.md](readme-template.md) and [logo.md](logo.md).
- **readme** — the user wants a README and no logo. Write `README.md` only. Read [readme-template.md](readme-template.md).
- **logo** — the user wants only a logo. Write `images/logo.svg`. Read [logo.md](logo.md).
- **website** — the user wants a documentation site. Write `website/` only. Read [website.md](website.md).
- **website-and-logo** — the user wants a documentation site and a logo. Write `website/` and `images/logo.svg`. Read [website.md](website.md) and [logo.md](logo.md).

Write every file into the target repository. This skill directory stays unchanged.

A logo file replaces an existing `images/logo.svg`. A website write fills `website/` and leaves the target root `README.md` as it was. On a branch that does not write a logo, refer to `images/logo.svg` only when that file is already in the target repository.

Write prose in the language the user requested. When they did not request one, match an existing README in the target. When the target has no README, write in English.

## Done

- **readme**: the target `README.md` exists and uses the sections in [readme-template.md](readme-template.md).
- **logo**: the target `images/logo.svg` exists and is the SVG from this run.
- **readme-and-logo**: both the README criterion and the logo criterion are met.
- **website**: `website/mkdocs.yml` and every page named in [website.md](website.md) exist, and the target root `README.md` is unchanged.
- **website-and-logo**: the website criterion is met and `images/logo.svg` is the SVG from this run.
