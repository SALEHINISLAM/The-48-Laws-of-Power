#!/usr/bin/env python3
"""Static site generator for ক্ষমতা — The 48 Laws of Power বাংলা পাঠ ও অনুশীলন.

Reads  content/book.json  (produced from the authorised PDF) and writes a fully static
site into  ../docs  (ready for GitHub Pages). No runtime dependencies.

Usage:  python3 build.py [--site-url https://USER.github.io/REPO/]
"""
import argparse, html, json, os, re, shutil, hashlib, datetime
from laws_en import EN_TITLES

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONFIG = json.load(open(os.path.join(HERE, 'config.json'), encoding='utf-8'))
BOOK = json.load(open(os.path.join(HERE, 'content', 'book.json'), encoding='utf-8'))

ap = argparse.ArgumentParser()
ap.add_argument('--site-url', default=CONFIG['site_url'])
ap.add_argument('--out', default=os.path.join(ROOT, 'docs'))
args = ap.parse_args()
SITE = args.site_url.rstrip('/') + '/'
OUT = args.out
BN = '০১২৩৪৫৬৭৮৯'
TODAY = datetime.date.today().isoformat()
M = BOOK['meta']


def bn(n):
    return ''.join(BN[int(c)] if c.isdigit() else c for c in str(n))


def e(s):
    return html.escape(str(s), quote=True)


def law_file(n):
    return f'law-{n:02d}.html'


def clip(s, n=155):
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    sp = cut.rfind(' ')
    return (cut[:sp] if sp > 60 else cut).rstrip(',;:—-') + '…'


# ------------------------------------------------------------------ icons
ICONS = {
    'menu': '<path d="M3 6h18M3 12h18M3 18h18"/>',
    'theme': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    'bookmark': '<path d="M6 3h12v18l-6-4-6 4z"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'minus': '<path d="M5 12h14"/>',
    'lines': '<path d="M8 6h13M8 12h13M8 18h13M3 4v16M1.5 6 3 4l1.5 2M1.5 18 3 20l1.5-2"/>',
    'focus': '<path d="M4 8V4h4M20 8V4h-4M4 16v4h4M20 16v4h-4"/>',
    'check': '<path d="m4 12 5 5L20 6"/>',
    'search': '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    'left': '<path d="m15 18-6-6 6-6"/>',
    'right': '<path d="m9 18 6-6-6-6"/>',
}


def icon(name, label=None):
    a = f' role="img" aria-label="{e(label)}"' if label else ' aria-hidden="true"'
    return f'<svg class="icon" viewBox="0 0 24 24"{a}>{ICONS[name]}</svg>'


NAV = [
    ('', 'হোম'),
    ('laws/', '৪৮টি আইন'),
    ('preface/', 'ভূমিকা'),
    ('bookmarks/', 'বুকমার্ক'),
    ('notes/', 'নোট'),
    ('settings/', 'সেটিংস'),
    ('about/', 'পরিচিতি'),
]

PREPAINT = ("(function(){try{var d=JSON.parse(localStorage.getItem('lop48:data')||'{}').prefs||{};var r=document.documentElement;"
            "if(d.theme==='light'||d.theme==='dark')r.setAttribute('data-theme',d.theme);"
            "if(d.font&&d.font!=='auto')r.setAttribute('data-font',d.font);"
            "if(d.fs)r.style.setProperty('--fs',d.fs/16+'rem');if(d.lh)r.style.setProperty('--lh',d.lh);"
            "if(d.width)r.style.setProperty('--measure',d.width+'rem')}catch(e){}})();")

ASSET_VER = ''


def page(path, *, title, desc, body, active='', root='./', jsonld=None, scripts=('app',), og_type='website',
         robots='index,follow', laws_data=False, extra_head=''):
    canonical = SITE + (path[:-10] if path.endswith('index.html') else path)
    nav = ''.join(
        f'<li><a href="{root}{href}"{" aria-current=\"page\"" if href == active else ""}>{lbl}</a></li>'
        for href, lbl in NAV)
    ld = ''
    if jsonld:
        ld = '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>'
    lawsjs = ''
    if laws_data:
        arr = [[L['n'], L['title'], EN_TITLES[L['n'] - 1]] for L in BOOK['laws']]
        lawsjs = '<script type="application/json" id="laws-data">' + json.dumps(arr, ensure_ascii=False, separators=(',', ':')) + '</script>'
    js = ''.join(f'<script src="{root}assets/js/{s}.js?v={ASSET_VER}" defer></script>' for s in scripts)
    return f'''<!doctype html>
<html lang="bn" data-root="{root}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{e(canonical)}">
<meta name="theme-color" content="#20235F">
<meta property="og:type" content="{og_type}">
<meta property="og:locale" content="bn_BD">
<meta property="og:site_name" content="{e(CONFIG['site_name'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:image" content="{SITE}assets/images/og-cover.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}assets/icons/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{root}assets/icons/icon-192.png">
<link rel="manifest" href="{root}manifest.webmanifest">
<link rel="preload" href="{root}assets/fonts/noto-serif-bengali-bengali-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{root}assets/css/main.css?v={ASSET_VER}">
<script>{PREPAINT}</script>
{extra_head}{ld}
</head>
<body>
<a class="skip" href="#main">মূল লেখায় যান</a>
<header class="site-header">
<div class="wrap">
<a class="brand" href="{root}"><span class="brand-mark" aria-hidden="true">ক্ষ</span><span>ক্ষমতা</span></a>
<button class="nav-toggle icon-btn" aria-expanded="false" aria-controls="site-nav">{icon('menu')}<span class="sr-only">মেনু</span></button>
<nav class="nav" id="site-nav" aria-label="প্রধান মেনু"><ul>{nav}</ul></nav>
<button class="icon-btn" id="theme-btn" type="button" aria-label="থিম পরিবর্তন">{icon('theme')}</button>
</div>
<div class="progress-bar" id="read-progress" aria-hidden="true"></div>
</header>
<p id="storage-warn" class="wrap muted" hidden role="note">আপনার ব্রাউজারে লোকাল স্টোরেজ বন্ধ আছে — পড়া চলবে, কিন্তু অগ্রগতি ও নোট সংরক্ষিত হবে না।</p>
<main id="main">
{body}
</main>
<footer class="site-footer">
<div class="wrap">
<p>মূল গ্রন্থ: <span class="en">The 48 Laws of Power</span> — রবার্ট গ্রিন (Robert Greene), জুস্ট এলফার্সের প্রযোজনা। এই ওয়েবসাইট রবার্ট গ্রিনের প্রতি উৎসর্গীকৃত একটি অবাণিজ্যিক, বিনামূল্যের পাঠ-প্রকল্প; এটি লেখক বা মূল প্রকাশকের দ্বারা পরিচালিত বা অনুমোদিত কোনো অফিসিয়াল সাইট নয়।</p>
<p>বিজ্ঞাপন নেই · ট্র্যাকিং নেই · আপনার নোট ও অগ্রগতি শুধু আপনার ব্রাউজারেই থাকে।</p>
<ul class="footer-links"><li><a href="{root}about/">পরিচিতি ও কৃতজ্ঞতা</a></li><li><a href="{root}bibliography/">গ্রন্থপঞ্জি</a></li><li><a href="{root}laws/">সব আইন</a></li><li><a href="{root}settings/">ডেটা ব্যাকআপ</a></li></ul>
</div>
</footer>
{lawsjs}{js}
</body>
</html>
'''


