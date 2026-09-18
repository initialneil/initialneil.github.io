#!/usr/bin/env python3
"""
index.md -> index.html for the homepage. Run from anywhere:
    python3 .claude/skills/author-homepage/build.py

index.md is the source of truth for page copy; do not hand-edit index.html.
Page chrome (head, analytics shim, hit counter, footer) lives in this script.

index.md contract:
  --- title / description / keywords ---     (frontmatter -> <head> meta)
  ## Profile   ![alt](photo)  name: / subname: / tagline: / links: [t](u) ...  (one links: line per row)
  ## About     paragraph(s)
  ## <Bio>     - bullets; a blank line starts a new group; ![alt](img) ![..](..) line = image row
  ## <Pubs>    intro line with links, then per paper:
               ### [venue] title / ![](thumb) / optional [label](url) ... line / authors line
  Inline: [text](url) (http links open in a new tab), **bold**. Raw HTML passes through.
"""
import os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LINK = r'\[([^\]]*)\]\(([^)]+)\)'

def a(text, url, pre='', post=''):
    tgt = ' target="_blank"' if url.startswith('http') else ''
    return f'<a href="{url}"{tgt}>{pre}{text}{post}</a>'

def inline(s):
    s = re.sub(r'(?<!!)' + LINK, lambda m: a(m[1], m[2]), s)
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)

def links_only(s):
    return re.fullmatch(r'\s*(' + LINK + r'\s*)+', s) is not None

src = open(os.path.join(ROOT, 'index.md'), encoding='utf-8').read()
meta, body = {}, src
if src.startswith('---'):
    head, body = src[3:].split('\n---', 1)
    for l in head.strip().splitlines():
        k, v = l.split(':', 1); meta[k.strip()] = v.strip()

sections, cur = {}, None   # name -> list of lines
order = []
for line in body.splitlines():
    if line.startswith('## '):
        cur = line[3:].strip(); sections[cur] = []; order.append(cur); continue
    if cur is not None: sections[cur].append(line.rstrip())

def key(word):   # find a section by keyword, so headings can be reworded freely
    return next((k for k in order if word.lower() in k.lower()), None)
prof_key, about_key, bio_key = key('Profile'), key('About'), key('Bio')
repo_key, pub_key = key('Repo'), key('Publication')

# --- profile ---
prof = {'links': []}
for l in sections[prof_key]:
    if l.startswith('!['):
        m = re.match(r'!' + LINK, l); prof['alt'], prof['photo'] = m[1], m[2]
    elif ':' in l:
        k, v = l.split(':', 1)
        if k.strip() == 'links': prof['links'].append(re.findall(LINK, v))
        else: prof[k.strip()] = v.strip()
link_rows = '\n'.join(
    '            <div class="contact-links">\n' +
    ''.join(f'                {a(t, u)}\n' for t, u in row) +
    '            </div>' for row in prof['links'])

# --- about ---
about = '\n'.join(f'                <p>{inline(l)}</p>' for l in sections[about_key] if l.strip())

# --- bio: groups split by blank lines ---
groups, g = [], []
for l in sections[bio_key] + ['']:
    if l.strip(): g.append(l)
    elif g: groups.append(g); g = []
bio_items = []
for g in groups:
    parts = []
    for l in g:
        if l.startswith('!['):
            imgs = ''.join(f'                        <img src="{u}" alt="{t}">\n' for t, u in re.findall(r'!' + LINK, l))
            parts.append('                    <div class="image-row">\n' + imgs + '                    </div>')
        else:
            parts.append(f'                    <p>• {inline(re.sub(r"^- ", "", l))}</p>')
    bio_items.append('                <div class="bio-item">\n' + '\n                    \n'.join(parts) + '\n                </div>')
bio = '\n\n'.join(bio_items)

# --- popular repos: ### name / description line(s) / links line ---
repos, r = [], None
for l in sections.get(repo_key) or []:
    if not l.strip(): continue
    if l.startswith('### '):
        r = {'name': l[4:].strip(), 'desc': [], 'links': []}; repos.append(r)
    elif r is None: continue
    elif l.startswith('!['):
        m = re.match(r'!' + LINK, l); r['alt'], r['img'] = m[1], m[2]
    elif links_only(l): r['links'] = re.findall(LINK, l)
    else: r['desc'].append(inline(l))

