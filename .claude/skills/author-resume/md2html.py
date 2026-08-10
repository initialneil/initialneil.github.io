#!/usr/bin/env python3
"""
Resume Markdown -> print-ready HTML (A4, Microsoft YaHei).

Usage:  python3 md2html.py <source.md> <out.html>
Then:   Chrome --headless --print-to-pdf   (see build.sh, which also compresses)

The .md is the single source of truth for copy. This script maps its structure
to the fixed résumé layout; do NOT hand-edit the generated HTML. Layout knobs
(fonts, sizes, image widths, columns) live in the CSS block below.

Markdown contract (see any *_CN.md):
  # Name
  - Email: ... / - Tele: ... / - Web/Scholar: [text](url)   (contact lines, before first ##)
  ## 自我简述            -> paragraphs
  ## 工作经历            -> ### <date> | <org>  +  - bullets      (blank line between jobs)
  ## 教育经历 / 荣誉/经历 -> ### <date> | <org>  +  plain sub-lines (no blank between)
  ## 论文发表…           -> ### <venue> <title> / ![](thumb) / 作者：… / 简介：…
  ## 专利…               -> - <patent line>          (forces a page break after)
  ## 项目介绍            -> ### <sub> + - bullets + one-or-more ![alt](img)
                            (2-column grid; multiple images in one project = product row w/ captions)
  Inline: **bold**, [text](url).
"""
import sys, re, html
md=open(sys.argv[1],encoding='utf-8').read().splitlines()
OUT=sys.argv[2]

def inline(s):
    out=[]; pos=0
    for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)|\*\*(.+?)\*\*', s):
        out.append(html.escape(s[pos:m.start()]))
        if m.group(1) is not None:
            out.append(f'<a href="{html.escape(m.group(2))}">{html.escape(m.group(1))}</a>')
        else:
            out.append(f'<b>{html.escape(m.group(3))}</b>')
        pos=m.end()
    out.append(html.escape(s[pos:]))
    return ''.join(out)

def classify(t):
    if '自我简述' in t: return 'about'
    if '工作经历' in t: return 'work'
    if '教育经历' in t: return 'edu'
    if '荣誉' in t: return 'honor'
    if '论文发表' in t: return 'papers'
    if '专利' in t: return 'patents'
    if '项目介绍' in t: return 'projects'
    return 'other'

BODY=[]; name='邵志兢'; section=None; work_first=True; proj_open=False; projgrid_open=False
paper=None; pat_title=None; pat_lines=[]; proj_imgs=[]
def flush_paper():
    global paper
    if paper:
        BODY.append(
          f'<div class="pub"><div class="pub-thumb"><img src="{paper.get("img","")}"></div>'
          f'<div class="pub-text"><div class="v">{inline(paper["vt"])}</div>'
          f'<div class="au">{inline(paper.get("au",""))}</div>'
          f'<div class="d">{inline(paper.get("de",""))}</div></div></div>')
        paper=None
def flush_proj():
    global proj_open, proj_imgs
    if proj_open:
        if len(proj_imgs)==1:
            BODY.append(f'<div class="fig"><img src="{proj_imgs[0][0]}"></div>')
        elif len(proj_imgs)>1:
            cells=''.join(f'<figure class="prod"><img src="{p}"><figcaption>{html.escape(a)}</figcaption></figure>' for p,a in proj_imgs)
            BODY.append(f'<div class="figrow">{cells}</div>')
        BODY.append('</div>'); proj_open=False; proj_imgs=[]
def flush_patents():
    global pat_title,pat_lines
    if pat_title is not None:
        lines='<br>'.join(inline(l) for l in pat_lines)
        BODY.append(f'<div class="patents"><b>{inline(pat_title)}</b><br>{lines}</div>')
        pat_title=None; pat_lines=[]

