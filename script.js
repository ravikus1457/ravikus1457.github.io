// year
document.getElementById('year').textContent = new Date().getFullYear();

// mobile nav
const nav = document.querySelector('.nav');
document.querySelector('.nav-toggle')?.addEventListener('click', () => nav.classList.toggle('open'));
document.querySelectorAll('.nav-links a').forEach(a => a.addEventListener('click', () => nav.classList.remove('open')));

// gentle slide-in; content is always visible (never parked at opacity 0)
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
}, {threshold:0.08});
document.querySelectorAll('.reveal').forEach(s => io.observe(s));

// count-up stats
function countUp(el){
  const target = +el.dataset.count; if (!target) return;
  let n = 0; const step = Math.max(1, Math.round(target/30));
  const id = setInterval(() => { n += step; if (n >= target){ n = target; clearInterval(id); } el.textContent = n; }, 30);
}
const statIO = new IntersectionObserver((es) => es.forEach(e => { if (e.isIntersecting){ countUp(e.target); statIO.unobserve(e.target); } }), {threshold:1});
document.querySelectorAll('.stats b[data-count]').forEach(b => statIO.observe(b));

// ── topology: the real nodes on this page, with packets moving along the real paths ──
(function topology(){
  const cv = document.getElementById('topo'); if (!cv) return;
  const ctx = cv.getContext('2d');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const C = { green:'#2ee6a6', blue:'#58a6ff', amber:'#f5a524', grey:'#c9d4e6', dim:'#6b7c99', line:'#2d3d63', text:'#e8eef7' };
  // positions in a 640x590 box; labels are what each node is
  const N = {
    county: {x:120, y:130, c:C.grey,  r:16, l:'county network', s:'DNS · AD · GlobalProtect'},
    op:     {x:120, y:430, c:C.grey,  r:14, l:'operator',       s:'Tailscale SSH'},
    pi:     {x:320, y:290, c:C.green, r:30, l:'Pi fleet',       s:'229 timers · systemd'},
    dns:    {x:180, y:300, c:C.green, r:12, l:'Pi-hole → Unbound', s:'DNSSEC'},
    edge:   {x:510, y:140, c:C.blue,  r:20, l:'Cloudflare edge', s:'3 tunnels · TLS'},
    web:    {x:560, y:50,  c:C.blue,  r:10, l:'public visitors', s:''},
    aws:    {x:530, y:420, c:C.amber, r:20, l:'AWS lab VPC',     s:'Terraform · ECS'},
    phone:  {x:470, y:300, c:C.grey,  r:11, l:'phone',          s:'OnFailure pages'},
  };
  // edges: [from, to, colour, label]; packets travel from→to (and back for two-way links)
  const E = [
    ['pi','edge',C.blue,'cloudflared (outbound)'], ['edge','web',C.blue,''], ['pi','aws',C.amber,'WireGuard S2S'],
    ['op','pi',C.grey,'Tailscale'], ['dns','pi',C.green,''], ['pi','phone',C.green,'alerts'], ['county','op',C.grey,'by day'],
  ];
  const pk = []; // packets
  function spawn(){
    const e = E[Math.floor(Math.random()*E.length)];
    const rev = Math.random() < 0.35 && e[0] !== 'pi' ? false : Math.random() < 0.3;
    pk.push({e, t:0, speed:0.004 + Math.random()*0.004, rev});
    if (pk.length > 18) pk.shift();
  }
  function line(a,b,col){ ctx.strokeStyle = col; ctx.globalAlpha = .35; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke(); ctx.globalAlpha = 1; }
  function node(n){
    ctx.beginPath(); ctx.arc(n.x,n.y,n.r+8,0,Math.PI*2); ctx.fillStyle = n.c; ctx.globalAlpha = .08; ctx.fill(); ctx.globalAlpha = 1;
    ctx.beginPath(); ctx.arc(n.x,n.y,n.r,0,Math.PI*2); ctx.fillStyle = '#0b1020'; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = n.c; ctx.stroke();
    ctx.fillStyle = C.text; ctx.font = '600 12px "IBM Plex Mono", monospace'; ctx.textAlign = 'center';
    const lx = Math.min(Math.max(n.x, 52), cv.width - 52);
    ctx.fillText(n.l, lx, n.y + n.r + 16);
    if (n.s){ ctx.fillStyle = C.dim; ctx.font = '11px "IBM Plex Mono", monospace'; ctx.fillText(n.s, lx, n.y + n.r + 30); }
  }
  function edgeLabel(a,b,txt,col){ if(!txt) return; const t=.58, mx=a.x+(b.x-a.x)*t, my=a.y+(b.y-a.y)*t; const dx=b.x-a.x, dy=b.y-a.y, L=Math.hypot(dx,dy)||1; const ox=-dy/L*11, oy=dx/L*11;
    ctx.fillStyle = col; ctx.globalAlpha=.9; ctx.font='10px "IBM Plex Mono", monospace'; ctx.textAlign='center'; ctx.fillText(txt, mx+ox, my+oy+3); ctx.globalAlpha=1; }
  let last = 0;
  function frame(ts){
    ctx.clearRect(0,0,cv.width,cv.height);
    for (const [a,b,col,txt] of E){ line(N[a],N[b],col); edgeLabel(N[a],N[b],txt,col); }
    for (const p of pk){
      const a = N[p.rev ? p.e[1] : p.e[0]], b = N[p.rev ? p.e[0] : p.e[1]];
      const x = a.x + (b.x-a.x)*p.t, y = a.y + (b.y-a.y)*p.t;
      ctx.beginPath(); ctx.arc(x,y,3.2,0,Math.PI*2); ctx.fillStyle = p.e[2]; ctx.shadowColor = p.e[2]; ctx.shadowBlur = 10; ctx.fill(); ctx.shadowBlur = 0;
      p.t += p.speed;
    }
    for (let i = pk.length-1; i >= 0; i--) if (pk[i].t >= 1) pk.splice(i,1);
    for (const k in N) node(N[k]);
    // pulse ring on the fleet node: the heartbeat the watchdog reads
    const ph = (ts/1400) % 1; ctx.beginPath(); ctx.arc(N.pi.x,N.pi.y,N.pi.r + 6 + ph*22,0,Math.PI*2); ctx.strokeStyle = C.green; ctx.globalAlpha = (1-ph)*.35; ctx.lineWidth = 1.5; ctx.stroke(); ctx.globalAlpha = 1;
    if (!reduced){ if (ts - last > 420){ spawn(); last = ts; } requestAnimationFrame(frame); }
  }
  if (reduced){ for (let i=0;i<6;i++){ spawn(); pk[pk.length-1].t = Math.random(); } frame(0); }
  else requestAnimationFrame(frame);
})();

