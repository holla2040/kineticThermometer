# Plan: shape round 2 — owner-chosen curves through reverse kinematics

Written 2026-08-03 for the agent who picks this up. Read `CLAUDE.md` first
(it loads automatically), then `README.md`'s "Dead center" section. This file
is the brief; follow it in order. Round 1 shipped `shape-01`…`shape-06` and
is documented in `REPORT.md` — the commit `0eb1dce` contains everything
referenced here. All tooling already exists; **you should not need to write
any new tools.**

## The loop (three stops, owner decides at each)

1. **Propose**: generate a fresh sheet of abstract curves. Owner picks the
   shapes to attempt.
2. **Synthesize**: for each picked shape, find what the mechanism can
   actually wear (match → refine → lift).
3. **Verdict**: ONE sheet, every design tile numbered and tagged
   BUILDABLE / NOT BUILDABLE. Owner picks tiles; those become presets
   `shape-07`, `shape-08`, … (never renumber anything).

## Non-negotiable presentation rules (round 1 broke these; do not repeat)

- **Never show the owner a design without a tile number and an explicit
  BUILDABLE / NOT BUILDABLE tag.** No unlabeled trade-off ladders. The owner
  treats every presented design as an implicit "this works".
- **BUILDABLE means, all four at once**: min transmission angle **≥6.0°**
  (the owner's stated criterion — NOT the README's 15°) measured over the
  shipped 0–15.5″ excursion; mount clearance ≥2.5″; stall ≥0.07″/°F;
  envelope ≤48×48″. Print the actual angle in the tag.
