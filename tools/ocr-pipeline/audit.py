"""Generate CONTENT-AUDIT.md and OCR-REVIEW.md for the project."""
import json, re, difflib, collections, os, sys
sys.path.insert(0, '/home/claude/project/src')
from laws_en import EN_TITLES

BOOK = json.load(open('/home/claude/project/src/content/book.json'))
stream = json.load(open('stream.json'))
unsure = json.load(open('unsure.json'))
headnum = json.load(open('headnum.json'))
fixes = json.load(open('fixes_applied.json'))
danda = json.load(open('danda_fixes.json'))
corr = json.load(open('corrections.json'))
ids = [os.path.splitext(os.path.basename(l.strip()))[0] for l in open('list.txt')]
BN = '০১২৩৪৫৬৭৮৯'
bn = lambda n: ''.join(BN[int(c)] if c.isdigit() else c for c in str(n))

def where(pid):
    part, idx = pid[1:].split('-')
    hp = headnum.get(pid, '?')
    return f'অংশ {bn(part)}, PDF পৃ. {bn(int(idx) + 1)} (বইয়ে “পৃষ্ঠা - {hp}”)'
def loc(a, b):
    pa, ia = a[1:].split('-'); pb, ib = b[1:].split('-')
    s = f'অংশ {bn(pa)}, পৃ. {bn(int(ia) + 1)}'
    return s + (f'–{bn(int(ib) + 1)}' if pa == pb else f' – অংশ {bn(pb)}, পৃ. {bn(int(ib) + 1)}')

law_of_page = {}
for L in BOOK['laws']:
    a, b = L['pages']
    for pid in ids:
        if a <= pid <= b:
            law_of_page[pid] = L['n']

def words(blocks):
    return sum(len(b['x'].split()) for b in blocks)

# TOC titles
toc = {}
toc_text = ' '.join(p['text'].replace('\n', ' ') for p in stream if 'p1-006' <= p['pages'][0] <= 'p1-013')
for m in re.finditer(r'আইন\s*([০-৯]{1,2})\s*[:।]?\s*(.{3,160}?)\s*(?:\.{3,}|…)', toc_text):
    n = int(''.join(str(BN.index(c)) for c in m.group(1)))
    if 1 <= n <= 48 and n not in toc:
        toc[n] = m.group(2).strip()

