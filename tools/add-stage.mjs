#!/usr/bin/env node
// Append a stage after a visit, bring the photo in, and recalculate.
//
//   npm run add-stage -- --date 2026-10-04 --left 60 --right 80 --photo ~/shot.jpg
//   npm run add-stage -- --date 2026-10-04 --photo ~/shot.jpg          (photo only)
//
// --left/--right are hexagons ADDED on each side since the previous stage.
// Use --total-left/--total-right to give cumulative totals instead.

import { readFileSync, writeFileSync, copyFileSync, existsSync, mkdirSync, readdirSync } from 'node:fs';
import { join, dirname, resolve, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DATA = join(ROOT, 'data', 'blanket.json');

/* ---------------------------------------------------------------- images */

/** Resize with macOS `sips`; fall back to copying if it isn't there. */
function resizeTo(src, dest, maxPx) {
  const r = spawnSync('sips', ['-Z', String(maxPx), '-s', 'format', 'jpeg', src, '--out', dest],
                      { stdio: 'ignore' });
  if (r.status === 0 && existsSync(dest)) return true;
  copyFileSync(src, dest);
  return false;
}

/**
 * Put a photo into photos/ and photos/thumbs/ under a date-based name.
 * Returns { photo, thumb } as project-relative paths.
 */
function importPhoto(src, name, dry) {
  const photo = `photos/${name}.jpg`;
  const thumb = `photos/thumbs/${name}.jpg`;
  if (!dry) {
    mkdirSync(join(ROOT, 'photos', 'thumbs'), { recursive: true });
    resizeTo(src, join(ROOT, photo), 1600);
    resizeTo(src, join(ROOT, thumb), 320);
  }
  return { photo, thumb };
}

/* ------------------------------------------------------------------ args */

function parseArgs(argv) {
  const o = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith('--')) o[key] = true;
    else { o[key] = next; i++; }
  }
  return o;
}
const args = parseArgs(process.argv.slice(2));

function die(msg) { console.error(`\n  ${msg}\n`); process.exit(1); }

/* ---------------------------------------------------------------- import */

if (typeof args.import === 'string') {
  const dir = resolve(args.import.replace(/^~(?=$|\/)/, process.env.HOME ?? '~'));
  if (!existsSync(dir)) die(`no folder at ${dir}`);
  const data = JSON.parse(readFileSync(DATA, 'utf8'));
  const found = readdirSync(dir)
    .filter((f) => /\.(jpe?g|png|heic|webp)$/i.test(f))
    .map((f) => ({ f, m: basename(f).match(/(\d{4})-(\d{2})-(\d{2})/) }))
    .filter((x) => x.m)
    .map((x) => ({ file: join(dir, x.f), date: `${x.m[1]}-${x.m[2]}-${x.m[3]}`, name: x.f }))
    .sort((a, b) => (a.date + a.name).localeCompare(b.date + b.name));

  if (!found.length) die(`no files with a YYYY-MM-DD date in their name under ${dir}`);

  const already = new Set(data.stages.map((s) => s.photo).filter(Boolean));
  const perDate = new Map();
  let added = 0, skipped = 0;
  for (const { file, date } of found) {
    const n = (perDate.get(date) ?? 0) + 1;
    perDate.set(date, n);
    const name = n === 1 ? date : `${date}-${n}`;
    if (already.has(`photos/${name}.jpg`)) { skipped++; continue; }
    const { photo, thumb } = importPhoto(file, name, args['dry-run']);
    data.stages.push({ date, photo, thumb, sewnLeft: null, sewnRight: null,
                       note: `Imported from ${basename(file)}. Photo only \u2014 no hexagon count for this date.` });
    console.log(`  + ${date}  ${basename(file)}  ->  ${photo}`);
    added++;
  }
  data.stages.sort((a, b) => (a.date + (a.photo ?? '')).localeCompare(b.date + (b.photo ?? '')));
  console.log(`\n  ${added} added, ${skipped} already present, ${data.stages.length} stages total`);
  if (args['dry-run']) { console.log(`  dry run \u2014 nothing written\n`); process.exit(0); }
  writeFileSync(DATA, JSON.stringify(data));
  console.log(`  written to data/blanket.json\n`);
  process.exit(0);
}

if (args.help || !args.date) {
  console.log(`
  Add a stage to Nonna's blanket.

    npm run add-stage -- --date YYYY-MM-DD [--left N] [--right N] [--photo PATH]

    --date          required, the date of the visit
    --left          hexagons added on the left (Sardinia) side since the last stage
    --right         hexagons added on the right (Puglia) side since the last stage
    --total-left    cumulative left count instead of an increment
    --total-right   cumulative right count instead of an increment
    --photo         path to the photo; it is copied into photos/
    --note          a line of context to store with the stage
    --dry-run       print what would change and write nothing

  Bulk import a folder of photos whose filenames contain dates:

    npm run add-stage -- --import reference/originals
`);
  process.exit(args.help ? 0 : 1);
}

if (!/^\d{4}-\d{2}-\d{2}$/.test(args.date)) die(`--date must look like 2026-10-04, got "${args.date}"`);

/* ------------------------------------------------------------------ load */

const data = JSON.parse(readFileSync(DATA, 'utf8'));
const stages = [...data.stages].sort((a, b) => a.date.localeCompare(b.date));
if (stages.some((s) => s.date === args.date)) die(`a stage for ${args.date} already exists`);

