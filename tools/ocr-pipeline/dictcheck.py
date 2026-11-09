import json, re, collections, time
S = set()
for line in open('dict/bn_BD.dic', encoding='utf-8').read().split('\n')[1:]:
    w = line.split('/')[0].strip()
    if w: S.add(w)
SUF = sorted(['র', 'এর', 'ের', 'কে', 'দের', 'রা', 'েরা', 'গুলো', 'গুলোর', 'গুলোকে', 'গুলি', 'গুলির', 'টি', 'টা', 'টির', 'টিকে', 'টার',
              'ে', 'য়', 'তে', 'ও', 'ই', 'য়ের', 'েই', 'েও', 'রই', 'রও', 'কেই', 'দেরকে', 'দেরও', 'েরও', 'েরই', 'জন', 'খানা', 'ভাবে', 'মতো',
              'হীন', 'পূর্ণ', 'গণ', 'বৃন্দ', 'সমূহ', 'িক', 'য়ে', 'েছে', 'েছিল', 'েছিলেন', 'লেন', 'তেন', 'বেন', 'ছেন', 'ছিল', 'ছিলেন', 'ল', 'ত', 'ব', 'ন', 'েন', 'ো', 'ুন'], key=len, reverse=True)
def lookup(w):
    if w in S: return True
    for suf in SUF:
        if w.endswith(suf) and len(w) - len(suf) >= 2 and w[:-len(suf)] in S:
            return True
    return False
PUN = '।,;:?!"\'()‘’“”—…-.'
SWAP = {'ু': 'ূ', 'ূ': 'ু', 'ি': 'ী', 'ী': 'ি'}
cache = {}
def ok(w):
    if w not in cache:
        try: cache[w] = lookup(w)
        except Exception: cache[w] = False
    return cache[w]
def cands(w):
    # only the OCR-bias direction: ু -> ূ ; plus restoring ঁ in a few known-lost spots
    out = set()
    idx = [i for i, c in enumerate(w) if c == '\u09c1']
    for i in idx:
        out.add(w[:i] + '\u09c2' + w[i + 1:])
    if 'পৌছ' in w: out.add(w.replace('পৌছ', 'পৌঁছ'))
    if 'জাকজমক' in w: out.add(w.replace('জাকজমক', 'জাঁকজমক'))
    if 'ঝাপ' in w: out.add(w.replace('ঝাপ', 'ঝাঁপ'))
    if 'ল্ন' in w: out.add(w.replace('ল্ন', 'ল্প'))
    if 'দাড়' in w: out.add(w.replace('দাড়', 'দাঁড়'))
    out.discard(w)
    return out
def _old_cands(w):
    out = set()
    idx = [i for i, c in enumerate(w) if c in SWAP]
    for i in idx:
        out.add(w[:i] + SWAP[w[i]] + w[i + 1:])
    for i, j in [(a, b) for a in idx for b in idx if a < b]:
        x = list(w); x[i] = SWAP[x[i]]; x[j] = SWAP[x[j]]; out.add(''.join(x))
    for i in range(1, len(w) + 1):
        out.add(w[:i] + 'ঁ' + w[i:])
    out.discard(w)
    return out
if __name__ == '__main__':
    s = json.load(open('stream.json'))
    freq = collections.Counter(tok.strip(PUN) for p in s for tok in p['text'].split())
    t = time.time(); n = 0; fixes = {}
    for w, f in freq.most_common():
        if not re.fullmatch('[ঀ-৿‌‍]+', w): continue
        n += 1
        if ok(w): continue
        good = [c for c in cands(w) if ok(c)]
        if len(good) == 1 and w not in ('মুসা', 'মুসার'):
            fixes[w] = good[0]
    print(n, 'words checked in', round(time.time() - t), 's;', len(fixes), 'fixes')
    for k, v in list(fixes.items())[:60]: print(k, '->', v)
    json.dump(fixes, open('dictfix.json', 'w'), ensure_ascii=False)
