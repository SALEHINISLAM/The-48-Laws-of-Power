# ক্ষমতা — The 48 Laws of Power বাংলা পাঠ ও অনুশীলন

রবার্ট গ্রিনের *The 48 Laws of Power* বইয়ের বাংলা অনুবাদ পড়ার জন্য একটি সম্পূর্ণ স্ট্যাটিক, দ্রুত, মোবাইল-ফার্স্ট ওয়েবসাইট। অবাণিজ্যিক, বিজ্ঞাপনহীন, নিবন্ধন বা ট্র্যাকিং ছাড়া — এবং মূল লেখক রবার্ট গ্রিনের প্রতি উৎসর্গীকৃত।

> এটি লেখক বা মূল প্রকাশকের অফিসিয়াল সাইট নয়। বাংলা অনুবাদ ব্যবহারের অনুমতি প্রকল্প-পরিচালক সংগ্রহ করেছেন; অনুমতিপত্রের কপি সংরক্ষণে রাখুন।

## ফোল্ডার কাঠামো

```
.
├── docs/                 ← তৈরি হওয়া ওয়েবসাইট (GitHub Pages এখান থেকে প্রকাশ করে)
│   ├── index.html        হোম / ড্যাশবোর্ড
│   ├── laws/             ৪৮টি আইনের তালিকা + law-01.html … law-48.html
│   ├── preface/          ভূমিকা
│   ├── notes/ bookmarks/ settings/ about/
│   ├── assets/css|js|fonts|icons|images
│   ├── data/laws.json    আইনের মেটাডেটা (শিরোনাম, সারকথা, URL)
│   ├── sitemap.xml robots.txt llms.txt manifest.webmanifest sw.js 404.html offline.html
├── tools/ocr-pipeline/   ← PDF থেকে লেখা বের করার স্ক্রিপ্ট (Tesseract OCR; শুধু পুনরায় OCR করতে চাইলে দরকার)
├── CONTENT-AUDIT.md      ← PDF বিশ্লেষণ ও কনটেন্ট অডিট রিপোর্ট
├── OCR-REVIEW.md         ← যাচাই করার মতো অনিশ্চিত শব্দের তালিকা
└── src/                  ← সোর্স
    ├── build.py          স্ট্যাটিক সাইট জেনারেটর (শুধু Python 3, কোনো প্যাকেজ লাগে না)
    ├── config.json       সাইটের URL, নাম, বর্ণনা
    ├── content/book.json বইয়ের সম্পূর্ণ লেখা (PDF থেকে নেওয়া) — লেখা সংশোধন এখানেই করুন
    ├── laws_en.py        ৪৮টি আইনের ইংরেজি শিরোনাম
    ├── assets/           CSS, JS, ফন্ট, আইকন
    └── sw.js             অফলাইন সার্ভিস ওয়ার্কার টেমপ্লেট
```

## GitHub Pages-এ প্রকাশ

1. GitHub-এ একটি নতুন repository তৈরি করুন (যেমন `48-laws-bn`) এবং এই পুরো ফোল্ডারটি push করুন।
2. `src/config.json`-এ `site_url` আপনার আসল ঠিকানা দিন, যেমন `https://salehinislam.github.io/The-48-Laws-of-Power/` (শেষে `/` রাখুন)।
3. সাইট আবার তৈরি করুন:
   ```bash
   cd src
   python3 build.py
   ```
   এতে `docs/` ফোল্ডার নতুন করে তৈরি হবে (canonical URL, sitemap, Open Graph সব নতুন ঠিকানায়)।
4. GitHub-এ **Settings → Pages → Build and deployment → Source: Deploy from a branch**, Branch: `main`, Folder: `/docs` বেছে নিন।
5. কয়েক মিনিট পর সাইট `https://salehinislam.github.io/The-48-Laws-of-Power/` ঠিকানায় চালু হবে।

