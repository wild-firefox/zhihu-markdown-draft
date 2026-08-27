---
name: zhihu-markdown-draft
description: Prepare Markdown articles and local images for Zhihu's article editor, detect known Zhihu Markdown incompatibilities, import into an existing or new Zhihu draft, and verify the saved draft without publishing. Use when a user asks to move a local Markdown article into 知乎专栏/知乎文章草稿 or diagnose that import workflow.
---

# Zhihu Markdown Draft

Turn a local Markdown article into a correctly formatted Zhihu article draft. Preserve the source document, make a dedicated import copy, detect import hazards, upload local images, and stop at a saved draft unless the user separately asks to publish.

## Scope and authorization

- Treat the local Markdown file as the canonical source. Never overwrite it merely to satisfy Zhihu-specific limitations; create a sibling import copy unless the user explicitly requests canonical-source changes.
- Importing a document, uploading images, and editing a cloud draft are external mutations. Follow the Browser confirmation policy at the moment required. Publishing is a separate action and is never implied by “导入”, “写入”, or “存入草稿”.
- Before replacing a nonempty editor body, explain that it will be cleared and re-imported, then obtain the confirmation required for deleting cloud content.
- Do not repeatedly import into a nonempty Zhihu editor: Zhihu appends imported content and can create duplicate articles.
- On first use, the user may need to complete Zhihu sign-in or QR-code login in the selected browser. Never request, read, or store their password, cookies, QR payload, or login token.

## Compatibility preflight

Read [references/zhihu-markdown-compatibility.md](references/zhihu-markdown-compatibility.md) whenever the source contains formulas, dollar signs, tables, italic markup, footnotes, task lists, indented code, or when the user reports raw Markdown symbols in Zhihu.

Important invariants from live-editor testing:

- Ordinary `**bold**` works. Do not remove it universally; visible `**` usually indicates escaping, code context, table loss, or a parser-corrupted paragraph.
- A currency-like `$100` outside code is dangerous because Zhihu can pair it with a later `$` across paragraphs and turn intervening prose into a formula. Use `USD 100`, `100 美元`, or `￥100` instead.
- Keep `$...$` and `$$...$$` only for complete mathematical expressions.
- Table cells should use plain text or Unicode math. Inline emphasis, code, and LaTeX are not reliable there.
- Zhihu collapses Markdown H2-H6 into one visible heading level. Use heading markers only for content that should enter the native table of contents.
- Prefer fenced code blocks, standard Markdown links, and plain “注：” paragraphs over indented code, bare URLs followed by CJK text, and Markdown footnotes.

## Workflow

1. Identify the source Markdown, desired article title, local image paths, target Zhihu draft URL, whether a native table of contents is requested, and whether the user wants draft-only or publication.
2. Run `scripts/prepare_zhihu_markdown.py` to create a Zhihu import copy and a JSON report. The script:
   - removes the first H1 when requested, so the editor title is not duplicated;
   - converts `\\(...\\)` / `\\[...\\]` math delimiters to `$...$` / `$$...$$` outside fenced code;
   - replaces local Markdown images with stable numbered placeholders and records their absolute paths;
   - flags table rows containing math or inline formatting;
   - flags currency-like dollar signs, unbalanced math delimiters, raw LaTeX, unsupported italics, task lists, footnotes, indented code, deep headings, and risky bare URLs.
3. Read the JSON report. Resolve every missing image, table-math warning, and blocking compatibility warning before browser import. Review non-blocking compatibility warnings and either fix them or document why they are intentional. For table cells, use concise Unicode/plain-text math such as `η(π̃)`, `ρπ`, `Âₜ`, `H⁻¹g`, `½ΔθᵀHΔθ`, `βₘₐₓ`, and `O(α²)`. Keep full formal equations outside tables.
4. If the task includes browser import, read [references/zhihu-editor-workflow.md](references/zhihu-editor-workflow.md) and use the Browser skill's in-app browser workflow. Reuse the signed-in target tab when available.
5. Import only into an empty editor body, with one deliberate exception: when the user requests a table of contents, insert exactly one native Zhihu TOC block into the cleared body first, then import the article so it appends below the TOC. Do not type a manual heading list. Set the title separately and wait for Zhihu to finish parsing and autosaving.
6. Upload local images to Zhihu first. Capture their resulting Zhihu-hosted URLs, replace the numbered placeholders in the import copy, then clear and re-import once. This avoids unreliable cursor placement in very long Draft.js documents. If a TOC is requested, insert it only after the final clear and immediately before the final import, not during the temporary placeholder import.
7. Verify the saved draft before handoff:
   - one copy of the first and last section;
   - zero TOC blocks when none was requested, or exactly one populated native TOC block when requested;
   - no image placeholders remain;
   - expected article-image count and correct surrounding sections;
   - no `\\command`, `_{...}`, or raw inline-math delimiters remain in table cells;
   - no unintended literal `**`, single-star/single-underscore italic markers, `<!--MATH_PH...-->`, or currency-like dollar delimiters remain;
   - headings, block formulas, links, tables, and at least one image visually render;
   - the status shows a saved draft, not “保存中”;
   - the Publish button was not used unless separately authorized.

## Preparation command

Use an absolute interpreter path when Python is not on `PATH`:

```powershell
python scripts/prepare_zhihu_markdown.py SOURCE.md --output ARTICLE_知乎导入版.md --strip-first-h1
```

The generated report is written beside the output as `ARTICLE_知乎导入版.report.json`. Inspect it rather than assuming conversion succeeded. Use `--fail-on-compatibility-errors` in automated checks when blocking warnings should produce a nonzero exit status.

For a reproducible diagnostic article, copy [assets/markdown-compatibility-test.md](assets/markdown-compatibility-test.md) into a temporary working directory and import it only into a separate test draft. It intentionally contains broken cases and must never be substituted for a normal article.
