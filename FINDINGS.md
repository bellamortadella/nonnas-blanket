# What the photos say, and what they don't

Twenty-three images. The grid was fitted from three of them:
`reference/blanket-2026-09-13.jpeg` (the whole blanket) and the two 20 Sep
close-ups, `blanket-2026-09-20-north.png` and `-south.png`, which arrived while
I was working. The other twenty are the 2025 archive in `reference/originals/` —
see **The photo archive** below. The `reference/` folder the brief described was
not in the project folder, so `italy-region-hex-counts.json` is treated as a
prior to check against rather than as truth.

The fit is reproducible — `tools/fit-grid/` holds the scripts and the order to
run them in.

**The headline: I could not pin the hexagon size, and that is the one number
everything else hangs off.** The app ships with my best fit, clearly labelled as
an estimate, and every figure that depends on it lives in one config block.

---

## What I am confident about

- **The map is finished and every region is in its right place.** I segmented the
  map into contiguous colour blobs and identified all twenty regions by
  geography, then rendered the result back as hexagons
  (`reference/digital-blanket-render.png`) and compared it with the photo. It is
  a faithful likeness. The region colours I sampled off the photo also match
  your table's palette closely once the warm indoor light is divided out, which
  is a good independent check that the regions are identified correctly.
- **Everything still to sew is ocean**, in two blocks at the top corners.
- **The left block is narrower than the right, in roughly a 3:4 ratio.** Measured
  at the step, the left block is 8.1% of the blanket's width and the right is
  11.8%. That ratio is scale-free, so it holds whatever the hexagon size turns
  out to be, and it matches your 6-across and 8-across patches.
- **Hexagons are flat-top**, as you thought — a neighbour sits directly above
  each one.
- **The blanket photographs taller than it is wide.** See the open question below.

## What I could not settle: the hexagon size

Three ways of counting Sardinia, which is the best target in the set because it
is an island with a clean boundary and it sits fully inside one close-up:

| Method | Sardinia |
|---|---:|
| Your earlier estimate, from the 20 Sep close-up | 41 |
| Counting hexagons by eye on the 20 Sep close-up | roughly 55 |
| My lattice fit on the 13 Sep photo | 78 |

They do not converge, and neither do the automated approaches I tried — boundary
scallop periods, 2-D FFT of the seams, and seam detection all gave answers
scattered from 28 to 78 for the same region. The seams are genuinely faint, the
batik print interferes with every frequency method, and the 13 Sep photo is too
angled and too small to read cells from — exactly as your brief predicted.

**So treat every per-region count in `data/blanket.json` as an estimate that
could be 30% out in either direction.** The map is somewhere around 600–1,100
hexagons. My fit says 1,110, which is likely at the top of the plausible range;
your table's 464 is likely at the bottom. The app says "fitted from the photo,
not an exact count" in every region tooltip, and keeps your figure alongside as
`priorEstimate`.

> An earlier draft of this file asserted that every region was 2.39× your
> estimate and presented that as settled. It was not — that conclusion came from
> the lattice fit alone, before the close-ups arrived, and the close-ups do not
> support it. This version replaces it.

### One piece of support for the current numbers

With the start at 27 May 2025, her pace to 13 Sep 2026 works out at **89
hexagons a week against a target of 88**, and 6,480 hexagons at 88 a week is
73.6 weeks — almost exactly the 18 months the target was set from. She is 67.7
weeks in and about 93% done, which is what an 18-month plan for 6,480 looks
like.

That is consistent rather than conclusive — the 88 was probably derived from
6,480 in the first place, so part of it is circular. But the elapsed time is
independent, and it does not fit a blanket of only ~4,600 hexagons, which is
what the low end of my measurements would imply. It nudges me toward the current
figures being closer to right than wrong.

### The one thing that would settle all of it

**Count one edge.** The number of hexagons along the bottom edge of the blanket,
or along one side, either counted off a photo or asked of Nonna, fixes the
hexagon size exactly. Every region count, the ocean total and the remaining
count all follow from it immediately, and I can regenerate the grid in minutes.

Failing that, a flat top-down photo with all four corners in frame, as the brief
anticipated.

