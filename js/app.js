import {
  loadData, Layout, hexPath, stateAt, tally, sectionStats, pace,
  nf, pctFmt, fmtDate, fmtDateShort, countdown, aheadText, OCEAN
} from './blanket.js';

const $ = (id) => document.getElementById(id);
const el = {
  canvas: $('blanket'), photo: $('photo'), tip: $('tooltip'), stage: $('stage'),
  card: $('card'), pct: $('pct'), sewn: $('sewn'), left: $('left'),
  countdown: $('countdown'), finish: $('finish'), more: $('more'),
  paceActual: $('paceActual'), paceTarget: $('paceTarget'), paceNeeded: $('paceNeeded'),
  startOut: $('startOut'), deadlineOut: $('deadlineOut'), assumptions: $('assumptions'),
  togglePhoto: $('togglePhoto'), latest: $('latest'),
  stripInner: $('stripInner'), err: $('loadError'), hint: $('cardHint')
};

const ctx = el.canvas.getContext('2d');
const DIM = 0.32;              // the rest of the blanket dims to about a third
const GLOW_MS = 130;           // the one animation on the page

let data, regionById, stages, idx = 0, spansYears = false;
let state, stats, layout, base, glowLayer = null, glowKey = null, glowColour = '#fff';
let sectionOf = new Map();     // cell index -> 'left' | 'right'
let glowHalo = 1;              // big regions need a lighter touch than small ones
let glowT = 0, glowRAF = 0, showPhoto = false;

/* ------------------------------------------------------------------ boot */

loadData().then(start).catch((e) => {
  el.err.hidden = false;
  el.err.textContent = `Could not load the blanket data — ${e.message}. ` +
    `This page reads data/blanket.json, so it needs to be served over http (see the README), not opened from the file system.`;
  console.error(e);
});

function start(d) {
  data = d;
  regionById = new Map(d.regions.map((r) => [r.id, r]));
  for (const side of ['left', 'right']) {
    for (const i of d.missing[side].order) sectionOf.set(i, side);
  }
  stages = [...d.stages].sort((a, b) =>
    (a.date + (a.photo ?? '')).localeCompare(b.date + (b.photo ?? '')));
  spansYears = new Set(stages.map((s) => s.date.slice(0, 4))).size > 1;
  idx = stages.length - 1;
  buildStrip();
  wire();
  select(idx);
  addEventListener('resize', relayout, { passive: true });
  setInterval(tickCountdown, 1000);
}

/* ------------------------------------------------------------ stage select */

function select(i) {
  idx = Math.max(0, Math.min(stages.length - 1, i));
  const stage = stages[idx];
  state = stateAt(data, stage, stages);
  stats = tally(data, state);
  cancelAnimationFrame(glowRAF);           // an in-flight glow would re-dim the new date
  glowLayer = null; glowKey = null; glowT = 0;
  el.tip.hidden = true;                    // last date's tooltip must not linger
  if (stage.photo) el.photo.src = stage.photo;
  el.togglePhoto.disabled = !stage.photo;
  // Nothing to draw for a date before the first counted stage, so show the
  // photo: it is the only record of what the blanket looked like then.
  if (!stage.photo) setPhoto(false);
  else setPhoto(state.basis === 'none');
  el.latest.disabled = idx === stages.length - 1;
  for (const b of el.stripInner.children) {
    b.setAttribute('aria-selected', String(Number(b.dataset.i) === idx));
  }
  const sel = el.stripInner.children[idx];
  if (sel) sel.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  relayout();
  renderCard();
}

/* --------------------------------------------------------------- drawing */

/** On the phone layout the card sits over the blanket, so give the stage
 *  room for it rather than letting it hide the bottom of the map. */
function fitStage() {
  const narrow = matchMedia('(max-width: 720px)').matches;
  el.stage.style.bottom = narrow
    ? `calc(var(--strip-h) + ${Math.round(el.card.offsetHeight) + 18}px)`
    : '';
}

