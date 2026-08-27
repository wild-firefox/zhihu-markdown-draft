# Zhihu Markdown import compatibility

Read this reference when preparing Markdown that contains formulas, dollar signs, tables, emphasis, task lists, footnotes, indented code, or when visible Markdown markers appear after import.

These findings were reproduced in Zhihu's article editor on 2026-08-27 with a dedicated draft. The editor can change, so use the bundled fixture to retest when behavior differs.

## Compatibility matrix

| Markdown source | Observed Zhihu result | Preparation rule |
|---|---|---|
| `**bold**` | Bold renders normally in ordinary paragraphs | Keep unless the user requests plain text |
| `__bold__` | Bold renders normally | Prefer `**bold**` for consistency |
| `*italic*` | Asterisks remain visible | Avoid |
| `_italic_` | Underscores remain visible | Avoid |
| `***bold italic***` | Bold italic renders | Supported in ordinary paragraphs |
| `~~strike~~` | Strikethrough renders | Supported |
| Inline backticks | Inline code renders and preserves literal `$` and `**` | Supported |
| Fenced code | Code block renders | Preferred code-block form |
| Four-space indented code | Math-like text may become `<!--MATH_PH...-->` | Convert to fenced code |
| `$E=mc^2$` | Inline formula renders | Use only for complete math |
| `$$...$$` | Display formula renders | Supported |
| `\\(...\\)` / `\\[...\\]` | Renders after preprocessing to dollar delimiters | Convert before import |
| Currency `$100` in prose | Can pair with a later `$` across paragraphs and absorb prose into a formula | Replace with `USD 100`, `100 美元`, or `￥100` |
| Raw `\\frac{1}{2}` | LaTeX command remains visible | Wrap in a complete formula or use Unicode/plain text |
| Formatting inside tables | Markers may disappear while formatting is lost | Use plain text in cells |
| Formula inside tables | Delimiters can disappear without formula rendering | Use Unicode/plain text in cells |
| Markdown H2-H6 | All become the same visible Zhihu heading level | Apply headings only to intended TOC entries |
| Nested ordered/unordered lists | Nesting renders | Supported |
| Task list `- [x]` | `[x]` / `[ ]` remains visible | Use a normal list or Unicode checkbox |
| Standard link `[text](URL)` | Link renders | Preferred |
| Angle autolink `<URL>` | Link renders | Supported |
| Bare URL followed by CJK text | Trailing text can become part of the URL | Use a standard link |
| `<strong>` / `<br>` | Renders in the tested editor | Do not rely on broader HTML support |
| Markdown footnote | Reference becomes a malformed link and definition can disappear | Use an ordinary `注：` paragraph |
| Named HTML entities | Some remain literal | Write the intended character directly |

## Required checks before import

1. Treat currency-like dollar signs as blocking until resolved.
2. Ensure each formula delimiter is intentional and paired on the same logical expression.
3. Rewrite table math and table formatting as plain text or Unicode.
4. Convert four-space indented code to fenced code.
5. Replace Markdown footnotes and task-list syntax.
6. Review every heading because heading depth is not preserved.
7. After import, inspect rendered DOM and visible text: a legitimate formula should become a formula node, while prose should contain no leftover `$`, raw LaTeX, or accidental `<!--MATH_PH...-->` markers.

## Reproducible fixture

The intentionally problematic test article is stored at `assets/markdown-compatibility-test.md`. Copy it to a temporary directory before running `prepare_zhihu_markdown.py`. Import it only into a new test draft, never into a real article draft.
