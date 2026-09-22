# Nonna's blanket

A progress tracker for Nonna's hexagon blanket of Italy: 6,480 hexagons, 72
across and 90 down, on navy batik ocean. Static HTML, CSS and JavaScript — no
backend, no build step.

**Read [FINDINGS.md](FINDINGS.md) first.** The hexagon size is not settled by any
photo in the project, so every region count here is an estimate that could be 30%
out. Counting the hexagons along one edge of the blanket would fix all of it.

## Running it

The page fetches `data/blanket.json`, so it needs to be served over http rather
than opened from the file system.

```bash
npm start
```

Then open <http://localhost:5173>. Any static server does — `python3 -m http.server`,
Netlify, GitHub Pages, an S3 bucket. There is nothing to compile.

## Using it

- **Hover or tap a hexagon.** Its whole region lights up, everything else drops
  to a third, and a tooltip gives the region, its hexagon count, its share of
  the blanket and how much of it is sewn. The ocean counts as one region.
- **Hover an empty outline** and it tells you what goes there on the finished
  blanket, and how much of that region was in place on the date you are looking
  at. Pieces finished but not yet joined — Sardinia through October and
  November 2025 — show as a coloured outline rather than a filled shape.
- **Hover a dim outline** in a missing corner and the whole section lights up in
  brightened navy, with the hexagons and patches still to go.
- **The card, top left,** carries the percentage, hexagons left, a live
  countdown to the deadline and the projected finish. Click it for pace detail.
- **The strip along the bottom** holds a dated photo per visit. Click a
  thumbnail, or use ← and →, to move the whole screen to that date. **Latest**
  jumps to the newest. **Show photo** swaps the drawn blanket for the real one.

## Importing a batch of photos

Drop photos anywhere with a `YYYY-MM-DD` somewhere in the filename — WhatsApp's
own names work as they come — and point the importer at the folder:

```bash
npm run add-stage -- --import reference/originals
```

It reads the date out of each filename, resizes a display copy into `photos/`
and a thumbnail into `photos/thumbs/`, and appends each one as a photo-only
stage. Photos already imported are skipped, so it is safe to re-run. Two photos
on the same day become `2025-06-09.jpg` and `2025-06-09-2.jpg`, and both show in
the strip. Add `--dry-run` to see what it would do first.

Full-resolution originals live in `reference/originals/`; `photos/` holds only
the web-sized copies the page loads.

## Adding a stage after a visit

```bash
npm run add-stage -- --date 2026-10-04 --left 60 --right 80 --photo ~/Desktop/blanket.jpg
```

`--left` and `--right` are hexagons **added** on each side since the last stage.
The script copies the photo into `photos/`, appends the stage, and prints the new
completion percent, pace and projected finish. It refuses counts that exceed
what is actually missing, dates that already exist, and anything that would
unsew hexagons.

Other flags: `--total-left` / `--total-right` for cumulative counts instead of
increments, `--note "..."`, and `--dry-run` to see the effect without writing.
Omit the counts entirely for a photo-only entry — the thumbnail still appears,
**Show photo** still works, and the card says there is no count for that date.

```bash
npm run add-stage -- --help
```

> Resizing uses macOS `sips`. On a machine without it the photo is copied at
> full size instead, which still works but makes the strip heavier.

## Fixing the grid by hand

Open <http://localhost:5173/editor.html>. Pick a region from the list, then
click or drag across the blanket to repaint cells. Counts update live beside the
earlier estimates, and anything more than 3 away is flagged. `Cmd/Ctrl-Z` undoes
a stroke. **Download blanket.json** gives you a complete file to drop over
`data/blanket.json`.

## Layout

```
index.html          the blanket
editor.html         click-a-cell grid editor
css/style.css
js/blanket.js       grid geometry, stage state, statistics
js/app.js           the main view
js/editor.js
data/blanket.json   config, regions, 6,480 cells, missing sections, stages, traces
photos/             web-sized image per stage, plus thumbs/
reference/          the brief, the earlier estimates, fit renders
reference/originals/  full-resolution photos as supplied
tools/add-stage.mjs
tools/fit-grid/     the Python that derived the grid from the photo
FINDINGS.md         what the photos say, what they can't settle, and why
```

## Everything that might change

It is all in the `config` block at the top of `data/blanket.json`:

| Key | Value | Confirmed? |
|---|---|---|
| `grid` | 72 cols × 90 rows | **no** — the photo suggests portrait, the brief says 90 × 72 |
| `total` | 6480 | from the brief |
| `startDate` | 2025-05-27 | **no** — date of the earliest photo in the archive |
| `deadline` | 2027-01-01 | **no** — assumed from "the 18 months end in January 2027" |
| `targetPerWeek` | 88 | from the brief |
| `patch` | 10 rows high; 6 across left, 8 across right | widths match the photo's 3:4 ratio |

`startDateConfirmed` and `deadlineConfirmed` are both `false`, so the card marks
those two with an asterisk. Set them to `true` once you know.

The missing sections are `missing.left` and `missing.right`: column range, row
range, and an `order` array giving the sewing sequence. Region counts are
derived from `cells`, never stored twice.

## Data model

`cells` is a flat array of 6,480 region ids, row-major — index `row * 72 + col`,
`0` for ocean. The lattice is flat-top: each hexagon has a flat top and bottom
and points left and right, so a neighbour sits directly above. Column 0 is the
low column; odd-numbered columns sit half a row higher.

A stage carries its state one of two ways. The 2025 stages have a `trace`:

- `bands` — the blanket's footprint, as `[col0, col1, row0, row1]` strips,
  inclusive. The top edge is a ridge, highest where the map had reached
  furthest north, because the ocean only gets built out around land that exists.
- `regions` — which map regions were in place. Anything not listed stays an
  empty outline. The footprint is automatically pulled back below any region
  not yet made, so the ocean never shows a hole where land will go.
- `clip` — narrows a region that was only partly done, to `[col0, col1, row0, row1]`.
- `loose` — regions finished but not joined on yet; they draw as an outline in
  their own colour.

These were traced by eye from each photo against the map, which is the one thing
whose grid position is known exactly. Good to a few cells, not measured — the
card says so on those dates.

Otherwise a stage records `sewnLeft` and `sewnRight` — how many hexagons of each
missing section were in place on that date. The sections fill along their
`order` lists, so the drawn layout inside a part-finished section is inferred
from the counts, and the interface says so. `null` means the count is unknown
and the entry is photo-only. The photos remain the record of what is really
sewn.