def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as fh:
        fh.write(content)


# ------------------------------------------------------------------ content rendering
def render_inline(t):
    return e(t).replace('\n', '<br>')


def render_blocks(blocks, toc=None, id_prefix='s'):
    out, k = [], 0
    for b in blocks:
        t = b['t']
        if t == 'h2':
            k += 1
            hid = f'{id_prefix}{k}'
            if toc is not None:
                toc.append((hid, b['x']))
            out.append(f'<h2 id="{hid}">{render_inline(b["x"])}</h2>')
        elif t == 'h3':
            tag = 'h3' if k or toc is None else 'h2'
            out.append(f'<{tag}>{render_inline(b["x"])}</{tag}>')
        elif t == 'ul':
            out.append('<ul class="biblio">' + ''.join(f'<li>{render_inline(x["x"])}</li>' for x in b['items']) + '</ul>')
        elif t == 'li':
            out.append(f'<li>{render_inline(b["x"])}</li>')
        elif t == 'q':
            out.append(f'<blockquote><p>{render_inline(b["x"])}</p></blockquote>')
        elif t == 'attr':
            out.append(f'<p class="attrib">— {render_inline(b["x"])}</p>')
        else:
            out.append(f'<p>{render_inline(b["x"])}</p>')
    return '\n'.join(out)
# (bibliography uses 'ul' blocks)


def plain(blocks):
    return ' '.join(b['x'] for b in blocks).replace('\n', ' ')


PUBLISHER_LINE = M.get('translation_credit', '')


def book_ld():
    return {
        '@type': 'Book', '@id': SITE + '#book', 'name': M['title_bn'], 'alternateName': 'The 48 Laws of Power',
        'inLanguage': 'bn',
        'author': {'@type': 'Person', '@id': SITE + '#robert-greene', 'name': 'Robert Greene', 'alternateName': 'রবার্ট গ্রিন'},
        'translationOfWork': {'@type': 'Book', 'name': 'The 48 Laws of Power', 'inLanguage': 'en',
                              'author': {'@id': SITE + '#robert-greene'}},
    }


def crumbs(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(items)]}


def breadcrumb_html(items, root):
    lis = []
    for i, (n, u) in enumerate(items):
        if i == len(items) - 1:
            lis.append(f'<li aria-current="page">{e(n)}</li>')
        else:
            lis.append(f'<li><a href="{root}{u}">{e(n)}</a></li>')
    return f'<nav class="breadcrumbs" aria-label="অবস্থান"><ol>{"".join(lis)}</ol></nav>'


def law_card(L, root, tag='li', h='h3', short=False):
    n = L['n']
    summ = plain(L['judgment'])
    if short:
        summ = clip(summ, 150)
    return (f'<{tag} class="law-card" data-law="{n}"><span class="law-num" aria-hidden="true">{bn(n)}</span>'
            f'<{h}><a href="{root}laws/{law_file(n)}">আইন {bn(n)}: {e(L["title"])}</a></{h}>'
            f'<p class="en" lang="en">{e(EN_TITLES[n - 1])}</p><div class="badges"></div>'
            f'<p class="summary">{e(summ)}</p></{tag}>')


# ------------------------------------------------------------------ pages
REFLECT = [
    ('learn', 'এই আইন থেকে আমি কী শিখলাম?'),
    ('core', 'আমার ভাষায় এর মূল বক্তব্য কী?'),
    ('life', 'বাস্তব জীবনে এর প্রাসঙ্গিকতা কোথায় দেখি?'),
    ('limits', 'এই ধারণার সীমাবদ্ধতা কী? কোথায় এটি খাটে না?'),
    ('ethics', 'এর নৈতিক দিকগুলো কীভাবে বিবেচনা করব? এটি প্রয়োগে কেউ ক্ষতিগ্রস্ত হতে পারে কি?'),
    ('own', 'আমার নিজের উপলব্ধি'),
]