const capL = data.missing.left.order.length;
const capR = data.missing.right.order.length;

// last stage with real counts
const prev = [...stages].reverse().find((s) => s.sewnLeft != null && s.sewnRight != null)
  ?? { sewnLeft: 0, sewnRight: 0, date: data.config.startDate };

const num = (v, name) => {
  if (v === undefined) return undefined;
  const n = Number(v);
  if (!Number.isInteger(n) || n < 0) die(`${name} must be a whole number of hexagons, got "${v}"`);
  return n;
};

let sewnLeft, sewnRight;
const addL = num(args.left, '--left'), addR = num(args.right, '--right');
const totL = num(args['total-left'], '--total-left'), totR = num(args['total-right'], '--total-right');

if (totL !== undefined || totR !== undefined) {
  sewnLeft = totL ?? prev.sewnLeft;
  sewnRight = totR ?? prev.sewnRight;
} else if (addL !== undefined || addR !== undefined) {
  sewnLeft = prev.sewnLeft + (addL ?? 0);
  sewnRight = prev.sewnRight + (addR ?? 0);
} else {
  sewnLeft = null; sewnRight = null;          // photo-only stage
}

if (sewnLeft !== null) {
  if (sewnLeft > capL) {
    die(`left side: ${sewnLeft} sewn but the left section only holds ${capL} ` +
        `(${prev.sewnLeft} were already in as of ${prev.date}, so at most ${capL - prev.sewnLeft} can be added)`);
  }
  if (sewnRight > capR) {
    die(`right side: ${sewnRight} sewn but the right section only holds ${capR} ` +
        `(${prev.sewnRight} were already in as of ${prev.date}, so at most ${capR - prev.sewnRight} can be added)`);
  }
  if (sewnLeft < prev.sewnLeft || sewnRight < prev.sewnRight) {
    die(`that would unsew hexagons: previous was left ${prev.sewnLeft}, right ${prev.sewnRight}`);
  }
}

/* ----------------------------------------------------------------- photo */

let photoRel = null, thumbRel = null;
if (typeof args.photo === 'string') {
  const src = resolve(args.photo.replace(/^~(?=$|\/)/, process.env.HOME ?? '~'));
  if (!existsSync(src)) die(`no photo at ${src}`);
  const taken = new Set(JSON.parse(readFileSync(DATA, 'utf8')).stages.map((s) => s.photo));
  let name = args.date;
  for (let n = 2; taken.has(`photos/${name}.jpg`); n++) name = `${args.date}-${n}`;
  ({ photo: photoRel, thumb: thumbRel } = importPhoto(src, name, args['dry-run']));
}

/* ------------------------------------------------------------ recalculate */

const stage = { date: args.date, photo: photoRel, thumb: thumbRel, sewnLeft, sewnRight };
if (typeof args.note === 'string') stage.note = args.note;

const total = data.config.total;
const before = { left: capL - prev.sewnLeft, right: capR - prev.sewnRight };
const after = sewnLeft === null ? before : { left: capL - sewnLeft, right: capR - sewnRight };
const leftNow = after.left + after.right;
const sewnNow = total - leftNow;
const pctNow = (sewnNow / total) * 100;

const nf = new Intl.NumberFormat('en-AU');
console.log(`\n  ${args.date}`);
if (photoRel) console.log(`  photo        ${photoRel}`);
if (sewnLeft === null) {
  console.log(`  counts       none given — photo-only stage`);
} else {
  console.log(`  added        left ${nf.format(sewnLeft - prev.sewnLeft)}, right ${nf.format(sewnRight - prev.sewnRight)}` +
              `  (since ${prev.date})`);
  console.log(`  section left left ${nf.format(after.left)} of ${nf.format(capL)}, ` +
              `right ${nf.format(after.right)} of ${nf.format(capR)}`);
  console.log(`  sewn         ${nf.format(sewnNow)} of ${nf.format(total)}`);
  console.log(`  complete     ${pctNow.toFixed(1)}%`);
  console.log(`  left to sew  ${nf.format(leftNow)}`);

  const asOf = new Date(args.date + 'T00:00:00');
  const start = new Date(data.config.startDate + 'T00:00:00');
  const deadline = new Date(data.config.deadline + 'T00:00:00');
  const WEEK = 7 * 864e5;
  const weeks = Math.max((asOf - start) / WEEK, 1 / 7);
  const rate = sewnNow / weeks;
  const projected = new Date(asOf.getTime() + (rate > 0 ? leftNow / rate : 0) * WEEK);
  const ahead = (deadline - projected) / WEEK;
  const fmt = (d) => d.toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' });
  console.log(`  pace         ${rate.toFixed(0)} a week (target ${data.config.targetPerWeek})`);
  console.log(`  projected    ${fmt(projected)} — ${Math.abs(ahead).toFixed(1)} weeks ` +
              `${ahead >= 0 ? 'ahead of' : 'behind'} ${fmt(deadline)}`);
}

if (args['dry-run']) { console.log(`\n  dry run — nothing written\n`); process.exit(0); }

data.stages.push(stage);
data.stages.sort((a, b) => a.date.localeCompare(b.date));
writeFileSync(DATA, JSON.stringify(data));
console.log(`\n  written to data/blanket.json\n`);