## The open question: which way round is 72 × 90?

The brief says 90 across by 72 down. The 13 Sep photo shows a blanket that is
**taller than it is wide**, and 90 across by 72 down of regular flat-top hexagons
would come out about 8% wider than tall.

I recovered the rectangle's true proportions from the perspective (the standard
single-imaged-rectangle method, which also returned a plausible focal length of
1,875 px ≈ 44 mm, so the fit is at least self-consistent) and got width ÷ height
≈ 0.78. That points to a portrait grid, and of every factor pair of 6,480,
72 × 90 fits it best.

**But I would not bet much on it.** That measurement leans on four corners
extrapolated well past the edges that define them, and the honest error bar
covers the difference between 0.78 and 1.0 — and at 1.0 your 90 × 72 is right.
Two further points cut against my reading:

- At 72 columns the missing blocks measure 5.9 and 8.5 columns wide, which is a
  lovely match to your 6 and 8. That is what first convinced me. But the same
  ratio holds at any width, so it argues for the *ratio*, not for 72.
- Measuring Sardinia on the close-up and scaling it up through my grid implies a
  blanket about 93 columns by 72 rows — which is 90 × 72, your numbers.

**The app ships at 72 × 90** because that is the geometry the cell map was fitted
at, and re-labelling 6,480 cells at a different aspect is not something to guess
at. If you confirm 90 × 72, say so and I will refit rather than transpose — the
map would need re-deriving, not rotating.

## The missing sections

Read off the 13 Sep photo at my grid's scale:

| Section | Columns | Rows | Hexagons |
|---|---|---|---:|
| Left, the Sardinia side | 0–5 (6 across) | 0–33 | 204 |
| Right, the Puglia side | 64–71 (8 across) | 0–33 | 272 |
| **Total** | | | **476** |

That is 92.7% complete on 13 Sep, against your 85.5% with 930 left on 20 Sep, a
week later. The counts scale with the hexagon size, so this gap is the same
unresolved question as above rather than a separate problem — at a hexagon size
about 40% smaller than my fit, 476 becomes roughly 930.

Two things that are not just scale, though:

- `930 = 60a + 80b` has no whole-number solution, so 930 was never a whole number
  of patches either way.
- Both blocks come out 34 rows tall on my grid, which is 3.4 patches of 10 on
  each side. The 3.4 being identical on both sides looks real; its not being a
  whole number does not. Worth checking how tall the blocks actually are.

## The loose patch, and where row 0 sits

I put row 0 on the top edge of the main blanket. **The finished patch lying above
that edge in the 13 Sep photo is outside my grid entirely** — roughly 9 columns
by 7 rows, unaccounted for.

If that patch is to join on and the blanket grows taller, my top edge is not row
0, and both the total and the missing counts move. This is your question 3 and it
is still open.

## The photo archive

Twenty photos came in, from 27 May to 21 Dec 2025. Two were dropped at Jordan's
request — the duller of the two 21 Nov shots, and 21 Dec, which shows a separate
navy section rather than the blanket — leaving eighteen 2025 photos. The 20 Sep
2026 entry was dropped as well, so the strip now ends on 13 Sep 2026, the one
date with a measured count. The
originals of both sit in `reference/originals/excluded/` so a re-import will not
bring them back.
They fall into two halves: **May to August 2025** is loose region pieces laid out
on a table, before the ocean existed; **September to December 2025** is the
blanket itself, assembled and growing.

**The eleven assembled photos now have a traced blanket.** I could not register
them to the grid automatically — I tried homography fitting against the map
silhouette, anchor matching on Sicily/Puglia/Sardinia/Calabria, and silhouette
matching for the loose pieces, and none of it converged. The photos are oblique,
the light swings from daylight to indoor, and the map itself keeps changing
shape as it is built, so there is nothing stable to register against.

So each one is **traced by eye against the map**, which is the one thing whose
grid position I know exactly. Each trace is a footprint in bands, the list of map
regions in place, and any pieces sitting loose. They run **21% on 8 Sep 2025 to
49% on 15 Dec 2025**, rising monotonically, with each footprint containing the
one before it, and well under the 92.7% measured for 13 Sep 2026. Accurate to a few cells, not measured — the card says so on every
traced date, and the numbers live in `stages[].trace` to correct by hand.