for raw in md:
    line=raw.rstrip()
    if line.strip()=='' or line.lstrip().startswith('<!--'): continue
    if line.startswith('# '):
        name=line[2:].strip()
        BODY.append(f'<p class="name">{inline(name)}</p>'); continue
    if line.startswith('## '):
        flush_paper(); flush_proj(); flush_patents()
        title=line[3:].strip(); section=classify(title); work_first=True
        if section!='projects': BODY.append('<p class="blank"></p>')   # section spacer (projects starts on a new page via the patents break)
        if section=='patents': pat_title=title
        elif section=='projects':
            BODY.append(f'<p class="h hproj">{inline(title)}</p>')
            BODY.append('<div class="projgrid">'); projgrid_open=True
        else: BODY.append(f'<p class="h">{inline(title)}</p>')
        continue
    if line.startswith('### '):
        title=line[4:].strip()
        if section in ('work','edu','honor'):
            if section=='work' and not work_first: BODY.append('<p class="blank"></p>')
            work_first=False
            date,content=(title.split(' | ',1)+[''])[:2] if ' | ' in title else ('',title)
            BODY.append(f'<div class="row"><div class="date">{inline(date.strip())}</div>'
                        f'<div class="content"><b>{inline(content.strip())}</b></div></div>')
        elif section=='papers':
            flush_paper(); paper={'vt':title}
        elif section=='projects':
            flush_proj(); BODY.append('<div class="proj">'); proj_open=True
            BODY.append(f'<p class="h">{inline(title)}</p>')
        continue
    if line.startswith('!['):
        m=re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line); alt=m.group(1) if m else ''; path=m.group(2) if m else ''
        if section=='papers' and paper is not None: paper['img']=path
        elif section=='projects': proj_imgs.append((path,alt))
        continue
    if line.startswith('- '):
        txt=line[2:].strip()
        if section is None: BODY.append(f'<p class="contact">{inline(txt)}</p>')
        elif section=='projects': BODY.append(f'<div class="bp"><span class="mk">●</span><span class="tx">{inline(txt)}</span></div>')
        elif section=='patents': pat_lines.append(txt)
        else: BODY.append(f'<div class="bw"><span class="mk">●</span><span class="tx">{inline(txt)}</span></div>')
        continue
    t=line.strip()
    if section=='papers' and paper is not None:
        if t.startswith('作者'): paper['au']=re.sub(r'^作者[：:]\s*','',t)
        elif t.startswith('简介'): paper['de']=re.sub(r'^简介[：:]\s*','',t)
    elif section=='about': BODY.append(f'<p class="body">{inline(t)}</p>')
    elif section in ('edu','honor'): BODY.append(f'<p class="cont">{inline(t)}</p>')
    else: BODY.append(f'<p class="body">{inline(t)}</p>')
flush_paper(); flush_proj(); flush_patents()
if projgrid_open: BODY.append('</div>')

# --- layout knobs. Metrics reverse-engineered from the original Word .docx. ---
# line-height 1.73 = YaHei's single spacing; text-autospace adds the CJK↔Latin gaps
# Word inserts. Content column @32.7mm, project images 2-col grid, patents force a
# page break so 项目介绍 starts fresh.
CSS='''
@page { size:210mm 297mm; margin:12.7mm; }
html,body{ margin:0; padding:0; }
body{ font-family:"Microsoft YaHei","微软雅黑",sans-serif; font-size:9.5pt; line-height:1.73; color:#000; text-autospace:normal; text-spacing-trim:normal; }
p{ margin:0; padding:0; }
a{ color:#0000FF; text-decoration:underline; }
.lk{ color:#0000FF; text-decoration:underline; }
b{ font-weight:700; }
.name{ text-align:center; font-size:11.5pt; }
.contact{ text-align:center; }
.blank{ height:1.73em; }
.h{ font-weight:700; padding-left:1.9mm; }
.hproj{ font-size:10.5pt; }
.body{ padding-left:1.9mm; }
.cont{ padding-left:32.7mm; }
.row{ display:flex; padding-left:1.9mm; }
.row .date{ flex:0 0 30.8mm; }
.row .content{ flex:1; }
.bw{ display:flex; padding-left:32.7mm; padding-right:3.4mm; }
.bw .mk{ flex:0 0 6.2mm; }
.bw .tx{ flex:1; }
.bp{ display:flex; padding-left:2.5mm; }
.bp .mk{ flex:0 0 4.9mm; }
.bp .tx{ flex:1; }
.pub{ display:flex; gap:3mm; padding-left:2mm; padding-right:2mm; margin-top:2.4mm; break-inside:avoid; }
.pub-thumb{ flex:0 0 24mm; }
.pub-thumb img{ width:24mm; height:14mm; object-fit:contain; background:#f3f3f3; display:block; }
.pub-text{ flex:1; }
.pub-text .d{ font-weight:700; }
.patents{ padding-left:7.4mm; text-indent:-4.9mm; page-break-after:always; }
.projgrid{ display:grid; grid-template-columns:1fr 1fr; column-gap:9mm; row-gap:7pt; margin-top:3pt; align-items:start; }
.proj{ break-inside:avoid; margin:0; padding-left:2mm; }
.fig{ margin:3pt 0 0; }
.fig img{ display:block; width:100%; height:auto; border:0.5pt solid #dcdcdc; }
.figrow{ display:flex; gap:2.5mm; margin-top:4pt; }
.figrow .prod{ flex:1; margin:0; text-align:center; }
.figrow .prod img{ width:100%; height:25mm; object-fit:contain; background:#fff; border:0.5pt solid #dcdcdc; }
.figrow .prod figcaption{ font-size:8pt; color:#555; margin-top:1.5pt; line-height:1.2; }
'''
HTML=f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>{html.escape(name)} CV</title>
<style>{CSS}</style></head>
<body>
{chr(10).join(BODY)}
</body></html>'''
open(OUT,'w',encoding='utf-8').write(HTML)
print("wrote",OUT,"blocks:",len(BODY))
