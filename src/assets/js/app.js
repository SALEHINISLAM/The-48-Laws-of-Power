/* Shared core: local storage, preferences, navigation, common UI.
   All personal data stays in this browser (localStorage). Nothing is sent anywhere. */
(function () {
  'use strict';
  var KEY = 'lop48:data';
  var VERSION = 1;
  var memory = null;           // in-memory fallback when localStorage is unavailable
  var storageOK = true;

  function blank() {
    return { version: VERSION, prefs: {}, progress: {}, bookmarks: [], notes: [], reflections: {}, last: null, recent: [] };
  }
  function migrate(d) {
    if (!d || typeof d !== 'object') return blank();
    var b = blank();
    for (var k in b) if (!(k in d) || typeof d[k] !== typeof b[k] && b[k] !== null) d[k] = b[k];
    if (!Array.isArray(d.bookmarks)) d.bookmarks = [];
    if (!Array.isArray(d.notes)) d.notes = [];
    if (!Array.isArray(d.recent)) d.recent = [];
    d.version = VERSION;
    return d;
  }
  function load() {
    if (memory) return memory;
    try {
      var raw = window.localStorage.getItem(KEY);
      memory = migrate(raw ? JSON.parse(raw) : null);
    } catch (e) {
      storageOK = false;
      memory = blank();
    }
    return memory;
  }
  function save() {
    if (!memory) return false;
    try {
      window.localStorage.setItem(KEY, JSON.stringify(memory));
      storageOK = true;
      return true;
    } catch (e) {
      storageOK = false;
      toast('সংরক্ষণ করা যায়নি — ব্রাউজারের স্টোরেজ বন্ধ বা পূর্ণ।');
      return false;
    }
  }
  function update(fn) { var d = load(); fn(d); return save(); }

  /* ---------- Preferences ---------- */
  var DEFAULT_PREFS = { theme: 'system', fs: 18, lh: 1.85, width: 40, font: 'auto' };
  function prefs() { var p = load().prefs || {}; var o = {}; for (var k in DEFAULT_PREFS) o[k] = (k in p) ? p[k] : DEFAULT_PREFS[k]; return o; }
  function applyPrefs(p) {
    p = p || prefs();
    var r = document.documentElement;
    if (p.theme === 'light' || p.theme === 'dark') r.setAttribute('data-theme', p.theme); else r.removeAttribute('data-theme');
    if (p.font && p.font !== 'auto') r.setAttribute('data-font', p.font); else r.removeAttribute('data-font');
    r.style.setProperty('--fs', (p.fs / 16) + 'rem');
    r.style.setProperty('--lh', String(p.lh));
    r.style.setProperty('--measure', p.width + 'rem');
    var mc = document.querySelector('meta[name="theme-color"]');
    if (mc) mc.setAttribute('content', '#20235F');
  }
  function setPref(k, v) { update(function (d) { d.prefs = d.prefs || {}; d.prefs[k] = v; }); applyPrefs(); }

  /* ---------- Progress / bookmarks ---------- */
  function status(n) {
    var p = load().progress[n];
    if (!p) return 'unread';
    if (p.done) return 'done';
    return 'reading';
  }
  function isBookmarked(n) { return load().bookmarks.indexOf(n) !== -1; }
  function toggleBookmark(n) {
    var on;
    update(function (d) {
      var i = d.bookmarks.indexOf(n);
      if (i === -1) { d.bookmarks.push(n); on = true; } else { d.bookmarks.splice(i, 1); on = false; }
      d.bookmarks.sort(function (a, b) { return a - b; });
    });
    return on;
  }

  /* ---------- Helpers ---------- */
  var BN = '০১২৩৪৫৬৭৮৯';
  function bn(n) { return String(n).replace(/\d/g, function (c) { return BN[c]; }); }
  function root() { return document.documentElement.getAttribute('data-root') || './'; }
  function lawUrl(n) { return root() + 'laws/law-' + (n < 10 ? '0' : '') + n + '.html'; }
  function lawsData() {
    var el = document.getElementById('laws-data');
    if (!el) return [];
    try { return JSON.parse(el.textContent); } catch (e) { return []; }
  }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function fmtDate(t) {
    try { return bn(new Date(t).toLocaleDateString('bn-BD', { year: 'numeric', month: 'short', day: 'numeric' })); }
    catch (e) { return new Date(t).toISOString().slice(0, 10); }
  }
  var toastTimer;
  function toast(msg) {
    var t = document.getElementById('toast');
    if (!t) { t = document.createElement('div'); t.id = 'toast'; t.className = 'toast'; t.setAttribute('role', 'status'); t.hidden = true; document.body.appendChild(t); }
    t.textContent = msg; t.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { t.hidden = true; }, 2600);
  }

  /* ---------- Status badges on any law card ---------- */
  function paintCards(scope) {
    var cards = (scope || document).querySelectorAll('[data-law]');
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i], n = +c.getAttribute('data-law'), box = c.querySelector('.badges');
      var s = status(n), bm = isBookmarked(n);
      c.setAttribute('data-status', s); c.setAttribute('data-bookmarked', bm ? '1' : '0');
      if (!box) continue;
      var h = '';
      if (s === 'done') h += '<span class="badge done">পড়া শেষ</span>';
      else if (s === 'reading') h += '<span class="badge reading">পড়ছি · ' + bn(Math.round((load().progress[n].pct || 0))) + '%</span>';
      if (bm) h += '<span class="badge mark">বুকমার্ক</span>';
      box.innerHTML = h;
    }
  }

  /* ---------- Navigation ---------- */
  function initNav() {
    var btn = document.querySelector('.nav-toggle'), nav = document.getElementById('site-nav');
    if (!btn || !nav) return;
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) { nav.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); btn.focus(); }
    });
  }
  function initThemeButton() {
    var b = document.getElementById('theme-btn');
    if (!b) return;
    var order = ['system', 'light', 'dark'];
    var names = { system: 'সিস্টেম থিম', light: 'লাইট থিম', dark: 'ডার্ক থিম' };
    function label() { var t = prefs().theme; b.setAttribute('aria-label', 'থিম পরিবর্তন (বর্তমান: ' + names[t] + ')'); b.title = names[t]; }
    label();
    b.addEventListener('click', function () {
      var t = prefs().theme, nx = order[(order.indexOf(t) + 1) % 3];
      setPref('theme', nx); label(); toast(names[nx]);
    });
  }

  /* ---------- Home dashboard ---------- */
  function initHome() {
    var box = document.getElementById('dash');
    if (!box) return;
    var d = load(), laws = lawsData(), total = laws.length || 48;
    var done = 0, reading = 0;
    for (var n = 1; n <= total; n++) { var s = status(n); if (s === 'done') done++; else if (s === 'reading') reading++; }
    var pct = Math.round(done / total * 100);
    document.getElementById('dash-done').textContent = bn(done);
    document.getElementById('dash-reading').textContent = bn(reading);
    document.getElementById('dash-marks').textContent = bn(d.bookmarks.length);
    document.getElementById('dash-notes').textContent = bn(d.notes.length);
    var m = document.getElementById('dash-meter'); if (m) m.style.width = pct + '%';
    var mp = document.getElementById('dash-pct'); if (mp) mp.textContent = bn(pct) + '%';
    var cont = document.getElementById('continue');
    if (cont && d.last && d.last.law) {
      var L = laws[d.last.law - 1];
      cont.innerHTML = '<p class="muted" style="margin:0 0 .5rem">শেষবার পড়ছিলেন</p><p style="margin:0 0 1rem;font-size:1.15rem"><strong>আইন ' + bn(d.last.law) + ':</strong> ' + esc(L ? L[1] : '') + '</p><a class="btn gold" href="' + lawUrl(d.last.law) + '">পড়া চালিয়ে যান</a>';
    }
    var rec = document.getElementById('recent');
    if (rec && d.recent.length) {
      var h = '';
      d.recent.slice(0, 5).forEach(function (r) { var L = laws[r - 1]; if (L) h += '<li><a href="' + lawUrl(r) + '">আইন ' + bn(r) + ' — ' + esc(L[1]) + '</a></li>'; });
      rec.innerHTML = '<ul style="margin:0;padding-left:1.2rem;line-height:2">' + h + '</ul>';
    }
  }

  /* ---------- Service worker (optional offline) ---------- */
  function initSW() {
    if (!('serviceWorker' in navigator) || location.protocol === 'file:') return;
    window.addEventListener('load', function () {
      navigator.serviceWorker.register(root() + 'sw.js').catch(function () {});
    });
  }

  var App = {
    load: load, save: save, update: update, prefs: prefs, setPref: setPref, applyPrefs: applyPrefs,
    status: status, isBookmarked: isBookmarked, toggleBookmark: toggleBookmark,
    bn: bn, esc: esc, root: root, lawUrl: lawUrl, lawsData: lawsData, fmtDate: fmtDate, toast: toast,
    paintCards: paintCards, storageOK: function () { load(); return storageOK; }, KEY: KEY, VERSION: VERSION, blank: blank, migrate: migrate,
    DEFAULT_PREFS: DEFAULT_PREFS
  };
  window.App = App;

  function ready() {
    applyPrefs();
    initNav(); initThemeButton(); paintCards(); initHome(); initSW();
    if (!App.storageOK()) {
      var w = document.getElementById('storage-warn'); if (w) w.hidden = false;
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready); else ready();
})();