সব লিংক relative, তাই repository-র সাব-পাথে (project page) বা নিজস্ব ডোমেইনে — দুই জায়গাতেই কাজ করে। নিজস্ব ডোমেইন ব্যবহার করলে `site_url` সেই ডোমেইনে বদলে আবার build করুন এবং `docs/CNAME` ফাইল যোগ করুন।

## লেখা সংশোধন

বইয়ের লেখা স্ক্যান করা পৃষ্ঠা থেকে OCR করে নেওয়া। কোনো শব্দ ভুল দেখলে:

1. `src/content/book.json` খুলে ভুল শব্দটি খুঁজে (Ctrl+F) ঠিক করুন।
2. `python3 build.py` চালান, তারপর commit ও push করুন।

`OCR-REVIEW.md` ফাইলে যেসব শব্দ নিয়ে OCR নিশ্চিত ছিল না, সেগুলোর তালিকা পৃষ্ঠা নম্বরসহ দেওয়া আছে।

## স্থানীয়ভাবে দেখা

```bash
cd docs
python3 -m http.server 8000
# ব্রাউজারে http://localhost:8000
```

(সরাসরি ফাইল ডাবল-ক্লিক করে খুললেও পড়া যায়, তবে অফলাইন ক্যাশ শুধু http/https-এ চলে।)

## বৈশিষ্ট্য

- প্রতিটি আইনের আলাদা স্ট্যাটিক HTML পাতা — জাভাস্ক্রিপ্ট ছাড়াও সম্পূর্ণ লেখা পড়া যায়
- ফন্টের আকার, লাইনের ফাঁক, কলামের প্রস্থ, লাইট/ডার্ক/সিস্টেম থিম, মনোযোগী পাঠ মোড
- পড়ার অগ্রগতি, শেষ অবস্থান থেকে আবার শুরু, “পড়া শেষ” চিহ্ন, সম্প্রতি পড়া
- বুকমার্ক, প্রতিটি আইনের জন্য প্রতিফলনের প্রশ্ন, ব্যক্তিগত নোট (তৈরি/সম্পাদনা/মোছা/খোঁজা)
- JSON ব্যাকআপ এক্সপোর্ট/ইমপোর্ট, সব ডেটা মোছা (নিশ্চিতকরণসহ)
- সব ব্যক্তিগত ডেটা শুধু ব্রাউজারের localStorage-এ (`lop48:data` কী, ভার্সনসহ); কোথাও পাঠানো হয় না
- অফলাইন: দেখা পাতাগুলো সার্ভিস ওয়ার্কারে ক্যাশ হয়
- SEO: প্রতিটি পাতায় আলাদা শিরোনাম/বর্ণনা, canonical, Open Graph, JSON-LD (WebSite, Book, Chapter, BreadcrumbList, FAQPage), sitemap.xml, robots.txt, llms.txt
- বাইরের কোনো নেটওয়ার্ক অনুরোধ নেই; ফন্ট স্থানীয়ভাবে রাখা (Noto Serif Bengali, SIL OFL)। ব্যবহারকারীর ডিভাইসে SolaimanLipi থাকলে সেটি আগে ব্যবহৃত হয়।

## SolaimanLipi ফন্ট

SolaimanLipi ফন্টের ফাইল এই প্রকল্পে দেওয়া হয়নি, কারণ এর পুনর্বিতরণ-লাইসেন্স নিশ্চিত করা যায়নি। বৈধভাবে বিতরণযোগ্য ফাইল থাকলে `src/assets/fonts/`-এ রেখে `main.css`-এর `Reader SolaimanLipi` `@font-face`-এ `url(...)` যোগ করুন।

## লাইসেন্স ও স্বত্ব

বইয়ের লেখার স্বত্ব সংশ্লিষ্ট স্বত্বাধিকারীদের (মূল ইংরেজি: © Robert Greene ও Joost Elffers, 1998)। ওয়েবসাইটের কোড (HTML/CSS/JS/Python) প্রকল্প-পরিচালক নিজের পছন্দমতো লাইসেন্সে দিতে পারেন। Noto ফন্ট: SIL Open Font License 1.1 (`assets/fonts/OFL.txt`)।
