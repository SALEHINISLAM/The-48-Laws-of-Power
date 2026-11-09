"""Assemble merged OCR pages into structured book.json + audit data."""
import json, re, os, collections

BNDIG = '০১২৩৪৫৬৭৮৯'
def to_int(s):
    s = ''.join(str(BNDIG.index(c)) if c in BNDIG else c for c in s)
    return int(s) if s.isdigit() else None

ids = [os.path.splitext(os.path.basename(l.strip()))[0] for l in open('list.txt')]
ids = [i for i in ids if os.path.exists(f'pages/{i}.json')]

PUNCT_FIX = [(re.compile(r'[ \t]+([।,;:?!)\]’”])'), r'\1'), (re.compile(r'([(\[‘“])\s+'), r'\1'),
             (re.compile(r'।\s*।'), '।'), (re.compile(r'[ \t]{2,}'), ' '),
             (re.compile(r'\.\s\.\s\.'), '...'), (re.compile(r'(?<=[ঀ-৿])\s+-\s+(?=[ঀ-৿])'), '—'),
             (re.compile(r'—\s+'), '—'), (re.compile(r'\s+—'), '—')]

unsure_log = []

import difflib
HEAD_BASE = ['আইনের লঙ্ঘন এবং পালন', 'আইন লঙ্ঘন এবং পালন', 'আইনের লঙ্ঘন', 'আইন লঙ্ঘন', 'আইনের পালন', 'আইন পালন',
             'ব্যাখ্যা', 'ক্ষমতার চাবিকাঠি', 'বিপরীত দিক', 'বিপরীত', 'বিচারবুদ্ধি', 'বিচার']
def line_words(line):
    return [w for w, f in line['toks']]
def heading_line(line):
    t = ' '.join(line_words(line)).strip().rstrip(':।')
    t = re.sub('\u0999(?=[\u0995-\u0998])', '\u0999\u09cd', t)
    if len(t.split()) > 6:
        return False
    base = re.sub(r'\s*[০-৯0-9IVX।|]+$', '', t).strip()
    if not base:
        return False
    return bool(difflib.get_close_matches(base, HEAD_BASE, n=1, cutoff=0.82))
def split_paras(paras):
    out = []
    for p in paras:
        cur = []
        for k, line in enumerate(p):
            if heading_line(line):
                if cur: out.append(cur)
                out.append([line]); cur = []
                continue
            # a short title line (no ending punctuation) followed by the বিচার heading line
            cur.append(line)
        if cur: out.append(cur)
    return out

def para_text(p, pid):
    global LAST_SHORT
    LAST_SHORT = bool(p and p[-1].get('short'))
    words = []
    flagged = []
    for li, line in enumerate(p):
        for w, f in line['toks']:
            words.append(w)
            if f == 'unsure':
                flagged.append(len(words) - 1)
        if line.get('short') and li < len(p) - 1 and words:
            words[-1] = words[-1] + '\n'
    for i in flagged:
        ctx = ' '.join(words[max(0, i - 5):i]) + ' 【' + words[i] + '】 ' + ' '.join(words[i + 1:i + 6])
        unsure_log.append((pid, words[i], ctx))
    t = ' '.join(words).replace('\n ', '\n')
    for rx, rep in PUNCT_FIX:
        t = rx.sub(rep, t)
    return t.strip()

FOOT_WORDS = {'আইন', 'সুচিপত্র', 'সূচিপত্র', 'সুচিপত্ৰ', 'ভূমিকা', 'প্রস্তাবনা', '(PREFACE)', 'PREFACE', '।', '|'}
RUNHEAD = re.compile(r'(আইন\s*[০-৯]{1,2}[।|]?\s+[0-9০-৯।| ]{1,6}|[0-9০-৯]{1,3}\s+আইন\s*[০-৯]{1,2})')
ROMAN = re.compile(r'^[ivxlcIVXLC]+$')

def is_header(t):
    return bool(re.match(r'^পৃষ্ঠা\s*[-–]?\s*\S*$', t)) or t.startswith('পৃষ্ঠা')

def is_footer(t):
    toks = t.replace('।', ' ').split()
    if not toks or len(toks) > 5:
        return False
    ok = 0
    for x in toks:
        if x in FOOT_WORDS or ROMAN.match(x) or to_int(x) is not None or re.match(r'^[০-৯0-9]+[।|]?$', x):
            ok += 1
    has_marker = any(x in FOOT_WORDS - {'।', '|'} for x in toks)
    has_num = any(to_int(x.strip('।|')) is not None or ROMAN.match(x) for x in toks)
    return has_marker and has_num and ok >= len(toks) - 1

HEADNUM = {}
pages = []  # (pid, [para texts])
for pid in ids:
    paras = []
    for p in split_paras(json.load(open(f'pages/{pid}.json'))):
        t = para_text(p, pid)
        if t and not re.fullmatch(r'Telegram:?\s*t\.me/BoierSomahar', t):
            paras.append((t, LAST_SHORT))
    texts_ = [t for t, _ in paras]
    shorts = [s_ for _, s_ in paras]
    paras = texts_
    if paras and is_header(paras[0]):
        HEADNUM[pid] = paras[0].replace('পৃষ্ঠা', '').strip(' -–')
        paras = paras[1:]; shorts = shorts[1:]
    while paras and (is_footer(paras[-1]) or (len(paras[-1].split()) <= 3 and any(w in paras[-1] for w in ('ভূমিকা', 'প্রস্তাবনা', 'সুচিপত্র', 'সূচিপত্র')))):
        paras = paras[:-1]; shorts = shorts[:-1]
    keep = [i for i, x in enumerate(paras) if not RUNHEAD.fullmatch(x)]
    pages.append((pid, [paras[i] for i in keep], [shorts[i] for i in keep]))

# join across pages
TERM = tuple('।?!"”’)')
stream = []  # list of dict(text, pid)
for pid, paras, shorts in pages:
    for i, t in enumerate(paras):
        cont = False
        if i == 0 and stream:
            prev = stream[-1]['text']
            if t.startswith(('...', '…')) or prev.endswith(('...', '…')) or (not stream[-1]['short'] and not prev.endswith(TERM)):
                # do not glue onto chapter heading lines
                if not re.fullmatch(r'আইন\s*[০-৯]+', prev) and not re.fullmatch(r'আইন\s*[০-৯]+', t):
                    cont = True
        if cont:
            a = re.sub(r'(\.\.\.|…)$', '', stream[-1]['text']).rstrip()
            b = re.sub(r'^(\.\.\.|…)', '', t).lstrip()
            stream[-1]['text'] = a + ' ' + b
            stream[-1]['pages'].append(pid)
            stream[-1]['short'] = shorts[i]
        else:
            stream.append(dict(text=t, pages=[pid], short=shorts[i]))

json.dump(stream, open('stream.json', 'w'), ensure_ascii=False, indent=0)
json.dump(unsure_log, open('unsure.json', 'w'), ensure_ascii=False)
json.dump(HEADNUM, open('headnum.json', 'w'), ensure_ascii=False)
print(len(stream), 'paragraphs;', len(unsure_log), 'unsure words')
