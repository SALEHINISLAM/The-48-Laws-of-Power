"""Turn stream.json (ordered paragraphs) into src/content/book.json."""
import json, re, difflib, sys

BNDIG = '০১২৩৪৫৬৭৮৯'
def bnum(s):
    return int(''.join(str(BNDIG.index(c)) for c in s))

stream = json.load(open('stream.json'))
# dictionary-confirmed OCR fixes (ু->ূ, lost ঁ); see dictcheck.py
import subprocess
subprocess.run([sys.executable, 'dictcheck.py'], check=True, stdout=subprocess.DEVNULL)
FIX = json.load(open('dictfix.json'))
PUNC = '।,;:?!"\'()‘’“”—…-.'
FIXCOUNT = {}
def _fix(t):
    def rep(mo):
        tok = mo.group(0); c = tok.strip(PUNC)
        if c in FIX:
            FIXCOUNT[c] = FIXCOUNT.get(c, 0) + 1
            return tok.replace(c, FIX[c])
        return tok
    return re.sub(r'\S+', rep, t)
GLOBAL = [('—-', '—'), ('-—', '—'), ('—_', '—'), ('_—', '—'), ('ৰ', 'র'), ('ৱ', 'ব'), ('পূু', 'পূ'), ('আ্যা', 'অ্যা'), ('স্বেরাচার', 'স্বৈরাচার'), ('দাড়িয়ে', 'দাঁড়িয়ে'), ('দাড়াল', 'দাঁড়াল'), ('এশ্বরিক', 'ঐশ্বরিক'), ('উধর্বতন', 'ঊর্ধ্বতন'), ('বিকল্ল', 'বিকল্প'), ('সদ্ধ্যবহার', 'সদ্ব্যবহার'), ('পরিচালন। করতে', 'পরিচালনা করতে'), ('পাশ। উল্টে', 'পাশা উল্টে'), ('পরিকল্ননা', 'পরিকল্পনা'), ('পূর্বাভাসযোগ্যত।', 'পূর্বাভাসযোগ্যতা')]
def _glob(t):
    for a, b in GLOBAL:
        t = t.replace(a, b)
    t = re.sub(r'(?<![\u0980-\u09ff])ংক্রমণ', 'সংক্রমণ', t)
    # "তার।" never ends a sentence (possessive) — when text continues, it is "তারা"
    t = re.sub(r'(?<![\u0980-\u09ff])তার।(?= [\u0980-\u09ff])', 'তারা', t)
    return t
import dictcheck as _dc
DANDA_FIX = {}
DANDA_SKIP = {'হব', 'ছোট', 'ফুল', 'নিক', 'ভন', 'চেন'}
def _danda(t):
    def rep(mo):
        w = mo.group(1)
        bad = (not _dc.ok(w) and _dc.ok(w + '\u09be')) or (w.endswith('ত') and len(w) > 4 and _dc.ok(w[:-1]) and not _dc.ok(w))
        if bad and len(w) >= 3 and w not in DANDA_SKIP:
            DANDA_FIX[w + '।'] = w + '\u09be'
            return w + '\u09be' + mo.group(2)
        return mo.group(0)
    return re.sub(r'(?<![\u0980-\u09ff])([\u0980-\u09ff]+[\u0995-\u09b9])।(\s+(?=[\u0980-\u09ff]))', rep, t)
for p in stream:
    p['text'] = _danda(_fix(_glob(p['text'])))
json.dump(DANDA_FIX, open('danda_fixes.json', 'w'), ensure_ascii=False)
# split "আইন N\n<title...>" glued paragraphs
_s2 = []
for p in stream:
    mo = re.match(r'^(আইন\s*[০-৯]{1,2})\s*\n(.+)$', p['text'], re.S)
    if mo:
        _s2.append(dict(p, text=mo.group(1).replace('\n', ' ')))
        _s2.append(dict(p, text=mo.group(2)))
    else:
        _s2.append(p)
stream = _s2
json.dump({k: [FIX[k], v] for k, v in FIXCOUNT.items()}, open('fixes_applied.json', 'w'), ensure_ascii=False)

LABELS = ['বিচারবুদ্ধি', 'বিচার', 'বিবেচনা', 'বিবেচন', 'মূলকথা', 'মুলকথা', 'সিদ্ধান্ত', 'রায়']
lab_rx = '|'.join(LABELS)
HEADINGS = ['আইনের লঙ্ঘন এবং পালন', 'আইন লঙ্ঘন এবং পালন', 'আইনের লঙ্ঘন', 'আইন লঙ্ঘন', 'আইনের পালন', 'আইন পালন',
            'ব্যাখ্যা', 'ক্ষমতার চাবিকাঠি', 'বিপরীত দিক', 'বিপরীত', 'বিচারবুদ্ধি', 'বিচার']

