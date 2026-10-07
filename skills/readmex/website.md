# Website branch

Write a MkDocs site under the target repository's `website/` directory. Leave the target root `README.md` unchanged.

Create these files:

- `website/mkdocs.yml`
- `website/docs/index.md`
- `website/docs/installation.md`
- `website/docs/usage.md`
- `website/docs/api/index.md`
- `website/docs/examples.md`
- `website/docs/architecture.md`
- `website/docs/contributing.md`
- `website/docs/changelog.md`

`mkdocs.yml` sets `site_name` from `git.repo_name`, or from the target directory name when the repo name is empty. `docs_dir` is `docs`. `theme.name` is `material`. The `nav` lists the eight pages above, with the API page pointing at `api/index.md`.

Write each page from the scan and the source files it points at.

- **index**: what the project is, the primary language, and the key features.
- **installation**: prerequisites and install commands supported by `dependency_files`.
- **usage**: how to run the project, with a concrete example.
- **api/index**: public entry points, commands, or modules visible in the tree. One section per entry point.
- **examples**: at least one end-to-end example.
- **architecture**: how the main directories fit together, using `structure`.
- **contributing**: how to change the project and send a contribution.
- **changelog**: releases or notable history visible in the repository. When none is visible, say that no changelog is recorded yet.

When `images/logo.svg` exists in the target, or this run also writes that logo, show it on the index page as `../../images/logo.svg`. When neither is true, the index page has no logo.

The website is done when `website/mkdocs.yml` and all eight pages exist, and the target root `README.md` is byte-for-byte the file that was there before this run.
