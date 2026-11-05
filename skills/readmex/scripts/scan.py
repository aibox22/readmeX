#!/usr/bin/env python3
"""Inventory repository files; print JSON and optionally persist the same scan."""

import argparse
import fnmatch
import json
import os
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
EXCERPT_LIMIT = 4000
STRUCTURE_LINE_LIMIT = 500
DEPENDENCY_FILE_LIMIT = 30


def load_json(name):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def git_command(root, args):
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    except FileNotFoundError:
        return None


def git_output(root, args):
    result = git_command(root, args)
    return result.stdout.decode("utf-8", errors="replace").strip() if result and result.returncode == 0 else ""


def git_info(root):
    remote = git_output(root, ["remote", "get-url", "origin"])
    remote = re.sub(r"^(https?://)[^/@]+@", r"\1", remote)
    return {
        "remote": remote,
        "revision": git_output(root, ["rev-parse", "HEAD"]),
        "repo_name": root.name,
    }


def ignore_patterns(root):
    config = load_json("ignore_patterns.json")
    patterns = config["ignore_dirs"] + config["ignore_files"]
    ignore = root / ".gitignore"
    if ignore.is_file():
        patterns += [line.strip() for line in ignore.read_text(encoding="utf-8", errors="replace").splitlines()
                     if line.strip() and not line.lstrip().startswith("#")]
    return patterns


def ignored(rel, patterns, is_dir=False):
    result = False
    parts = Path(rel).parts
    for pattern in patterns:
        negated = pattern.startswith("!")
        body = pattern[1:] if negated else pattern
        directory = body.endswith("/")
        body = body.rstrip("/")
        anchored = body.startswith("/")
        body = body.lstrip("/")
        candidates = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]
        if directory and not is_dir:
            candidates = candidates[:-1]
        match = any(fnmatch.fnmatch(candidate, body) for candidate in candidates)
        if not anchored and "/" not in body:
            match = match or any(fnmatch.fnmatch(part, body) for part in (parts if is_dir or not directory else parts[:-1]))
        if match:
            result = not negated
    return result


def repository_files(root, patterns):
    # Git supplies nested ignore and negation semantics without traversing vendored trees.
    listed = git_command(root, ["ls-files", "--cached", "--others", "--exclude-standard", "-z"])
    if listed and listed.returncode == 0:
        candidates = [root / os.fsdecode(item) for item in listed.stdout.split(b"\0") if item]
    else:
        candidates = []
        for directory, dirs, files in os.walk(root, followlinks=False):
            base = Path(directory)
            dirs[:] = sorted(name for name in dirs
                             if not (base / name).is_symlink()
                             and not ignored((base / name).relative_to(root).as_posix(), patterns, True))
            candidates.extend(base / name for name in sorted(files))
    found = []
    for file in candidates:
        rel = file.relative_to(root).as_posix()
        if file.is_symlink() or not file.is_file() or ignored(rel, patterns):
            continue
        found.append(file)
    return sorted(set(found), key=lambda file: file.relative_to(root).as_posix())


def extension_map():
    return {ext.lower(): language for language, extensions in load_json("language_mapping.json").items()
            for ext in extensions}


def detect_language(file, extensions):
    matched = extensions.get(file.name.lower()) or extensions.get(file.suffix.lower())
    if matched:
        return matched
    try:
        with file.open(encoding="utf-8", errors="replace") as handle:
            first = handle.readline(256).lower()
    except OSError:
        return None
    if first.startswith("#!"):
        for token, language in [("python", "python"), ("node", "javascript"), ("ruby", "ruby"),
                                ("perl", "perl"), ("php", "php"), ("sh", "shell")]:
            if token in first:
                return language
    return None


def analyze_languages(files):
    extensions = extension_map()
    stats = defaultdict(lambda: {"files": 0, "lines": 0, "bytes": 0})
    for file in files:
        language = detect_language(file, extensions)
        if not language:
            continue
        try:
            with file.open(encoding="utf-8", errors="replace") as handle:
                lines = sum(1 for _ in handle)
            size = file.stat().st_size
        except OSError:
            continue
        stats[language]["files"] += 1
        stats[language]["lines"] += lines
        stats[language]["bytes"] += size
    total = sum(value["lines"] for value in stats.values()) or 1
    languages = [{"language": language, **value, "line_percentage": round(value["lines"] * 100 / total, 1)}
                 for language, value in stats.items()]
    languages.sort(key=lambda value: (-value["lines"], value["language"]))
    return languages[0]["language"] if languages else "", languages


def project_structure(root, files):
    tree = {}
    for file in files:
        branch = tree
        for part in file.relative_to(root).parts:
            branch = branch.setdefault(part, {})
    lines = [root.name + "/"]

    def walk(branch, depth):
        for name, children in sorted(branch.items(), key=lambda item: (not bool(item[1]), item[0].lower())):
            if len(lines) >= STRUCTURE_LINE_LIMIT:
                return False
            lines.append("    " * depth + "├── " + name + ("/" if children else ""))
            if children and not walk(children, depth + 1):
                return False
        return True

    complete = walk(tree, 1)
    if not complete:
        lines.append("    └── …")
    return "\n".join(lines), not complete


def excerpt(file, root):
    with file.open(encoding="utf-8", errors="replace") as handle:
        text = handle.read(EXCERPT_LIMIT + 1)
    return {"path": file.relative_to(root).as_posix(), "excerpt": text[:EXCERPT_LIMIT],
            "truncated": len(text) > EXCERPT_LIMIT}


def scan(root):
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    files = repository_files(root, ignore_patterns(root))
    primary, languages = analyze_languages(files)
    structure, truncated = project_structure(root, files)
    manifests = [name for group in load_json("dependency_files.json").values() for name in group]
    dependencies = [file for file in files if any(fnmatch.fnmatch(file.name, name) for name in manifests)]
    docs = [file for file in files if file.parent == root and
            re.match(r"(?i)^(readme|license|licence|copying|security)([._-]|$)", file.name)]
    return {
        "project_path": str(root), "git": git_info(root),
        "primary_language": primary, "languages": languages,
        "structure": structure, "structure_truncated": truncated,
        "dependency_files": [excerpt(file, root) for file in dependencies[:DEPENDENCY_FILE_LIMIT]],
        "dependency_files_truncated": len(dependencies) > DEPENDENCY_FILE_LIMIT,
        "documentation": [excerpt(file, root) for file in docs],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", default=".", type=Path)
    parser.add_argument("--output", type=Path, help="Persist JSON as well as printing it")
    args = parser.parse_args()
    try:
        text = json.dumps(scan(args.target), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.output.parent,
                                             delete=False, prefix=".scan-") as handle:
                temporary = Path(handle.name)
                handle.write(text)
            try:
                temporary.replace(args.output)
            finally:
                temporary.unlink(missing_ok=True)
        print(text, end="")
    except (OSError, ValueError) as error:
        parser.exit(1, f"scan: {error}\n")


if __name__ == "__main__":
    main()
