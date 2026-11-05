#!/usr/bin/env python3
"""Check README image alt/references and static SVG basics, not visual quality."""

from __future__ import annotations

import argparse
import html
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


def visible_markdown(text: str) -> str:
    """Blank fenced and inline code, retaining original line positions."""
    result = []
    fence = None
    for line in text.splitlines(keepends=True):
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= fence[1] and not match.group(2).strip():
                fence = None
            result.append("\n" if line.endswith("\n") else "")
        elif match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
            fence = (match.group(1)[0], len(match.group(1)))
            result.append("\n" if line.endswith("\n") else "")
        else:
            result.append(re.sub(r"(`+)(?!`)(.*?)\1(?!`)", lambda m: " " * len(m.group(0)), line))
    return "".join(result)


def balanced_end(text: str, start: int, opener: str, closer: str) -> int | None:
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
    return None


def destination(body: str) -> str:
    """Read GFM destination with angle paths, escaped spaces or balanced parens."""
    body = body.strip()
    if body.startswith("<"):
        end = body.find(">")
        return body[1:end] if end > 0 else ""
    result = []
    depth = 0
    escaped = False
    for char in body:
        if escaped:
            result.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char.isspace() and depth == 0:
            break
        else:
            result.append(char)
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
    return "".join(result)


def reference_id(value: str) -> str:
    return " ".join(value.split()).casefold()


def markdown_images(text: str) -> tuple[list[dict], list[str]]:
    refs = {}
    for match in re.finditer(r"^\s{0,3}\[([^\]\n]+)\]:\s*(.+)$", text, re.M):
        refs[reference_id(match.group(1))] = destination(match.group(2))
    images = []
    issues = []
    cursor = 0
    while True:
        start = text.find("![", cursor)
        if start < 0:
            break
        cursor = start + 2
        if start and text[start - 1] == "\\":
            continue
        end = balanced_end(text, start + 1, "[", "]")
        if end is None:
            continue
        alt = text[start + 2:end]
        after = end + 1
        line = text.count("\n", 0, start) + 1
        src = None
        if after < len(text) and text[after] == "(":
            close = balanced_end(text, after, "(", ")")
            if close is None:
                continue
            src = destination(text[after + 1:close])
            cursor = close + 1
        elif after < len(text) and text[after] == "[":
            close = balanced_end(text, after, "[", "]")
            if close is None:
                continue
            key = reference_id(text[after + 1:close] or alt)
            src = refs.get(key)
            if src is None:
                issues.append(f"line {line}: undefined image reference [{key}]")
            cursor = close + 1
        else:
            src = refs.get(reference_id(alt))
            cursor = end + 1
        if src is not None:
            images.append({"src": src, "alt": alt, "line": line, "kind": "Markdown"})
    return images, issues


class ImageTags(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag.casefold() == "img":
            values = dict(attrs)
            self.images.append({"src": values.get("src", ""), "alt": values.get("alt", ""), "line": self.getpos()[0], "kind": "HTML"})

    handle_startendtag = handle_starttag


def useful_alt(value: str | None) -> bool:
    clean = html.unescape(value or "")
    clean = re.sub(r"<[^>]*>|[*_~`\\]", "", clean).strip()
    return bool(clean)


def local_target(src: str, base: Path) -> Path | None:
    parsed = urlsplit(html.unescape(src))
    if parsed.scheme or parsed.netloc or src.startswith("#"):
        return None
    return (base / unquote(parsed.path)).resolve()


def audit_svg(path: Path) -> list[str]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        return [f"invalid SVG: {exc}"]
    issues = []
    if root.tag.rsplit("}", 1)[-1] != "svg":
        issues.append("root is not <svg>")
    viewbox = root.attrib.get("viewBox", "")
    try:
        numbers = [float(value) for value in re.split(r"[\s,]+", viewbox.strip())]
        if len(numbers) != 4 or numbers[2] <= 0 or numbers[3] <= 0:
            raise ValueError
        full_width_asset = path.name in {"hero.svg", "architecture.svg", "workflow.svg"} or path.name.startswith("section-")
        if full_width_asset and numbers[2] != 1200:
            issues.append("viewBox width must be 1200 for README assets")
    except ValueError:
        issues.append("missing or invalid viewBox")
    title_found = False
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag == "title" and "".join(node.itertext()).strip():
            title_found = True
        if tag in {"script", "foreignObject", "animate", "animateTransform", "set"}:
            issues.append(f"contains unsupported <{tag}>")
        for key, value in node.attrib.items():
            key = key.rsplit("}", 1)[-1].casefold()
            if key.startswith("on"):
                issues.append(f"contains event handler {key}")
            if key in {"href", "src"} and value.strip().casefold().startswith("javascript:"):
                issues.append("contains JavaScript URL")
            if tag == "image" and key in {"href", "src"} and not value.startswith("data:"):
                issues.append("published SVG depends on a raster image reference")
        if tag == "style":
            style = "".join(node.itertext())
            if re.search(r"@import|@font-face|https?://", style, re.I):
                issues.append("depends on external styles or fonts")
    if not title_found:
        issues.append("missing useful <title>")
    return list(dict.fromkeys(issues))


def audit(readme: Path) -> dict:
    text = visible_markdown(readme.read_text(encoding="utf-8"))
    images, issues = markdown_images(text)
    parser = ImageTags()
    parser.feed(text)
    images.extend(parser.images)
    checked = set()
    svg_checked = set()
    for item in images:
        src = item["src"] or ""
        if not useful_alt(item["alt"]):
            issues.append(f"line {item['line']}: {item['kind']} image missing useful alt text: {src}")
        if not src:
            issues.append(f"line {item['line']}: image has no source")
            continue
        target = local_target(src, readme.parent)
        if target is None:
            continue
        if target in checked:
            continue
        checked.add(target)
        if not target.is_file():
            issues.append(f"missing image: {src}")
            continue
        if target.suffix.casefold() == ".gif":
            fallback = target.with_suffix(".svg")
            if not fallback.is_file():
                issues.append(f"{src}: GIF missing same-name static SVG fallback")
            else:
                svg_checked.add(fallback)
        if target.suffix.casefold() == ".svg":
            svg_checked.add(target)
    for target in sorted(svg_checked):
        for issue in audit_svg(target):
            issues.append(f"{target.relative_to(readme.parent) if target.is_relative_to(readme.parent) else target}: {issue}")
    return {"readme": str(readme), "images": len(images), "local_images_checked": len(checked), "svg_checked": len(svg_checked), "issues": issues, "ok": not issues}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readme", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    readme = args.readme.expanduser().resolve()
    if not readme.is_file():
        parser.error(f"README not found: {readme}")
    try:
        result = audit(readme)
    except (OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"README: {readme}")
        print(f"Local images checked: {result['local_images_checked']}; SVG checked: {result['svg_checked']}")
        if result["issues"]:
            print("Issues:")
            for issue in result["issues"]:
                print(f"- {issue}")
        else:
            print("OK: image references, alt and SVG basics passed")
        print("Visual preview at 900/360 widths still required.")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
