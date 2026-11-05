#!/usr/bin/env python3
"""Report README mechanics as facts; never execute commands or assign review scores.

Usage: readme_factor_audit.py [README-or-repository] [--json] [--output PATH]
Adapted from samber/readme-optimization's MIT readme-audit.sh.
Only the Python standard library is required.
"""

import argparse
from collections import Counter
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


CATEGORIES = {
    "What / 简介": r"intro|about|overview|what is|description|synopsis|简介|介绍|概览|概述|是什么",
    "Why / 差异": r"why|motivation|compar|alternativ|advantage|when to use|trade.?off|为什么|为何|动机|对比|替代|优势|差异|适用|取舍",
    "How / 使用": r"install|usage|getting started|quick.?start|setup|configur|requirement|example|run|build|api|cli|command|安装|使用|用法|入门|快速开始|配置|要求|示例|运行|构建|命令|前提",
    "When / 状态": r"status|roadmap|version|stability|maturity|release|caveat|limitation|known issue|状态|路线图|版本|稳定|成熟|发布|限制|已知问题|维护",
    "Licence / 许可证": r"licen[cs]e|许可证|许可|授权协议|开源协议",
    "References / 文档": r"document|docs|support|faq|resource|related|see also|link|learn more|文档|支持|常见问题|资源|相关|参考|链接|了解更多",
    "Contribution / 贡献": r"contribut|development setup|hacking|dev environment|贡献|开发环境|参与开发",
}
BADGE_SOURCE = re.compile(r"shields\.io|badgen\.|codecov|coveralls|circleci|travis-ci|appveyor|/badge(?:s|/|\.)|badge\.svg", re.I)


def visible_lines(text):
    """Blank fenced/indented/inline code while retaining original line numbers."""
    result, blocks, fence = [], [], None
    for number, line in enumerate(text.splitlines(), 1):
        marker = re.match(r"^\s*(?:>\s*)*(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
            result.append("")
        elif marker:
            fence = (marker[1][0], len(marker[1]))
            blocks.append({"line": number, "language": marker[2].strip()})
            result.append("")
        elif line.startswith("    ") or line.startswith("\t"):
            result.append("")
        else:
            result.append(re.sub(r"(`+).*?\1", lambda match: " " * len(match[0]), line))
    return result, blocks, fence is not None


def word_count(text):
    # CJK has no required spaces. Count characters there and words elsewhere;
    # this is explicitly an estimate, not an automatic B2 score.
    return len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]|[^\W_\u3400-\u4dbf\u4e00-\u9fff]+", text))


def closing(text, start, left, right):
    depth, index = 1, start + 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == left:
            depth += 1
        elif text[index] == right:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def destination(body):
    body = body.strip()
    if body.startswith("<"):
        end = body.find(">")
        return body[1:end] if end >= 0 else None
    value, depth, index = [], 0, 0
    while index < len(body):
        char = body[index]
        if char == "\\" and index + 1 < len(body):
            value.append(body[index + 1])
            index += 2
            continue
        if char.isspace() and depth == 0:
            break
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        value.append(char)
        index += 1
    return "".join(value)


def label_key(label):
    return " ".join(label.split()).casefold()


def markdown_items(lines):
    refs, definition_lines = {}, set()
    for number, line in enumerate(lines, 1):
        match = re.match(r"^ {0,3}\[([^\]]+)\]:\s*(.*)$", line)
        if match:
            value = match[2] or (lines[number].strip() if number < len(lines) else "")
            refs.setdefault(label_key(match[1]), destination(value))
            definition_lines.add(number)
            if not match[2] and number < len(lines):
                definition_lines.add(number + 1)

    items = []
    for number, line in enumerate(lines, 1):
        if number in definition_lines:
            continue
        for index, char in enumerate(line):
            if char != "[" or (index and line[index - 1] == "\\"):
                continue
            image = bool(index and line[index - 1] == "!")
            if image and index > 1 and line[index - 2] == "\\":
                continue
            end = closing(line, index, "[", "]")
            if end is None:
                continue
            label, after = line[index + 1:end], end + 1
            value, reference = None, None
            if after < len(line) and line[after] == "(":
                dest_end = closing(line, after, "(", ")")
                if dest_end is None:
                    continue
                value = destination(line[after + 1:dest_end])
            elif after < len(line) and line[after] == "[":
                ref_end = closing(line, after, "[", "]")
                if ref_end is None:
                    continue
                reference = line[after + 1:ref_end] or label
                value = refs.get(label_key(reference))
            elif label_key(label) in refs:
                value = refs[label_key(label)]
            else:
                continue
            items.append({"line": number, "kind": "image" if image else "link", "alt": label if image else None,
                          "destination": value, "reference": reference, "syntax": "markdown"})
    return items


