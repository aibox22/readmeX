# README branch

Write the target repository's root `README.md` from the scan JSON. Describe the repository that was scanned. Keep the sections below, in this order. Drop a section only when the scan and the repository contain nothing that can fill it.

When this run also writes a logo, put this under the title:

```html
<img src="images/logo.svg" alt="Logo" height="100">
```

When this run does not write a logo, include that image only if `images/logo.svg` already exists in the target.

Fill `OWNER` and `REPO` from `git.github_username` and `git.repo_name`. Include the shield block only when both values are non-empty.

## Sections

1. Title and one-sentence description.
2. Shields, when GitHub coordinates exist:

```markdown
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]

[contributors-shield]: https://img.shields.io/github/contributors/OWNER/REPO.svg?style=flat-round
[contributors-url]: https://github.com/OWNER/REPO/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/OWNER/REPO.svg?style=flat-round
[forks-url]: https://github.com/OWNER/REPO/network/members
[stars-shield]: https://img.shields.io/github/stars/OWNER/REPO.svg?style=flat-round
[stars-url]: https://github.com/OWNER/REPO/stargazers
[issues-shield]: https://img.shields.io/github/issues/OWNER/REPO.svg?style=flat-round
[issues-url]: https://github.com/OWNER/REPO/issues
[license-shield]: https://img.shields.io/github/license/OWNER/REPO.svg?style=flat-round
[license-url]: https://github.com/OWNER/REPO/blob/master/LICENSE.txt
```

3. About the project, including what it does.
4. Key features grounded in the scanned source.
5. Built with: languages from `languages` and packages named in `dependency_files`. Use shields.io badges for the ones you can identify.
6. Project structure: a fenced copy of `structure`. When `structure_truncated` is true, say the tree is truncated.
7. Getting started: prerequisites, installation, and configuration taken from the dependency manifests and entry files. Quote commands that the manifests support.
8. Usage, with a runnable example when the repository has an entry point.
9. Roadmap, only for work the repository already marks as unfinished.
10. Contributing.
11. License, naming the license file when one is in the tree.
12. Contact: the project link `https://github.com/OWNER/REPO` when both coordinates exist. Otherwise use `git.remote` when it is non-empty.

The README is done when these sections are present and each filled section cites the scan or a file in the target repository.