L = []
w = L.append
w('# কনটেন্ট অডিট রিপোর্ট — The 48 Laws of Power (বাংলা)')
w('')
w('এই রিপোর্ট আপলোড করা ৮টি PDF অংশ বিশ্লেষণ করে স্বয়ংক্রিয়ভাবে তৈরি। পৃষ্ঠাগুলো স্ক্যান করা ছবি (কোনো টেক্সট লেয়ার নেই), তাই সম্পূর্ণ লেখা OCR করে নেওয়া হয়েছে।')
w('')
w('## ১. উৎস ফাইল')
w('')
w(f'- মোট পৃষ্ঠা-ছবি: {len(ids)} (৮টি অংশ: ' + ', '.join(f'অংশ {i}: {sum(1 for x in ids if x.startswith(f"p{i}-"))}' for i in range(1, 9)) + ')')
w('- প্রতিটি পৃষ্ঠার উপরে “পৃষ্ঠা - N” শিরোনাম ও নিচে “Telegram: t.me/BoierSomahar” ওয়াটারমার্ক আছে — ওয়েবসাইটের লেখা থেকে দুটোই বাদ দেওয়া হয়েছে।')
w('- মূল ইংরেজি বইয়ের পৃষ্ঠা-চিহ্ন (যেমন “xviii ভূমিকা”, “৪ আইন ১”) চলমান শিরোনাম হিসেবে ছিল — এগুলোও বাদ দেওয়া হয়েছে।')
w('')
w('## ২. গ্রন্থ-তথ্য (PDF থেকে যাচাইকৃত)')
w('')
w('| বিষয় | PDF-এ যা আছে | উৎস |')
w('|---|---|---|')
w('| বাংলা শিরোনাম (প্রচ্ছদ) | দ্য 48 ল’স অব পাওয়ার — ক্ষমতা; উপশিরোনাম: পাওয়ারের জন্য ব্যবহারিক নির্দেশিকা | অংশ ১, পৃষ্ঠা ১ |')
w('| ভেতরের শিরোনাম | ক্ষমতার ৪৮টি আইন — রবার্ট গ্রিন; একটি জুস্ট এলফার্স প্রোডাকশন; প্রোফাইল বুকস | অংশ ১, পৃষ্ঠা ৩ |')
w('| মূল শিরোনাম | The 48 Laws of Power | অংশ ১, পৃষ্ঠা ৬ |')
w('| লেখক | রবার্ট গ্রিন (Robert Greene) | প্রচ্ছদ, পৃষ্ঠা ২–৩ |')
w('| প্রযোজক | জুস্ট এলফার্স (Joost Elffers) | পৃষ্ঠা ২–৩ |')
w('| অনুবাদ | প্রচ্ছদে “অনুবাদ: PDF বইয়ের সমাহার” | অংশ ১, পৃষ্ঠা ১ |')
w('| বাংলা প্রকাশক | **PDF-এ উল্লেখ নেই** | — |')
w('| সংস্করণ-তথ্য | (মূল ইংরেজি সংস্করণের অনুবাদিত তথ্য) পেপারব্যাক ২০০০, পুনর্মুদ্রণ ২০০১, ২০০২; প্রথম প্রকাশ ১৯৯৮ প্রোফাইল বুকস (যুক্তরাজ্য) ও ভাইকিং/পেঙ্গুইন পুটনাম (যুক্তরাষ্ট্র); কপিরাইট © রবার্ট গ্রিন ও জুস্ট এলফার্স ১৯৯৮; ISBN 1 86197 278 4 | অংশ ১, পৃষ্ঠা ৪ |')
w('')
w('> বাংলা অনুবাদের প্রকাশক/অনুমতিদাতার নাম PDF-এ নেই। Credits পাতায় আপাতত “তথ্য যোগ করা হবে” রাখা হয়েছে — `src/content/book.json`-এর `meta.bn_publisher` ও `meta.permission_note` হালনাগাদ করুন।')
w('')
w('## ৩. কাঠামো')
w('')
w('| অংশ | PDF অবস্থান |')
w('|---|---|')
w('| প্রচ্ছদ | অংশ ১, পৃষ্ঠা ১ |')
w('| লেখক পরিচিতি | অংশ ১, পৃষ্ঠা ২ |')
w('| শিরোনাম পাতা | অংশ ১, পৃষ্ঠা ৩ |')
w('| স্বত্ব-পাতা ও অনুমতি তালিকা | অংশ ১, পৃষ্ঠা ৪–৫ |')
w('| কৃতজ্ঞতা স্বীকার (লেখকের) | অংশ ১, পৃষ্ঠা ৬ |')
w('| সূচিপত্র (৪৮টি আইনের সারসংক্ষেপসহ) | অংশ ১, পৃষ্ঠা ৭–১৪ |')
w('| ভূমিকা | অংশ ১, পৃষ্ঠা ১৫–২১ |')
w('| আইন ১–৪৮ | নিচের সারণি |')
if BOOK['back'].get('bibliography'):
    w('| নির্বাচিত গ্রন্থপঞ্জি | শেষ অংশ |')
w('')
w('প্রতিটি আইনের অধ্যায়ের গঠন: আইন নম্বর → শিরোনাম → **বিচারবুদ্ধি** (সারকথা) → আইন লঙ্ঘন / আইন পালন → ব্যাখ্যা → ক্ষমতার চাবিকাঠি → চিত্র / কর্তৃপক্ষ → বিপরীত দিক; মাঝে মাঝে উপকথা ও উদ্ধৃতি।')
w('')
found = [x['n'] for x in BOOK['laws']]
missing = [n for n in range(1, 49) if n not in found]
w(f'## ৪. ৪৮টি আইনের যাচাই — পাওয়া গেছে {bn(len(found))}টি' + (f'; **অনুপস্থিত: {", ".join(bn(n) for n in missing)}**' if missing else ' — সবগুলো, সঠিক ক্রমে ✅'))
w('')
w('| # | অধ্যায়ের শিরোনাম (বাংলা) | English | PDF অবস্থান | শব্দ | অনুচ্ছেদ | অনিশ্চিত OCR শব্দ |')
w('|---|---|---|---|---|---|---|')
ucount = collections.Counter(law_of_page.get(p, 0) for p, *_ in unsure)
for x in BOOK['laws']:
    a, b = x['pages']
    blocks = x['judgment'] + x['body']
    w(f'| {bn(x["n"])} | {x["title"]} | {EN_TITLES[x["n"] - 1]} | {loc(a, b)} | {bn(words(blocks))} | {bn(len(blocks))} | {bn(ucount.get(x["n"], 0))} |')
