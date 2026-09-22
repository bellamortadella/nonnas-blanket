// Grid geometry, stage state and statistics for Nonna's blanket.
// The blanket is a flat-top hexagon lattice: each hexagon has a flat top and
// bottom and points left and right, so a neighbour sits directly above.
// Columns are offset by half a row. Column 0 is the LOW column; odd-indexed
// columns sit half a row higher. cells[] is row-major: index = row*cols + col.

export const OCEAN = 0;
const SQRT3 = Math.sqrt(3);

export async function loadData(url = 'data/blanket.json') {
  const res = await fetch(url, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${url}: ${res.status} ${res.statusText}`);
  const d = await res.json();
  const { cols, rows } = d.config.grid;
  if (d.cells.length !== cols * rows) {
    throw new Error(`cells has ${d.cells.length} entries, expected ${cols * rows}`);
  }
  return d;
}

/* ------------------------------------------------------------------ layout */

export class Layout {
  /** Fit the whole grid inside w x h and remember the hexagon size. */
  constructor(cols, rows, w, h, pad = 24) {
    this.cols = cols; this.rows = rows;
    // width  = (1.5*cols + 0.5) * R ; height = sqrt(3) * (rows + 0.5) * R
    const R = Math.min(
      (w - pad * 2) / (1.5 * cols + 0.5),
      (h - pad * 2) / (SQRT3 * (rows + 0.5))
    );
    this.R = Math.max(1, R);
    this.w = (1.5 * cols + 0.5) * this.R;
    this.h = SQRT3 * (rows + 0.5) * this.R;
    this.x0 = (w - this.w) / 2 + this.R;          // centre of column 0
    this.y0 = (h - this.h) / 2 + SQRT3 * this.R / 2;
  }
  cx(col) { return this.x0 + col * 1.5 * this.R; }
  cy(col, row) {
    // odd columns sit half a row higher
    const off = (col % 2 === 0) ? 0.5 : 0;
    return this.y0 + (row + off) * SQRT3 * this.R;
  }
  /** Cell under a point, or null. */
  hit(x, y) {
    const approx = Math.round((x - this.x0) / (1.5 * this.R));
    let best = null, bestD = Infinity;
    for (let c = approx - 1; c <= approx + 1; c++) {
      if (c < 0 || c >= this.cols) continue;
      const off = (c % 2 === 0) ? 0.5 : 0;
      const rApprox = Math.round((y - this.y0) / (SQRT3 * this.R) - off);
      for (let r = rApprox - 1; r <= rApprox + 1; r++) {
        if (r < 0 || r >= this.rows) continue;
        const dx = x - this.cx(c), dy = y - this.cy(c, r);
        const d = dx * dx + dy * dy;
        if (d < bestD) { bestD = d; best = { col: c, row: r }; }
      }
    }
    // reject points outside the hexagon's incircle-ish bound
    return best && bestD <= (this.R * 1.02) ** 2 ? best : null;
  }
}

/** Trace a flat-top hexagon. Caller handles fill/stroke. */
export function hexPath(ctx, cx, cy, R) {
  ctx.beginPath();
  for (let k = 0; k < 6; k++) {
    const a = Math.PI / 3 * k;
    const x = cx + R * Math.cos(a), y = cy + R * Math.sin(a);
    k ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  }
  ctx.closePath();
}

/* ------------------------------------------------------- stage -> sewn map */

/**
 * Which cells are sewn at a given stage.
 * A stage records how many hexagons of each missing section were in place.
 * Sections fill along their `order` list.
 * A photo-only stage has no counts of its own, so it carries forward the most
 * recent stage that does have them.
 * `basis` says what the drawn blanket rests on: 'own' (this stage is counted),
 * 'carried' (carried forward from an earlier counted stage) or 'none' (the date
 * is before any counted stage, so the photo is the only record).
 * Returns { sewn, known, basis, sewnLeft, sewnRight, carriedFrom }.
 */
export function stateAt(data, stage, stages = data.stages) {
  const { cols, rows } = data.config.grid;
  const sewn = new Uint8Array(cols * rows).fill(1);

  // A traced stage carries its own state, read by eye off that day's photo.
  if (stage.trace) {
    const t = stage.trace;
    const byName = new Map(data.regions.map((r) => [r.name, r.id]));
    const foot = new Uint8Array(cols * rows);
    for (const [c0, c1, r0, r1] of t.bands) {
      for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) foot[r * cols + c] = 1;
    }
    // map cells count only for regions that existed on this date
    const keep = new Uint8Array(cols * rows);
    for (const name of t.regions ?? []) {
      const id = byName.get(name);
      if (!id) continue;
      const cl = t.clip?.[name];
      for (let i = 0; i < data.cells.length; i++) {
        if (data.cells[i] !== id) continue;
        if (cl) {
          const c = i % cols, r = (i / cols) | 0;
          if (c < cl[0] || c > cl[1] || r < cl[2] || r > cl[3]) continue;
        }
        keep[i] = 1;
      }
    }
    const looseIds = new Set((t.loose ?? []).map((n) => byName.get(n)).filter(Boolean));

    // She builds ocean around land that exists, so the footprint cannot reach
    // past a region that has not been made. Pull each column down below any
    // unmade land in it. Loose pieces are exempt: their slot is legitimately
    // empty, waiting on the piece lying beside the blanket.
    for (let c = 0; c < cols; c++) {
      let lowestUnmade = -1;
      for (let r = 0; r < rows; r++) {
        const i = r * cols + c, id = data.cells[i];
        if (foot[i] && id !== OCEAN && !keep[i] && !looseIds.has(id)) lowestUnmade = r;
      }
      for (let r = 0; r <= lowestUnmade; r++) foot[r * cols + c] = 0;
    }

    const loose = new Uint8Array(cols * rows);
    sewn.fill(0);
    for (let i = 0; i < data.cells.length; i++) {
      const id = data.cells[i];
      // a loose piece is lying beside the blanket, so it shows wherever it
      // belongs on the finished map - in or out of the footprint
      if (id !== OCEAN && looseIds.has(id)) { loose[i] = 1; continue; }
      if (!foot[i]) continue;
      if (id !== OCEAN && !keep[i]) continue;      // that region wasn't made yet
      sewn[i] = 1;
    }
    return { sewn, loose, known: true, basis: 'traced', sewnLeft: null, sewnRight: null,
             carriedFrom: null };
  }

  const counted = (s) => s.sewnLeft != null && s.sewnRight != null;
  const known = counted(stage);
  const src = known ? stage : [...stages]
    .filter((s) => counted(s) && s.date <= stage.date)
    .sort((a, b) => a.date.localeCompare(b.date))
    .at(-1) ?? null;
  const L = src?.sewnLeft ?? 0;
  const Rt = src?.sewnRight ?? 0;
  for (const [side, done] of [['left', L], ['right', Rt]]) {
    const sec = data.missing[side];
    for (let i = done; i < sec.order.length; i++) sewn[sec.order[i]] = 0;
  }
  const basis = known ? 'own' : (src ? 'carried' : 'none');
  return { sewn, loose: null, known, basis, sewnLeft: L, sewnRight: Rt,
           carriedFrom: known ? null : src?.date ?? null };
}

/* ------------------------------------------------------------- statistics */

export const WEEK = 7 * 24 * 3600 * 1000;
const DAY = 24 * 3600 * 1000;

export function tally(data, state) {
  const { cells } = data;
  const total = data.config.total;
  const perRegion = new Map();           // id -> { total, sewn }
  let sewnTotal = 0;
  for (let i = 0; i < cells.length; i++) {
    const id = cells[i];
    let e = perRegion.get(id);
    if (!e) perRegion.set(id, e = { total: 0, sewn: 0 });
    e.total++;
    if (state.sewn[i]) { e.sewn++; sewnTotal++; }
  }
  return { total, sewnTotal, left: total - sewnTotal, perRegion };
}

/** Remaining hexagons in one missing section at this stage. */
export function sectionStats(data, state, side) {
  const sec = data.missing[side];
  const done = side === 'left' ? state.sewnLeft : state.sewnRight;
  const total = sec.order.length;
  return {
    side, label: sec.label, total,
    sewn: done, left: total - done,
    perPatch: sec.perPatch,
    patchesLeft: (total - done) / sec.perPatch
  };
}

export function pace(data, stage, t) {
  const cfg = data.config;
  const start = new Date(cfg.startDate + 'T00:00:00');
  const deadline = new Date(cfg.deadline + 'T00:00:00');
  const asOf = new Date(stage.date + 'T00:00:00');
  const weeksElapsed = Math.max((asOf - start) / WEEK, 1 / 7);
  const actual = t.sewnTotal / weeksElapsed;
  const weeksToDeadline = (deadline - asOf) / WEEK;
  const needed = weeksToDeadline > 0 ? t.left / weeksToDeadline : Infinity;
  const weeksAtActual = actual > 0 ? t.left / actual : Infinity;
  const projected = new Date(asOf.getTime() + weeksAtActual * WEEK);
  const aheadWeeks = (deadline - projected) / WEEK;
  return {
    start, deadline, asOf, actual, target: cfg.targetPerWeek,
    needed, weeksToDeadline, projected, aheadWeeks,
    weeksAtTarget: t.left / cfg.targetPerWeek
  };
}

/* ------------------------------------------------------------ formatting */

export const nf = new Intl.NumberFormat('en-AU');
export const pctFmt = (n) => `${(n * 100).toFixed(1)}%`;

export function fmtDate(d) {
  return d.toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' });
}
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
/** "13 Sep", or "13 Sep 26" when the archive spans more than one year. */
export function fmtDateShort(iso, withYear = false) {
  const [y, m, d] = iso.split('-').map(Number);
  return `${d} ${MON[m - 1]}${withYear ? ` ${String(y).slice(2)}` : ''}`;
}

/** Live countdown, e.g. "101 days 4h 12m 09s". */
export function countdown(to, now = Date.now()) {
  let ms = to - now;
  if (ms <= 0) return 'deadline passed';
  const days = Math.floor(ms / DAY); ms -= days * DAY;
  const h = Math.floor(ms / 3600000); ms -= h * 3600000;
  const m = Math.floor(ms / 60000); ms -= m * 60000;
  const s = Math.floor(ms / 1000);
  const p = (n) => String(n).padStart(2, '0');
  return `${nf.format(days)}d ${p(h)}:${p(m)}:${p(s)}`;
}

/** "10.6 weeks ahead" / "2.1 weeks behind" */
export function aheadText(weeks) {
  if (!isFinite(weeks)) return 'no pace yet';
  const w = Math.abs(weeks);
  const unit = w === 1 ? 'week' : 'weeks';
  return `${w.toFixed(1)} ${unit} ${weeks >= 0 ? 'ahead of' : 'behind'} the deadline`;
}
