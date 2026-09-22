// Click a cell to change its region. Counts update live against the earlier
// estimates, and anything more than 3 away from its estimate is flagged.

import { loadData, Layout, hexPath, stateAt, nf, OCEAN } from './blanket.js';

const $ = (id) => document.getElementById(id);
const wrap = $('edCanvasWrap'), cv = $('edCanvas'), ctx = cv.getContext('2d');
const tbody = $('tbody'), foot = $('foot');
const btnUndo = $('undo'), btnRevert = $('revert'), btnDownload = $('download');

const FLAG_AT = 3;               // the brief: flag anything more than 3 from the estimate

let data, original, cells, regionById, layout, state;
let brush = OCEAN, undoStack = [], painting = false, strokeTouched = null;

loadData().then((d) => {
  data = d;
  original = Int16Array.from(d.cells);
  cells = Int16Array.from(d.cells);
  regionById = new Map(d.regions.map((r) => [r.id, r]));
  const ordered = [...d.stages].sort((a, b) => a.date.localeCompare(b.date));
  state = stateAt(d, ordered.at(-1), ordered);
  buildTable();
  relayout();
  addEventListener('resize', relayout, { passive: true });
  wire();
}).catch((e) => {
  foot.textContent = `Could not load data/blanket.json — ${e.message}`;
  console.error(e);
});

/* ------------------------------------------------------------------ paint */

function relayout() {
  const w = wrap.clientWidth, h = wrap.clientHeight;
  if (w < 2 || h < 2) { requestAnimationFrame(relayout); return; }
  const dpr = Math.min(devicePixelRatio || 1, 2);
  cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const { cols, rows } = data.config.grid;
  layout = new Layout(cols, rows, w, h, 14);
  draw();
}

function draw() {
  const { cols, rows } = data.config.grid;
  const w = wrap.clientWidth, h = wrap.clientHeight;
  const R = layout.R, ocean = data.config.oceanColour;
  ctx.clearRect(0, 0, w, h);
  ctx.lineWidth = Math.max(0.5, R * 0.08);
  for (let col = 0; col < cols; col++) {
    const cx = layout.cx(col);
    for (let row = 0; row < rows; row++) {
      const i = row * cols + col;
      const cy = layout.cy(col, row);
      const id = cells[i];
      ctx.fillStyle = id === OCEAN ? ocean : (regionById.get(id)?.colour ?? ocean);
      hexPath(ctx, cx, cy, R * 0.97);
      ctx.fill();
      if (!state.sewn[i]) {                      // not sewn yet, shown hollow
        ctx.strokeStyle = 'rgba(150,168,196,.5)';
        hexPath(ctx, cx, cy, R * 0.6);
        ctx.stroke();
      }
      if (cells[i] !== original[i]) {            // edited since load
        ctx.strokeStyle = '#ffffff';
        hexPath(ctx, cx, cy, R * 0.97);
        ctx.stroke();
      }
    }
  }
}

function paintAt(x, y) {
  const c = layout.hit(x, y);
  if (!c) return;
  const i = c.row * data.config.grid.cols + c.col;
  if (cells[i] === brush || strokeTouched?.has(i)) return;
  strokeTouched?.add(i);
  undoStack.at(-1)?.push([i, cells[i]]);
  cells[i] = brush;
  draw();
  refreshCounts();
}

/* ------------------------------------------------------------------ table */

function buildTable() {
  tbody.textContent = '';
  const rows = [
    { id: OCEAN, name: data.config.oceanName, colour: data.config.oceanColour, priorEstimate: null },
    ...data.regions
  ];
  for (const r of rows) {
    const tr = document.createElement('tr');
    tr.dataset.id = r.id;
    tr.innerHTML =
      `<td><i class="sw" style="background:${r.colour}"></i>${r.name}</td>` +
      `<td class="n" data-now></td>` +
      `<td class="n">${r.priorEstimate ?? '—'}</td>` +
      `<td class="n" data-diff></td>`;
    tr.addEventListener('click', () => setBrush(r.id));
    tbody.append(tr);
  }
  setBrush(OCEAN);
  refreshCounts();
}

