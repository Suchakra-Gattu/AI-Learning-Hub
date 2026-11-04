// Small, dependency-free behavior: progress, theme, search, copy buttons, mobile menu, table of contents.
(function () {
  var KEY = 'ai-course-progress-v1';
  var body = document.body;
  var prefix = body.dataset.prefix || '';

  function load() { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } }
  function save(d) { try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) {} }

  // ---- Progress ----
  var lessons = window.__LESSONS__ || [];
  function paintProgress() {
    var done = load();
    var n = 0;
    lessons.forEach(function (p) { if (done[p]) n++; });
    document.querySelectorAll('a[data-lesson]').forEach(function (a) {
      a.classList.toggle('is-done', !!done[a.dataset.lesson]);
    });
    var text = document.getElementById('progress-text');
    if (text) text.textContent = n + ' of ' + lessons.length;
    var fill = document.getElementById('progress-fill');
    if (fill) {
      var pct = lessons.length ? Math.round((n / lessons.length) * 100) : 0;
      fill.style.width = pct + '%';
      fill.parentElement.setAttribute('aria-valuenow', pct);
    }
    document.querySelectorAll('.sidebar .track-count[data-track]').forEach(function (el) {
      var t = el.dataset.track, total = 0, d = 0;
      lessons.forEach(function (p) { if (p.indexOf(t + '/') === 0) { total++; if (done[p]) d++; } });
      el.textContent = d + '/' + total;
    });
    document.querySelectorAll('.mark-done').forEach(function (b) {
      b.classList.toggle('on', !!done[b.dataset.done]);
      b.setAttribute('aria-pressed', done[b.dataset.done] ? 'true' : 'false');
    });
    // Start button: continue where you left off
    var start = document.getElementById('start-btn');
    if (start && n > 0) {
      var nextP = lessons.filter(function (p) { return !done[p]; })[0];
      if (nextP) { start.href = nextP + '.html'; start.textContent = 'Continue where you left off'; }
    }
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('.mark-done');
    if (!b) return;
    var d = load();
    if (d[b.dataset.done]) delete d[b.dataset.done]; else d[b.dataset.done] = 1;
    save(d);
    paintProgress();
  });
  paintProgress();

  // ---- Theme ----
  var root = document.documentElement;
  var themeBtn = document.querySelector('.theme-btn');
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var cur = root.getAttribute('data-theme');
    var dark = cur === 'dark' || (cur === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches);
    var next = dark ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) {}
  });

  // ---- Mobile menu ----
  var side = document.getElementById('sidebar');
  var scrim = document.querySelector('.scrim');
  var menuBtn = document.querySelector('.menu-btn');
  function setMenu(open) {
    side.classList.toggle('open', open);
    scrim.hidden = !open;
    menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  if (menuBtn) {
    menuBtn.addEventListener('click', function () { setMenu(!side.classList.contains('open')); });
    scrim.addEventListener('click', function () { setMenu(false); });
    side.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
  }

  // Keep the current lesson visible in the sidebar
  var cur = document.querySelector('.sidebar [aria-current="page"]');
  if (cur) cur.scrollIntoView({ block: 'center' });

  // ---- Copy buttons ----
  document.addEventListener('click', function (e) {
    var b = e.target.closest('.copy');
    if (!b) return;
    var code = b.closest('.code').querySelector('code').innerText;
    var done = function () {
      b.textContent = 'Copied'; b.classList.add('copied');
      setTimeout(function () { b.textContent = 'Copy'; b.classList.remove('copied'); }, 1400);
    };
    if (navigator.clipboard && window.isSecureContext !== false) {
      navigator.clipboard.writeText(code).then(done, function () { b.textContent = 'Press Ctrl+C'; });
    } else {
      var ta = document.createElement('textarea'); ta.value = code; document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); done(); } catch (er) {} ta.remove();
    }
  });

  // ---- On-this-page highlight ----
  var tocLinks = [].slice.call(document.querySelectorAll('.toc a'));
  if (tocLinks.length && 'IntersectionObserver' in window) {
    var map = {};
    tocLinks.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          tocLinks.forEach(function (a) { a.classList.remove('on'); });
          var a = map[en.target.id]; if (a) a.classList.add('on');
        }
      });
    }, { rootMargin: '-10% 0px -80% 0px' });
    Object.keys(map).forEach(function (id) { var el = document.getElementById(id); if (el) io.observe(el); });
  }

  // ---- Glossary filter ----
  var gf = document.getElementById('gloss-filter');
  if (gf) gf.addEventListener('input', function () {
    var q = gf.value.toLowerCase();
    document.querySelectorAll('.gloss-item').forEach(function (it) {
      it.hidden = q && it.textContent.toLowerCase().indexOf(q) === -1;
    });
  });

  // ---- Search ----
  var dlg = document.getElementById('search');
  var input = document.getElementById('search-input');
  var list = document.getElementById('search-results');
  var index = window.__SEARCH__ || [];
  var sel = 0;

  function score(item, terms) {
    var s = 0, t = item.title.toLowerCase(), h = (item.heads || '').toLowerCase(), x = (item.text || '').toLowerCase(), su = (item.summary || '').toLowerCase();
    for (var i = 0; i < terms.length; i++) {
      var w = terms[i], hit = false;
      if (t.indexOf(w) > -1) { s += 10; hit = true; }
      if (h.indexOf(w) > -1) { s += 5; hit = true; }
      if (su.indexOf(w) > -1) { s += 3; hit = true; }
      if (x.indexOf(w) > -1) { s += 1; hit = true; }
      if (!hit) return 0;
    }
    return s;
  }
  function snippet(item, terms) {
    var x = item.text || '', low = x.toLowerCase(), pos = low.indexOf(terms[0]);
    if (pos < 0) return item.summary || '';
    var start = Math.max(0, pos - 50);
    return (start ? '… ' : '') + x.slice(start, start + 130).trim() + ' …';
  }
  function render() {
    var q = input.value.trim().toLowerCase();
    list.innerHTML = '';
    if (!q) return;
    var terms = q.split(/\s+/);
    var res = index.map(function (it) { return { it: it, s: score(it, terms) }; })
      .filter(function (r) { return r.s > 0; })
      .sort(function (a, b) { return b.s - a.s; }).slice(0, 8);
    if (!res.length) { list.innerHTML = '<li class="none">Nothing found. Try a simpler word.</li>'; return; }
    res.forEach(function (r, i) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = prefix + r.it.path + '.html';
      if (i === 0) a.className = 'sel';
      var b = document.createElement('b'); b.textContent = r.it.title;
      var sm = document.createElement('small'); sm.textContent = r.it.track + ' · ' + snippet(r.it, terms);
      a.appendChild(b); a.appendChild(sm); li.appendChild(a); list.appendChild(li);
    });
    sel = 0;
  }
  function openSearch() { if (!dlg.showModal) return; dlg.showModal(); input.value = ''; list.innerHTML = ''; input.focus(); }
  document.querySelector('.search-btn').addEventListener('click', openSearch);
  document.addEventListener('keydown', function (e) {
    var tag = (document.activeElement && document.activeElement.tagName) || '';
    if ((e.key === '/' && !/INPUT|TEXTAREA/.test(tag)) || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k')) {
      e.preventDefault(); openSearch();
    }
  });
  input.addEventListener('input', render);
  input.addEventListener('keydown', function (e) {
    var links = list.querySelectorAll('a');
    if (!links.length) return;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      links[sel].classList.remove('sel');
      sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + links.length) % links.length;
      links[sel].classList.add('sel'); links[sel].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter') {
      e.preventDefault(); location.href = links[sel].href;
    }
  });
  dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
})();