class HTMLItems(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items, self.tags = [], Counter()

    def handle_starttag(self, tag, attrs):
        self.tags[tag] += 1
        attrs = dict(attrs)
        number = self.getpos()[0]
        if tag == "img":
            self.items.append({"line": number, "kind": "image", "alt": attrs.get("alt"),
                               "destination": attrs.get("src"), "reference": None, "syntax": "html"})
        elif tag == "a" and attrs.get("href"):
            self.items.append({"line": number, "kind": "link", "alt": None,
                               "destination": attrs["href"], "reference": None, "syntax": "html"})
        elif tag == "source" and attrs.get("src"):
            self.items.append({"line": number, "kind": "link", "alt": None,
                               "destination": attrs["src"], "reference": None, "syntax": "html"})
        if tag in {"img", "source"} and attrs.get("srcset") and not attrs["srcset"].startswith("data:"):
            for candidate in attrs["srcset"].split(","):
                if candidate.strip():
                    self.items.append({"line": number, "kind": "link", "alt": None,
                                       "destination": candidate.split()[0], "reference": None, "syntax": "html-srcset"})

    handle_startendtag = handle_starttag


def locate(target, explicit_root=None):
    target = target.resolve()
    shadowed = []
    if target.is_dir():
        root = target
        candidates = [target / part for part in (".github/README.md", "README.md", "docs/README.md")]
        found = [path for path in candidates if path.is_file()]
        if not found:
            raise ValueError(f"No README found under {target} (.github/, root, docs/)")
        file, shadowed = found[0], found[1:]
    elif target.is_file():
        file, root = target, target.parent
        if root.name in {".github", "docs"}:
            root = root.parent
    else:
        raise ValueError(f"Not a README file or repository directory: {target}")
    return file, (explicit_root.resolve() if explicit_root else root), shadowed


def audit(target, explicit_root=None):
    file, root, shadowed = locate(target, explicit_root)
    text = file.read_text(encoding="utf-8", errors="replace")
    lines, blocks, unclosed_fence = visible_lines(text)
    headings = []
    for number, line in enumerate(lines, 1):
        match = re.match(r"^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            headings.append({"line": number, "level": len(match[1]), "text": match[2]})
        elif number > 1 and re.fullmatch(r" {0,3}(?:={3,}|-{3,})\s*", line) and lines[number - 2].strip():
            previous = lines[number - 2].strip()
            if not re.match(r"^(?:#|>|[-*+]\s|\d+[.)]\s)", previous):
                headings.append({"line": number - 1, "level": 1 if "=" in line else 2, "text": previous})

    items = markdown_items(lines)
    html = HTMLItems()
    html.feed("\n".join(lines))
    items.extend(html.items)
    images = [item for item in items if item["kind"] == "image"]
    empty_alt = [item for item in images if not unescape(item["alt"] or "").strip()]
    broken, unresolved, missing_destination = [], [], []
    seen = set()
    for item in items:
        value = item["destination"]
        if value is None:
            (unresolved if item["reference"] is not None else missing_destination).append(item)
            continue
        value = unescape(value).strip()
        if not value or value.startswith("#"):
            continue
        try:
            parsed = urlsplit(value)
        except ValueError:
            broken.append({**item, "reason": "invalid URL"})
            continue
        if parsed.scheme or parsed.netloc:
            continue
        path = unquote(parsed.path)
        if not path:
            continue
        resolved = root / path.lstrip("/") if path.startswith("/") else file.parent / path
        key = (item["line"], value)
        if not resolved.exists() and key not in seen:
            broken.append({**item, "resolved": str(resolved.resolve()), "reason": "missing path"})
            seen.add(key)

    first = dict(blocks[0]) if blocks else None
    if first:
        first["words_before"] = word_count("\n".join(lines[:first["line"] - 1]))
    warnings = []
    size = len(file.read_bytes())
    if size > 512000:
        warnings.append("Over 500 KiB: GitHub rendered README truncation risk")
    if unclosed_fence:
        warnings.append("Unclosed code fence: following prose may be hidden as code")
    if shadowed:
        warnings.append("Multiple README locations: the selected host copy can diverge from the root README")
    placeholders = [{"line": number, "text": line.strip()} for number, line in enumerate(lines, 1)
                    if re.search(r"\bTODO\b|\bFIXME\b|coming soon|lorem ipsum|<your |\bxxx+\b|placeholder|\[insert |待补充|待完善|占位|敬请期待", line, re.I)]
    return {
        "file": str(file), "repository_root": str(root), "shadowed": [str(path) for path in shadowed],
        "size": {"bytes": size, "lines": len(text.splitlines()), "words_estimate": word_count(text)},
        "headings": headings, "section_count": sum(heading["level"] >= 2 for heading in headings),
        "first_code_block": first, "code_blocks": blocks,
        "badges_first_40_lines": sum(item["line"] <= 40 and bool(BADGE_SOURCE.search(item["destination"] or "")) for item in images),
        "images": images, "empty_alt": empty_alt, "html_tags": dict(sorted(html.tags.items())),
        "github_alerts": sum(bool(re.match(r"^\s*>\s*\[!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", line)) for line in lines),
        "broken_relative_links": broken, "unresolved_reference_links": unresolved,
        "missing_image_destinations": missing_destination,
        "content_categories": {name: any(re.search(pattern, heading["text"], re.I) for heading in headings)
                               for name, pattern in CATEGORIES.items()},
        "placeholders": placeholders[:10],
        "handwritten_toc": [heading for heading in headings if re.fullmatch(r"table of contents|contents|目录|目次|内容目录", heading["text"], re.I)],
        "warnings": warnings,
        "limitations": ["Mechanical facts only: no command execution, claim verification, remote-link fetch or A/B score.",
                        "Word counts estimate CJK characters and words elsewhere; inspect the actual first screen.",
                        "Markdown parsing covers common inline/reference images and links, not every extension."],
    }


def as_text(report):
    size, first = report["size"], report["first_code_block"]
    output = [f"FILE: {report['file']}",
              f"SIZE: {size['bytes']} bytes / {size['lines']} lines / {size['words_estimate']} estimated words", "HEADINGS:"]
    output.extend(f"  line {item['line']}: {'#' * item['level']} {item['text']}" for item in report["headings"])
    if not report["headings"]:
        output.append("  (none)")
    output.append(f"SECTION COUNT (h2-h6): {report['section_count']} [descriptive, not a score]")
    output.append(f"FIRST CODE BLOCK: line {first['line']}, after {first['words_before']} estimated words, language={first['language'] or '(none)'}"
                  if first else "FIRST CODE BLOCK: none")
    output.extend([f"BADGE-LIKE IMAGES IN FIRST 40 LINES: {report['badges_first_40_lines']}",
                   f"IMAGES WITH EMPTY/MISSING ALT: {len(report['empty_alt'])}"])
    output.extend(f"  line {item['line']}: {item['destination'] or item['reference'] or '(no source)'} ({item['syntax']})" for item in report["empty_alt"])
    output.extend([f"RAW HTML TAGS: {json.dumps(report['html_tags'], ensure_ascii=False)}",
                   f"GITHUB ALERTS: {report['github_alerts']}"])
    for key, title in (("shadowed", "SHADOWED READMES"), ("broken_relative_links", "BROKEN RELATIVE LINKS"),
                       ("unresolved_reference_links", "UNRESOLVED REFERENCE LINKS"),
                       ("missing_image_destinations", "MISSING IMAGE SOURCES")):
        output.append(title + ":")
        if not report[key]:
            output.append("  (none)")
        for item in report[key]:
            output.append("  " + item if isinstance(item, str) else f"  line {item['line']}: {item['destination'] or item['reference'] or '(no source)'}")
    output.append("CONTENT CATEGORIES (heading heuristic, not required sections):")
    output.extend(f"  {name}: {'present' if present else 'not detected'}" for name, present in report["content_categories"].items())
    output.append("PLACEHOLDERS:")
    output.extend(f"  line {item['line']}: {item['text']}" for item in report["placeholders"])
    if not report["placeholders"]:
        output.append("  (none)")
    output.extend(f"HAND-WRITTEN TOC: line {item['line']} ({item['text']})" for item in report["handwritten_toc"])
    output.extend("WARNING: " + item for item in report["warnings"])
    output.extend("LIMIT: " + item for item in report["limitations"])
    return "\n".join(output) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", default=".", type=Path)
    parser.add_argument("--repo-root", type=Path, help="Root for repository-absolute /path links")
    parser.add_argument("--json", action="store_true", help="Emit mechanical facts as JSON")
    parser.add_argument("--output", type=Path, help="Write the report instead of stdout")
    args = parser.parse_args()
    try:
        report = audit(args.target, args.repo_root)
        result = json.dumps(report, ensure_ascii=False, indent=2) + "\n" if args.json else as_text(report)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(result, encoding="utf-8")
        else:
            sys.stdout.write(result)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