def heading_of(t):
    t2 = t.replace('\n', ' ').strip().rstrip(':।')
    if len(t2.split()) > 6 or len(t2) > 40:
        return None
    m = re.match(r'^(.*?)\s*([০-৯]{1,2})?[।|]?$', t2)
    base, num = m.group(1).strip(), m.group(2)
    best = difflib.get_close_matches(base, HEADINGS, n=1, cutoff=0.82)
    if not best:
        return None
    h = best[0]
    if h == 'বিচার':
        h = 'বিচারবুদ্ধি'
    return h + (' ' + num if num else '')

YEAR = re.compile(r'[০-৯]{2,4}\s*[-–—]\s*[০-৯]{2,4}|খ্রিস্টপূর্ব|খ্রিস্টাব্দ|শতাব্দী|শতক')

def classify(paras):
    """paras: list of texts -> blocks"""
    merged = []
    for t in paras:
        if merged and merged[-1].endswith(',') and len(merged[-1].split()) <= 6 and len(t.split()) <= 6:
            merged[-1] = merged[-1] + ' ' + t
        else:
            merged.append(t)
    paras = merged
    out = []
    for t in paras:
        if re.fullmatch(r'আইন\s*[০-৯0-9&]{1,3}', t.strip()) or re.fullmatch(r'[০-৯0-9ivxlIVXL।|. ]{1,6}', t.strip()):
            continue  # stray running head
        h = heading_of(t)
        if h:
            out.append({'t': 'h2', 'x': h})
            continue
        words = t.split()
        if len(words) <= 7 and not re.search(r'[।?!:;,"”’]$', t) and not YEAR.search(t) and not re.search(r'[0-9০-৯]', t):
            out.append({'t': 'h3', 'x': t})
            continue
        if len(words) <= 14 and YEAR.search(t) and not t.endswith('।'):
            out.append({'t': 'attr', 'x': t})
            # preceding paragraph is the quotation
            if out[-2:-1] and out[-2]['t'] == 'p' and len(out[-2]['x']) < 900:
                out[-2]['t'] = 'q'
            continue
        out.append({'t': 'p', 'x': t})
    return out

def pg(p):
    return p['pages'][0]

