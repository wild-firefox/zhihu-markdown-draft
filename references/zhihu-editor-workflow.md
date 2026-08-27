# Zhihu editor workflow

Read this reference only when the task includes interacting with the live Zhihu article editor.

## Important editor behavior

- Zhihu imports Markdown into its Draft.js-based rich-text editor.
- Importing into a nonempty body appends content. It does not safely replace the article.
- A single intentionally pre-inserted native TOC block is the only supported exception to the empty-body import rule: appending the article below that block is deliberate.
- Long imported documents may not accept reliable automated cursor placement at a searched paragraph. Use the hosted-image/re-import method instead of trying to insert each image at a placeholder with mouse coordinates.
- Block formulas generally import correctly after `\\[...\\]` becomes `$$...$$`. Inline formulas inside Markdown tables do not: delimiters may disappear while LaTeX commands remain as visible text.
- Clearing a Draft.js body with locator `fill("")` may have no effect. After the required confirmation, focus the main contenteditable body, press `Control+A`, then `Backspace`, and verify that the displayed word count is zero.
- Draft image URLs can be private, signed, and time-limited. They are suitable for immediately rebuilding the same draft, but a stale import copy may require re-uploading its local images later.

## Browser sequence

Use the Browser skill and read its file-upload documentation before uploading.

1. Reuse or claim the Zhihu editor tab. On first use, the browser may show Zhihu's login page; ask the user to complete QR-code or other sign-in themselves in that same browser, then resume only after the editor is authenticated. Never inspect credentials, cookies, QR payloads, or tokens.
2. Inspect the URL, title field, body, word count, draft status, and whether Publish is enabled.
3. If the body is nonempty and replacement is required, stop at the destructive step and obtain the required confirmation. Clear it only after confirmation, then verify word count `0` and that the title remains intact.
4. Open the toolbar's Import menu, choose document import, open the local-document chooser, and upload the prepared `.md` file. The import UI can have two layers: choosing "导入文档" first opens a modal; the modal's local-document button is what emits the file chooser.
5. Wait until the first and last headings each occur once. Set the article title in the title textbox.

## Native table of contents

Add a TOC only when the user requests it. Use Zhihu's native "目录" block so it updates from the document headings; do not build a manual list of links.

For a fresh or rebuilt draft, use this reliable sequence:

1. Finish all preparation, hosted-image replacement, and table-math repair first.
2. At the final rebuild, obtain any confirmation required to clear the cloud body, then verify that the word count is zero.
3. While the body is empty, activate the toolbar's "目录" control exactly once. Verify that one native TOC block now exists.
4. Import the final prepared Markdown. In this one case, the import is expected to append below the TOC.
5. Verify that the TOC populated from the imported heading hierarchy, the first article section follows it, and no second TOC was created.

For an existing draft that will not be rebuilt, first detect whether a native TOC already exists. If none exists, place the editor selection at the stable start of the body and use the native "目录" control once. Confirm the resulting TOC position and contents visually. If the editor cannot verify the insertion point, stop rather than risk inserting a TOC in the middle of a long article.

Treat inserting or removing a TOC as a cloud-draft edit and follow the Browser confirmation policy. TOC insertion never authorizes publishing.

## Local-image insertion for long articles

Use this method when the report contains local image placeholders.

1. Import the placeholder version into an empty body so the article structure is available for inspection.
2. Open the Image tool, choose the upload tab, activate the local-image upload control, and set one or more files through the file chooser.
3. The upload panel may require a separate "插入图片" action after files reach the uploaded list. Perform it only within the user's authorization.
4. Read the inserted article images' `src` or `data-original-src` attributes. Match them to the local files by upload order and image dimensions when needed.
5. In the prepared Markdown copy, replace each `【ZHIHU_IMAGE_NNN：...】` marker with `![alt](ZHIHU_HOSTED_URL)`.
6. Obtain confirmation for clearing the nonempty cloud draft, clear it, and import the final prepared file exactly once.
7. Confirm that no marker remains and that each image appears near the intended surrounding paragraphs. Do not rely only on total image count: avatars and application logos also appear as `<img>` elements, so scope checks to article images.

## Table-math repair

Before import, rewrite math inside table cells to compact Unicode/plain text. Examples:

| LaTeX-like source | Table-safe form |
|---|---|
| `\\eta(\\tilde\\pi)` | `η(π̃)` |
| `\\rho_\\pi` | `ρπ` |
| `\\hat A_t` | `Âₜ` |
| `H^{-1}g` | `H⁻¹g` |
| `\\frac12\\Delta\\theta^\\top H\\Delta\\theta` | `½ΔθᵀHΔθ` |
| `\\beta_{\\max}` | `βₘₐₓ` |
| `O(\\alpha^2)` | `O(α²)` |

For long identities, keep the exact display equation outside the table and put only a compact reminder or an equation reference in the cell. Never silently change the mathematics to make it shorter.

After import, inspect every table cell for:

- backslash commands such as `\\eta`, `\\frac`, or `\\mathrm`;
- raw subscript/superscript groups such as `_{...}` and `^{...}`;
- leftover `$` or `\\(...\\)` delimiters;
- clipped rows, unintended line breaks, or duplicated text.

If repairing the live draft directly, use the table cell's editable control and replace only the affected cell. Keep a parallel change in the prepared Markdown copy so a later import does not reintroduce the defect.

## Final verification

Verify observable state rather than assuming autosave succeeded:

- exact title;
- expected word count range;
- requested TOC state: exactly one populated native TOC, or none when not requested;
- first and last headings each appear once;
- expected table count and image count;
- no image placeholders or raw table LaTeX;
- spot-check a block formula, the densest table, and at least one image visually;
- status changes from "保存中" to a saved-draft timestamp;
- no Publish action occurred.

Leave the editor tab available to the user at the most useful inspection position.