def build_law(L):
    n = L['n']
    root = '../'
    label = L.get('label', 'বিচারবুদ্ধি')
    toc = [('judgment', label)]
    content = render_blocks(L['body'], toc)
    prev_n, next_n = n - 1, n + 1
    title_full = f'আইন {bn(n)}: {L["title"]}'
    summ = plain(L['judgment'])
    side = ''.join(
        f'<li><a href="{law_file(x["n"])}"{" aria-current=\"page\"" if x["n"] == n else ""}><span class="n">{bn(x["n"])}</span>{e(x["title"])}</a></li>'
        for x in BOOK['laws'])
    toc_html = ''.join(f'<li><a href="#{hid}">{e(t)}</a></li>' for hid, t in toc)
    nav_prev = (f'<a class="prev" href="{law_file(prev_n)}" rel="prev"><small>← আগের আইন</small>আইন {bn(prev_n)}: {e(BOOK["laws"][prev_n - 1]["title"])}</a>'
                if prev_n >= 1 else f'<a class="prev" href="../preface/" rel="prev"><small>← আগে</small>ভূমিকা</a>')
    nav_next = (f'<a class="next" href="{law_file(next_n)}" rel="next"><small>পরের আইন →</small>আইন {bn(next_n)}: {e(BOOK["laws"][next_n - 1]["title"])}</a>'
                if next_n <= len(BOOK["laws"]) else '<a class="next" href="../laws/"><small>সমাপ্তি →</small>সব আইনের তালিকা</a>')
    reflect = ''.join(
        f'<div class="field"><label for="r-{k}">{e(q)}</label><textarea id="r-{k}" data-reflect="{k}" rows="4"></textarea>'
        f'<span class="saved" id="saved-{k}" aria-live="polite"></span></div>' for k, q in REFLECT)
    faq_q = f'আইন {bn(n)} — “{L["title"]}” — বইয়ে এর মূল বক্তব্য কী?'
    body = f'''
<div class="wrap">
<div class="reader-layout">
<aside class="side left" aria-label="সব আইন"><div class="sticky"><h2>৪৮টি আইন</h2><ol>{side}</ol></div></aside>
<article class="article" data-law-page="{n}" lang="bn">
{breadcrumb_html([('হোম', ''), ('৪৮টি আইন', 'laws/'), (f'আইন {bn(n)}', '')], root)}
<header class="law-head">
<p class="kicker">আইন {bn(n)}</p>
<h1>{e(L["title"])}</h1>
<p class="en" lang="en">Law {n}: {e(EN_TITLES[n - 1])}</p>
<div class="controls" role="toolbar" aria-label="পাঠের নিয়ন্ত্রণ">
<button class="icon-btn" id="bm-btn" type="button" aria-pressed="false">{icon('bookmark')}<span class="label">বুকমার্ক</span></button>
<button class="icon-btn" id="fs-down" type="button" aria-label="ফন্ট ছোট করুন">{icon('minus')}<span class="label" aria-hidden="true">অ</span></button>
<button class="icon-btn" id="fs-up" type="button" aria-label="ফন্ট বড় করুন">{icon('plus')}<span class="label" aria-hidden="true">অ</span></button>
<button class="icon-btn" id="lh-toggle" type="button" aria-label="লাইনের ফাঁক পরিবর্তন">{icon('lines')}</button>
<button class="icon-btn" id="focus-btn" type="button" aria-pressed="false" aria-label="মনোযোগী পাঠ মোড">{icon('focus')}</button>
<button class="icon-btn" id="done-btn" type="button" aria-pressed="false">{icon('check')}<span class="label">পড়া শেষ চিহ্নিত করুন</span></button>
</div>
<p id="resume" hidden class="note-box">আগে এই অধ্যায়ের মাঝপথে ছিলেন। <button class="btn small ghost" type="button">যেখানে ছিলেন সেখানে যান</button></p>
</header>
<div class="prose" id="content">
<h2 id="judgment">{e(label)}</h2>
<div class="judgment">{render_blocks(L['judgment'])}</div>
{content}
</div>
<nav class="chapter-nav" aria-label="অধ্যায় নেভিগেশন">{nav_prev}{nav_next}</nav>
<section class="practice" aria-labelledby="practice-h">
<h2 id="practice-h">অনুশীলন ও প্রতিফলন</h2>
<p class="note-box">নিচের প্রশ্নগুলো ঐচ্ছিক। আপনার লেখা শুধু এই ব্রাউজারে সংরক্ষিত থাকে, কোথাও পাঠানো হয় না। বইটি ইতিহাস থেকে ক্ষমতার কৌশল বর্ণনা করে — পড়ার সময় সমালোচনামূলক ও নৈতিক দৃষ্টিভঙ্গি রাখুন; এই কৌশলগুলো দিয়ে অন্যকে প্রতারণা বা ক্ষতি করা এই প্রকল্পের উদ্দেশ্য নয়।</p>
<details><summary>প্রতিফলনের প্রশ্ন</summary><div class="inner">{reflect}</div></details>
<details><summary>এই আইন নিয়ে একটি নোট লিখুন</summary><div class="inner">
<form id="quick-note" class="note-form"><div class="field"><label for="qn">নোট</label><textarea id="qn" rows="4"></textarea></div>
<div><button class="btn small" type="submit">নোট সংরক্ষণ করুন</button> <a href="../notes/?law={n}">সব নোট দেখুন</a></div></form></div></details>
<details><summary>সাধারণ জিজ্ঞাসা</summary><div class="inner"><dl class="faq">
<dt>{e(faq_q)}</dt><dd>বইয়ের “{e(label)}” অংশ অনুযায়ী: {e(summ)}</dd>
<dt>এই আইনের ইংরেজি নাম কী?</dt><dd lang="en">Law {n}: {e(EN_TITLES[n - 1])}</dd>
</dl><p class="editorial">উত্তরগুলো সরাসরি অনূদিত বইয়ের পাঠ থেকে নেওয়া; এখানে লেখকের নামে কোনো নতুন মন্তব্য যোগ করা হয়নি।</p></div></details>
</section>
</article>
<aside class="side right" aria-label="এই অধ্যায়ে"><div class="sticky"><h2>এই অধ্যায়ে</h2><ol>{toc_html}</ol></div></aside>
</div>
</div>'''
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': SITE + f'laws/{law_file(n)}', 'url': SITE + f'laws/{law_file(n)}', 'name': title_full,
         'inLanguage': 'bn', 'isPartOf': {'@id': SITE + '#website'}, 'about': {'@id': SITE + '#book'},
         'mainEntity': {'@type': 'Chapter', 'name': title_full, 'alternateName': f'Law {n}: {EN_TITLES[n - 1]}', 'position': n,
                        'isPartOf': {'@id': SITE + '#book'}, 'author': {'@id': SITE + '#robert-greene'}, 'abstract': summ}},
        book_ld(),
        crumbs([('হোম', ''), ('৪৮টি আইন', 'laws/'), (f'আইন {bn(n)}', f'laws/{law_file(n)}')]),
        {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': faq_q,
                                             'acceptedAnswer': {'@type': 'Answer', 'text': summ}}]},
    ]}
    title = f'আইন {bn(n)}: {L["title"]} | The 48 Laws of Power বাংলা'
    desc = clip(f'Law {n} ({EN_TITLES[n - 1]}) — {summ}', 160)
    write(f'laws/{law_file(n)}', page(f'laws/{law_file(n)}', title=title, desc=desc, body=body, active='laws/', root=root,
                                       jsonld=ld, scripts=('app', 'reader'), og_type='article'))