def repo_html(r):
    links = ''
    if r['links']:
        links = ('                <div class="repo-links">\n' +
                 ''.join(f'                    {a(t, u, "[", "]")}\n' for t, u in r['links']) +
                 '                </div>\n')
    fig = ''
    if r.get('img'):
        fig = (f'                <div class="repo-fig">'
               f'<img src="{r["img"]}" alt="{r.get("alt", "")}"></div>\n')
    return (f'            <div class="repo">\n'
            f'                <div class="repo-name">{r["name"]}</div>\n'
            f'                <div class="repo-desc">{" ".join(r["desc"])}</div>\n'
            f'{links}{fig}            </div>')

repos_section = ''
if repos:
    repos_section = (f'''    <section id="repos">
        <h2>{repo_key}</h2>
        <div class="repo-grid">
''' + '\n'.join(repo_html(r) for r in repos) + '''
        </div>
    </section>

''')

# --- publications ---
intro, pubs, p = [], [], None
for l in sections[pub_key]:
    if not l.strip(): continue
    if l.startswith('### '):
        m = re.match(r'\[(.*?)\]\s*(.*)', l[4:].strip())
        p = {'venue': m[1], 'title': m[2], 'links': []}; pubs.append(p)
    elif p is None: intro.append(l)
    elif l.startswith('!['): p['img'] = re.match(r'!' + LINK, l)[2]
    elif links_only(l): p['links'] = re.findall(LINK, l)
    else: p['authors'] = inline(l)

intro_html = []
for l in intro:
    text = re.split(LINK, l, maxsplit=1)[0]
    intro_html.append(f'        <p>{text}\n' +
                      ''.join(f'            {a(t, u)}\n' for t, u in re.findall(LINK, l)) + '        </p>')

def pub_html(p):
    links = ''
    if p['links']:
        links = ('                <div class="publication-links">\n' +
                 ''.join(f'                    {a(t, u, "[", "]")}\n' for t, u in p['links']) +
                 '                </div>\n')
    return f'''        <div class="publication">
            <div class="publication-thumb"><img src="{p.get('img', '')}" alt=""></div>
            <div class="publication-info">
                <div>
                    <span class="publication-venue">[{p['venue']}]</span>
                    <span class="publication-title">{p['title']}</span>
                </div>
{links}                <div class="publication-authors">
                    {p.get('authors', '')}
                </div>
            </div>
        </div>'''

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{meta['description']}">
    <meta name="keywords" content="{meta['keywords']}">
    <meta name="author" content="Zhijing Shao">
    <title>{meta['title']}</title>
    <link rel="icon" href="assets/img/art_tree_1024.gif" type="image/gif">
    <link rel="stylesheet" href="style.css">

    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-SRNMM4RT7F');
    </script>
</head>
<body>
    <div class="two-column-container">
        <div class="left-column">
            <img src="{prof['photo']}" alt="{prof['alt']}" class="profile-photo">
            <h1>{prof['name']}</h1>
            <h2>{prof['subname']}</h2>
            <p class="tagline">{prof['tagline']}</p>
{link_rows}
            <p></p>
            <img src="https://hitscounter.dev/api/hit?url=https%3A%2F%2Finitialneil.github.io%2F&label=initialNeil&icon=cup-hot&color=%233d8bfd&message=&style=flat&tz=Hongkong">
        </div>

        <div class="right-column">
            <section id="about">
{about}
            </section>

            <section id="bio">
                <h2>{bio_key}</h2>

{bio}
            </section>
        </div>
    </div>

{repos_section}    <section id="publications">
        <h2>{pub_key}</h2>
{chr(10).join(intro_html)}

{(chr(10) + chr(10)).join(pub_html(p) for p in pubs)}
    </section>

    <footer>
        <p>© 2026 Zhijing Shao. Hosted on GitHub Pages.</p>
    </footer>
</body>
</html>
'''
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(html)
print(f'wrote index.html: {len(pubs)} publications, {len(bio_items)} bio groups')
