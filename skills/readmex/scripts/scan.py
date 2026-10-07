#!/usr/bin/env python3
"""Scan a repository and print facts as JSON. Does not call a model or write docs."""

import fnmatch
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
EXCERPT_LIMIT = 4000
STRUCTURE_LINE_LIMIT = 500
DEPENDENCY_FILE_LIMIT = 30


def load_json(name):
    with open(DATA_DIR / name, encoding="utf-8") as handle:
        return json.load(handle)


def gitignore_patterns(project_dir):
    path = project_dir / ".gitignore"
    if not path.is_file():
        return []
    patterns = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)
    return patterns


def pattern_matches(rel, name, is_dir, pattern):
    dir_only = pattern.endswith("/")
    body = pattern[:-1] if dir_only else pattern
    if dir_only and not is_dir:
        return False
    if fnmatch.fnmatch(name, body) or fnmatch.fnmatch(rel, body) or fnmatch.fnmatch(rel, pattern):
        return True
    return any(fnmatch.fnmatch(part, body) for part in Path(rel).parts)


def should_ignore(rel, name, is_dir, patterns):
    if not rel or rel == ".":
        return False
    return any(pattern_matches(rel, name, is_dir, pattern) for pattern in patterns)


def build_extension_map(language_mapping):
    extension_map = {}
    for language, extensions in language_mapping.items():
        for ext in extensions:
            key = ext if not ext.startswith(".") else ext.lower()
            extension_map[key] = language
    return extension_map


def shebang_language(first_line):
    shebang = first_line.lower()
    if "python" in shebang:
        return "python"
    if "node" in shebang:
        return "javascript"
    if "ruby" in shebang:
        return "ruby"
    if "perl" in shebang:
        return "perl"
    if "php" in shebang:
        return "php"
    if "bash" in shebang or "sh" in shebang:
        return "shell"
    return None


def detect_language(file_path, extension_map):
    if file_path.name in extension_map:
        return extension_map[file_path.name]
    suffix = file_path.suffix.lower()
    if suffix in extension_map:
        return extension_map[suffix]
    try:
        first_line = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    except (OSError, IndexError):
        return None
    if first_line.startswith("#!"):
        return shebang_language(first_line)
    return None


def count_lines(file_path):
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def analyze_languages(project_dir, extension_map, patterns):
    stats = defaultdict(lambda: {"files": 0, "lines": 0, "bytes": 0})
    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(project_dir).as_posix()
        if any(should_ignore(str(Path(*rel.split("/")[: i + 1])), part, True, patterns) for i, part in enumerate(rel.split("/")[:-1])):
            continue
        if should_ignore(rel, path.name, False, patterns):
            continue
        language = detect_language(path, extension_map)
        if not language:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        stats[language]["files"] += 1
        stats[language]["lines"] += count_lines(path)
        stats[language]["bytes"] += size

    total_lines = sum(item["lines"] for item in stats.values()) or 1
    languages = []
    for language, item in stats.items():
        languages.append({
            "language": language,
            "files": item["files"],
            "lines": item["lines"],
            "bytes": item["bytes"],
            "line_percentage": round(item["lines"] * 100 / total_lines, 1),
        })
    languages.sort(key=lambda item: item["lines"], reverse=True)
    primary = languages[0]["language"] if languages else ""
    return primary, languages


def project_structure(project_dir, patterns):
    lines = [project_dir.name + "/"]
    truncated = False

    def walk(directory, depth):
        nonlocal truncated
        if truncated:
            return
        try:
            children = sorted(directory.iterdir(), key=lambda path: (path.is_file(), path.name.lower()))
        except OSError:
            return
        indent = "    " * depth
        for child in children:
            rel = child.relative_to(project_dir).as_posix()
            if should_ignore(rel, child.name, child.is_dir(), patterns):
                continue
            if len(lines) >= STRUCTURE_LINE_LIMIT:
                lines.append(indent + "└── …")
                truncated = True
                return
            suffix = "/" if child.is_dir() else ""
            lines.append(f"{indent}├── {child.name}{suffix}")
            if child.is_dir():
                walk(child, depth + 1)

    walk(project_dir, 1)
    return "\n".join(lines), truncated


def dependency_patterns(dependency_files):
    found = []
    for names in dependency_files.values():
        for name in names:
            if name not in found:
                found.append(name)
    return found


def find_dependency_files(project_dir, patterns, manifests):
    matches = []
    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(project_dir).as_posix()
        if any(should_ignore(str(Path(*rel.split("/")[: i + 1])), part, True, patterns) for i, part in enumerate(rel.split("/")[:-1])):
            continue
        if should_ignore(rel, path.name, False, patterns):
            continue
        if not any(fnmatch.fnmatch(path.name, manifest) for manifest in manifests):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        excerpt = text[:EXCERPT_LIMIT]
        matches.append({
            "path": rel,
            "excerpt": excerpt,
            "truncated": len(text) > EXCERPT_LIMIT,
        })
        if len(matches) >= DEPENDENCY_FILE_LIMIT:
            break
    matches.sort(key=lambda item: item["path"])
    return matches


def git_info(project_dir):
    result = subprocess.run(
        ["git", "-C", str(project_dir), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
    )
    remote = result.stdout.strip() if result.returncode == 0 else ""
    username = ""
    repo_name = ""
    if "github.com" in remote:
        tail = remote.split("github.com", 1)[1].lstrip(":/")
        if tail.endswith(".git"):
            tail = tail[:-4]
        parts = [part for part in tail.split("/") if part]
        if len(parts) >= 2:
            username, repo_name = parts[0], parts[1]
    return {"remote": remote, "github_username": username, "repo_name": repo_name}


def scan(project_dir):
    project_dir = project_dir.resolve()
    if not project_dir.is_dir():
        raise SystemExit(f"Not a directory: {project_dir}")

    ignore_config = load_json("ignore_patterns.json")
    patterns = list(ignore_config.get("ignore_dirs", [])) + list(ignore_config.get("ignore_files", []))
    patterns.extend(gitignore_patterns(project_dir))
    extension_map = build_extension_map(load_json("language_mapping.json"))
    primary, languages = analyze_languages(project_dir, extension_map, patterns)
    structure, structure_truncated = project_structure(project_dir, patterns)
    manifests = dependency_patterns(load_json("dependency_files.json"))
    return {
        "project_path": str(project_dir),
        "git": git_info(project_dir),
        "primary_language": primary,
        "languages": languages,
        "structure": structure,
        "structure_truncated": structure_truncated,
        "dependency_files": find_dependency_files(project_dir, patterns, manifests),
    }


def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else "."
    payload = scan(Path(raw))
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
