/* Page-specific behaviour for: all-laws list (search/filter), notes, bookmarks, settings. */
(function () {
  'use strict';
  var A = window.App;
  if (!A) return;

  /* Normalise Bengali/English text for searching (digits + case). */
  function norm(s) {
    return String(s || '').toLowerCase().replace(/[০-৯]/g, function (c) { return '০১২৩৪৫৬৭৮৯'.indexOf(c); }).replace(/\s+/g, ' ').trim();
  }

  /* ================= All laws ================= */
  var list = document.getElementById('law-list');
  if (list) {
    var q = document.getElementById('law-q'), filter = 'all';
    var chips = document.querySelectorAll('[data-filter]');
    var count = document.getElementById('law-count');
    var items = Array.prototype.slice.call(list.querySelectorAll('[data-law]'));
    items.forEach(function (li) { li._t = norm(li.textContent + ' ' + li.getAttribute('data-law')); });
    var run = function () {
      A.paintCards(list);
      var t = norm(q ? q.value : ''), shown = 0;
      items.forEach(function (li) {
        var s = li.getAttribute('data-status'), b = li.getAttribute('data-bookmarked') === '1';
        var ok = (!t || li._t.indexOf(t) !== -1) &&
          (filter === 'all' || (filter === 'bookmarked' ? b : s === filter));
        li.hidden = !ok; if (ok) shown++;
      });
      if (count) count.textContent = A.bn(shown) + 'টি আইন দেখানো হচ্ছে';
      var empty = document.getElementById('law-empty'); if (empty) empty.hidden = shown !== 0;
    };
    Array.prototype.forEach.call(chips, function (c) {
      c.addEventListener('click', function () {
        filter = c.getAttribute('data-filter');
        Array.prototype.forEach.call(chips, function (x) { x.setAttribute('aria-pressed', x === c ? 'true' : 'false'); });
        run();
      });
    });
    if (q) {
      q.addEventListener('input', run);
      var param = new URLSearchParams(location.search).get('q'); if (param) q.value = param;
    }
    run();
  }

  /* ================= Bookmarks ================= */
  var bmBox = document.getElementById('bookmark-list');
  if (bmBox) {
    var renderBm = function () {
      var laws = A.lawsData(), d = A.load(), h = '';
      d.bookmarks.forEach(function (n) {
        var L = laws[n - 1]; if (!L) return;
        h += '<li class="law-card" data-law="' + n + '"><span class="law-num" aria-hidden="true">' + A.bn(n) + '</span>' +
          '<h3><a href="' + A.lawUrl(n) + '">আইন ' + A.bn(n) + ': ' + A.esc(L[1]) + '</a></h3>' +
          '<p class="en">' + A.esc(L[2]) + '</p><div class="badges"></div>' +
          '<div style="grid-column:1/-1;position:relative;z-index:1"><button class="btn small danger" data-unmark="' + n + '">বুকমার্ক সরান</button></div></li>';
      });
      bmBox.innerHTML = h;
      document.getElementById('bookmark-empty').hidden = !!h;
      A.paintCards(bmBox);
    };
    bmBox.addEventListener('click', function (e) {
      var b = e.target.closest('[data-unmark]'); if (!b) return;
      A.toggleBookmark(+b.getAttribute('data-unmark')); renderBm(); A.toast('বুকমার্ক সরানো হয়েছে');
    });
    renderBm();
  }

  /* ================= Notes ================= */
  var notesBox = document.getElementById('note-list');
  if (notesBox) {
    var laws = A.lawsData();
    var form = document.getElementById('note-form');
    var sel = document.getElementById('note-law'), ta = document.getElementById('note-text'), idF = document.getElementById('note-id');
    var nq = document.getElementById('note-q'), lawFilter = document.getElementById('note-filter');
    var opts = '<option value="0">সাধারণ নোট (কোনো আইন নয়)</option>';
    laws.forEach(function (L) { opts += '<option value="' + L[0] + '">আইন ' + A.bn(L[0]) + ': ' + A.esc(L[1]) + '</option>'; });
    sel.innerHTML = opts;
    if (lawFilter) lawFilter.innerHTML = '<option value="">সব আইন</option>' + opts.replace('value="0">সাধারণ নোট (কোনো আইন নয়)', 'value="0">শুধু সাধারণ নোট');
    var pre = +(new URLSearchParams(location.search).get('law') || 0); if (pre) sel.value = String(pre);

    var renderNotes = function () {
      var d = A.load(), t = norm(nq ? nq.value : ''), lf = lawFilter ? lawFilter.value : '';
      var arr = d.notes.slice().sort(function (a, b) { return b.updated - a.updated; });
      var h = '';
      arr.forEach(function (x) {
        var L = laws[x.law - 1];
        var title = x.law ? 'আইন ' + A.bn(x.law) + (L ? ': ' + L[1] : '') : 'সাধারণ নোট';
        if (lf !== '' && String(x.law) !== lf) return;
        if (t && norm(x.text + ' ' + title).indexOf(t) === -1) return;
        h += '<li class="note"><header><span>' + (x.law ? '<a href="' + A.lawUrl(x.law) + '">' + A.esc(title) + '</a>' : A.esc(title)) + '</span>' +
          '<span>হালনাগাদ: ' + A.fmtDate(x.updated) + '</span></header><p>' + A.esc(x.text) + '</p>' +
          '<div class="row"><button class="btn small ghost" data-edit="' + x.id + '">সম্পাদনা</button>' +
          '<button class="btn small danger" data-del="' + x.id + '">মুছুন</button></div></li>';
      });
      notesBox.innerHTML = h;
      document.getElementById('note-empty').hidden = !!h;
      document.getElementById('note-count').textContent = A.bn(d.notes.length) + 'টি নোট';
    };
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var txt = ta.value.trim(); if (!txt) { ta.focus(); return; }
      var id = idF.value, now = Date.now(), law = +sel.value;
      A.update(function (d) {
        if (id) { d.notes.forEach(function (x) { if (x.id === id) { x.text = txt; x.law = law; x.updated = now; } }); }
        else d.notes.push({ id: now.toString(36) + Math.random().toString(36).slice(2, 6), law: law, text: txt, created: now, updated: now });
      });
      ta.value = ''; idF.value = ''; document.getElementById('note-submit').textContent = 'নোট সংরক্ষণ করুন';
      document.getElementById('note-cancel').hidden = true;
      A.toast(id ? 'নোট হালনাগাদ হয়েছে' : 'নোট সংরক্ষিত হয়েছে'); renderNotes();
    });
    document.getElementById('note-cancel').addEventListener('click', function () {
      ta.value = ''; idF.value = ''; this.hidden = true; document.getElementById('note-submit').textContent = 'নোট সংরক্ষণ করুন';
    });
    notesBox.addEventListener('click', function (e) {
      var ed = e.target.closest('[data-edit]'), del = e.target.closest('[data-del]');
      if (ed) {
        var x = A.load().notes.filter(function (y) { return y.id === ed.getAttribute('data-edit'); })[0]; if (!x) return;
        ta.value = x.text; sel.value = String(x.law || 0); idF.value = x.id;
        document.getElementById('note-submit').textContent = 'পরিবর্তন সংরক্ষণ করুন';
        document.getElementById('note-cancel').hidden = false; ta.focus();
        form.scrollIntoView({ block: 'start' });
      }
      if (del && window.confirm('এই নোটটি স্থায়ীভাবে মুছে ফেলতে চান?')) {
        var id = del.getAttribute('data-del');
        A.update(function (d) { d.notes = d.notes.filter(function (y) { return y.id !== id; }); });
        A.toast('নোট মুছে ফেলা হয়েছে'); renderNotes();
      }
    });
    if (nq) nq.addEventListener('input', renderNotes);
    if (lawFilter) lawFilter.addEventListener('change', renderNotes);
    renderNotes();
  }

  /* ================= Settings ================= */
  var st = document.getElementById('settings-form');
  if (st) {
    var p = A.prefs();
    var setRadio = function (name, v) { var r = st.querySelector('input[name="' + name + '"][value="' + v + '"]'); if (r) r.checked = true; };
    setRadio('theme', p.theme); setRadio('font', p.font);
    var rng = { fs: ['fs-val', function (v) { return A.bn(v) + 'px'; }], lh: ['lh-val', function (v) { return A.bn(v); }], width: ['width-val', function (v) { return A.bn(v) + 'rem'; }] };
    Object.keys(rng).forEach(function (k) {
      var el = document.getElementById('set-' + k), out = document.getElementById(rng[k][0]);
      el.value = p[k]; out.textContent = rng[k][1](p[k]);
      el.addEventListener('input', function () { var v = +el.value; A.setPref(k, v); out.textContent = rng[k][1](v); });
    });
    st.addEventListener('change', function (e) {
      var t = e.target; if (t.type === 'radio') A.setPref(t.name, t.value);
    });
    document.getElementById('reset-prefs').addEventListener('click', function () {
      A.update(function (d) { d.prefs = {}; }); A.applyPrefs(); location.reload();
    });

    /* export */
    document.getElementById('export-btn').addEventListener('click', function () {
      var data = JSON.stringify({ app: '48-laws-bn', exported: new Date().toISOString(), data: A.load() }, null, 2);
      var blob = new Blob([data], { type: 'application/json' });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = '48-laws-bn-backup-' + new Date().toISOString().slice(0, 10) + '.json';
      document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
      A.toast('ব্যাকআপ ফাইল ডাউনলোড হচ্ছে');
    });
    /* import */
    var file = document.getElementById('import-file');
    file.addEventListener('change', function () {
      var f = file.files && file.files[0]; if (!f) return;
      var rd = new FileReader();
      rd.onload = function () {
        try {
          var obj = JSON.parse(rd.result); var d = obj && obj.data ? obj.data : obj;
          if (!d || typeof d !== 'object' || !('notes' in d || 'progress' in d || 'bookmarks' in d)) throw new Error('bad');
          if (!window.confirm('ইমপোর্ট করলে এই ব্রাউজারের বর্তমান ডেটা ব্যাকআপের ডেটা দিয়ে প্রতিস্থাপিত হবে। চালিয়ে যাবেন?')) return;
          var cur = A.load(); var m = A.migrate(d);
          for (var k in m) cur[k] = m[k];
          if (A.save()) { A.toast('ডেটা ইমপোর্ট সম্পন্ন'); setTimeout(function () { location.reload(); }, 800); }
        } catch (e) { A.toast('ফাইলটি পড়া যায়নি — সঠিক ব্যাকআপ ফাইল নির্বাচন করুন।'); }
        file.value = '';
      };
      rd.readAsText(f);
    });
    /* reset */
    document.getElementById('reset-all').addEventListener('click', function () {
      if (!window.confirm('সব অগ্রগতি, বুকমার্ক, নোট, অনুশীলনের লেখা ও সেটিংস মুছে যাবে। এটি ফেরানো যাবে না। আগে ব্যাকআপ নিয়েছেন তো?')) return;
      if (!window.confirm('নিশ্চিতভাবে সব ব্যক্তিগত ডেটা মুছে ফেলবেন?')) return;
      var cur = A.load(), b = A.blank(); for (var k in b) cur[k] = b[k];
      A.save(); A.toast('সব ডেটা মুছে ফেলা হয়েছে'); setTimeout(function () { location.reload(); }, 800);
    });
  }
})();