function relayout() {
  fitStage();
  const w = el.stage.clientWidth, h = el.stage.clientHeight;
  if (w < 2 || h < 2) { requestAnimationFrame(relayout); return; }   // not laid out yet
  const dpr = Math.min(devicePixelRatio || 1, 2);
  el.canvas.width = Math.round(w * dpr);
  el.canvas.height = Math.round(h * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const { cols, rows } = data.config.grid;
  layout = new Layout(cols, rows, w, h, Math.min(24, w * 0.03));
  base = null; glowLayer = null;
  draw();
}

/** The blanket as it stands, painted once and reused. */
function buildBase() {
  const c = document.createElement('canvas');
  c.width = el.canvas.width; c.height = el.canvas.height;
  const g = c.getContext('2d');
  const dpr = el.canvas.width / el.stage.clientWidth;
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  const { cols, rows } = data.config.grid;
  const ocean = data.config.oceanColour;
  const R = layout.R;
  g.lineWidth = Math.max(0.5, R * 0.07);
  g.strokeStyle = 'rgba(133,152,184,.42)';
  for (let col = 0; col < cols; col++) {
    const cx = layout.cx(col);
    for (let row = 0; row < rows; row++) {
      const i = row * cols + col;
      const cy = layout.cy(col, row);
      if (state.sewn[i]) {
        const id = data.cells[i];
        g.fillStyle = id === OCEAN ? ocean : (regionById.get(id)?.colour ?? ocean);
        hexPath(g, cx, cy, R * 0.97);
        g.fill();
      } else if (state.loose && state.loose[i]) {
        // finished as a loose piece but not joined on yet
        const id = data.cells[i];
        g.save();
        g.strokeStyle = regionById.get(id)?.colour ?? ocean;
        g.lineWidth = Math.max(0.7, R * 0.16);
        hexPath(g, cx, cy, R * 0.82);
        g.stroke();
        g.restore();
      } else {
        // not sewn yet: a dim outline so you can see what comes next
        hexPath(g, cx, cy, R * 0.86);
        g.stroke();
      }
    }
  }
  return c;
}

/** The hexagons of the hovered region or section, on a transparent layer. */
function buildGlow(target) {
  const c = document.createElement('canvas');
  c.width = el.canvas.width; c.height = el.canvas.height;
  const g = c.getContext('2d');
  const dpr = el.canvas.width / el.stage.clientWidth;
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  const { cols } = data.config.grid;
  const R = layout.R;

  if (target.kind === 'loose' || target.kind === 'future') {
    const isOcean = target.id === OCEAN;
    const colour = isOcean ? data.config.oceanColour : regionById.get(target.id).colour;
    glowHalo = 1;
    glowColour = brighten(colour, isOcean ? 0.55 : 0.30);
    g.strokeStyle = glowColour;
    g.lineWidth = Math.max(0.9, R * 0.14);
    const want = target.kind === 'loose' ? state.loose : null;
    for (let i = 0; i < data.cells.length; i++) {
      if (data.cells[i] !== target.id) continue;
      if (want ? !want[i] : (state.sewn[i] || state.loose?.[i])) continue;
      hexPath(g, layout.cx(i % cols), layout.cy(i % cols, (i / cols) | 0), R * 0.84);
      g.stroke();
    }
  } else if (target.kind === 'region') {
    const isOcean = target.id === OCEAN;
    const colour = isOcean ? data.config.oceanColour : regionById.get(target.id).colour;
    // The ocean covers most of the blanket. Lifting it as hard as a small region
    // floods the screen, so large areas get a gentler lift and a smaller halo.
    const size = stats.perRegion.get(target.id)?.sewn ?? 0;
    const big = size > 600;
    glowHalo = big ? 0.35 : 1;
    glowColour = brighten(colour, big ? 0.13 : 0.18);
    g.fillStyle = glowColour;
    for (let i = 0; i < data.cells.length; i++) {
      if (data.cells[i] !== target.id || !state.sewn[i]) continue;
      hexPath(g, layout.cx(i % cols), layout.cy(i % cols, (i / cols) | 0), R * 0.97);
      g.fill();
    }
  } else {
    // a missing section: light every outline in it, in brightened ocean navy
    glowHalo = 1;
    glowColour = brighten(data.config.oceanColour, 0.52);
    g.strokeStyle = glowColour;
    g.lineWidth = Math.max(0.9, R * 0.12);
    const sec = data.missing[target.side];
    for (const i of sec.order) {
      if (state.sewn[i]) continue;
      hexPath(g, layout.cx(i % cols), layout.cy(i % cols, (i / cols) | 0), R * 0.86);
      g.stroke();
    }
  }
  return c;
}

function draw() {
  if (!layout || !el.canvas.width || !el.canvas.height) return;
  if (!base) base = buildBase();
  const w = el.stage.clientWidth, h = el.stage.clientHeight;
  ctx.clearRect(0, 0, w, h);

  const k = glowT;                      // 0 = nothing hovered, 1 = full glow
  ctx.globalAlpha = 1 - (1 - DIM) * k;
  ctx.drawImage(base, 0, 0, w, h);
  ctx.globalAlpha = 1;

  if (k > 0 && glowLayer) {
    ctx.save();
    ctx.globalAlpha = k;
    ctx.shadowColor = glowColour;
    if (glowHalo >= 1) {
      ctx.shadowBlur = layout.R * 2.6;
      ctx.drawImage(glowLayer, 0, 0, w, h); // soft halo
    }
    ctx.shadowBlur = layout.R * 1.2 * glowHalo;
    ctx.drawImage(glowLayer, 0, 0, w, h);
    ctx.shadowBlur = 0;
    ctx.drawImage(glowLayer, 0, 0, w, h);   // crisp pass
    ctx.restore();
  }
}

function animateGlow(to) {
  cancelAnimationFrame(glowRAF);
  const from = glowT, t0 = performance.now();
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) { glowT = to; draw(); return; }
  const step = (t) => {
    const p = Math.min(1, (t - t0) / GLOW_MS);
    glowT = from + (to - from) * p;
    draw();
    if (p < 1) glowRAF = requestAnimationFrame(step);
  };
  glowRAF = requestAnimationFrame(step);
}

