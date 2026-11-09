"""Merge two Tesseract outputs (ben = primary, bsc = Bengali script model) per page.
Produces pages/<id>.json : list of paragraphs, each a list of lines, each a list of
(word, flag) where flag in {'', 'fix', 'unsure'}.
"""
import csv, json, os, re, sys, glob, collections

csv.field_size_limit(10**9)
LAT = re.compile(r'[A-Za-z]')
BEN = re.compile(r'[ঀ-৿]')
HALANT_OR_SIGN = set('ািীুূৃৄেৈোৌ্ঁংঃৗ')


def read_tsv(path):
    words = []
    with open(path, encoding='utf-8') as fh:
        for row in csv.reader(fh, delimiter='\t', quoting=csv.QUOTE_NONE):
            if len(row) < 12 or row[0] != '5':
                continue
            t = row[11].strip()
            if not t:
                continue
            words.append(dict(block=int(row[2]), par=int(row[3]), line=int(row[4]),
                              x=int(row[6]), y=int(row[7]), w=int(row[8]), h=int(row[9]),
                              conf=float(row[10]), text=t))
    return words


CONS = set(chr(c) for c in range(0x0995, 0x09BA)) | set('ড়ঢ়য়ৎ')
VSIGN = set('ািীুূৃেৈোৌঁংঃ')
MARKS = '|!৷'

def norm(t):
    """Fix systematic glyph confusions. Ambiguous trailing bars become markers:
    \x01 = after bare consonant (া or ।), \x02 = after vowel sign (। or nothing)."""
    t = t.replace('-_', '—').replace('_-', '—').replace('--', '—')
    if t in ('|', 'I', 'l', '1|', '৷', '!|'):
        return '।'
    out = []
    n = len(t)
    for i, ch in enumerate(t):
        if ch in MARKS:
            prev = out[-1] if out else ''
            last = all(c in MARKS + '।,;:?)"”’' for c in t[i + 1:])
            if prev in CONS:
                out.append('\x01' if last else 'া')
            elif prev in VSIGN or prev == '্':
                out.append('\x02' if last else '')
            elif ch == '!' and not prev:
                out.append('!')
            elif ch == '!':
                out.append('!')
            else:
                out.append('।' if last else '')
        else:
            out.append(ch)
    t = ''.join(out)
    # collapse duplicated markers
    t = re.sub(r'[\x01\x02]+(?=[\x01\x02])', '', t)
    t = re.sub('ঙ(?=[ক-ঘ])', 'ঙ্', t)   # ঙক -> ঙ্ক etc. (hasanta lost)
    t = t.replace('।।', '।')
    return t


PUN = '।,;:?!"\'()‘’“”—…-.\x01\x02'
def core(t):
    return t.strip(PUN).replace('\x01', '').replace('\x02', '')

def resolve(t, freq, other=''):
    """Resolve ambiguous trailing markers using the other model's reading, then frequency."""
    if '\x01' in t:
        stem = t.replace('\x01', '')
        oc = core(other)
        if other and oc == stem + 'া':
            return stem + 'া' + ('।' if other.rstrip().endswith('।') else '')
        if other and oc == stem and other.endswith('।'):
            return stem + '।'
        fa = freq.get(core(stem + 'া'), 0); fd = freq.get(core(stem), 0)
        return stem + 'া' if fa > fd else stem + '।'
    if '\x02' in t:
        stem = t.replace('\x02', '')
        if other and other.endswith('।'):
            return stem + '।'
        return stem
    return t

def overlap(a, b):
    x1 = max(a['x'], b['x']); x2 = min(a['x'] + a['w'], b['x'] + b['w'])
    y1 = max(a['y'], b['y']); y2 = min(a['y'] + a['h'], b['y'] + b['h'])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    return inter / min(a['w'] * a['h'], b['w'] * b['h'])

def iou(a, b):
    x1 = max(a['x'], b['x']); x2 = min(a['x'] + a['w'], b['x'] + b['w'])
    y1 = max(a['y'], b['y']); y2 = min(a['y'] + a['h'], b['y'] + b['h'])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    return inter / max(a['w'] * a['h'], b['w'] * b['h'])


def lines_of(words):
    d = collections.OrderedDict()
    for w in words:
        d.setdefault((w['block'], w['par'], w['line']), []).append(w)
    out = []
    for k, ws in d.items():
        y = min(w['y'] for w in ws); y2 = max(w['y'] + w['h'] for w in ws)
        x = min(w['x'] for w in ws); x2 = max(w['x'] + w['w'] for w in ws)
        out.append(dict(key=k, words=ws, y=y, h=y2 - y, x=x, w=x2 - x))
    return out


