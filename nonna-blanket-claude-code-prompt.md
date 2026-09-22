# Build a progress tracker for Nonna's hexagon blanket

You are helping me (Jordan) build a static web app that tracks my nonna's hexagon blanket. Read this whole brief and look at the files in `reference/`. Then ask me the questions under "Open questions" before you write any code.

## Files to put in the project first

- `reference/blanket-2026-09-20.png`: close-up photo of the Italy map. It crops the blanket edges.
- `reference/blanket-2026-09-13.jpeg`: whole-blanket photo. It shows the blanket outline and the missing sections.
- `reference/italy-region-hex-counts.json`: region hexagon counts and colours, estimated from the close-up.

## The blanket

- The blanket shows a map of Italy in 20 region colours, sewn from hexagons and set on navy batik "ocean" hexagons. Each hexagon is a separate piece.
- Finished size: 90 across by 72 down, which is 6,480 hexagons.
- Status on 20 Sep 2026: 85.5% finished, 930 hexagons left. 930 left of 6,480 is 85.6%, so one number is rounded or the total is slightly off. Treat "930 left" as the anchor and keep the total in one config value.
- Target pace: 88 hexagons a week. It was set to finish inside 18 months, and the 18 months end in **January 2027**. The start date and the exact January day are unknown. I think Nonna started around July 2025.
- At 88 a week, 930 hexagons take about 10.6 weeks, which lands around 3 Dec 2026. To finish by January 2027 from 20 Sep, she needs roughly 49 to 63 a week depending on the day, so she is ahead of target.
- The map is finished. Everything left to sew is navy ocean.
- The hexagons look flat-top (a neighbour sits directly above each one), tilted a few degrees by the camera. Confirm this from the photo.

## Where the missing hexagons go

- Nonna sews in patches that are always 10 hexagons high.
  - Left side (the Sardinia side): patches are 6 across, so 60 hexagons each.
  - Right side (the Puglia side): patches are 8 across, so 80 hexagons each.
- The 13 Sep photo shows the blanket narrower at the top than in its lower half. The missing sections look like the top-left and top-right corner blocks, and one finished loose patch sits above the top edge. I have not confirmed this.
- The numbers do not close yet. Six plus eight across over 72 rows is 1,008 hexagons, not 930. I will mark the missing areas on the photo so you can see them.

## Region counts (estimates)

I estimated these from the 20 Sep close-up using three methods: seam fitting, boundary fitting, and area divided by hexagon size. Sicily and Sardinia are solid. The mainland regions can be off by a hexagon or two, and Puglia is the least certain because it is a thin diagonal band.

| Region | Colour in the blanket | Estimate | Range |
|---|---|---|---|
| Sicily | red | 61 | 60-61 |
| Sardinia | green | 41 | 41-42 |
| Tuscany | yellow | 38 | 35-39 |
| Puglia | light teal | 33 | 30-34 |
| Piedmont | amber | 32 | 30-33 |
| Lombardy | maroon | 31 | 30-32 |
| Calabria | salmon pink | 30 | 28-31 |
| Emilia-Romagna | dark olive | 27 | 27-29 |
| Lazio | steel blue | 25 | 24-27 |
| Campania | orange | 24 | 23-26 |
| Veneto | purple | 19 | 17-19 |
| Abruzzo | lime green | 18 | 16-19 |
| Basilicata | sand | 16 | 15-17 |
| Umbria | cream | 15 | 13-15 |
| Trentino-Alto Adige | khaki olive | 13 | 12-14 |
| Marche | tan | 13 | 13-15 |
| Friuli-Venezia Giulia | peach | 9 | 8-10 |
| Liguria | pale cream | 8 | 7-9 |
| Molise | mauve | 6 | 5-8 |
| Aosta Valley | brown | 5 | 5-6 |
| **Total** | | **464** | **439-486** |

Ocean hexagons: 6,480 minus 464 gives about 6,016. About 5,086 are sewn and 930 remain, assuming everything left is ocean.

Once we have a corrected cell-by-cell grid, compute region counts from the grid and use this table only as a check. Flag any region that differs from the table by more than 3.

## What to build

A static site (HTML, CSS, JavaScript, no backend) that I can host as plain files. The screen is the most up-to-date digital version of the blanket. Everything else stays small and quiet.

1. **The blanket fills the screen.** Draw the 90 by 72 grid on a canvas. Sewn hexagons show their region colour or navy ocean. Unsewn hexagons, including the two missing sections, show as a dim outline so I can see what comes next. The page opens on the latest date.

2. **Hover glows a region and tells me about it.** When the cursor is over a sewn hexagon:
   - The whole region that hexagon belongs to glows. It brightens and gets a soft halo in its own colour, and the rest of the blanket dims to about a third.
   - A small tooltip near the cursor shows the region name, the number of hexagons in the region, and its completion rate.
   - For a map region, completion is sewn hexagons out of hexagons in the region, which is 100% for every region because the map is finished. Also show the region's share of the whole blanket.
   - The ocean counts as one region. Its tooltip shows total ocean hexagons and how many are sewn, for example "5,086 of 6,016 sewn, 84.5%".
   - Hovering an incomplete area works the same way. When the cursor is over a dim outline in a missing section, every outline in that section lights up so I can see where the hexagons will go, and the rest of the blanket dims. The outlines glow in the navy ocean colour, brightened enough to read on the dark background.
   - The tooltip for a missing section shows the side ("Left, the Sardinia side" or "Right, the Puglia side"), how many hexagons remain in that section, how many patches that is (60 hexagons per left patch, 80 per right patch), and sewn out of total for the section.
   - The two sections must add up to the 930 hexagons left. If the missing areas I annotate do not add up to 930, tell me before you continue.
   - Touch screens get the same on tap.

