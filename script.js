/* Lyric Code – efek mengetik lirik bergaya kode.
   Data ada di lyrics.js (dibuat dari lyrics.txt lewat convert_lyrics.py). */

const CONFIG = {
  cps: 16,            // karakter per detik (dipakai jika tidak ada timestamp)
  pauseBetween: 0.7,  // jeda antar baris (detik, mode tanpa timestamp)
  maxTypeTime: 3.5,   // batas maksimum waktu mengetik satu baris (mode timestamp)
  visibleLines: 3,    // jumlah baris yang tampak
  loop: false
};

const editor = document.getElementById('editor');
const startBtn = document.getElementById('start');
const audio = document.getElementById('audio');

/* ---------- Tokenizer sederhana untuk syntax highlight ---------- */
function tokenize(code){
  if (code.trim().startsWith('//')) return [{t:code, c:'comment'}];
  const re = /("[^"]*"?)|([A-Za-z_][\w]*)|([(){};:,])|(\s+)|(.)/g;
  const raw = [];
  let m;
  while ((m = re.exec(code))) {
    if (m[1]) raw.push({t:m[1], c:'str'});
    else if (m[2]) raw.push({t:m[2], c:'id'});
    else if (m[3]) raw.push({t:m[3], c:'brace'});
    else if (m[4]) raw.push({t:m[4], c:'sp'});
    else raw.push({t:m[5], c:'plain'});
  }
  let firstId = true;
  raw.forEach((tok, i) => {
    if (tok.c !== 'id') return;
    const next = raw.slice(i+1).find(x => x.c !== 'sp');
    if (next && next.t === '(') tok.c = 'fn';
    else if (next && next.t === ':') tok.c = 'key';
    else if (firstId && next && next.t === '.') tok.c = 'obj';
    else tok.c = 'plain';
    firstId = false;
  });
  return raw;
}

function renderPartial(tokens, n){
  let out = '', left = n;
  for (const tok of tokens){
    if (left <= 0) break;
    const piece = tok.t.slice(0, left);
    left -= piece.length;
    const esc = piece.replace(/&/g,'&amp;').replace(/</g,'&lt;');
    out += `<span class="t-${tok.c === 'sp' ? 'plain' : tok.c}">${esc}</span>`;
  }
  return out;
}

/* ---------- Jadwal ---------- */
const lines = (window.LYRICS || []).map(l => ({
  code: l.code, t: l.t, tokens: tokenize(l.code)
}));

function buildSchedule(){
  const hasTime = lines.some(l => typeof l.t === 'number');
  let clock = 0.5;
  lines.forEach((l, i) => {
    if (hasTime && typeof l.t === 'number') {
      l.start = l.t;
      const next = lines.slice(i+1).find(x => typeof x.t === 'number');
      const gap = next ? next.t - l.t : CONFIG.maxTypeTime + 1;
      l.dur = Math.max(0.4, Math.min(CONFIG.maxTypeTime, gap * 0.85));
    } else {
      l.start = clock;
      l.dur = l.code.length / CONFIG.cps;
      clock += l.dur + CONFIG.pauseBetween;
    }
  });
  return hasTime;
}
const timed = buildSchedule();
const totalEnd = lines.length ? lines[lines.length-1].start + lines[lines.length-1].dur + 3 : 0;

/* ---------- Render ---------- */
const els = lines.map(() => {
  const d = document.createElement('div');
  d.className = 'line gone';
  editor.appendChild(d);
  return d;
});
let lastActive = -1;

function frame(now){
  let active = -1;
  for (let i = 0; i < lines.length; i++) if (now >= lines[i].start) active = i;

  els.forEach((el, i) => {
    const age = active - i;
    el.classList.remove('active','old1','old2','gone');
    if (i > active || age >= CONFIG.visibleLines) { el.classList.add('gone'); return; }
    if (age === 0) el.classList.add('active');
    else if (age === 1) el.classList.add('old1');
    else el.classList.add('old2');
  });

  if (active >= 0){
    const l = lines[active];
    const p = Math.min(1, Math.max(0, (now - l.start) / l.dur));
    const n = Math.floor(p * l.code.length);
    const typing = p < 1;
    els[active].innerHTML = renderPartial(l.tokens, n) +
      `<span class="cursor ${typing ? 'typing':''}"></span>`;
    if (active !== lastActive){
      els[active].classList.add('enter');
      if (lastActive >= 0) els[lastActive].innerHTML = renderPartial(lines[lastActive].tokens, 9999);
      lastActive = active;
    }
  }
}

/* ---------- Pemutar ---------- */
let t0 = 0, raf = 0, hasAudio = false;
function tick(){
  const now = hasAudio && !audio.paused ? audio.currentTime : (performance.now() - t0) / 1000;
  frame(now);
  if (now > totalEnd){
    if (CONFIG.loop) return restart();
    return;
  }
  raf = requestAnimationFrame(tick);
}
function restart(){
  cancelAnimationFrame(raf); lastActive = -1;
  els.forEach(e => { e.innerHTML=''; e.className='line gone'; });
  begin();
}
async function begin(){
  t0 = performance.now();
  hasAudio = false;
  try { audio.currentTime = 0; await audio.play(); hasAudio = !audio.paused; } catch(e){ /* tanpa audio */ }
  if (!hasAudio) t0 = performance.now();
  tick();
}
startBtn.addEventListener('click', () => { startBtn.classList.add('hidden'); begin(); });
document.addEventListener('keydown', e => { if (e.key === 'r') restart(); });