def choose(bw, cands, freq):
    raw_b = norm(''.join(c['text'] for c in cands)) if cands else ''
    b_res = resolve(raw_b, freq) if cands else ''
    a = resolve(norm(bw['text']), freq, b_res)
    a = a.replace('!', '') if re.search('[ঀ-৿]!', a) else a
    if not cands:
        flag = 'unsure' if (bw['conf'] < 60 or (LAT.search(a) and BEN.search(a))) else ''
        if flag == '' and BEN.search(a) and freq.get(core(a), 0) <= 1 and bw['conf'] < 90:
            flag = 'unsure'
        return a, flag
    b = b_res.replace('!', '') if re.search('[ঀ-৿]!', b_res) else b_res
    if a == b or core(a) == core(b):
        return a, ''
    a_lat, b_lat = bool(LAT.search(a)), bool(LAT.search(b))
    if a_lat and not b_lat and BEN.search(b):
        return b, 'fix'
    if b_lat and not a_lat:
        return a, ''
    fa, fb = freq.get(core(a), 0), freq.get(core(b), 0)
    if bw['conf'] >= 93 and fa >= 2:
        return a, ''
    if fb >= 3 * max(fa, 1) and fb >= 3:
        # keep a's punctuation
        tail = a[len(a.rstrip(PUN)):] if a.rstrip(PUN) != a else ''
        return core(b) + tail if tail else b, 'fix'
    if fa >= 2:
        return a, ''
    return a, ('unsure' if (bw['conf'] < 85 or fa <= 1) else '')


REOCR = json.load(open('reocr.json')) if os.path.exists('reocr.json') else {}

def merge_page(pid, freq):
    ben = read_tsv(f'ocr/{pid}.ben.tsv')
    bsc = read_tsv(f'ocr/{pid}.bsc.tsv')
    blines = lines_of(ben)
    slines = lines_of(bsc)
    # map bsc lines to ben lines
    used = set()
    out_lines = []  # (y, block, [(w,flag)], from_bsc)
    assign = collections.defaultdict(list)
    for sw in bsc:
        best, bo = None, 0.3
        for bw in ben:
            o = iou(bw, sw)
            if o > bo:
                best, bo = bw, o
        if best is not None:
            assign[id(best)].append(sw)
    for L in blines:
        toks = []
        for bw in L['words']:
            cands = sorted(assign.get(id(bw), []), key=lambda c: c['x'])
            key = f"{pid}|{bw['x']}|{bw['y']}"
            if key in REOCR:
                w_, f_ = choose(bw, cands, freq)
                if LAT.search(w_):
                    toks.append((norm(REOCR[key]).replace('\x01', '\u09be').replace('\x02', ''), 'unsure'))
                    continue
            for c in cands:
                used.add(id(c))
            toks.append(choose(bw, cands, freq))
        bots = sorted(w['y'] + w['h'] for w in L['words'])
        out_lines.append(dict(y=L['y'], h=L['h'], x=L['x'], w=L['w'], block=L['key'][0], toks=toks, extra=False, mb=bots[len(bots) // 2]))
    # lines found only by bsc
    for S in slines:
        if any(id(w) in used for w in S['words']):
            continue
        if any(overlap(S, dict(x=L['x'], y=L['y'], w=L['w'], h=L['h'])) > 0.3 for L in blines):
            continue
        toks = [(norm(w['text']), 'unsure') for w in S['words']]
        bots = sorted(w['y'] + w['h'] for w in S['words'])
        out_lines.append(dict(y=S['y'], h=S['h'], x=S['x'], w=S['w'], block=-1, toks=toks, extra=True, mb=bots[len(bots) // 2]))
    out_lines.sort(key=lambda l: l['y'])
    if not out_lines:
        return []
    # paragraph breaks from line pitch measured on per-line median word bottoms (robust to matras/ascenders)
    pitches = [out_lines[i + 1]['mb'] - out_lines[i]['mb'] for i in range(len(out_lines) - 1)]
    ps = sorted(p for p in pitches if p > 0)
    med = ps[len(ps) // 2] if ps else 0
    rights = sorted(l['x'] + l['w'] for l in out_lines)
    lefts = sorted(l['x'] for l in out_lines)
    R = rights[int(len(rights) * 0.9)] if rights else 0
    Lm = lefts[len(lefts) // 4] if lefts else 0
    width = max(1, R - Lm)
    for l in out_lines:
        l['short'] = (l['x'] + l['w']) < R - 0.12 * width
    paras, cur = [], [out_lines[0]]
    for i, p in enumerate(pitches):
        if med and p > med * 1.28:
            paras.append(cur); cur = []
        cur.append(out_lines[i + 1])
    paras.append(cur)
    return [[dict(toks=l['toks'], extra=l['extra'], short=l['short']) for l in p] for p in paras]


def build_freq():
    freq = collections.Counter()
    for f in glob.glob('ocr/*.tsv'):
        for w in read_tsv(f):
            if w['conf'] > 80:
                c = core(norm(w['text']))
                if c: freq[c] += 1
    return freq


if __name__ == '__main__':
    freq = build_freq()
    json.dump(freq, open('freq.json', 'w'), ensure_ascii=False)
    os.makedirs('pages', exist_ok=True)
    ids = sorted({os.path.basename(f).split('.')[0] for f in glob.glob('ocr/*.bsc.tsv')})
    for pid in ids:
        json.dump(merge_page(pid, freq), open(f'pages/{pid}.json', 'w'), ensure_ascii=False)
    print(len(ids), 'pages merged')
