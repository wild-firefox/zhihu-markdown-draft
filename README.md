# Zhihu Markdown Draft

一个用于 Codex 的 Skill：把本地 Markdown 文章整理后导入知乎文章编辑器，处理本地图片、公式与表格兼容问题、原生目录和草稿验证。

默认行为是**只保存草稿，不发布文章**。

## 功能

- 保留原始 Markdown，生成专用的“知乎导入版”副本。
- 可移除第一个一级标题，避免与知乎标题重复。
- 转换常见的 LaTeX 行内与块级公式分隔符。
- 将本地图片替换成稳定占位符并生成检查报告。
- 检测危险的货币 `$`、未配对公式、裸 LaTeX、表格格式、斜体、脚注、任务列表、缩进代码和标题层级。
- 支持知乎原生目录，而不是手写目录列表。
- 导入后检查标题、目录、图片、表格、公式和草稿保存状态。

## 安装

### 使用 Skill Installer（推荐）

把仓库地址发送给 Codex：

```text
使用 $skill-installer 安装这个 Skill：
https://github.com/wild-firefox/zhihu-markdown-draft
```

### 手动安装

将整个仓库复制到个人 Skill 目录：

```text
Windows: %USERPROFILE%\.codex\skills\zhihu-markdown-draft
macOS/Linux: ~/.codex/skills/zhihu-markdown-draft
```

保留 `SKILL.md`、`agents/`、`scripts/`、`references/` 和 `assets/` 的相对结构，然后重启 Codex 或开启新任务。

如果目前只有本地开源副本，直接使用手动安装方式即可；上传 GitHub 后再把上面的示例地址换成实际仓库地址。

## 第一次使用与知乎登录

第一次控制知乎编辑器时，Codex 打开的浏览器可能尚未登录。请在那个浏览器页面中自行扫码或完成其他登录步骤，再告诉 Codex 已登录。

Skill 不需要也不应读取密码、Cookie、二维码内容或登录令牌。之后它会复用该浏览器中已经登录的知乎会话。

## 使用示例

```text
使用 $zhihu-markdown-draft，把 D:\文章\示例.md 写入一个新的知乎草稿。
添加知乎原生目录，只保存草稿，不发布。
```

只做本地预处理：

```text
使用 $zhihu-markdown-draft，为这篇 Markdown 生成知乎导入版和检查报告，不要打开知乎。
```

修复已有草稿：

```text
检查这篇知乎草稿是否存在裸露的 **、$、LaTeX 或图片占位符；先生成修正版，清空正文前再向我确认。
```

## 单独运行预处理脚本

需要 Python 3.9 或更高版本：

```powershell
python scripts/prepare_zhihu_markdown.py SOURCE.md --output ARTICLE_知乎导入版.md --strip-first-h1
```

在自动检查中让危险兼容问题返回非零状态：

```powershell
python scripts/prepare_zhihu_markdown.py SOURCE.md --fail-on-compatibility-errors
```

输出旁会生成 `*.report.json`，其中包含：

- 标题与数学分隔符转换；
- 本地图片及缺失图片；
- 表格数学和表格格式警告；
- 兼容性警告及其严重级别；
- 必须处理后才能导入的阻塞问题。

## 已验证的知乎兼容性

完整结论位于 [references/zhihu-markdown-compatibility.md](references/zhihu-markdown-compatibility.md)。可复现实验原稿位于 [assets/markdown-compatibility-test.md](assets/markdown-compatibility-test.md)。

最重要的实测规则：

- 普通正文中的 `**粗体**` 能正常工作，不应一概删除。
- 普通货币金额不要写成 `$100`；知乎可能跨段匹配后续 `$` 并把中间正文误当公式。
- 金额优先写 `USD 100`、`100 美元` 或 `￥100`。
- 表格单元格使用纯文本或 Unicode 数学符号。
- H2 到 H6 会被压成同一个知乎标题层级，只有需要进入目录的内容才使用标题标记。

## 隐私与安全

- 仓库不包含作者本机路径、知乎账号、Cookie、访问令牌或个人信息。
- 预处理报告会记录运行者自己的绝对路径，不要把运行生成的 `*.report.json`、导入副本或已托管图片地址提交到公开仓库。
- 导入、上传图片和修改云端草稿属于外部操作，应按 Codex 的确认机制执行。
- “导入”“写入草稿”不代表授权发布；发布文章必须单独明确授权。

## 许可证

[MIT License](LICENSE)