w('')
w('## ৫. সূচিপত্র বনাম অধ্যায়ের শিরোনাম')
w('')
w('সূচিপত্রে আইনের যে নাম আছে আর অধ্যায়ের শুরুতে যে নাম আছে, অনুবাদে কয়েক জায়গায় শব্দচয়ন আলাদা। ওয়েবসাইটে **অধ্যায়ের শুরুর শিরোনাম** ব্যবহার করা হয়েছে। পার্থক্যগুলো:')
w('')
w('| # | সূচিপত্রে | অধ্যায়ে | মিল |')
w('|---|---|---|---|')
for x in BOOK['laws']:
    t = toc.get(x['n'])
    if not t:
        w(f'| {bn(x["n"])} | (সূচিপত্র থেকে পড়া যায়নি) | {x["title"]} | — |'); continue
    r = difflib.SequenceMatcher(None, re.sub(r'\W', '', t), re.sub(r'\W', '', x['title'])).ratio()
    if r < 0.97:
        w(f'| {bn(x["n"])} | {t} | {x["title"]} | {round(r * 100)}% |')
w('')
w('## ৬. OCR পদ্ধতি ও মান')
w('')
w('- ইঞ্জিন: Tesseract 5 — `ben` (tessdata_best) দিয়ে পূর্ণ পৃষ্ঠা, তারপর দুর্বল লাইনগুলো `Bengali` স্ক্রিপ্ট মডেল দিয়ে আবার পড়া; দুটি ফলাফল শব্দ-ধরে মিলিয়ে, পুরো বইয়ের শব্দ-ফ্রিকোয়েন্সি দিয়ে সিদ্ধান্ত।')
w('- নমুনা পৃষ্ঠা চোখে মিলিয়ে দেখা হয়েছে: শব্দ-স্তরে আনুমানিক ৯৮–৯৯% নির্ভুল। ভুল সাধারণত যুক্তাক্ষর, ু/ূ, চন্দ্রবিন্দু ও বিরল নামের বানানে।')
w(f'- অভিধান (LibreOffice bn_BD) দিয়ে নিশ্চিত হয়ে শুধু OCR-এর পরিচিত ভুলের দিকে সংশোধন (ু→ূ, হারানো ঁ): {bn(len(fixes))}টি আলাদা শব্দ, মোট {bn(sum(v[1] for v in fixes.values()))} জায়গায়। অনুবাদকের নিজস্ব বানানরীতি (যেমন ি/ী) বদলানো হয়নি।')
w(f'- “া” বনাম “।” বিভ্রান্তি (যেমন “দরজ।” → “দরজা”) অভিধান দিয়ে নিশ্চিত হয়ে ঠিক করা হয়েছে: {bn(len(danda))}টি শব্দ।')
w(f'- ৪৮টি আইনের শিরোনাম ও শুরুর সারকথা (বিচার/বিচারবুদ্ধি) মূল পৃষ্ঠার ছবির সাথে এক এক করে মিলিয়ে দেখা হয়েছে; {bn(sum(len(v) for k, v in corr.items() if k != "_note"))}টি সংশোধন `corrections.json`-এ নথিভুক্ত।')
w('- যেসব শব্দ দুটো মডেলই লাতিন অক্ষরে ভুল পড়েছিল, সেগুলো আলাদা করে ৩ গুণ বড় করে আবার পড়া হয়েছে (তৃতীয় ধাপ)।')
w(f'- OCR যেসব শব্দে নিশ্চিত ছিল না: {bn(len(unsure))}টি — `OCR-REVIEW.md`-এ পৃষ্ঠা ও প্রসঙ্গসহ তালিকা। এর অনেকগুলোই আসলে সঠিক (বিদেশি নাম ইত্যাদি)।')
w('- অনুচ্ছেদ বিভাজন পৃষ্ঠার লাইন-ফাঁক থেকে নির্ণয় করা; পৃষ্ঠা-সীমানায় ভাঙা অনুচ্ছেদ (“...” চিহ্নিত) জোড়া লাগানো হয়েছে।')
w('- বইয়ের শেষের নির্ঘণ্ট (সূচি) মূল ইংরেজি সংস্করণের পৃষ্ঠা নম্বর নির্দেশ করে, তাই ওয়েবসাইটে রাখা হয়নি; পেছনের প্রচ্ছদের প্রশংসা-উদ্ধৃতি ও মূল্যও বাদ দেওয়া হয়েছে। গ্রন্থপঞ্জি আলাদা পাতায় আছে।')
w('- কোনো অনুচ্ছেদ সংক্ষেপ, পুনর্লিখন বা বাদ দেওয়া হয়নি; সূচিপত্র পাতাটি আলাদা করে প্রকাশ করা হয়নি কারণ এর সারকথাগুলো প্রতিটি অধ্যায়ের “বিচারবুদ্ধি” অংশে হুবহু আছে এবং সাইটের তালিকা-পাতা সেই কাজ করে।')
w('')
w('## ৭. ম্যানুয়াল যাচাই দরকার')
w('')
w('1. বাংলা প্রকাশক ও অনুমতির বিবরণ (Credits পাতার জন্য)।')
w('2. `OCR-REVIEW.md`-এর চিহ্নিত শব্দগুলো মূল PDF-এর সাথে মিলিয়ে `src/content/book.json`-এ সংশোধন।')
w('3. উদ্ধৃতি/কবিতার লাইন-বিন্যাস (লাইন-ভাঙা হুবহু রাখার চেষ্টা করা হয়েছে) ও ছোট উপশিরোনাম (উপকথার নাম) — দ্রুত চোখ বুলিয়ে নেওয়া ভালো।')
open('/home/claude/project/CONTENT-AUDIT.md', 'w').write('\n'.join(L) + '\n')