function brighten(hex, amt) {
  const n = parseInt(hex.slice(1), 16);
  const f = (v) => Math.round(v + (255 - v) * amt);
  return `rgb(${f(n >> 16 & 255)},${f(n >> 8 & 255)},${f(n & 255)})`;
}

/* ------------------------------------------------------------ interaction */

function targetAt(x, y) {
  if (!layout) return null;
  const c = layout.hit(x, y);
  if (!c) return null;
  const { cols } = data.config.grid;
  const i = c.row * cols + c.col;
  if (state.sewn[i]) return { kind: 'region', id: data.cells[i], key: `r${data.cells[i]}` };
  if (state.loose?.[i]) return { kind: 'loose', id: data.cells[i], key: `l${data.cells[i]}` };
  const side = sectionOf.get(i);
  if (side && state.basis === 'own') return { kind: 'section', side, key: `s${side}` };
  return { kind: 'future', id: data.cells[i], key: `f${data.cells[i]}` };
}

function setHover(t, px, py) {
  const key = t ? t.key : null;
  if (key !== glowKey) {
    glowKey = key;
    glowLayer = t ? buildGlow(t) : null;
    animateGlow(t ? 1 : 0);
  }
  if (t) { el.tip.hidden = false; el.tip.innerHTML = tipHTML(t); placeTip(px, py); }
  else { el.tip.hidden = true; }
}

function placeTip(x, y) {
  const r = el.tip.getBoundingClientRect();
  const w = el.stage.clientWidth, h = el.stage.clientHeight;
  let tx = x + 16, ty = y + 16;
  if (tx + r.width > w - 8) tx = x - r.width - 16;
  if (ty + r.height > h - 8) ty = y - r.height - 16;
  el.tip.style.left = `${Math.max(8, tx)}px`;
  el.tip.style.top = `${Math.max(8, ty)}px`;
}

