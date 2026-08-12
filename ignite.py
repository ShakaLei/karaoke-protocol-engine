"""STATION 4 · IGNITE — song.json + audio → karaoke.html (flames, word sync, chords)"""
import sys, json, base64, html

song_f, audio_f, title, out_f = sys.argv[1:5]
song = json.load(open(song_f))
audio_b64 = base64.b64encode(open(audio_f, "rb").read()).decode()

HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ — karaoke 🔥</title>
<style>
  :root { --bg:#0b0710; --ink:#f5efe6; --dim:#6b5f7a; --fire1:#ff6a00; --fire2:#ffd23f; --fire3:#ff2d55; }
  * { box-sizing:border-box; margin:0; }
  body { background:radial-gradient(120% 100% at 50% 110%, #2b0a2e 0%, var(--bg) 60%); color:var(--ink);
         font-family:ui-rounded,system-ui,-apple-system,'Segoe UI',sans-serif; min-height:100vh;
         display:flex; flex-direction:column; align-items:center; padding:2rem 1rem 8rem; }
  h1 { font-size:clamp(1.2rem,3.5vw,2rem); letter-spacing:.06em; margin-bottom:.3rem; }
  .sub { color:var(--dim); font-size:.85rem; margin-bottom:2rem; }
  #stage { width:min(880px,94vw); }
  .line { margin:1.4rem 0; opacity:.32; transition:opacity .25s, transform .25s; transform:scale(.98); }
  .line.hot { opacity:1; transform:scale(1.02); }
  .chord { color:var(--fire2); font-weight:700; font-size:clamp(.85rem,2vw,1.1rem); letter-spacing:.1em; min-height:1.2em; }
  .words { font-size:clamp(1.4rem,4.5vw,2.6rem); font-weight:800; line-height:1.35; }
  .w { display:inline-block; padding:.05em .12em; border-radius:.3em; position:relative; transition:color .12s; }
  .line.hot .w.now {
    color:#fff;
    background:linear-gradient(180deg, transparent 30%, var(--fire3) 30%, var(--fire1) 60%, var(--fire2) 100%);
    text-shadow:0 0 18px var(--fire2), 0 0 42px var(--fire1);
    animation:flick .12s infinite alternate;
  }
  @keyframes flick { from { filter:brightness(1);} to { filter:brightness(1.35);} }
  .w.sung { color:var(--fire2); }
  #controls { position:fixed; bottom:0; left:0; right:0; background:rgba(11,7,16,.92); backdrop-filter:blur(8px);
              padding:.8rem 1rem; display:flex; gap:.8rem; align-items:center; justify-content:center; border-top:1px solid #ffffff14; }
  button { background:linear-gradient(135deg,var(--fire1),var(--fire3)); color:#fff; border:0; border-radius:999px;
           padding:.7rem 1.6rem; font-size:1.05rem; font-weight:800; cursor:pointer; letter-spacing:.05em; }
  button.ghost { background:#ffffff14; }
  #bar { flex:1; max-width:340px; height:8px; border-radius:99px; background:#ffffff1c; overflow:hidden; cursor:pointer; }
  #fill { height:100%; width:0%; background:linear-gradient(90deg,var(--fire2),var(--fire3)); }
  .brand { position:fixed; top:.8rem; right:1rem; color:var(--dim); font-size:.75rem; }
  #langbar { position:fixed; top:.8rem; left:1rem; display:flex; gap:.4rem; z-index:50; }
  #langbar button { background:#ffffff12; border:1px solid #ffffff22; color:var(--ink); border-radius:999px;
                    padding:.3rem .8rem; font-size:.8rem; font-weight:700; cursor:pointer; }
  #langbar button.on { background:linear-gradient(135deg,var(--fire1),var(--fire3)); border-color:transparent; }
  .w.trnow { color:#fff; text-shadow:0 0 18px var(--fire2), 0 0 42px var(--fire1);
             background:linear-gradient(180deg, transparent 30%, var(--fire3) 30%, var(--fire1) 60%, var(--fire2) 100%); }
  a { color:var(--fire2); }
</style></head><body>
<div class="brand">THE KARAOKE PROTOCOL v0.1 🔥 · <a href="https://islpoap.xyz">a gift from the AI ʻohana 🌺</a></div>
<h1>__TITLEHTML__</h1>
<div class="sub" id="meta">loading the fire…</div>
<div id="langbar"></div>
<div id="stage"></div>
<div id="controls">
  <button id="play">▶ SING</button>
  <div id="bar"><div id="fill"></div></div>
  <button class="ghost" id="restart">↺</button>
</div>
<script>
const SONG = __SONGJSON__;
let LANG = 'orig';
const langbar = document.getElementById('langbar');
(function(){
  const names = Object.assign({orig: 'original'}, SONG.lang_names || {});
  const langs = ['orig'].concat(Object.keys(SONG.langs || {}));
  if (langs.length < 2) { langbar.style.display='none'; return; }
  langs.forEach(l => {
    const b = document.createElement('button');
    b.textContent = names[l] || l; b.dataset.lang = l;
    if (l === 'orig') b.classList.add('on');
    b.onclick = () => { LANG = l; [...langbar.children].forEach(x => x.classList.toggle('on', x.dataset.lang === l)); renderTexts(); };
    langbar.appendChild(b);
  });
})();
function renderTexts(){
  lineEls.forEach((L, i) => {
    const ln = SONG.lines[i];
    if (LANG === 'orig' || !(SONG.langs && SONG.langs[LANG])) {
      L.spans.forEach((s, j) => { s.style.display=''; s.textContent = ln.words[j].w; });
      L.el.classList.remove('trmode');
    } else {
      L.spans.forEach((s, j) => { s.style.display = j === 0 ? '' : 'none'; });
      L.spans[0].textContent = (SONG.langs[LANG][i] || ln.text);
      L.el.classList.add('trmode');
    }
  });
}
const AUDIO = "data:audio/mpeg;base64,__AUDIOB64__";
const stage = document.getElementById('stage');
const audio = new Audio(AUDIO);
document.getElementById('meta').textContent =
  SONG.lines.length + " lines · ♩=" + (SONG.bpm||'?') + " · every word a node 🎻";
// build DOM
const lineEls = SONG.lines.map(ln => {
  const d = document.createElement('div'); d.className='line';
  const c = document.createElement('div'); c.className='chord'; c.textContent = ln.chord||'';
  const w = document.createElement('div'); w.className='words';
  const spans = ln.words.map(wd => {
    const s = document.createElement('span'); s.className='w'; s.textContent = wd.w;
    s.dataset.t0 = wd.t0; s.dataset.t1 = wd.t1; w.appendChild(s); return s;
  });
  d.appendChild(c); d.appendChild(w); stage.appendChild(d);
  return {el:d, spans, t0:ln.t0, t1:ln.t1};
});
let raf=null;
function tick(){
  const t = audio.currentTime;
  let active=null;
  for (const L of lineEls){
    const hot = t >= L.t0 - .05 && t <= L.t1 + .4;
    L.el.classList.toggle('hot', hot);
    if (hot) active=L;
    const tr = LANG !== 'orig';
    for (const s of L.spans){
      const t0=+s.dataset.t0, t1=+s.dataset.t1;
      s.classList.toggle('now', !tr && t>=t0 && t<t1);
      s.classList.toggle('sung', t>=t1);
    }
    if (tr && hot) L.spans[0].classList.add('trnow'); else L.spans[0].classList.remove('trnow');
  }
  if (active) active.el.scrollIntoView({block:'center', behavior:'smooth'});
  document.getElementById('fill').style.width = (audio.duration? 100*t/audio.duration : 0) + '%';
  if (!audio.paused) raf=requestAnimationFrame(tick);
}
document.getElementById('play').onclick = () => {
  if (audio.paused){ audio.play(); document.getElementById('play').textContent='⏸ FEEL IT'; raf=requestAnimationFrame(tick); }
  else { audio.pause(); document.getElementById('play').textContent='▶ SING'; cancelAnimationFrame(raf); }
};
document.getElementById('restart').onclick = () => { audio.currentTime=0; };
document.getElementById('bar').onclick = e => {
  const r = e.currentTarget.getBoundingClientRect();
  audio.currentTime = audio.duration * (e.clientX - r.left) / r.width;
};
</script></body></html>"""

out = (HTML
    .replace("__TITLE__", html.escape(title))
    .replace("__TITLEHTML__", html.escape(title))
    .replace("__SONGJSON__", json.dumps(song))
    .replace("__AUDIOB64__", audio_b64))
open(out_f, "w").write(out)
print(f"IGNITE ✓ karaoke page → {out_f} ({len(out)//1024} KB, audio embedded)")
