// year
document.getElementById('year').textContent = new Date().getFullYear();

// mobile nav
const nav = document.querySelector('.nav');
document.querySelector('.nav-toggle')?.addEventListener('click', () => nav.classList.toggle('open'));
document.querySelectorAll('.nav-links a').forEach(a => a.addEventListener('click', () => nav.classList.remove('open')));

// typed terminal in hero
(function typeHero(){
  const el = document.getElementById('typed');
  if (!el) return;
  const lines = [
    {t:'$ whoami', c:'cmd'},
    {t:'ravi kumar — cloud & network engineer', c:'out'},
    {t:'$ cat focus.txt', c:'cmd'},
    {t:'AWS VPC · EC2 · IAM · Site-to-Site VPN · TCP/IP · Linux · PowerShell', c:'out'},
    {t:'$ ./labs --status', c:'cmd'},
    {t:'5 live AWS Terraform labs — apply → verify → auto-destroy ✔', c:'ok'},
  ];
  let li = 0, ci = 0, buf = '';
  function tick(){
    if (li >= lines.length){ return; }
    const line = lines[li];
    buf += line.t[ci] ?? '';
    el.textContent = buf;
    ci++;
    if (ci > line.t.length){
      buf += '\n'; li++; ci = 0;
      setTimeout(tick, 380);
    } else {
      setTimeout(tick, 18 + Math.random()*30);
    }
  }
  tick();
})();

// scroll reveal
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
}, {threshold:0.12});
document.querySelectorAll('.reveal').forEach(s => io.observe(s));

// count-up stats
function countUp(el){
  const target = +el.dataset.count; if (!target) return;
  let n = 0; const step = Math.max(1, Math.round(target/30));
  const id = setInterval(() => { n += step; if (n >= target){ n = target; clearInterval(id); } el.textContent = n; }, 30);
}
const statIO = new IntersectionObserver((es) => es.forEach(e => { if (e.isIntersecting){ countUp(e.target); statIO.unobserve(e.target); } }), {threshold:1});
document.querySelectorAll('.stats b[data-count]').forEach(b => statIO.observe(b));

// render labs from labs.json (auto-updating source of truth)
fetch('labs.json', {cache:'no-cache'})
  .then(r => r.ok ? r.json() : Promise.reject(r.status))
  .then(data => {
    const grid = document.getElementById('labs-grid');
    if (!data.labs?.length){ grid.innerHTML = '<p class="muted">No labs found.</p>'; return; }
    grid.innerHTML = data.labs.map(lab => `
      <article class="lab">
        <span class="lab-id">LAB ${lab.id}${lab.has_evidence ? ' · evidence ✔' : ''}</span>
        <h3>${esc(lab.title)}</h3>
        <p>${esc(lab.demonstrates)}</p>
        <div class="lab-tags">${(lab.tags||[]).map(t=>`<span>${esc(t)}</span>`).join('')}</div>
        <div class="lab-foot">
          <span class="lab-cost">▲ ${esc(lab.cost)}</span>
          <a class="lab-link" href="${lab.repo_url}" target="_blank" rel="noopener">code ↗</a>
        </div>
      </article>`).join('');
    if (data.repo){ const link = document.getElementById('labs-repo-link'); if (link) link.href = data.repo; }
  })
  .catch(() => {
    document.getElementById('labs-grid').innerHTML =
      '<p class="muted">Labs load from <code>labs.json</code> — view the full repo on GitHub.</p>';
  });

function esc(s){ return String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