function tipHTML(t) {
  if (t.kind === 'loose' || t.kind === 'future') {
    const isOcean = t.id === OCEAN;
    const name = isOcean ? data.config.oceanName : regionById.get(t.id).name;
    const colour = isOcean ? data.config.oceanColour : regionById.get(t.id).colour;
    const e = stats.perRegion.get(t.id) ?? { total: 0, sewn: 0 };
    return `
      <span class="tt-name"><i class="tt-swatch" style="background:${colour}"></i>${esc(name)}</span>
      ${t.kind === 'loose'
        ? 'Finished as a loose piece — not joined on yet.'
        : `Not sewn yet on this date.${isOcean ? '' : ` ${nf.format(e.sewn)} of ${nf.format(e.total)} of it was in place.`}`}
      <br><span class="tt-est">this is where it goes on the finished blanket</span>`;
  }
  if (t.kind === 'region') {
    const e = stats.perRegion.get(t.id) ?? { total: 0, sewn: 0 };
    const isOcean = t.id === OCEAN;
    const name = isOcean ? data.config.oceanName : regionById.get(t.id).name;
    const colour = isOcean ? data.config.oceanColour : regionById.get(t.id).colour;
    const share = e.total / stats.total;
    const done = e.total ? e.sewn / e.total : 1;
    const prior = !isOcean ? regionById.get(t.id).priorEstimate : null;
    return `
      <span class="tt-name"><i class="tt-swatch" style="background:${colour}"></i>${esc(name)}</span>
      ${nf.format(e.total)} hexagons · ${pctFmt(share)} of the blanket<br>
      ${nf.format(e.sewn)} of ${nf.format(e.total)} sewn, ${pctFmt(done)}
      ${prior ? `<br><span class="tt-est">fitted from the photo, not an exact count · earlier estimate ${prior}</span>` : ''}
      ${isOcean ? `<br><span class="tt-est">fitted from the photo, not an exact count</span>` : ''}`;
  }
  const s = sectionStats(data, state, t.side);
  const patches = s.patchesLeft;
  const pTxt = Number.isInteger(patches) ? nf.format(patches)
    : patches.toFixed(1).replace(/\.0$/, '');
  return `
    <span class="tt-name"><i class="tt-swatch" style="background:${data.config.oceanColour}"></i>${esc(s.label)}</span>
    ${nf.format(s.left)} hexagons still to sew<br>
    ${pTxt} ${patches === 1 ? 'patch' : 'patches'} at ${s.perPatch} a patch<br>
    ${nf.format(s.sewn)} of ${nf.format(s.total)} sewn in this section
    <br><span class="tt-est">layout inferred from counts</span>`;
}

const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

/* ---------------------------------------------------------------- the card */

function renderCard() {
  const stage = stages[idx];
  const traced = state.basis === 'traced';
  if (!state.known) {
    el.pct.textContent = '—';
    el.sewn.textContent = 'No count for this date';
    el.left.textContent = '—';
    el.finish.innerHTML = state.basis === 'carried'
      ? `Photo only — <b>${fmtDateShort(stage.date, spansYears)}</b> has no hexagon count, so the blanket above is ` +
        `carried forward from <b>${fmtDateShort(state.carriedFrom, spansYears)}</b>.`
      : `Photo only — <b>${fmtDateShort(stage.date, spansYears)}</b> is before the first counted date, so the ` +
        `photo is the record for this one. There is no digital blanket to draw yet.`;
    el.paceActual.textContent = el.paceNeeded.textContent = '—';
  } else {
    el.pct.textContent = pctFmt(stats.sewnTotal / stats.total);
    el.sewn.textContent = `${nf.format(stats.sewnTotal)} of ${nf.format(stats.total)} sewn`;
    el.left.textContent = nf.format(stats.left);
    const p = pace(data, stage, stats);
    el.finish.innerHTML = traced
      ? `Traced by eye from the photo — approximate, not a measured count.`
      : stats.left === 0
        ? `<b>Finished.</b>`
        : `At her pace so far she finishes about <b>${fmtDate(p.projected)}</b> — ${aheadText(p.aheadWeeks)}.`;
    el.paceActual.textContent = `${p.actual.toFixed(0)} a week`;
    el.paceNeeded.textContent = isFinite(p.needed) ? `${Math.max(0, p.needed).toFixed(0)} a week` : '—';
  }
  el.paceTarget.textContent = `${data.config.targetPerWeek} a week`;
  const cfg = data.config;
  el.startOut.textContent = fmtDate(new Date(cfg.startDate + 'T00:00:00')) + (cfg.startDateConfirmed ? '' : ' *');
  el.deadlineOut.textContent = fmtDate(new Date(cfg.deadline + 'T00:00:00')) + (cfg.deadlineConfirmed ? '' : ' *');
  const unconfirmed = [];
  if (!cfg.startDateConfirmed) unconfirmed.push('start date');
  if (!cfg.deadlineConfirmed) unconfirmed.push('deadline');
  el.assumptions.textContent = unconfirmed.length
    ? `* ${unconfirmed.join(' and ')} not confirmed — assumed in data/blanket.json.`
    : '';
  tickCountdown();
}