> Two passes of this were too generous and Jordan caught both. The first showed
> 44–92% with Piedmont, Aosta, Trentino, Veneto and Friuli all finished by late
> November; through 26 Nov and 15 Dec the north in fact has only
> Emilia-Romagna, a little Liguria and a bit of Lombardy. Measuring the 15 Dec
> photo against the map confirms the blanket was about 52 columns of 72 wide
> then, not near complete.
>
> The second pass still ran the map too far north early on. Checking every photo
> at full size: **the map sits at Lazio and Abruzzo from 8 Sep right through
> 7 Oct** — four dates, no Umbria, Marche or Tuscany. Tuscany's yellow only
> appears on 30 Oct and Emilia-Romagna's dark green on 7 Nov. What grows over
> those seven weeks is the ocean, not the land.
>
> A third pass fixed the left side. Jordan: "the water line doesn't pass
> Sardinia, and at times there is no water connecting Sardinia to the land."
> Right on both counts, and then right again: there is **no water under her
> either**. From Sep through 21 Nov the ocean simply has not been built out to
> the left of the map at all — the blanket's left edge is a clean line at column
> 24 and Sardinia lies off to the side of it. It only reaches out to her when
> she is joined on for 26 Nov, and even at 15 Dec it stops barely a column or
> two past her. That pulled 15 Dec from 58% to 49% and 30 Oct from 41% to 31%.
>
> Worth noting for later corrections: the left band had to come off the
> September dates too, not just the two flagged. Leaving it there would have
> meant the blanket losing its left arm between 7 Oct and 30 Oct, and it can
> only grow. Every footprint is now checked to contain the one before it.
>
> A **loose piece now draws wherever it belongs on the finished map**, in or out
> of the footprint — so Sardinia shows as an outline off to the left of the
> blanket on those dates, which is exactly what the photos show.
>
> The region list is explicit per date rather than a north–south cut-off, which
> could not express "Lombardy but not Piedmont". The footprint is also trimmed
> so it never reaches past land that has not been made — otherwise the ocean
> showed holes where a region would later go, which is not how she builds it.

**The eight May-to-August photos have no trace.** They show loose pieces in
bright kelly green, vivid red and cyan — nothing like the final palette — and
the shapes do not match any region silhouette. Shape matching returned noise:
every piece scored 0.4-0.6 against everything, with "Tuscany+Lazio" winning
almost every time, which only means "a blob of roughly that size". Until I know
what those pieces are, those dates show the photo and say the blanket cannot be
drawn for them.

One thing I noticed but did not chase: the ocean reads as a **bright blue** in
most of the 2025 photos and as **dark navy** in the 2026 ones. The dot print
matches, so it is most likely daylight versus indoor light rather than two
fabrics — but if she did change batik partway, the app's single ocean colour
would need splitting by date. Worth a glance next time you see it.

## Smaller things

- **Sewing order is assumed** (your question 4). Each section fills from its
  bottom row upward, and within a row from the column nearest the map outward to
  the blanket edge. The tooltip says "layout inferred from counts", as asked.
  Change the `order` arrays in `data/blanket.json` if she works the other way —
  nothing else depends on it.
- **The start date now comes from the archive** (your question 1). The twenty
  photos you added run from **27 May 2025**, which is `startDate` in the config —
  earlier than the "around July 2025" in the brief. It is still marked
  unconfirmed, and the card prints an asterisk against it. `deadline` is still
  the assumed 1 Jan 2027, from "the 18 months end in January 2027".
- **13 Sep to 20 Sep** (your question 5): no count, so 20 Sep is a photo-only
  stage. The card says so and carries the blanket forward from 13 Sep.
- **Question 6** — yes, digital blanket as the main view with the photo one click
  away. That is how it is built.
- **Question 7** — I assumed you on a phone plus family on a link, so it works
  with a thumb and with a mouse, and it is plain static files you can host
  anywhere.