3. **A small overview card in one corner.** It shows the stats for the selected date and nothing more:
   - Percent complete in large type, with "5,550 of 6,480 sewn" beneath it.
   - Hexagons left.
   - Time left to the January 2027 deadline, counting down live.
   - One line with the projected finish date and how many weeks ahead or behind the deadline she is. Base it on pace since the start date. If the start date is unknown, use the 88 a week target.
   - Pace details (actual pace, the 88 target, the pace needed to hit the deadline) sit behind a click on the card. The card never grows beyond a small corner.

4. **A photo strip along the bottom.** A horizontal, scrollable row of dated photo thumbnails of the blanket, oldest on the left and newest on the right, with a date under each one.
   - Selecting a thumbnail jumps the whole screen to that date. The blanket shows its digital state as of that date and the overview card updates to match.
   - A small "Show photo" button on the screen swaps the digital blanket for that date's real photo.
   - A "Latest" button and the left and right arrow keys move along the strip. The newest date is selected on load.
   - A photo can exist without a digital state (see the data model). Its thumbnail still shows, the "Show photo" button works, and the overview card shows "no count for this date".

5. **No transition effects.** Changing the date swaps the view straight away. The hover glow is the only animation on the page.

6. **Look and feel.**
   - Simple and clean. A plain dark background so the region colours and the hover glow stand out. No gradients, scan lines, or neon effects.
   - The blanket supplies the colour. Text is white or grey.
   - Two typefaces at most. I suggest Unbounded for the large numbers and Newsreader for labels, in sentence case. Change them if you have a better pairing.
   - It works on a phone (tap instead of hover, strip scrolls with a thumb) and on a laptop.

## Data model (suggested)

```
data/blanket.json
{
  "grid": { "cols": 90, "rows": 72 },
  "startDate": "TBC",
  "deadline": "2027-01-TBC",
  "targetPerWeek": 88,
  "regions": [{ "id": 1, "name": "Sicily", "colour": "#..." }],
  "cells": [ ...6480 region ids, 0 = ocean ],
  "missing": {
    "left":  { "across": 6, "high": 10, "order": [ ...cell indexes in sewing order ] },
    "right": { "across": 8, "high": 10, "order": [ ...cell indexes in sewing order ] }
  },
  "stages": [
    { "date": "2026-09-13", "photo": "photos/2026-09-13.jpeg", "sewnLeft": null, "sewnRight": null },
    { "date": "2026-09-20", "photo": "photos/2026-09-20.png", "sewnLeft": 0, "sewnRight": 0 }
  ]
}
```

Each stage records how many hexagons of the missing sections were sewn as of that date. The app fills the `order` lists in that sequence. `null` means the count for that date is unknown, so the entry is photo-only. Where the app infers positions from counts, label it in the interface as "layout inferred from counts". The photos remain the record of what is really sewn.

Two photos exist today: 13 Sep (whole blanket) and 20 Sep (close-up). I do not yet know how many hexagons went in between them.

## Building the grid from photos (one-off)

I need each of the 6,480 cells labelled with a region or ocean. Do this in steps:

1. Ask me for a flat, top-down photo of the whole blanket with all four corners in frame. The close-up crops the edges, and the 13 Sep photo is too small and angled to read cells from.
2. Find the four blanket corners and rectify the photo with a homography. Perspective rotates and rescales the hexagon lattice by a few degrees and a few percent across the frame, and a single rigid grid did not fit the unrectified close-up.
3. Fit a 90 by 72 flat-top lattice to the rectified image.
4. Sample the colour at each cell centre and classify it into one of the 20 region colours or ocean.
5. Open an editor where I click a cell to change its region. Show live region counts next to the estimates above.

What I learned when I tried this on the close-up:

- The seams between hexagons are faint. The colour boundaries between regions are the strong signal.
- Scoring a lattice by how cleanly each hexagon falls inside one colour region worked. Scoring by seam lines alone gave inconsistent hexagon sizes.
- In the close-up, neighbouring hexagon centres are about 34 to 35 pixels apart.
- Do not let the fit choose the hexagon size freely on small regions. It drifts to the smallest size allowed, because smaller cells always look purer.

## Updating after each visit

I will send you a photo and the number of hexagons added on each side. Add a small script, for example `npm run add-stage -- --date 2026-10-04 --left 60 --right 80 --photo path`, that:

- appends the stage and adds its thumbnail to the bottom strip,
- checks that the counts do not exceed the hexagons still missing,
- recalculates every statistic,
- and tells me the new completion percent and projected finish.

## Open questions (ask me these first)

1. What is the start date, and what is the exact day in January 2027 for the deadline?
2. Is the total 6,480, or nearer 6,414 (which is what 85.5% with 930 left implies)?
3. Where exactly are the missing sections? I will annotate the 13 Sep photo. The hover outlines and the remaining counts depend on this. Is the loose patch above the top edge part of what remains?
4. Which way does Nonna sew each patch (top to bottom or bottom to top), and does she alternate sides?
5. How many hexagons went in between the 13 Sep and 20 Sep photos? If I do not know, keep 13 Sep as a photo-only entry.
6. When I pick a date in the bottom strip, is the digital blanket as of that date the right main view, with the photo one click away? I chose that as the default.
7. Who looks at this and on what device (my phone, family, a hosted link)?

## Rules

- Show estimates as estimates. Do not present a fitted count as exact.
- Keep the project in one small folder with a README that explains how to add a stage.
- Put every number that may change (total, start date, deadline, target pace) in one config block at the top of the data file.