// render labs from labs.json (auto-updating source of truth)
function renderLabs(labs, gridId, metaIcon){
  const grid = document.getElementById(gridId);
  if (!grid) return;
  if (!labs?.length){ grid.innerHTML = '<p class="muted">No labs found.</p>'; return; }
  grid.innerHTML = labs.map(lab => `
    <article class="lab">
      <span class="lab-id">LAB ${esc(lab.id)}${lab.has_evidence ? ' · <span class="ev">evidence ✔</span>' : ''}</span>
      <h3>${esc(lab.title)}</h3>
      <p>${esc(lab.demonstrates)}</p>
      <div class="lab-tags">${(lab.tags||[]).map(t=>`<span>${esc(t)}</span>`).join('')}</div>
      <div class="lab-foot">
        <span class="lab-cost">${metaIcon} ${esc(lab.meta||'')}</span>
        <a class="lab-link" href="${lab.repo_url}" target="_blank" rel="noopener">code ↗</a>
      </div>
    </article>`).join('');
}
fetch('labs.json', {cache:'no-cache'})
  .then(r => r.ok ? r.json() : Promise.reject(r.status))
  .then(data => {
    renderLabs(data.labs, 'labs-grid', '▲');
    renderLabs(data.networking, 'net-labs-grid', '⚙');
    if (data.repo){ const link = document.getElementById('labs-repo-link'); if (link) link.href = data.repo; }
    const n = (data.labs?.length||0) + (data.networking?.length||0);
    const stat = document.querySelector('.stats b[data-count="11"]'); if (stat && n){ stat.dataset.count = n; stat.textContent = n; }
  })
  .catch(() => {
    document.getElementById('labs-grid').innerHTML =
      '<p class="muted">Labs load from <code>labs.json</code> — view the full repo on GitHub.</p>';
  });

function esc(s){ return String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

// in-demand skills, regenerated by the portfolio-improver agent
function renderBars(items, gridId){
  const el = document.getElementById(gridId);
  if (!el || !items) return;
  el.innerHTML = items.map(it => `
    <div class="bar">
      <div class="bar-row"><b>${esc(it.skill)}</b><span>${it.count ? it.count + ' postings' : 'market'}</span></div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.max(6, it.pct)}%"></div></div>
    </div>`).join('');
}
fetch('market.json', {cache:'no-cache'})
  .then(r => r.ok ? r.json() : Promise.reject())
  .then(m => {
    const j = document.getElementById('market-jobs'); if (j) j.textContent = (m.sampled_jobs ?? '—').toLocaleString?.() ?? m.sampled_jobs;
    renderBars(m.aws, 'market-aws');
    renderBars(m.networking, 'market-net');
  })
  .catch(() => { const s = document.getElementById('market'); if (s) s.style.display = 'none'; });