def build_laws_index():
    root = '../'
    cards = '\n'.join(law_card(L, root, h='h2') for L in BOOK['laws'])
    body = f'''<div class="wrap">
<header class="page-head">{breadcrumb_html([('হোম', ''), ('৪৮টি আইন', 'laws/')], root)}
<h1>ক্ষমতার ৪৮টি আইন</h1><p>রবার্ট গ্রিনের <span class="en">The 48 Laws of Power</span> বইয়ের সব আইন, বইয়ের ক্রম অনুযায়ী। প্রতিটির নিচে অধ্যায়ের শুরুর সারকথা (বইয়ের “বিচার” বা “বিচারবুদ্ধি” অংশ) দেওয়া আছে।</p></header>
<div class="toolbar">
<label class="search" for="law-q">{icon('search')}<span class="sr-only">আইন খুঁজুন</span><input id="law-q" type="search" placeholder="নাম, নম্বর বা ইংরেজি শিরোনাম দিয়ে খুঁজুন" autocomplete="off"></label>
<div class="filters" role="group" aria-label="ফিল্টার">
<button class="chip" type="button" data-filter="all" aria-pressed="true">সব</button>
<button class="chip" type="button" data-filter="unread" aria-pressed="false">অপঠিত</button>
<button class="chip" type="button" data-filter="reading" aria-pressed="false">পড়ছি</button>
<button class="chip" type="button" data-filter="done" aria-pressed="false">পড়া শেষ</button>
<button class="chip" type="button" data-filter="bookmarked" aria-pressed="false">বুকমার্ক</button>
</div></div>
<p id="law-count" class="muted" aria-live="polite">৪৮টি আইন</p>
<ol class="law-list" id="law-list">{cards}</ol>
<p id="law-empty" class="empty" hidden>কোনো আইন পাওয়া যায়নি।</p>
</div>'''
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', '@id': SITE + 'laws/', 'url': SITE + 'laws/', 'name': 'ক্ষমতার ৪৮টি আইন — সম্পূর্ণ তালিকা', 'inLanguage': 'bn',
         'isPartOf': {'@id': SITE + '#website'}, 'about': {'@id': SITE + '#book'},
         'mainEntity': {'@type': 'ItemList', 'numberOfItems': 48, 'itemListElement': [
             {'@type': 'ListItem', 'position': L['n'], 'name': f'আইন {bn(L["n"])}: {L["title"]}', 'url': SITE + f'laws/{law_file(L["n"])}'} for L in BOOK['laws']]}},
        crumbs([('হোম', ''), ('৪৮টি আইন', 'laws/')])]}
    write('laws/index.html', page('laws/index.html', title='ক্ষমতার ৪৮টি আইন — সম্পূর্ণ তালিকা | The 48 Laws of Power বাংলা',
                                  desc='রবার্ট গ্রিনের The 48 Laws of Power বইয়ের ৪৮টি আইনের বাংলা নাম, ইংরেজি শিরোনাম ও সারকথা — ক্রম অনুযায়ী, খোঁজা ও ফিল্টারসহ।',
                                  body=body, active='laws/', root=root, jsonld=ld, scripts=('app', 'pages')))


