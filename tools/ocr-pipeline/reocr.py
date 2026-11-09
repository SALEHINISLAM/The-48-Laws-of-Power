"""Third pass: words that both models read as Latin garbage inside Bengali text get re-read
individually (single-word mode, 3x scale, both models). Writes reocr.json {pid|x|y: text}."""
import json, re, glob, os, tesserocr
from PIL import Image
import merge
P = '/usr/share/tesseract-ocr/5/tessdata/'
apis = [tesserocr.PyTessBaseAPI(path=P, lang=l, psm=tesserocr.PSM.SINGLE_WORD) for l in ('ben', 'Bengali')]
LAT = re.compile(r'^[\W_]*[A-Za-z][A-Za-z&]*[\W_]*$')
BEN = re.compile('[ঀ-৿]')
out = {}
n = 0
for f in sorted(glob.glob('ocr/*.ben.tsv'))[1:]:
    pid = os.path.basename(f).split('.')[0]
    ws = merge.read_tsv(f)
    targets = []
    for i, w in enumerate(ws):
        t = w['text']
        if not LAT.match(t) or t.startswith('(') or t.endswith(')'):
            continue
        prev = ws[i - 1]['text'] if i else ''; nxt = ws[i + 1]['text'] if i + 1 < len(ws) else ''
        if BEN.search(prev) or BEN.search(nxt):
            targets.append(w)
    if not targets:
        continue
    src = f'img/{pid}.jpg' if os.path.exists(f'img/{pid}.jpg') else f'img/{pid}.ppm'
    im = Image.open(src).convert('L')
    for w in targets:
        x, y, ww, hh = [v // 2 for v in (w['x'], w['y'], w['w'], w['h'])]  # TSV is at 2x
        pad = 6
        crop = im.crop((max(0, x - pad), max(0, y - pad), min(im.width, x + ww + pad), min(im.height, y + hh + pad)))
        crop = crop.resize((crop.width * 3, crop.height * 3), Image.LANCZOS)
        res = []
        for api in apis:
            api.SetImage(crop); api.Recognize()
            txt = api.GetUTF8Text().strip(); conf = api.MeanTextConf()
            res.append((txt, conf))
        cands = [r for r in res if r[0] and BEN.search(r[0]) and not re.search('[A-Za-z]', r[0]) and ' ' not in r[0]]
        if cands:
            best = max(cands, key=lambda r: r[1])
            out[f"{pid}|{w['x']}|{w['y']}"] = best[0]
        n += 1
json.dump(out, open('reocr.json', 'w'), ensure_ascii=False)
print(n, 'words re-read;', len(out), 'replaced')
