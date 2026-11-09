/* Law reading page: progress, resume position, bookmarks, reader controls, reflections. */
(function () {
  'use strict';
  var A = window.App;
  var art = document.querySelector('[data-law-page]');
  if (!A || !art) return;
  var n = +art.getAttribute('data-law-page');
  var prose = document.getElementById('content');
  var bar = document.getElementById('read-progress');
  var paras = prose ? prose.querySelectorAll('p,h2,blockquote') : [];

  /* ---- record visit ---- */
  A.update(function (d) {
    d.recent = [n].concat(d.recent.filter(function (x) { return x !== n; })).slice(0, 10);
    if (!d.progress[n]) d.progress[n] = { pct: 0, done: false, pos: 0, t: Date.now() };
  });

  /* ---- progress ---- */
  function pct() {
    if (!prose) return 0;
    var r = prose.getBoundingClientRect();
    var total = r.height - window.innerHeight * 0.6;
    var seen = -r.top + window.innerHeight * 0.4;
    return Math.max(0, Math.min(100, total > 0 ? seen / total * 100 : 100));
  }
  function currentIndex() {
    for (var i = 0; i < paras.length; i++) if (paras[i].getBoundingClientRect().bottom > 80) return i;
    return 0;
  }
  var pending = false, lastSave = 0;
  function onScroll() {
    if (pending) return; pending = true;
    window.requestAnimationFrame(function () {
      pending = false;
      var p = pct();
      if (bar) bar.style.width = p + '%';
      var now = Date.now();
      if (now - lastSave > 1200) { lastSave = now; persist(p); }
    });
  }
  function persist(p) {
    var idx = currentIndex();
    A.update(function (d) {
      var pr = d.progress[n] || { pct: 0, done: false };
      pr.pct = Math.max(pr.pct || 0, Math.round(p));
      pr.pos = idx; pr.t = Date.now();
      if (p >= 97) pr.done = true;
      d.progress[n] = pr;
      d.last = { law: n, pos: idx, t: Date.now() };
    });
    paintDone();
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('pagehide', function () { persist(pct()); });

  /* ---- resume ---- */
  var resumeBox = document.getElementById('resume');
  var pr0 = A.load().progress[n];
  if (resumeBox && pr0 && pr0.pos > 2 && !location.hash) {
    resumeBox.hidden = false;
    resumeBox.querySelector('button').addEventListener('click', function () {
      var el = paras[pr0.pos]; if (el) el.scrollIntoView({ block: 'start' });
      resumeBox.hidden = true;
    });
  }

  /* ---- done toggle ---- */
  var doneBtn = document.getElementById('done-btn');
  function paintDone() {
    if (!doneBtn) return;
    var d = A.status(n) === 'done';
    doneBtn.setAttribute('aria-pressed', d ? 'true' : 'false');
    doneBtn.querySelector('.label').textContent = d ? 'পড়া শেষ ✓' : 'পড়া শেষ চিহ্নিত করুন';
  }
  if (doneBtn) {
    paintDone();
    doneBtn.addEventListener('click', function () {
      var on = A.status(n) !== 'done';
      A.update(function (d) { var p = d.progress[n] || { pct: 0 }; p.done = on; if (on) p.pct = 100; d.progress[n] = p; });
      paintDone(); A.paintCards(); A.toast(on ? 'পড়া শেষ হিসেবে চিহ্নিত' : 'চিহ্ন সরানো হয়েছে');
    });
  }

  /* ---- bookmark ---- */
  var bm = document.getElementById('bm-btn');
  function paintBm() {
    if (!bm) return;
    var on = A.isBookmarked(n);
    bm.setAttribute('aria-pressed', on ? 'true' : 'false');
    bm.querySelector('.label').textContent = on ? 'বুকমার্ক করা হয়েছে' : 'বুকমার্ক';
  }
  if (bm) {
    paintBm();
    bm.addEventListener('click', function () { var on = A.toggleBookmark(n); paintBm(); A.paintCards(); A.toast(on ? 'বুকমার্কে যোগ হয়েছে' : 'বুকমার্ক সরানো হয়েছে'); });
  }

  /* ---- font size / line height ---- */
  function bump(k, delta, min, max, dec) {
    var p = A.prefs(); var v = Math.round((p[k] + delta) * (dec || 1)) / (dec || 1);
    v = Math.max(min, Math.min(max, v)); A.setPref(k, v); return v;
  }
  var map = {
    'fs-up': function () { A.toast('ফন্ট: ' + A.bn(bump('fs', 1, 14, 28))); },
    'fs-down': function () { A.toast('ফন্ট: ' + A.bn(bump('fs', -1, 14, 28))); },
    'lh-toggle': function () {
      var steps = [1.6, 1.85, 2.1], p = A.prefs(), i = steps.indexOf(p.lh);
      var v = steps[(i + 1) % steps.length]; A.setPref('lh', v); A.toast('লাইন স্পেস: ' + A.bn(v));
    },
    'focus-btn': function (b) {
      var on = document.body.classList.toggle('focus-mode');
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
      A.toast(on ? 'মনোযোগী পাঠ মোড চালু' : 'মনোযোগী পাঠ মোড বন্ধ');
    }
  };
  Object.keys(map).forEach(function (id) {
    var b = document.getElementById(id); if (b) b.addEventListener('click', function () { map[id](b); });
  });

  /* ---- reflections (autosave) ---- */
  var fields = document.querySelectorAll('[data-reflect]');
  var refl = (A.load().reflections || {})[n] || {};
  var timers = {};
  Array.prototype.forEach.call(fields, function (f) {
    var key = f.getAttribute('data-reflect');
    if (refl[key]) f.value = refl[key];
    var status = document.getElementById('saved-' + key);
    f.addEventListener('input', function () {
      clearTimeout(timers[key]);
      timers[key] = setTimeout(function () {
        var ok = A.update(function (d) { d.reflections[n] = d.reflections[n] || {}; d.reflections[n][key] = f.value; });
        if (status) status.textContent = ok ? 'সংরক্ষিত হয়েছে (শুধু এই ব্রাউজারে)' : 'সংরক্ষণ ব্যর্থ';
      }, 500);
    });
  });

  /* ---- quick note ---- */
  var qf = document.getElementById('quick-note');
  if (qf) qf.addEventListener('submit', function (e) {
    e.preventDefault();
    var ta = qf.querySelector('textarea'), txt = ta.value.trim();
    if (!txt) { ta.focus(); return; }
    A.update(function (d) {
      var now = Date.now();
      d.notes.push({ id: now.toString(36) + Math.random().toString(36).slice(2, 6), law: n, text: txt, created: now, updated: now });
    });
    ta.value = ''; A.toast('নোট সংরক্ষিত হয়েছে');
  });

  onScroll();
})();