function tickCountdown() {
  if (!data) return;
  el.countdown.textContent = countdown(new Date(data.config.deadline + 'T00:00:00').getTime());
}

/* ------------------------------------------------------------- photo strip */

function buildStrip() {
  el.stripInner.textContent = '';
  stages.forEach((s, i) => {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'thumb'; b.dataset.i = i;
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-selected', 'false');
    const label = fmtDateShort(s.date, spansYears);
    if (s.thumb) {
      const im = document.createElement('img');
      im.src = s.thumb; im.alt = `The blanket on ${label}`; im.loading = 'lazy';
      b.append(im);
    } else {
      const ph = document.createElement('span');
      ph.className = 'ph'; ph.textContent = 'no photo yet';
      b.append(ph);
    }
    const d = document.createElement('span');
    d.className = 'd'; d.textContent = label;
    b.append(d);
    b.addEventListener('click', () => select(i));
    el.stripInner.append(b);
  });
}

function setPhoto(on) {
  showPhoto = on && !!stages[idx].photo;
  el.photo.hidden = !showPhoto;
  el.canvas.classList.toggle('photo-on', showPhoto);
  el.togglePhoto.textContent = showPhoto ? 'Show blanket' : 'Show photo';
  el.togglePhoto.setAttribute('aria-pressed', String(showPhoto));
  if (showPhoto) setHover(null);
}

/* ------------------------------------------------------------------ events */

function wire() {
  el.canvas.addEventListener('pointermove', (e) => {
    if (showPhoto) return;
    const r = el.canvas.getBoundingClientRect();
    const x = e.clientX - r.left, y = e.clientY - r.top;
    setHover(targetAt(x, y), x, y);
  });
  el.canvas.addEventListener('pointerleave', () => setHover(null));
  el.canvas.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse' || showPhoto) return;
    const r = el.canvas.getBoundingClientRect();
    const x = e.clientX - r.left, y = e.clientY - r.top;
    const t = targetAt(x, y);
    if (t && t.key === glowKey) setHover(null); else setHover(t, x, y);
  });

  el.togglePhoto.addEventListener('click', () => setPhoto(!showPhoto));
  el.latest.addEventListener('click', () => select(stages.length - 1));

  const toggleCard = () => {
    const open = el.more.hidden;
    el.more.hidden = !open;
    el.card.setAttribute('aria-expanded', String(open));
    el.hint.textContent = open ? 'Hide pace detail' : 'Pace detail';
    relayout();
  };
  el.card.addEventListener('click', toggleCard);
  el.card.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleCard(); }
  });

  addEventListener('keydown', (e) => {
    const t = e.target;
    if (t instanceof HTMLElement && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
    if (e.key === 'ArrowLeft') { select(idx - 1); e.preventDefault(); }
    else if (e.key === 'ArrowRight') { select(idx + 1); e.preventDefault(); }
    else if (e.key === 'Escape') setHover(null);
  });
}
