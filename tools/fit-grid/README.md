# How the grid was derived from the photo

These are the scripts that turned `reference/blanket-2026-09-13.jpeg` into the
6,480 labelled cells in `data/blanket.json`. You only need them if you want to
redo the fit — say, when you get a flat, top-down photo with all four corners in
frame, which would let the whole thing be done properly rather than from an
angled shot. Nothing in the web app depends on them.

They are throwaway analysis scripts, not a library: each one writes `.npy` and
`.png` files into the working directory and the next one reads them, so run them
from one scratch directory in order.

## Setup

```bash
python3 -m venv venv
./venv/bin/pip install numpy pillow scipy
```

## Order

```bash
cd /tmp/blanket-fit                       # any empty scratch directory
P="/path/to/Nonnas Blanket"
for s in seg fitgrid classify build_grid blobs finalgrid export writejson; do
  BLANKET_PROJ="$P" "$P/tools/fit-grid/venv/bin/python" "$P/tools/fit-grid/$s.py" || break
done
```

| Script | What it does |
|---|---|
| `seg.py` | Segments the blanket from the wooden floor by flood-filling the warm background inward from the image border. Writes `blanket_mask.npy`. |
| `edges.py` | Prints where the outline steps in — this is what located the two missing corner blocks. Diagnostic only. |
| `fitgrid.py` | Fits robust straight lines to the four blanket edges and intersects them to get the corners of the full rectangle, including the part not yet sewn. Writes `corners.npy`. |
| `aspect.py` | Recovers the rectangle's true width:height and the camera's focal length from the perspective. This is what showed the grid is 72 × 90, not 90 × 72. Diagnostic only. |
| `classify.py` | Fits a quadratic illumination model to the ocean pixels and divides it out, so region colours can be compared across the warm, unevenly lit photo. Writes `corr.npy`. |
| `build_grid.py` | Builds the homography to a 72 × 90 flat-top lattice and searches the sub-cell phase and column parity for the best fit. Scored 99.4% agreement with the colour boundaries. |
| `blobs.py` | Segments the map into contiguous colour blobs and writes `blobs_labelled.png` with each blob numbered — the image used to assign region names by geography. |
| `finalgrid.py` | Maps blobs to region names, labels every cell, and forces each region to a single connected shape. **The blob→region table at the top is specific to this photo**; if you rerun `blobs.py` on a new photo, look at `blobs_labelled.png` and rewrite it. |
| `export.py` | Snaps the missing sections to clean rectangles, samples each region's colour, and renders `render.png` — the digital blanket, to eyeball against the photo. |
| `hexoverlay2.py` | Draws the fitted hexagons back onto the photo at two candidate scales. This is the check that confirmed the cell size by eye. |
| `writejson.py` | Writes `data/blanket.json`. **This overwrites the file, including your stages**, so back it up first. |

`BLANKET_PROJ` defaults to the project root three levels up from the script.

## If you reshoot the blanket

The fit will be far better from a flat, top-down photo with all four corners
visible. Two things to redo by hand after `blobs.py`:

1. Open `blobs_labelled.png` and rewrite `BLOB2REG` at the top of `finalgrid.py`
   so each numbered blob maps to the right region.
2. Check `render.png` against the photo before running `writejson.py`.

Then fix the rest by clicking in `editor.html`.