def build_home():
    root = './'
    cards = '\n'.join(law_card(L, root, short=True) for L in BOOK['laws'])
    intro = plain(BOOK['front']['preface'][:1])
    body = f'''<section class="hero" aria-labelledby="hero-h">
<div class="wrap">
<div class="cover" aria-hidden="true"><span>ক্ষ</span><span>ম</span><span>তা</span><small>রবার্ট গ্রিন</small></div>
<p class="hero-kicker">পাওয়ারের জন্য ব্যবহারিক নির্দেশিকা · বাংলা পাঠ ও অনুশীলন</p>
<div><h1 id="hero-h">ক্ষমতা</h1><p class="en-title" lang="en">The 48 Laws of Power</p><p class="author">রবার্ট গ্রিন</p></div>
<p class="lede">রবার্ট গ্রিনের বিখ্যাত বইয়ের বাংলা অনুবাদ — অধ্যায় ধরে পড়ুন, নিজের নোট রাখুন, প্রতিটি আইন নিয়ে ভাবুন। সম্পূর্ণ বিনামূল্যে, বিজ্ঞাপন ও নিবন্ধন ছাড়া।</p>
<div class="actions"><a class="btn gold" href="preface/">পড়া শুরু করুন</a><a class="btn ghost" href="laws/">৪৮টি আইন দেখুন</a></div>
</div></section>
<div class="wrap">
<section class="section" aria-labelledby="dash-h" id="dash">
<h2 id="dash-h">আপনার পড়ার অগ্রগতি</h2>
<div class="grid two">
<div class="panel"><p class="muted" style="margin:0">শেষ করা আইন</p><p class="stat"><span id="dash-done">০</span> / ৪৮</p>
<div class="meter" role="presentation"><span id="dash-meter"></span></div><p class="muted" style="margin:0"><span id="dash-pct">০%</span> সম্পন্ন · পড়ছেন <span id="dash-reading">০</span>টি · বুকমার্ক <span id="dash-marks">০</span>টি · নোট <span id="dash-notes">০</span>টি</p></div>
<div class="panel" id="continue"><p class="muted" style="margin:0 0 .5rem">নতুন পাঠক?</p><p style="margin:0 0 1rem">বইয়ের ভূমিকা দিয়ে শুরু করুন, অথবা সরাসরি প্রথম আইনে যান। কোনো অ্যাকাউন্ট লাগবে না — আপনার অগ্রগতি এই ব্রাউজারেই সংরক্ষিত থাকবে।</p><a class="btn" href="laws/{law_file(1)}">আইন ১ থেকে শুরু</a></div>
</div>
<div class="panel" style="margin-top:1rem"><h3 style="margin:0 0 .5rem;font-size:1.1rem">সম্প্রতি পড়া</h3><div id="recent"><p class="muted" style="margin:0">এখনো কোনো আইন পড়েননি।</p></div></div>
</section>
<section class="section" aria-labelledby="about-h">
<h2 id="about-h">বইটি সম্পর্কে</h2>
<div class="grid two">
<div><p style="margin-top:0">{e(clip(intro, 420))}</p><p><a href="preface/">সম্পূর্ণ ভূমিকা পড়ুন →</a></p></div>
<dl class="panel" style="margin:0;display:grid;grid-template-columns:auto 1fr;gap:.4rem 1rem">
<dt><strong>মূল বই</strong></dt><dd style="margin:0" lang="en" class="en">The 48 Laws of Power</dd>
<dt><strong>লেখক</strong></dt><dd style="margin:0">রবার্ট গ্রিন (Robert Greene)</dd>
<dt><strong>প্রযোজনা</strong></dt><dd style="margin:0">জুস্ট এলফার্স (Joost Elffers)</dd>
<dt><strong>বাংলা অনুবাদ</strong></dt><dd style="margin:0">{e(M['translator'])}</dd>
<dt><strong>অধ্যায়</strong></dt><dd style="margin:0">৪৮টি আইন</dd>
</dl></div>
</section>
<section class="section" aria-labelledby="all-h">
<h2 id="all-h">৪৮টি আইন এক নজরে</h2>
<ol class="law-list compact">{cards}</ol>
</section>
<section class="section" aria-labelledby="ded-h">
<h2 id="ded-h">উৎসর্গ</h2>
<div class="dedication"><p style="margin:0">ইতিহাসের পাতা থেকে ক্ষমতার নিয়মগুলো খুঁজে এনে যিনি আমাদের ভাবতে শিখিয়েছেন — সেই লেখক <strong>রবার্ট গ্রিন</strong>-এর প্রতি শ্রদ্ধা ও কৃতজ্ঞতায় এই পাঠ-প্রকল্প উৎসর্গ করা হলো।</p></div>
<p class="muted">এটি একটি অবাণিজ্যিক পাঠক-প্রকল্প; লেখক বা মূল প্রকাশকের অফিসিয়াল সাইট নয়। <a href="about/">বিস্তারিত পরিচিতি ও কৃতজ্ঞতা</a></p>
</section>
</div>'''
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebSite', '@id': SITE + '#website', 'url': SITE, 'name': CONFIG['site_name'], 'inLanguage': 'bn',
         'description': CONFIG['description']},
        {'@type': 'WebPage', '@id': SITE, 'url': SITE, 'name': CONFIG['site_name'], 'inLanguage': 'bn',
         'isPartOf': {'@id': SITE + '#website'}, 'about': {'@id': SITE + '#book'}},
        book_ld(),
        {'@type': 'Person', '@id': SITE + '#robert-greene', 'name': 'Robert Greene', 'alternateName': 'রবার্ট গ্রিন'}]}
    write('index.html', page('index.html', title='The 48 Laws of Power বাংলা — ক্ষমতার ৪৮টি আইন | রবার্ট গ্রিন',
                             desc=CONFIG['description'], body=body, active='', root=root, jsonld=ld, scripts=('app',), laws_data=True))


def build_text_page(slug, h1, blocks, title, desc, kicker=''):
    root = '../'
    toc = []
    content = render_blocks(blocks, toc)
    nxt = '' if slug != 'preface' else f'<nav class="chapter-nav"><span></span><a class="next" href="../laws/{law_file(1)}"><small>পরের অধ্যায় →</small>আইন ১: {e(BOOK["laws"][0]["title"])}</a></nav>'
    body = f'''<div class="wrap"><article class="article" style="padding:1.5rem 0 2rem">
{breadcrumb_html([('হোম', ''), (h1, slug + '/')], root)}
<header class="law-head">{f'<p class="kicker">{kicker}</p>' if kicker else ''}<h1>{e(h1)}</h1></header>
<div class="prose" id="content">{content}</div>{nxt}
</article></div>'''
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', '@id': SITE + slug + '/', 'url': SITE + slug + '/', 'name': h1, 'inLanguage': 'bn',
         'isPartOf': {'@id': SITE + '#website'}, 'about': {'@id': SITE + '#book'}}, book_ld(),
        crumbs([('হোম', ''), (h1, slug + '/')])]}
    write(f'{slug}/index.html', page(f'{slug}/index.html', title=title, desc=desc, body=body, active=slug + '/', root=root, jsonld=ld))


