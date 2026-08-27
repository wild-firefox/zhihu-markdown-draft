#!/usr/bin/env python3
"""Prepare a Markdown article for import into Zhihu's article editor."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
H1_RE = re.compile(r"^#\s+(.+?)\s*$")
IMAGE_RE = re.compile(
    r"!\[([^\]]*)\]\((<[^>]+>|[^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)"
)
INLINE_CODE_RE = re.compile(r"(`+)(.*?)(\1)")
TABLE_MATH_RE = re.compile(r"\$|\\(?:frac|sum|mathbb|mathrm|text|hat|bar|tilde|sqrt|eta|pi|rho|gamma|delta|beta|alpha|theta|Delta|le|ge|to|top|approx|propto|lvert|rvert)\b")
TABLE_SEPARATOR_RE = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
TABLE_FORMAT_RE = re.compile(r"\*\*|__|~~|`|(?<!\*)\*(?!\*)|(?<!_)_(?!_)")
CURRENCY_DOLLAR_RE = re.compile(r"(?<!\\)\$(?=\d)")
UNESCAPED_DOLLAR_RE = re.compile(r"(?<!\\)\$")
RAW_LATEX_RE = re.compile(
    r"\\(?:frac|sum|mathbb|mathrm|text|hat|bar|tilde|sqrt|eta|pi|rho|gamma|delta|beta|alpha|theta|Delta|le|ge|to|top|approx|propto|lvert|rvert)\b"
)
SINGLE_STAR_ITALIC_RE = re.compile(r"(?<![\\*])\*([^*\n]+)\*(?!\*)")
SINGLE_UNDERSCORE_ITALIC_RE = re.compile(r"(?<![\\\w_])_([^_\n]+)_(?![\w_])")
TASK_LIST_RE = re.compile(r"^\s*[-+*]\s+\[[ xX]\]\s+")
FOOTNOTE_RE = re.compile(r"\[\^[^\]]+\]")
INDENTED_CODE_RE = re.compile(r"^(?: {4}|\t)(?![-+*]\s|\d+[.)]\s)\S")
DEEP_HEADING_RE = re.compile(r"^#{3,6}\s+")
RISKY_BARE_URL_RE = re.compile(r"(?<![<(])https?://[^\s<>()\]]*[\u3000-\u9fff\uff00-\uffef]")
NAMED_HTML_ENTITY_RE = re.compile(r"&(?:lt|gt|copy|nbsp);", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Zhihu-oriented Markdown copy plus an image/warning report."
    )
    parser.add_argument("source", type=Path, help="Source Markdown file")
    parser.add_argument("--output", type=Path, help="Prepared Markdown output path")
    parser.add_argument("--report", type=Path, help="JSON report output path")
    parser.add_argument(
        "--strip-first-h1",
        action="store_true",
        help="Remove the first H1 so it can be used as the Zhihu editor title",
    )
    parser.add_argument(
        "--fail-on-missing-images",
        action="store_true",
        help="Return a nonzero status when a referenced local image is missing",
    )
    parser.add_argument(
        "--fail-on-compatibility-errors",
        action="store_true",
        help="Return a nonzero status when blocking Zhihu compatibility warnings remain",
    )
    return parser.parse_args()


def default_output(source: Path) -> Path:
    return source.with_name(f"{source.stem}_知乎导入版{source.suffix}")


def is_remote_image(target: str) -> bool:
    if re.match(r"^[A-Za-z]:[\\/]", target):
        return False
    scheme = urlparse(target).scheme.lower()
    return scheme in {"http", "https", "data", "blob"}


def resolve_local_image(source_dir: Path, target: str) -> Path:
    clean = unquote(target.strip("<>"))
    candidate = Path(clean)
    if not candidate.is_absolute():
        candidate = source_dir / candidate
    return candidate.resolve()


def convert_math_delimiters_outside_inline_code(line: str) -> tuple[str, int]:
    conversions = 0
    output: list[str] = []
    cursor = 0
    for match in INLINE_CODE_RE.finditer(line):
        plain = line[cursor : match.start()]
        converted, count = convert_math_delimiters(plain)
        output.extend((converted, match.group(0)))
        conversions += count
        cursor = match.end()
    converted, count = convert_math_delimiters(line[cursor:])
    output.append(converted)
    return "".join(output), conversions + count


def mask_inline_code(line: str) -> str:
    """Replace inline-code content with spaces while preserving character offsets."""
    output: list[str] = []
    cursor = 0
    for match in INLINE_CODE_RE.finditer(line):
        output.append(line[cursor : match.start()])
        output.append(" " * (match.end() - match.start()))
        cursor = match.end()
    output.append(line[cursor:])
    return "".join(output)


def compatibility_warning(
    source_line: int,
    category: str,
    severity: str,
    excerpt: str,
    guidance: str,
) -> dict:
    return {
        "source_line": source_line,
        "category": category,
        "severity": severity,
        "excerpt": excerpt.strip(),
        "guidance": guidance,
    }


def convert_math_delimiters(text: str) -> tuple[str, int]:
    replacements = ((r"\[", "$$"), (r"\]", "$$"), (r"\(", "$"), (r"\)", "$"))
    count = 0
    for old, new in replacements:
        count += text.count(old)
        text = text.replace(old, new)
    return text, count


def markdown_table_line_numbers(lines: list[str]) -> set[int]:
    """Return one-based line numbers belonging to actual Markdown tables."""
    result: set[int] = set()
    for index in range(len(lines) - 1):
        if "|" not in lines[index] or not TABLE_SEPARATOR_RE.match(lines[index + 1].rstrip("\r\n")):
            continue
        cursor = index
        while cursor < len(lines):
            stripped = lines[cursor].strip()
            if not stripped or "|" not in stripped:
                break
            result.add(cursor + 1)
            cursor += 1
    return result


def prepare(source: Path, output: Path, report_path: Path, strip_first_h1: bool) -> dict:
    raw = source.read_text(encoding="utf-8-sig")
    lines = raw.splitlines(keepends=True)
    source_dir = source.parent.resolve()
    title: str | None = None
    stripped_h1 = False
    in_fence = False
    fence_char = ""
    in_display_math = False
    delimiter_conversions = 0
    images: list[dict] = []
    table_warnings: list[dict] = []
    table_format_warnings: list[dict] = []
    compatibility_warnings: list[dict] = []
    prepared: list[str] = []
    table_lines = markdown_table_line_numbers(lines)

    for source_line_number, line in enumerate(lines, start=1):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)[0]
            if not in_fence:
                in_fence = True
                fence_char = marker
            elif marker == fence_char:
                in_fence = False
                fence_char = ""
            prepared.append(line)
            continue

        if not in_fence:
            h1_match = H1_RE.match(line.rstrip("\r\n"))
            if h1_match and title is None:
                title = h1_match.group(1).strip()
                if strip_first_h1 and not stripped_h1:
                    stripped_h1 = True
                    continue

            def image_replacer(match: re.Match[str]) -> str:
                target = match.group(2).strip("<>")
                if is_remote_image(target):
                    return match.group(0)
                absolute = resolve_local_image(source_dir, target)
                number = len(images) + 1
                alt = match.group(1).strip() or absolute.stem
                marker = f"【ZHIHU_IMAGE_{number:03d}：{alt}】"
                images.append(
                    {
                        "id": number,
                        "marker": marker,
                        "alt": alt,
                        "source_target": target,
                        "absolute_path": str(absolute),
                        "exists": absolute.is_file(),
                    }
                )
                return marker

            line = IMAGE_RE.sub(image_replacer, line)
            line, count = convert_math_delimiters_outside_inline_code(line)
            delimiter_conversions += count

            stripped = line.strip()
            if source_line_number in table_lines and TABLE_MATH_RE.search(line):
                table_warnings.append(
                    {
                        "source_line": source_line_number,
                        "row": stripped,
                        "guidance": "Rewrite inline LaTeX in this table row as Unicode/plain text before import.",
                    }
                )
            if source_line_number in table_lines and TABLE_FORMAT_RE.search(line):
                table_format_warnings.append(
                    {
                        "source_line": source_line_number,
                        "row": stripped,
                        "guidance": "Use plain text in Zhihu table cells; emphasis and inline-code formatting may be lost.",
                    }
                )

            masked = mask_inline_code(line)
            display_delimiter_count = len(re.findall(r"(?<!\\)\$\$", masked))
            in_display_context = in_display_math or bool(display_delimiter_count)
            if source_line_number not in table_lines:
                if not in_display_context and CURRENCY_DOLLAR_RE.search(masked):
                    compatibility_warnings.append(
                        compatibility_warning(
                            source_line_number,
                            "currency-dollar",
                            "error",
                            stripped,
                            "Replace currency-like $ amounts with 'USD 100', '100 美元', or '￥100'; Zhihu may pair the dollar sign with a later formula delimiter across paragraphs.",
                        )
                    )
                dollar_count = len(UNESCAPED_DOLLAR_RE.findall(masked))
                if not in_display_context and dollar_count % 2:
                    compatibility_warnings.append(
                        compatibility_warning(
                            source_line_number,
                            "unbalanced-dollar-delimiter",
                            "error",
                            stripped,
                            "Keep each mathematical expression inside a complete $...$ pair on the same logical expression.",
                        )
                    )
                if not in_display_context and RAW_LATEX_RE.search(masked) and "$" not in masked:
                    compatibility_warnings.append(
                        compatibility_warning(
                            source_line_number,
                            "raw-latex",
                            "error",
                            stripped,
                            "Wrap complete mathematics in supported delimiters or rewrite it as Unicode/plain text.",
                        )
                    )
                if not in_display_context and SINGLE_STAR_ITALIC_RE.search(masked):
                    compatibility_warnings.append(
                        compatibility_warning(
                            source_line_number,
                            "single-star-italic",
                            "warning",
                            stripped,
                            "Zhihu may display single-star italic markers literally; use plain text or another deliberate style.",
                        )
                    )
                if not in_display_context and SINGLE_UNDERSCORE_ITALIC_RE.search(masked):
                    compatibility_warnings.append(
                        compatibility_warning(
                            source_line_number,
                            "single-underscore-italic",
                            "warning",
                            stripped,
                            "Zhihu may display single-underscore italic markers literally; use plain text or another deliberate style.",
                        )
                    )
                if TASK_LIST_RE.match(masked):
                    compatibility_warnings.append(
                        compatibility_warning(
                            source_line_number,
                            "task-list",
                            "warning",
                            stripped,
                            "Replace Markdown task-list syntax with a normal list or Unicode checkbox.",
                        )
                    )
                if FOOTNOTE_RE.search(masked):
                    compatibility_warnings.append(
                        compatibility_warning(
                            source_line_number,
                            "footnote",
                            "error",
                            stripped,
                            "Replace Markdown footnotes with ordinary '注：' paragraphs.",
                        )
                    )
                if INDENTED_CODE_RE.match(line):
                    compatibility_warnings.append(
                        compatibility_warning(
                            source_line_number,
                            "indented-code",
                            "error",
                            stripped,
                            "Convert four-space indented code to a fenced code block.",
                        )
                    )
                if DEEP_HEADING_RE.match(line):
                    compatibility_warnings.append(
                        compatibility_warning(
                            source_line_number,
                            "deep-heading",
                            "warning",
                            stripped,
                            "Zhihu collapses Markdown H2-H6 to one visible level; keep a heading only if it should enter the native TOC.",
                        )
                    )
                if RISKY_BARE_URL_RE.search(masked):
                    compatibility_warnings.append(
                        compatibility_warning(
                            source_line_number,
                            "bare-url-cjk-suffix",
                            "warning",
                            stripped,
                            "Use [text](URL); Zhihu can absorb adjacent CJK text or punctuation into a bare URL.",
                        )
                    )
                if NAMED_HTML_ENTITY_RE.search(masked):
                    compatibility_warnings.append(
                        compatibility_warning(
                            source_line_number,
                            "named-html-entity",
                            "warning",
                            stripped,
                            "Write the intended character directly because named HTML entities are not consistently decoded.",
                        )
                    )

            if display_delimiter_count % 2:
                in_display_math = not in_display_math

        prepared.append(line)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(prepared), encoding="utf-8", newline="")

    missing = [item for item in images if not item["exists"]]
    blocking_compatibility_warnings = [
        item for item in compatibility_warnings if item["severity"] == "error"
    ]
    report = {
        "source": str(source.resolve()),
        "output": str(output.resolve()),
        "detected_title": title,
        "stripped_first_h1": stripped_h1,
        "math_delimiter_conversions": delimiter_conversions,
        "local_images": images,
        "missing_local_images": missing,
        "table_math_warnings": table_warnings,
        "table_format_warnings": table_format_warnings,
        "compatibility_warnings": compatibility_warnings,
        "blocking_compatibility_warnings": blocking_compatibility_warnings,
        "next_step": "Resolve missing images, table-math warnings, and blocking compatibility warnings; review other compatibility warnings; then import only into an empty Zhihu editor body.",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline=""
    )
    return report


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    if not source.is_file():
        print(f"Source Markdown not found: {source}", file=sys.stderr)
        return 2
    output = (args.output or default_output(source)).resolve()
    report_path = (args.report or output.with_suffix(".report.json")).resolve()
    report = prepare(source, output, report_path, args.strip_first_h1)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.fail_on_missing_images and report["missing_local_images"]:
        return 3
    if args.fail_on_compatibility_errors and report["blocking_compatibility_warnings"]:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