# locate law starts
starts = {}
expect = 1
AMB = {'8': '48', '9': '79', '0': '0', '&': '0123456789', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7'}
def num_ok(s, n):
    s = ''.join(str(BNDIG.index(c)) if c in BNDIG else c for c in s)
    t = str(n)
    if len(s) != len(t): s = s.replace('&', '')
    if len(s) != len(t): return False
    return all(b in AMB.get(a, a) for a, b in zip(s, t))
for i, p in enumerate(stream):
    if expect > 48: break
    m_ = re.fullmatch(r'আইন\s*([০-৯0-9&]{1,3})', p['text'].strip())
    if not m_ or pg(p) < 'p1-021' or not num_ok(m_.group(1), expect):
        continue
    nxt = stream[i + 1]['text'] if i + 1 < len(stream) else ''
    if heading_of(nxt):
        continue
    starts[expect] = i
    expect += 1
found = sorted(starts)
print('laws found:', len(found), 'missing:', [n for n in range(1, 49) if n not in starts], file=sys.stderr)

def page_slice(a, b):
    return [p for p in stream if a <= pg(p) <= b]

texts = lambda ps: [p['text'] for p in ps]

# front matter
pre = page_slice('p1-014', 'p1-020')
pre_t = texts(pre)
if pre_t and pre_t[0].strip().startswith('ভূমিকা'):
    first = pre_t[0].strip()[len('ভূমিকা'):].strip()
    pre_t = ([first] if first else []) + pre_t[1:]
# remove TOC tail that may be glued ("নির্বাচিত গ্রন্থপঞ্জি ভূমিকা")
pre_t = [t for t in pre_t if not re.fullmatch(r'.*গ্রন্থপঞ্জি\s*ভূমিকা', t)]
front = {
    'about_author': classify(texts(page_slice('p1-001', 'p1-001'))),
    'title_page': classify(texts(page_slice('p1-002', 'p1-002'))),
    'copyright': classify(texts(page_slice('p1-003', 'p1-004'))),
    'acknowledgments': classify([t for t in texts(page_slice('p1-005', 'p1-005')) if not t.startswith('কৃতজ্ঞতা স্বীকার')]),
    'preface': classify(pre_t),
}
for k in ('acknowledgments',):
    bl = front[k]
    if bl and bl[-1]['x'].startswith('রবার্ট গ্রিন'):
        bl[-1] = {'t': 'attr', 'x': 'রবার্ট গ্রিন'}

CORR = json.load(open('corrections.json'))
laws = []
for n in found:
    i = starts[n]
    j = starts.get(n + 1, len(stream))
    seg = stream[i + 1:j]
    if n == found[-1]:
        # cut back matter
        for k, p in enumerate(seg):
            if re.match(r'^(নির্বাচিত গ্রন্থপ|নির্ঘণ্ট|সুচী|সূচি)', p['text']):
                seg = seg[:k]
                break
    title = seg[0]['text'].replace('\n', ' ').strip().rstrip('।') if seg else ''
    rest = texts(seg[1:])
    judgment, body = [], []
    k = 0
    # title may have been glued to the বিচার/বিচারবুদ্ধি label + summary
    label = None
    mm = re.match(r'^(.*?)\s+(' + lab_rx + r')[।]?\s+(.*)$', title, re.S)
    if mm and len(mm.group(1).split()) >= 2:
        title = mm.group(1).strip(); label = mm.group(2); rest = [mm.group(3)] + rest
    while rest and heading_of(rest[0]) == 'বিচারবুদ্ধি':
        label = label or rest[0].strip().rstrip('।|'); rest = rest[1:]
    if rest:
        mo2 = re.match(r'^(' + lab_rx + r')[।|]?\s*\n?\s*(.+)$', rest[0], re.S)
        if mo2 and len(rest[0].split('\n')[0].split()) <= 2:
            label = label or mo2.group(1); rest[0] = mo2.group(2).strip()
    if rest and not heading_of(rest[0]):
        judgment.append(rest[0]); k = 1
    body = classify(rest[k:])
    for a_, b_ in CORR.get(str(n), []):
        title = title.replace(a_, b_)
        judgment = [t.replace(a_, b_) for t in judgment]
        for bl in body:
            bl['x'] = bl['x'].replace(a_, b_)
    judgment = [t.replace('\n', ' ') for t in judgment]
    label = {'বিবেচন': 'বিবেচনা', 'মুলকথা': 'মূলকথা', 'বিচার': 'বিচার'}.get(label, label) or 'বিচারবুদ্ধি'
    if label not in LABELS: label = 'বিচারবুদ্ধি'
    laws.append({'n': n, 'label': label, 'title': title, 'judgment': [{'t': 'p', 'x': t} for t in judgment], 'body': body,
                 'pages': [pg(seg[0]) if seg else '', pg(seg[-1]) if seg else '']})

back = {}
if found and found[-1] == 48:
    i = starts[48]
    tail = stream[i:]
    for k, p in enumerate(tail):
        if re.match(r'^নির্বাচিত গ্রন্থপ', p['text']):
            items = []
            for q in tail[k:]:
                t = q['text']
                if re.match(r'^(সুচী|সূচি|সূচী)', t):
                    break
                t = re.sub(r'^নির্বাচিত গ্রন্থপ\S*\s*', '', t)
                if not t or re.fullmatch(r'গ্রন্থপঞ্জি\s*[০-৯0-9]*', t.strip()):
                    continue
                for x in re.split(r'\n|\s\*\s', t):
                    if x.strip(): items.append(x.strip().lstrip('*').strip())
            # glue continuation lines (not starting a new entry) onto previous entry
            merged = []
            for x in items:
                if merged and not re.match(r'^[^\s,]+(?:\s[^\s,]+){0,3},', x):
                    merged[-1] += ' ' + x
                else:
                    merged.append(x)
            back['bibliography'] = [{'t': 'li', 'x': x} for x in merged]
            break

meta = {
    'title_bn': 'দ্য ৪৮ ল’স অব পাওয়ার — ক্ষমতা',
    'title_bn_full': 'দ্য 48 ল’স অব পাওয়ার: ক্ষমতা — পাওয়ারের জন্য ব্যবহারিক নির্দেশিকা',
    'translator': 'PDF বইয়ের সমাহার (প্রচ্ছদে উল্লিখিত অনুবাদ-কৃতিত্ব)',
    'bn_publisher': 'তথ্য যোগ করা হবে',
    'original_pub': 'প্রথম প্রকাশ ১৯৯৮ — প্রোফাইল বুকস লিমিটেড (গ্রেট ব্রিটেন) ও ভাইকিং/পেঙ্গুইন পুটনাম (মার্কিন যুক্তরাষ্ট্র); কপিরাইট © রবার্ট গ্রিন ও জুস্ট এলফার্স, ১৯৯৮',
    'permission_note': 'প্রকল্প-পরিচালকের তথ্য অনুযায়ী, এই বাংলা অনুবাদ ওয়েবসাইটে ব্যবহারের জন্য প্রকাশকের অনুমতি নেওয়া হয়েছে।',
}
book = {'meta': meta, 'front': front, 'laws': laws, 'back': back}
json.dump(book, open('/home/claude/project/src/content/book.json', 'w'), ensure_ascii=False, indent=1)
print('laws:', len(laws), file=sys.stderr)