def build_about():
    root = '../'
    copyright_html = render_blocks(BOOK['front'].get('copyright', []))
    ack = render_blocks(BOOK['front'].get('acknowledgments', []))
    body = f'''<div class="wrap"><article class="page-prose" style="padding-top:1.5rem">
{breadcrumb_html([('হোম', ''), ('পরিচিতি ও কৃতজ্ঞতা', 'about/')], root)}
<header class="law-head"><h1>পরিচিতি, উৎসর্গ ও কৃতজ্ঞতা</h1></header>
<h2>এই প্রকল্পের উদ্দেশ্য</h2>
<p>“ক্ষমতা — The 48 Laws of Power বাংলা পাঠ ও অনুশীলন” একটি সম্পূর্ণ বিনামূল্যের, অবাণিজ্যিক ডিজিটাল পাঠ-প্রকল্প। উদ্দেশ্য একটাই: বাংলাভাষী পাঠকদের জন্য বইটি পড়া, বোঝা, নিজের ভাবনা লিখে রাখা এবং প্রতিটি আইন নিয়ে সমালোচনামূলকভাবে চিন্তা করা সহজ করা। এখানে কোনো বিজ্ঞাপন, বিক্রয়, সাবস্ক্রিপশন, নিবন্ধন বা ট্র্যাকিং নেই।</p>
<h2>উৎসর্গ</h2>
<div class="dedication"><p style="margin:0">এই পাঠ-প্রকল্প মূল লেখক <strong>রবার্ট গ্রিন</strong>-এর প্রতি উৎসর্গীকৃত — যাঁর গবেষণা ও লেখনী তিন হাজার বছরের ইতিহাস থেকে ক্ষমতার গতিপ্রকৃতিকে পাঠকের সামনে তুলে ধরেছে।</p></div>
<h2>গ্রন্থ-তথ্য</h2>
<dl>
<dt>মূল গ্রন্থ</dt><dd lang="en" class="en">The 48 Laws of Power</dd>
<dt>লেখক</dt><dd>রবার্ট গ্রিন (Robert Greene)</dd>
<dt>প্রযোজনা</dt><dd>জুস্ট এলফার্স (Joost Elffers) — “একটি জুস্ট এলফার্স প্রোডাকশন”</dd>
<dt>মূল প্রকাশ</dt><dd>{e(M['original_pub'])}</dd>
<dt>বাংলা শিরোনাম</dt><dd>{e(M['title_bn_full'])}</dd>
<dt>বাংলা অনুবাদ</dt><dd>{e(M['translator'])}</dd>
<dt>বাংলা প্রকাশক</dt><dd>{e(M['bn_publisher'])}</dd>
</dl>
<h2>স্বত্ব ও অনুমতি</h2>
<p>{e(M['permission_note'])}</p>
<p>এই ওয়েবসাইট রবার্ট গ্রিন, জুস্ট এলফার্স বা মূল প্রকাশকের দ্বারা তৈরি, পরিচালিত বা অনুমোদিত কোনো অফিসিয়াল সাইট নয়। বইয়ের সব স্বত্ব সংশ্লিষ্ট স্বত্বাধিকারীদের।</p>
<details><summary>বইয়ের স্বত্ব-পৃষ্ঠা (অনূদিত সংস্করণ থেকে)</summary><div class="prose" style="margin-top:1rem">{copyright_html}</div></details>
<h2>লেখকের কৃতজ্ঞতা স্বীকার</h2>
<div class="prose">{ack}</div>
<h2>লেখার মান ও সংশোধন</h2>
<p>বইয়ের পাঠ স্ক্যান করা পৃষ্ঠা থেকে OCR-এর মাধ্যমে নেওয়া হয়েছে এবং মূল ক্রম ও শব্দ অপরিবর্তিত রাখার চেষ্টা করা হয়েছে। কোথাও বানান বা শব্দের ভুল চোখে পড়লে সংশোধনের জন্য জানালে কৃতজ্ঞ থাকব।</p>
<h2>গোপনীয়তা</h2>
<p>এই সাইট কোনো ব্যক্তিগত তথ্য সংগ্রহ করে না, কুকি বা অ্যানালিটিক্স ব্যবহার করে না। আপনার পড়ার অগ্রগতি, বুকমার্ক, নোট ও সেটিংস শুধু আপনার ব্রাউজারের লোকাল স্টোরেজে থাকে। ব্রাউজারের ডেটা মুছলে এগুলোও মুছে যাবে — তাই মাঝে মাঝে <a href="../settings/">সেটিংস</a> থেকে ব্যাকআপ নিন।</p>
<h2>প্রযুক্তি</h2>
<p>সম্পূর্ণ স্ট্যাটিক HTML, CSS ও সামান্য জাভাস্ক্রিপ্ট; কোনো ব্যাকএন্ড বা বাইরের সার্ভিস নেই। বাংলা ফন্ট: Noto Serif Bengali (SIL Open Font License)। আপনার কম্পিউটারে SolaimanLipi ইনস্টল থাকলে সেটিই ব্যবহৃত হয়।</p>
</article></div>'''
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'AboutPage', '@id': SITE + 'about/', 'url': SITE + 'about/', 'name': 'পরিচিতি, উৎসর্গ ও কৃতজ্ঞতা', 'inLanguage': 'bn',
         'isPartOf': {'@id': SITE + '#website'}, 'about': {'@id': SITE + '#book'}}, book_ld(),
        crumbs([('হোম', ''), ('পরিচিতি ও কৃতজ্ঞতা', 'about/')])]}
    write('about/index.html', page('about/index.html', title='পরিচিতি, উৎসর্গ ও কৃতজ্ঞতা | The 48 Laws of Power বাংলা',
                                   desc='রবার্ট গ্রিনের প্রতি উৎসর্গীকৃত অবাণিজ্যিক বাংলা পাঠ-প্রকল্পের উদ্দেশ্য, গ্রন্থ-তথ্য, অনুবাদ ও স্বত্ব সংক্রান্ত তথ্য এবং গোপনীয়তা নীতি।',
                                   body=body, active='about/', root=root, jsonld=ld))