function setBrush(id) {
  brush = Number(id);
  for (const tr of tbody.children) tr.classList.toggle('sel', Number(tr.dataset.id) === brush);
}

function refreshCounts() {
  const counts = new Map();
  for (const v of cells) counts.set(v, (counts.get(v) ?? 0) + 1);
  let mapTotal = 0, flagged = 0;
  for (const tr of tbody.children) {
    const id = Number(tr.dataset.id);
    const n = counts.get(id) ?? 0;
    if (id !== OCEAN) mapTotal += n;
    tr.querySelector('[data-now]').textContent = nf.format(n);
    const est = id === OCEAN ? null : regionById.get(id).priorEstimate;
    const cell = tr.querySelector('[data-diff]');
    if (est == null) { cell.textContent = '—'; cell.className = 'n ok'; continue; }
    const d = n - est;
    if (Math.abs(d) > FLAG_AT) flagged++;
    cell.textContent = d > 0 ? `+${d}` : String(d);
    cell.className = `n ${Math.abs(d) > FLAG_AT ? 'off' : 'ok'}`;
  }
  const edited = countEdited();
  foot.innerHTML =
    `Map ${nf.format(mapTotal)} hexagons, ocean ${nf.format(data.config.total - mapTotal)}, ` +
    `total ${nf.format(data.config.total)}.<br>` +
    `<b>${flagged}</b> of ${data.regions.length} regions differ from the earlier estimate by more than ${FLAG_AT}.` +
    (edited ? `<br>${nf.format(edited)} cell${edited === 1 ? '' : 's'} edited — outlined in white.` : '') +
    `<br><br>Download writes a full <kbd>blanket.json</kbd>; drop it over <kbd>data/blanket.json</kbd> to keep it.`;
  btnUndo.disabled = undoStack.length === 0;
  btnRevert.disabled = edited === 0;
}

function countEdited() {
  let n = 0;
  for (let i = 0; i < cells.length; i++) if (cells[i] !== original[i]) n++;
  return n;
}

/* ----------------------------------------------------------------- events */

function wire() {
  const xy = (e) => {
    const r = cv.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
  };
  cv.addEventListener('pointerdown', (e) => {
    painting = true; strokeTouched = new Set(); undoStack.push([]);
    cv.setPointerCapture(e.pointerId);
    paintAt(...xy(e));
  });
  cv.addEventListener('pointermove', (e) => { if (painting) paintAt(...xy(e)); });
  const end = () => {
    if (!painting) return;
    painting = false; strokeTouched = null;
    if (undoStack.at(-1)?.length === 0) undoStack.pop();
    refreshCounts();
  };
  cv.addEventListener('pointerup', end);
  cv.addEventListener('pointercancel', end);

  btnUndo.addEventListener('click', () => {
    const stroke = undoStack.pop();
    if (!stroke) return;
    for (let k = stroke.length - 1; k >= 0; k--) cells[stroke[k][0]] = stroke[k][1];
    draw(); refreshCounts();
  });
  btnRevert.addEventListener('click', () => {
    if (!confirm('Throw away every edit and go back to the loaded grid?')) return;
    cells = Int16Array.from(original); undoStack = [];
    draw(); refreshCounts();
  });
  btnDownload.addEventListener('click', download);

  addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); btnUndo.click(); }
  });
}

function download() {
  const counts = new Map();
  for (const v of cells) counts.set(v, (counts.get(v) ?? 0) + 1);
  const out = structuredClone(data);
  out.cells = Array.from(cells);
  out.regions = out.regions.map((r) => ({ ...r, count: counts.get(r.id) ?? 0 }));
  const map = out.regions.reduce((s, r) => s + r.count, 0);
  out.provenance = {
    ...out.provenance,
    counted: { map, ocean: out.config.total - map, total: out.config.total },
    editedInBrowser: new Date().toISOString().slice(0, 10)
  };
  const blob = new Blob([JSON.stringify(out)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'blanket.json';
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
