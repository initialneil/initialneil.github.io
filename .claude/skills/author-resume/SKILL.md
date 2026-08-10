---
name: author-resume
description: Author / update Neil's Chinese résumé (邵志兢 CV) as a Markdown-sourced, print-faithful A4 PDF. Use when the user types /author-resume, asks to update the résumé / CV / 简历, edit its copy, regenerate the PDF from a *_CN.md, resize résumé images, or refresh the publication list. Everything lives in resume/.
---

# author-resume — Neil's CV pipeline

The résumé is **Markdown-in, print-faithful PDF-out**. The `.md` is the single source of
truth for copy; a generator maps it to a fixed A4 layout (Microsoft YaHei, reverse-engineered
from the original Word doc). **Never hand-edit the generated HTML** — edit the `.md` and rebuild.

**Tooling** (tracked, here in the skill): `md2html.py` (Markdown → print HTML; all layout/CSS)
and `build.sh` (md → HTML → PDF → compress, one step).

**Content** lives in the repo's **`resume/`** dir, which is **git-ignored** (private CV — never
published on the Pages site) but kept on disk:
- `<date>_CN.md` — the editable source (e.g. `2025.2.25_CN.md`). One file per version.
- `images/` — `image1..5.png` (project photos), `pub_*.png` (11 paper thumbnails), `prod_*.png` (Kandao products).
- `<date>_CN.html` / `<date>_CN.pdf` — generated outputs.

## Build / update the PDF

```bash
.claude/skills/author-resume/build.sh 2025.2.25_CN     # -> resume/2025.2.25_CN.pdf
```

`build.sh` finds `resume/` on its own, installs Microsoft YaHei from MS Word's bundle if missing
(needed for correct glyphs + pagination), runs the generator, prints the PDF via headless Chrome,
then Ghostscript-compresses the images (vector text + links untouched). Output is ~400 KB, print-grade.

**New dated version** (the common case — user copies the md and wants a fresh PDF):
```bash
cp resume/2025.2.25_CN.md resume/2026.8.10_CN.md          # edit copy in the new file, then:
.claude/skills/author-resume/build.sh 2026.8.10_CN         # -> resume/2026.8.10_CN.pdf
```
Each `<name>.md` builds to `<name>.pdf` independently — old versions are never touched.

## Editing copy — the Markdown contract

Edit text directly; keep the structure. `md2html.py` classifies by section heading:

| Markdown | Renders as |
| --- | --- |
| `# 邵志兢` then `- Email: …` / `- Web: [t](url)` | centered name + contact lines |
| `## 自我简述` + plain lines | intro paragraphs |
| `## 工作经历` → `### <date> \| <org>` + `- bullets` | two-column row (date \| bold org) + ● bullets; **blank line between jobs** |
| `## 教育经历` / `## 荣誉/经历` → `### <date> \| <org>` + plain lines | same row; sub-lines indent under the org (no blank between entries) |
| `## 论文发表…` → `### <venue> <title>` / `![](thumb)` / `作者：…` / `简介：…` | paper card: thumbnail + venue/title + authors + bold CN one-liner |
| `## 专利…` + `- <line>` | patents block (**forces a page break after** → 项目介绍 starts fresh) |
| `## 项目介绍` → `### <sub>` + `- bullets` + `![alt](img)` | 2-column project grid |
| inline `**bold**`, `[text](url)` | bold, blue link |

Bold **Zhijing Shao** in each author list. Section order is fixed by the headings above.

## Images

- **Project photos** (`## 项目介绍`): one `![alt](images/x.png)` per project → fills its grid column
  (~88 mm), framed. **Multiple images in one project → a product row** (uniform 25 mm boxes +
  captions from the alt text) — e.g. the 看到 project's Obsidian Pro · Kandao Meeting · QooCam.
- **Paper thumbnails**: `pub_<key>.png`, shown 24×14 mm. Sourced from the homepage teasers.
- **Sizing knobs** are in `md2html.py` CSS: project image width (`.fig img`), product-row height
  (`.figrow .prod img`), thumbnail box (`.pub-thumb img`). Change there, not per-image.
- **Adding an image**: drop a right-sized PNG in `images/` (project photos ≥ ~900 px wide;
  products ~600 px; on white if it's a product). Reference it from the md. Rebuild.
- **Compression is automatic** in `build.sh` (gs, 200 dpi). Don't pre-compress by hand.

## Suggest: refresh the publication list

The résumé's 11 papers mirror the homepage. When updating, **check `index.html` for new
publications** and offer to sync:
```bash
grep -A3 'class="publication"' index.html      # or read the publication-* blocks
```
Homepage order = **newest first, by year then conference** (its documented convention). New papers
there but not in the résumé → add a `### [venue] Title.` / `![](images/pub_<key>.png)` / `作者：` /
`简介：` block (copy a teaser into `images/pub_<key>.png`), keeping newest-first order.

## Gotchas (learned the hard way)

- **Microsoft YaHei is required.** Not installed system-wide by default; `build.sh` copies it from
  `/Applications/Microsoft Word.app/.../DFonts/`. Without it, glyphs and page breaks drift.
- **Test renders must run from `resume/`** (or copy `images/`) so `images/…` paths resolve — a variant
  written elsewhere 404s every image and reports a *false* low page count.
- **Line-height is 1.73** (YaHei's single spacing, measured — not 1.0) and **`text-autospace:normal`**
  reproduces Word's CJK↔Latin gaps (Chrome 131+). Both are load-bearing for pagination.
- **Projects use a CSS `grid` (2 cols), not `column-count`** — multicol left the last project alone on
  a sparse page in Chrome print; grid pairs row-by-row.
- Chrome renders YaHei *Latin* a hair wider than Word, so long Latin lines may wrap one word earlier
  than the original — cosmetic, doesn't affect the current layout.