def build_tool_pages():
    root = '../'
    notes = f'''<div class="wrap" style="max-width:48rem"><header class="page-head"><h1>আমার নোট</h1><p>নোট শুধু এই ব্রাউজারে সংরক্ষিত থাকে। <span id="note-count"></span></p></header>
<form id="note-form" class="note-form panel"><input type="hidden" id="note-id">
<div class="field"><label for="note-law">কোন আইন সম্পর্কে</label><select id="note-law"></select></div>
<div class="field"><label for="note-text">নোট</label><textarea id="note-text" rows="5" required></textarea></div>
<div><button class="btn" id="note-submit" type="submit">নোট সংরক্ষণ করুন</button> <button class="btn ghost" type="button" id="note-cancel" hidden>বাতিল</button></div></form>
<div class="toolbar" style="margin-top:1.5rem"><label class="search" for="note-q">{icon('search')}<span class="sr-only">নোট খুঁজুন</span><input type="search" id="note-q" placeholder="নোটে খুঁজুন"></label>
<label class="sr-only" for="note-filter">আইন অনুযায়ী ফিল্টার</label><select id="note-filter" style="flex:0 1 16rem"></select></div>
<ul class="note-list" id="note-list"></ul><p class="empty" id="note-empty">কোনো নোট নেই।</p></div>'''
    write('notes/index.html', page('notes/index.html', title='আমার নোট | The 48 Laws of Power বাংলা', desc='প্রতিটি আইন নিয়ে নিজের ব্যক্তিগত নোট লিখুন, খুঁজুন ও সম্পাদনা করুন — সব কিছু শুধু আপনার ব্রাউজারে।',
                                   body=notes, active='notes/', root=root, scripts=('app', 'pages'), laws_data=True, robots='noindex,follow'))
    bms = '''<div class="wrap"><header class="page-head"><h1>বুকমার্ক</h1><p>যেসব আইন আপনি চিহ্নিত করে রেখেছেন।</p></header>
<ul class="law-list" id="bookmark-list"></ul><p class="empty" id="bookmark-empty">এখনো কোনো বুকমার্ক নেই। কোনো আইনের পাতায় “বুকমার্ক” বোতাম চাপুন। <a href="../laws/">সব আইন দেখুন</a></p></div>'''
    write('bookmarks/index.html', page('bookmarks/index.html', title='বুকমার্ক | The 48 Laws of Power বাংলা', desc='আপনার বুকমার্ক করা আইনগুলো এক জায়গায়।',
                                       body=bms, active='bookmarks/', root=root, scripts=('app', 'pages'), laws_data=True, robots='noindex,follow'))
    def radios(name, opts):
        return '<div class="seg">' + ''.join(f'<label><input type="radio" name="{name}" value="{v}"> {l}</label>' for v, l in opts) + '</div>'
    settings = f'''<div class="wrap" style="max-width:48rem"><header class="page-head"><h1>সেটিংস</h1><p>পছন্দগুলো সঙ্গে সঙ্গে সংরক্ষিত হয় (শুধু এই ব্রাউজারে)।</p></header>
<form id="settings-form" class="panel" onsubmit="return false">
<fieldset class="setting" style="border:0;margin:0"><legend><strong>থিম</strong></legend>{radios('theme', [('system', 'সিস্টেম'), ('light', 'লাইট'), ('dark', 'ডার্ক')])}</fieldset>
<fieldset class="setting" style="border:0;margin:0"><legend><strong>পাঠের ফন্ট</strong></legend>{radios('font', [('auto', 'স্বয়ংক্রিয়'), ('solaiman', 'SolaimanLipi (ইনস্টল থাকলে)'), ('serif', 'Noto Serif Bengali'), ('sans', 'Noto Sans Bengali')])}</fieldset>
<div class="setting"><label for="set-fs"><strong>ফন্টের আকার:</strong> <output id="fs-val"></output></label><input type="range" id="set-fs" min="14" max="28" step="1"></div>
<div class="setting"><label for="set-lh"><strong>লাইনের ফাঁক:</strong> <output id="lh-val"></output></label><input type="range" id="set-lh" min="1.4" max="2.4" step="0.05"></div>
<div class="setting"><label for="set-width"><strong>লেখার কলামের প্রস্থ:</strong> <output id="width-val"></output></label><input type="range" id="set-width" min="28" max="56" step="1"></div>
<div class="setting"><p class="preview">ক্ষমতা হলো একটি সামাজিক খেলা। এই নমুনা লেখায় আপনার বেছে নেওয়া ফন্ট, আকার ও লাইনের ফাঁক দেখা যাচ্ছে।</p>
<div><button class="btn small ghost" type="button" id="reset-prefs">পাঠ-সেটিংস ডিফল্টে ফেরান</button></div></div>
</form>
<section class="section"><h2>ব্যক্তিগত ডেটা</h2>
<p>আপনার অগ্রগতি, বুকমার্ক, নোট ও অনুশীলনের লেখা শুধু এই ব্রাউজারে আছে। ব্রাউজারের ডেটা মুছলে বা অন্য ডিভাইসে গেলে এগুলো পাওয়া যাবে না — নিয়মিত ব্যাকআপ নিন।</p>
<div class="grid two">
<div class="panel"><h3 style="margin-top:0">এক্সপোর্ট</h3><p>সব ডেটা একটি JSON ফাইলে ডাউনলোড করুন।</p><button class="btn" id="export-btn" type="button">ব্যাকআপ ডাউনলোড</button></div>
<div class="panel"><h3 style="margin-top:0">ইমপোর্ট</h3><p>আগে নেওয়া ব্যাকআপ ফাইল থেকে ডেটা ফিরিয়ে আনুন।</p><label class="btn ghost" for="import-file">ফাইল বেছে নিন</label><input type="file" id="import-file" accept="application/json,.json" class="sr-only"></div>
</div>
<div class="panel" style="margin-top:1rem;border-color:var(--red)"><h3 style="margin-top:0">সব ডেটা মুছুন</h3><p>অগ্রগতি, বুকমার্ক, নোট, অনুশীলন ও সেটিংস স্থায়ীভাবে মুছে যাবে।</p><button class="btn danger" id="reset-all" type="button">সব ব্যক্তিগত ডেটা মুছুন</button></div>
</section></div>'''
    write('settings/index.html', page('settings/index.html', title='সেটিংস | The 48 Laws of Power বাংলা', desc='থিম, ফন্ট, লেখার আকার ও লাইনের ফাঁক ঠিক করুন; ব্যক্তিগত ডেটা এক্সপোর্ট, ইমপোর্ট বা মুছুন।',
                                      body=settings, active='settings/', root=root, scripts=('app', 'pages'), robots='noindex,follow'))


def build_404():
    body = '''<div class="wrap" style="max-width:40rem;padding:3rem 1rem;text-align:center"><p class="stat">৪০৪</p><h1>পাতাটি পাওয়া যায়নি</h1>
<p class="muted">ঠিকানাটি হয়তো ভুল, অথবা পাতাটি সরানো হয়েছে।</p><p><a class="btn" href="ROOT">হোমে ফিরুন</a> <a class="btn ghost" href="ROOTlaws/">৪৮টি আইন</a></p></div>'''
    # GitHub Pages serves 404.html from any depth, so use absolute site path for links/assets.
    from urllib.parse import urlparse
    base = urlparse(SITE).path or '/'
    write('404.html', page('404.html', title='পাতা পাওয়া যায়নি | The 48 Laws of Power বাংলা', desc='পাতাটি পাওয়া যায়নি।',
                           body=body.replace('ROOT', base), root=base, robots='noindex'))
    write('offline.html', page('offline.html', title='অফলাইন | The 48 Laws of Power বাংলা', desc='ইন্টারনেট সংযোগ নেই।',
                               body='<div class="wrap" style="max-width:40rem;padding:3rem 1rem;text-align:center"><h1>আপনি এখন অফলাইনে</h1><p class="muted">এই পাতাটি আগে খোলা হয়নি বলে সংরক্ষিত নেই। আগে পড়া অধ্যায়গুলো অফলাইনেও খোলা যাবে।</p><p><a class="btn" href="./">হোম</a></p></div>',
                               root='./', robots='noindex'))


