/* Pandit feedback layer — no backend, no signup, no login.
   Notes are kept in the browser (localStorage) so nothing is lost on refresh,
   and "Send" opens his own email app pre-filled with everything he wrote. */
(function () {
  var KEY = 'ebht_notes_' + location.pathname.replace(/[^a-z]/gi, '');
  var TO = 'ravikus1457@gmail.com';
  var notes = {};
  try { notes = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) {}

  var css = document.createElement('style');
  css.textContent = [
    '.pf-btn{position:fixed;right:16px;bottom:16px;z-index:9999;background:#6b1f1f;color:#fff;',
    'border:0;border-radius:999px;padding:14px 22px;font:600 15px/1.2 system-ui,sans-serif;',
    'box-shadow:0 4px 18px rgba(0,0,0,.3);cursor:pointer}',
    '.pf-note{display:block;width:100%;margin:8px 0 22px;padding:10px 12px;border:2px dashed #c9a227;',
    'border-radius:8px;background:#fffdf5;font:15px/1.5 system-ui,sans-serif;min-height:58px;color:#2b1d14}',
    '.pf-note::placeholder{color:#9a8b7a;opacity:.75}',
    '.pf-lab{display:block;margin-top:14px;font:600 13px/1.4 system-ui,sans-serif;color:#6b1f1f;',
    'letter-spacing:.04em;text-transform:uppercase}',
    '@media print{.pf-btn{display:none}}'
  ].join('');
  document.head.appendChild(css);

  function save(id, val) { notes[id] = val; localStorage.setItem(KEY, JSON.stringify(notes)); }

  // put a note box under every major heading
  var heads = document.querySelectorAll('h1,h2,h3');
  heads.forEach(function (h, i) {
    var id = 'sec' + i + '-' + (h.textContent || '').trim().slice(0, 40);
    var lab = document.createElement('span');
    lab.className = 'pf-lab';
    lab.textContent = 'Your notes on: ' + (h.textContent || '').trim().slice(0, 46);
    var ta = document.createElement('textarea');
    ta.className = 'pf-note';
    ta.placeholder = 'Type any change you want here — wording, prices, photos, anything.';
    ta.value = notes[id] || '';
    ta.addEventListener('input', function () { save(id, ta.value); });
    var anchor = h.nextElementSibling && h.nextElementSibling.tagName !== 'H2' ? h.nextElementSibling : h;
    anchor.parentNode.insertBefore(lab, anchor.nextSibling);
    lab.parentNode.insertBefore(ta, lab.nextSibling);
  });

  var btn = document.createElement('button');
  btn.className = 'pf-btn';
  btn.textContent = '✓ Send my notes';
  btn.onclick = function () {
    var lines = [], any = false;
    Object.keys(notes).forEach(function (k) {
      if ((notes[k] || '').trim()) {
        any = true;
        lines.push('— ' + k.replace(/^sec\d+-/, '') + '\n' + notes[k].trim() + '\n');
      }
    });
    if (!any) { alert('You have not written any notes yet. Type in any box, then press this again.'); return; }
    var body = 'My notes on the ' + document.title + ' page:\n\n' + lines.join('\n');
    location.href = 'mailto:' + TO + '?subject=' +
      encodeURIComponent('Temple website notes — ' + document.title) +
      '&body=' + encodeURIComponent(body);
  };
  document.body.appendChild(btn);
})();