- Do not cross-reference other preset families when presenting ("stop
  bringing up the other examples"). The owner picks by eye and by tile
  number.
- Shapes the mechanism cannot reach: say so plainly, with the best distance
  achieved. Never lower a gate silently.
- DM the owner (`/dm` skill) when the proposal sheet is ready and when the
  verdict sheet is ready. STOP and wait at each decision point.

## Step 1 — proposals

    python3 tools/propose_shapes.py proposals2.json proposals2.png --seed 29

- Fresh `--seed` (round 1 used 11). ~16 tiles; the tool gates plausibility
  (turn 2.5–7 rad each way, dens 1.2–3.0, open endpoints) and novelty ≥7.0
  rad against every preset currently in index.html (it re-parses the page,
  so the six shape-* are included automatically).
- The tile captions carry stats; make sure the sheet reads as **round 2**
  (IDs restart at prop-01 — that's fine, just caption the sheet clearly).
- If the owner supplies their own sketch instead: digitize to
  `[{"id": "...", "pts": [[x,y], ...]}]` with ≥500 points; that file feeds
  `--targetpts` directly (the loader arc-resamples and drops zero-length
  segments).

## Step 2 — synthesis per picked shape

One-time seed pool (the only memory-heavy run — `--batch 6000`, ≤5 parallel
processes machine-wide, launch with `setsid`, watch `free -g`):

    python3 tools/explore_designs.py --emitpool 3000 --trials 3000000 \
        --batch 6000 --nsamp 261 --seed 19 --out pool.json

Then per picked shape (index IX into proposals2.json, 0-based):

    # stage A: match, two independent seeds (~10 min each, light memory)
    tools/explore_designs.py --seedfrom pool.json --targetpts proposals2.json \
        --targetix IX --objective match --nsamp 1041 --seeds 600 --iters 2400 \
        --emit 4 --seed 7  --minlen 80 --out mA-ixIX-s7.json
    (same with --seed 31)

    # stage B: REFINE — re-climb from the better stage-A output. Round 1
    # gained 0.5–1.5 rad here; do not skip it.
    ... --seedfrom mA-ixIX-sBEST.json ... --iters 3600 --seed 51 --out mB-ixIX.json

    # stage C: lift ladder — hold the matched shape, climb transmission angle.
    # T* = the DENSE tdist of stage B's best (from its json), never a
    # coarse-grid number. Rungs: T*+0.1, +0.3, +1.0; extend by +0.8 steps
    # while the angle is still climbing and below ~25°.
    ... --seedfrom mB-ixIX.json --targetpts proposals2.json --targetix IX \
        --targetdist D --objective ta ... --out L-ixIX-dD.json

Climbs are light (~0.15 GB each); up to ~10 in parallel is safe, but keep
the sampling run's 5-process rule when `--batch` is involved.

### Calibration from round 1 (so expectations are honest)

- A drawn wild shape is always MATCHED at/near dead center; safety is bought
  with shape drift. Distance ladder: **~2 = the drawing, ~4 = clearly
  related, ~5+ = generic**. The two family gap is 6.3.
- Some shapes are flatly unreachable (round 1: a double spiral at dist 11.7;
  a 6.7-rad-both-ways ribbon at 5.2). Detect early: if stage-A best is >5,
  say so and spend the compute elsewhere.
- `--minlen` matters: without the length floor the scale-free descriptor
  converges on 20″ midgets (fixed in `score_match`, but keep `--minlen 80`
  for targets that deserve size; drop toward 60 only consciously).
- Drawn-vs-traced descriptors carry ~0.5 rad parametrization bias
  (documented in `polyline_desc`) — irrelevant at decision thresholds, but
  don't chase distances below ~0.5.

## Step 3 — the verdict sheet (`verdict2.png`)

Format exactly like the committed `verdict.png` (round 1's final form):

- One row per picked shape: leftmost tile = the drawing, labelled
  "target, not a design", no tag.
- Every design tile globally numbered `#1…#N` in reading order, with a
  colored tag: green `#n — BUILDABLE · X°`, red `#n — NOT BUILDABLE — X°
  from dead center` (6.0° is the line; if something lands within ~1° of it,
  amber `JUST UNDER/OVER` with the number).
- Small caption under each: `dist D from its drawing · L″ scale`.
- Renders come through the real page (`tools/render_designs.py <run>.json
  <outdir>`); tile images are `<outdir>/creative-01-path.png`. Near-singular
  designs can trip its 1%-length assert — render a one-entry copy of the
  json rather than weakening the assert.
- Build the grid as HTML screenshotted by playwright (see round 1's inline
  script pattern; `render_designs.sheet()` needs PNG inputs, the drawings
  are inline SVG).
- Deliver: repo root + `SendUserFile` + `/dm`. Wait for tile numbers.

## Step 4 — insertion (mechanics proven twice; checklist)

For each chosen tile, in this order:

0. Round geo to 4 decimals; page-measure label numbers on the ROUNDED geo at
   `extMin:0, extMax:15.5` (playwright: scale int = sum of `__ct.chunks`
   segments; angle = floor of min over 401 `pose()` samples using §13's
   `ta()` JS). Labels never use full-stroke numbers.
1. PRESETS entry in `index.html` after the last shape-* (mind the trailing
   comma). **Exactly 22 keys**: the 18 geo keys + `actT:1, aLmin:24,
   aStroke:18, aClamp:23.23` — `presetOf()` matches entry keys at 1e-9;
   extra/missing keys silently break re-identification. Provenance comment.
2. `python3 tools/sync_core.py --apply`.
3. `<option>` rows by hand in BOTH pages (index 4-space indent ~line 160,
   mobile 6-space ~line 225): `shape-NN — L&Prime; scale · A° min`, plus
   trailing ` *` ONLY if the measured angle is under 6° (should not happen —
   nothing under 6° is presented as buildable).
4. `tools/verify_export.py` §13: add each new preset to the `SHAPE_TA`
   pinned-angle table (±0.5° tolerance, [6,40) band) — in the SAME edit as
   the presets or the check silently under-asserts.
5. Help prose (both pages, outside the shared core — search `shape-*`
   paragraph) and docs: CLAUDE.md gallery bullet, README shape section +
   angle-table row ranges, `tools/make_diagrams.py ruler()` shape-row span →
   regenerate `images/dead-center-ruler.svg`, TODO.md, REPORT.md outcome.
   Regenerate `contact-sheet-shape.png`:
   `python3 tools/render_designs.py --presets contact-sheet-shape.png /tmp/x shape-`
6. **All four verifiers green**: `tools/verify_export.py`,
   `tools/verify_mobile.py`, `tools/sync_core.py` (--check),
   `tools/crosscheck_port.py`. If you touched `tools/explore_designs.py`
   (you shouldn't need to): `--selfcheck` too.
7. No commits, no pushes, unless the owner explicitly says the words.

## Facts that will bite if forgotten

- CLAUDE.md's round-1 note said the family was complete at six; the owner
  reopened it 2026-08-03 for this round — this file supersedes that line.
- The owner identifies designs ONLY by the numbers printed on the sheet.
  Keep every number stable between what they see and what you ship.
- `verify_mobile.py` asserts the two pages' preset dropdown value-lists are
  identical — a forgotten mobile row fails loudly now.
- Gallery presets force `actT` to 1 and that persists to localStorage —
  expected behavior, not a bug.
- example-02 does not assemble at exactly 16.0″ extension; anything
  comparing shipped curves must use the 0–15.5″ excursion (propose_shapes
  already does).