def build_meta_files(pages):
    urls = ''.join(f'<url><loc>{SITE}{p}</loc><lastmod>{TODAY}</lastmod></url>' for p in pages)
    write('sitemap.xml', f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n')
    lines = [f'# {CONFIG["site_name"]}', '', f'> {CONFIG["description"]}', '',
             'মূল লেখক: Robert Greene (রবার্ট গ্রিন)। অবাণিজ্যিক বাংলা পাঠ-প্রকল্প; অফিসিয়াল সাইট নয়।', '',
             '## প্রধান পাতা', f'- [৪৮টি আইনের তালিকা]({SITE}laws/)', f'- [ভূমিকা]({SITE}preface/)', f'- [পরিচিতি ও স্বত্ব]({SITE}about/)', '', '## আইনসমূহ']
    lines += [f'- [আইন {bn(L["n"])}: {L["title"]} (Law {L["n"]}: {EN_TITLES[L["n"] - 1]})]({SITE}laws/{law_file(L["n"])})' for L in BOOK['laws']]
    write('llms.txt', '\n'.join(lines) + '\n')
    manifest = {'name': CONFIG['site_name'], 'short_name': 'ক্ষমতা', 'lang': 'bn', 'start_url': './', 'scope': './',
                'display': 'standalone', 'background_color': '#F7F4ED', 'theme_color': '#20235F',
                'description': CONFIG['description'],
                'icons': [{'src': 'assets/icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                          {'src': 'assets/icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
                          {'src': 'assets/icons/icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]}
    write('manifest.webmanifest', json.dumps(manifest, ensure_ascii=False, indent=1))
    write('.nojekyll', '')
    write('data/laws.json', json.dumps([{'n': L['n'], 'title_bn': L['title'], 'title_en': EN_TITLES[L['n'] - 1],
                                         'summary_bn': plain(L['judgment']), 'url': f'laws/{law_file(L["n"])}'} for L in BOOK['laws']],
                                       ensure_ascii=False, indent=1))


def minify_assets():
    """CSS: safe whitespace/comment minification. JS: terser if available (optional)."""
    import subprocess
    css_dir = os.path.join(OUT, 'assets', 'css')
    for f in os.listdir(css_dir):
        p = os.path.join(css_dir, f)
        s = open(p, encoding='utf-8').read()
        s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
        s = re.sub(r'\s*\n\s*', '', s)
        s = re.sub(r'\s*([{};,>])\s*', r'\1', s)
        s = s.replace(';}', '}')
        open(p, 'w', encoding='utf-8').write(s)
    js_dir = os.path.join(OUT, 'assets', 'js')
    terser = shutil.which('terser')
    for base in (os.environ.get('TERSER_CWD', ''), HERE, ROOT):
        cand = os.path.join(base, 'node_modules', '.bin', 'terser')
        if base and os.path.exists(cand):
            terser = cand
    if not terser:
        print('terser not found — JS left unminified (optional: npm i -g terser)')
        return
    for f in os.listdir(js_dir):
        p = os.path.join(js_dir, f)
        subprocess.run([terser, p, '-c', '-m', '-o', p], check=True, timeout=120)
    sw = os.path.join(OUT, 'sw.js')
    subprocess.run([terser, sw, '-c', '-m', '-o', sw], check=True, timeout=120)


def main():
    global ASSET_VER
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(HERE, 'assets'), os.path.join(OUT, 'assets'))
    h = hashlib.sha1()
    for d, _, fs in sorted(os.walk(os.path.join(HERE, 'assets'))):
        for f in sorted(fs):
            h.update(open(os.path.join(d, f), 'rb').read())
    ASSET_VER = h.hexdigest()[:8]
    sw = open(os.path.join(HERE, 'sw.js'), encoding='utf-8').read().replace('__VERSION__', ASSET_VER)
    write('sw.js', sw)
    build_home()
    build_laws_index()
    for L in BOOK['laws']:
        build_law(L)
    pre = BOOK['front']['preface']
    build_text_page('preface', 'ভূমিকা', pre, 'ভূমিকা — The 48 Laws of Power বাংলা | রবার্ট গ্রিন',
                    clip('রবার্ট গ্রিনের The 48 Laws of Power বইয়ের ভূমিকা: ' + plain(pre[:1]), 160), kicker='শুরুর কথা')
    extra = []
    if BOOK.get('back', {}).get('bibliography'):
        bib = [{'t': 'p', 'x': 'বইয়ের শেষে লেখক যেসব গ্রন্থের তালিকা দিয়েছেন, তার বাংলা প্রতিবর্ণীকৃত রূপ। স্ক্যান করা পাতা থেকে OCR করা হয়েছে বলে বিদেশি নামের বানানে ভুল থাকতে পারে।'}]
        bib += [{'t': 'ul', 'items': BOOK['back']['bibliography']}]
        build_text_page('bibliography', 'নির্বাচিত গ্রন্থপঞ্জি', bib, 'নির্বাচিত গ্রন্থপঞ্জি | The 48 Laws of Power বাংলা',
                        'The 48 Laws of Power বইয়ে রবার্ট গ্রিন যেসব গ্রন্থের উল্লেখ করেছেন তার নির্বাচিত তালিকা।')
        extra.append('bibliography/')
    build_about()
    build_tool_pages()
    build_404()
    pages = ['', 'laws/', 'preface/', 'about/'] + extra + [f'laws/{law_file(L["n"])}' for L in BOOK['laws']]
    build_meta_files(pages)
    minify_assets()
    print('built', OUT, 'asset version', ASSET_VER)


if __name__ == '__main__':
    main()