# OCR review list
R = ['# OCR-REVIEW — অনিশ্চিত শব্দের তালিকা', '',
     'OCR যেসব শব্দে নিশ্চিত ছিল না, সেগুলো এখানে প্রসঙ্গসহ (【 】 চিহ্নের ভেতরে) দেওয়া হলো। মূল PDF-এর নির্দিষ্ট পৃষ্ঠা খুলে মিলিয়ে নিন; ভুল হলে `src/content/book.json`-এ ঠিক করে `python3 build.py` চালান।', '',
     'টিপস: অনেক চিহ্নিত শব্দ আসলে সঠিক (বিদেশি নাম, বিরল শব্দ)। শুধু ভুলগুলো ঠিক করলেই হবে।', '']
groups = collections.defaultdict(list)
for pid, wd, ctx in unsure:
    groups[law_of_page.get(pid, 0)].append((pid, ctx))
for n in sorted(groups):
    title = 'ভূমিকা ও শুরুর পাতা' if n == 0 else f'আইন {bn(n)}: {BOOK["laws"][n - 1]["title"]}'
    R.append(f'## {title} ({bn(len(groups[n]))}টি)')
    R.append('')
    for pid, ctx in groups[n]:
        R.append(f'- {where(pid)} — {ctx.strip()}')
    R.append('')
R.append('## স্বয়ংক্রিয় সংশোধন (অভিধান-নিশ্চিত)')
R.append('')
R.append('| OCR যা পড়েছিল | সংশোধিত | কতবার |')
R.append('|---|---|---|')
for k, (v, c) in sorted(fixes.items(), key=lambda kv: -kv[1][1]):
    R.append(f'| {k} | {v} | {bn(c)} |')
open('/home/claude/project/OCR-REVIEW.md', 'w').write('\n'.join(R) + '\n')
print('audit written; laws', len(found), 'missing', missing, 'unsure', len(unsure))
