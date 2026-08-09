# Seeded transmission-angle search — report (2026-08-03)

## The question, answered plainly

**Is the example-08 / example-00 shape reachable at a safe transmission angle?**

- **At 40° ("clean"): NO.** Neither seed's shape survives to 40°, in the
  original box or the widened one. Nothing here may be called clean, and
  nothing is named clean.
- **At 15–33°: YES.** The shape family holds together far above the README's
  15° "rebuild line". Recognisably-example-08 designs (shape distance ≤3)
  reach **25.4°**; loosening to same-family distance 4 reaches **32.9°** —
  within a degree of Grand Arc's 33.9°. Example-00's crescent reaches
  **20.8°** at distance 3 and **25.6°** at distance 5.

Example-08 itself sits at 0.8°. A2 (18.7°) is 23× further from dead center;
A7 (32.9°) is 41× further.

## The frontier (best dense-measured ta among finalists that held the shape)

| shape dist allowed | ex-08, orig box | ex-08, wide box | ex-00, orig box | ex-00, wide box |
|--:|--:|--:|--:|--:|
| 2 | 13.1° | **18.7°** | **16.7°** | 14.2° |
| 3 | 19.9° | **25.4°** | **20.8°** | 17.5° |
| 4 | **32.9°** | 28.3° | **21.8°** | 20.2° |
| 5 | 22.3° | **30.5°** | 24.6° | **25.6°** |

Distance scale: ~3 = recognisably the same design, ~5 = same family (the two
original clean families sit 6.3 apart). The non-monotone cells (ex-08 D=5
orig box) are hill-climb luck, not physics — the true frontier can only
improve as the allowance loosens.

The wide box (`--widebox`: cv2 ±32, cu2 0–34, L5 8–32; envelope cap still
48×48) helped example-08 at D=2/3/5 but was NOT the unlock it looked like it
would be — both seeds sat pinned at cv2=20, yet the best single point (32.9°)
came from the ORIGINAL box. Wide-box designs are marked on the sheet and are
not comparable to earlier runs.

## The 12 candidates (owner picks; suggested keep: five)

All: mount clearance ≥2.5″ ✓, stall ≥0.15″/°F ✓ (the search's min-segment
rule, not just the 0.07 floor), envelope ≤48×48 ✓, assembles over the full
16″ Joyce stroke ✓. None reach 40° — this family must NOT be named clean-*.

| | run | ta° | scale″ | loops | both | dens | stall | clear | envelope | d(ex08) | d(ex00) |
|--|--|--:|--:|--:|--:|--:|--:|--:|--|--:|--:|
| A1 | ta08b-d2 #1 | 13.1 | 92 | 1 | 4.09 | 1.66 | 0.154 | 5.5 | 37×42 | 2.0 | 13.6 |
| A2 | ta08w-d2 #1 | 18.7 | 86 | 1 | 4.09 | 1.56 | 0.150 | 3.8 | 35×43 | 2.0 | 14.5 |
| A3 | ta08b-d3 #1 | 19.9 | 67 | 1 | 3.79 | 1.11 | 0.150 | 6.6 | 45×41 | 3.0 | 14.1 |
| A4 | ta08w-d3 #1 | 25.4 | 96 | 1 | 3.77 | 1.49 | 0.150 | 7.2 | 45×46 | 3.0 | 14.3 |
| A5 | ta08w-d4 #1 | 28.3 | 89 | 1 | 3.65 | 1.45 | 0.150 | 11.5 | 42×45 | 3.7 | 14.9 |
| A6 | ta08w-d5 #1 | 30.5 | 95 | 1 | 3.76 | 1.53 | 0.150 | 11.9 | 44×44 | 4.7 | 13.8 |
| A7 | ta08b-d4 #1 | 32.9 | 62 | 1 | 3.57 | 1.10 | 0.150 | 6.6 | 38×43 | 4.0 | 14.5 |
| B1 | ta00-d2 #1 | 16.7 | 156 | 1 | 5.93 | 2.65 | 0.168 | 2.6 | 46×37 | 14.4 | 2.0 |
| B2 | ta00-d3 #1 | 20.8 | 134 | 1 | 5.36 | 2.29 | 0.152 | 2.5 | 45×38 | 14.3 | 3.0 |
| B3 | ta00-d4 #1 | 21.8 | 124 | 1 | 5.14 | 2.17 | 0.151 | 2.5 | 43×37 | 13.7 | 3.8 |
| B4 | ta00-d5 #1 | 24.6 | 88 | 1 | 4.31 | 1.54 | 0.150 | 2.5 | 44×37 | 14.6 | 5.0 |
| B5 | ta00w-d5 #1 | 25.6 | 93 | 2 | 4.26 | 1.61 | 0.151 | 2.5 | 46×35 | 14.3 | 5.0 |

Reference: example-08 is both 4.71 / dens 1.99 / stall 0.169; example-00 is
both 7.06 / dens 3.29 / stall 0.140. B1 is essentially example-00's wildness
(both 5.93, dens 2.65, 156″, stall 0.168) at 20× its distance from dead
center. Every candidate's nearest shipped preset is its own seed, margin ≥3
to anything else — no accidental clean-* lookalikes.

Wide-box entries (A2, A4, A5, A6, B5): found in the widened parameter box;
flagged because they are not comparable to original-box runs.

## Method (SEARCH-PLAN step 1 + 3)

- `--seedfrom` / `--target` / `--targetdist` / `--widebox` added to
  `tools/explore_designs.py`; `--selfcheck` extended and passing;
  `crosscheck_port.py` still matches the page to 1e-13.
- 600 jittered copies of the seed, hill-climbed 2400 iterations on
  `score_ta`: transmission angle, minus 150/rad of shape drift beyond the
  allowance, with stall and mount-clearance priced in. Sweep D = 2,3,4,5 ×
  two seeds × two boxes = 16 runs at `--nsamp 1041`.
- Step 4 of the plan (fresh gated random search) was NOT run: steps 1–3
  answered the question.
- **A measurement bug found and fixed on the way** (it predates this work):
  `measure()` decimated paths by array stride, silently dropping the curve's
  endpoint at some sample counts — at DENSE=1301 a hooked curve read up to
  5 rad from its own converged shape. Reference descriptors are now traced at
  2601 samples (where the descriptor converges), decimation keeps the
  endpoint, DENSE is 2601, and the selfcheck pins both. Consequence worth
  knowing: shape/novelty numbers previously computed at DENSE (e.g. in
  merge reports) wobbled by ~0.2 rad; the clean-1x novelty gating itself ran
  at 261 samples and is unaffected in substance.
- Coarse grids carry ~0.3–0.6 rad of corner-cutting shape bias (measured;
  canary assert added), which is why the climbs ran at `--nsamp 1041`.

## Outcome (updated 2026-08-03, later the same day)

The owner kept **A1 and B1 only** — shipped as presets **`shape-01`** (88″ as
shipped, 13° min) and **`shape-02`** (138″, 16° min) in both pages, verified —
and rejected the other ten as lookalikes of presets that already exist. The
remaining three designs will be found shape-FIRST: abstract proposal curves
(novelty ≥7.0 vs all 21 shipped shapes), owner picks from a contact sheet,
then approximate path synthesis reports how close the mechanism can get and
at what transmission angle. See TODO.md "New scale-curve designs".

Files: `candidates.png` (contact sheet), `candidates.json` (geometries +
metrics, labels A1–B5), `allrows.json` (all 128 finalists), seed/target JSONs
and all 16 run outputs, in the session scratchpad.

## Reverse pipeline calibration (2026-08-03, evening)

The shape-first pipeline (`tools/propose_shapes.py` →
`explore_designs.py --targetpts --objective match` → `--objective ta` lift)
was calibrated on four proposals before the owner's pick. See
`calibration.png` and `proposals.png`. What the numbers say:

- **A drawn wild shape is always matched AT dead center.** Best full-size
  matches: prop-05 dist 2.1 (visibly the drawing) at 0.8°; prop-12 dist 3.9
  at 0.2°; prop-01 dist 4.3 at 0.7°; prop-08 (wildest, 6.7 rad both ways)
  only reaches dist 6.1 — its wildness exceeds the mechanism's.
- **Lifting to safety is cheap at first, then steep, and shape-dependent.**
  prop-12: +0.1 rad of drift → 21.8°, +0.3 → 32.8°, +1.0 → 42.4°
  (clean-grade, but the lineage is gone by eye). prop-05: does not lift —
  8.4° at +2.0 rad is its ceiling; the meander IS a singular shape here.
- **Distance calibration by eye:** ~2 = the drawing; ~4 = clearly related
  (loop + ribbon survive); ~5+ = generic. The usable sweet spot for a
  drawn shape is dist ~4 at ~20-25° — inside the band the owner already
  accepted for shape-01/02.
- Two tool lessons, both fixed and selfchecked: `score_match` needs a length
  floor (the scale-free descriptor otherwise converges on 20″ midgets), and
  drawn-vs-traced descriptors carry a ~0.5 rad parametrization bias
  (arc-uniform vs stroke-uniform vertices; documented in `polyline_desc`).

Awaiting the owner's proposal picks; per pick the deliverable is this same
frontier — closest match plus lifted versions — judged by eye.

## Verdict on the owner's picks: props 4, 8, 9, 11, 15 (2026-08-03, night)

Full ladder in `verdict.png`. Two match rounds (2 seed pools + a refinement
climb) and 15 lift runs per the calibration protocol:

| pick | closest match | lift behaviour |
|---|---|---|
| prop-15 | **2.6** (the drawing, 91″) at 0.1° | does not lift: 2.3° at +1, 7.5° at generic |
| prop-09 | 3.1 (related, 80″) at 1.0° | does not lift: 9.0° at generic |
| prop-04 | 4.8 (loose) at 0.1° | lifts 11.8° → 23.8°, but rungs read generic |
| prop-08 | 5.2 — wilder than the mechanism | (lifts only because already generic) |
| prop-11 | 11.7 — **out of reach**, no such curve family | — |

Plain statement: **none of the five picked drawings is wearable at ≥13° while
still recognisable.** The two proposals with a usable pocket — prop-05 (the
drawing at 0.8°) and prop-12 (clearly related at 21.8°) — were not picked.

## Final outcome (2026-08-03, late)

A process failure surfaced here, worth recording: the owner expected every
design presented to be BUILDABLE, and the ladders above presented trade-offs
instead. Recovery: `verdict.png` was relabelled — every design numbered
(#1–#16) and tagged BUILDABLE / NOT at the 15° line, with the owner's actual
criterion clarified as **6°** (consistent with the serpentine's own 7.7°).
From that tagged sheet the owner chose tiles **#4, #7, #11, #14**, shipped as:

| preset | tile | ta° | scale″ (0–15.5″) | from drawing |
|---|---|--:|--:|---|
| shape-03 | #4 | 7.5 | 71 | prop-15, dist 5.0 |
| shape-04 | #7 | 6.9 | 43 | prop-09, dist 4.1 |
| shape-05 | #11 | 14.0 | 35 | prop-04, dist 5.1 |
| shape-06 | #14 | 25.3 | 36 | prop-08, dist 5.5 |

All four verifiers green; §13 pins each shape preset's angle to its label
value. The shape family is complete at six per the owner. Lesson applied
going forward: designs are presented ONLY with explicit numbered tiles and
buildable/not tags at the owner's stated criterion.

# Benchtop 3D-print model + native Fusion rebuild (branch `3dfab-level`, 2026-08-09)

Two pieces of work, in order: a generator that turns the flat serpentine into a
printable 3D model, and a hand transcription of that model into Fusion 360 as
jointed components so the thing actually articulates on screen.

## 1. The print pipeline (`tools/print3d.py`, `print/`) — commit ec9ee4e

The flat mechanism is lifted into 3D: a back plate carries posts of differing
lengths at the four fixed mounts, every moving link rides its own plane parallel
to the plate, and sleeves couple the joints across planes. The actuator is
replaced by a hand drive — a bar pivoting on the anchor post with a slot along
its axis, and a shuttle puck that rides the slot and pins to the crank's R hole.
That reproduces the actuator constraint exactly: R stays on the anchor line the
way `lenOf()` puts it, and **the slot ends ARE the stops at ext 0 and 15.5″**, so
the model cannot be pushed past the dA+rA ceiling.

Scale **5 mm per real inch** (1:5.1), chosen by `pick_scale` as the largest tidy
0.1 step that fits plate + margin on a 210 mm bed. Back plate 186 × 164 mm, bar
210 mm — everything prints flat, no supports.

**The level assignment is searched, not chosen.** `assign_levels` enumerates
every stacking of the six links and rejects any that collides at any of the 141
poses (same sampling as the page's `rangeValid`), where "collides" covers link
vs link, post shaft crossing a link's plane, sleeve crossing a link's plane, and
sleeve/post passing through the air band a puck or ring stub occupies. Survivors
are ranked by fewest levels, then least post+sleeve metal. The winner:

| level | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| part | rocker1 | plate1 | crank | bar | rocker2 | plate2 |

Pitch 12 mm (4 link + 8 air). `verify_hardware` then clears what the level
search does not: post shafts, sleeves, the puck, the ring and every nut/head
protrusion, checked pairwise per pose wherever two share an air band.

Four results here are load-bearing and must not be "improved":

- **The plates are hollow triangles**, not filled hulls. A filled plate2 sweeps
  over the O2 post at some pose and then *no* collision-free stacking exists at
  all. Hollow rings sweep far less and print just as flat.
- **The bar tip is trimmed** to `lmax + 0.1`. A longer tip collided with the P
  sleeve (7.1 mm centre distance against 10.75 needed). The outline's own end cap
  forms the stop wall.
- **B and R take flush heads in pockets** in the laminated crank, B from above
  and R from below. They sit only |rA−L2| = 6.2 mm apart on the crank arm, so a
  head beside the neighbouring joint's sleeve does not fit. `screw_table`
  asserts the orientation policy (`plate1 < crank < bar`) that makes this valid.
- **Level order**, as above.

Outputs: 16 STLs plus `assembly.stl` (everything placed at mid-stroke),
`PRINT.md` (BOM, screw/washer table, assembly order) and `fusion-data.json`
(exact mm coordinates, level table, post/sleeve lengths, pose checkpoints).
`PROMPT.md` is the handover written so the Fusion rebuild could happen on
another machine.

## 2. Native Fusion 360 assembly (2026-08-09)

Design **`kineticThermometer-bench-3dfab`** in project *solohm*, units mm, built
through the Fusion MCP link by transcribing `print/fusion-data.json`. Nothing
was re-derived; the owner's existing designs were not touched.

**15 components, 18 occurrences** — back plate (with feet, mount holes and the
raised scale ridge), the five links, bar, shuttle, ring, four posts, and sleeves
(8 mm ×4, 44 mm ×1). All flat extrusions on XY. Every hole landed within
**0.0016 mm** of its published mid-stroke world position; the residual is the
3-decimal rounding in the JSON, nothing else.

**20 as-built joints** (as-built, so creating them moved nothing): back plate
grounded; 10 rigid — four posts to the plate, five sleeves to the link they
stand on, ring to plate2 at Q; nine revolutes at O2, O4, O6, ANCH, B, C, P, D, R;
and one pin-slot, shuttle to bar, sliding on the bar's own X axis with limits at
the slot ends (−38.7498 / +38.7502 mm about mid = 120 … 197.5 from ANCH).

### Verification (all three asked for, all pass)

1. **Articulation stop to stop** — smooth, no popped joints, stops at both slot
   ends.
2. **Checkpoints** — R, B, C, P, D and Q at ext0 / mid / ext15.5 against
   `pose_checkpoints`: **worst error 0.0019 mm** (tolerance was 0.1). Q reads
   (−6.908, 110.455), (70.625, 129.587), (4.971, 99.500).
3. **Interference** at all three poses, coincident faces ignored: **zero pairs**
   — re-run after the scale ridge was added, still zero.

### Findings worth not re-deriving

- **A slider joint shuttle↔bar silently locks Fusion's solver; a pin-slot does
  not.** The joint is created without error and then joint values simply refuse
  to stick. Bisected by suppression: both four-bar loops drive correctly on
  their own, and the freeze appears only when the slider is added on top of the
  revolute at R. `PROMPT.md` predicted this and named pin-slot as the robust
  choice; it is not optional, it is the only one that works.
- **Consequence: the assembly has 2 DOF, not 1.** A pin-slot leaves the shuttle
  free to spin about its own screw — which a round boss on a round screw
  genuinely is. Only one DOF moves the mechanism. Making shuttle↔crank *rigid*
  instead would give exactly 1 and is kinematically identical; it was not done
  because `PROMPT.md` specifies a revolute there.
- **Drive in small steps or the second loop flips branch.** One large jump sends
  plate2/rocker2 to the other assembly solution (both are valid: |D−O6| = 70.000
  and |D−P| = 29.500 either way) and it does not come back on its own. Stepping
  at 0.4 mm tracks perfectly across the whole stroke. Dragging in the UI is
  continuous so a human will not hit this, but any script that drives this model
  must step. `Design.snapshots.revertPendingSnapshot()` restores the as-built
  pose; there is no `revert()`.
- **The scale ridge is a union of 140 capsules, not a sweep or loft.** The Q path
  self-crosses once, so a swept 1.2 × 1.2 profile fails there. Drawing the 140
  capsules into one sketch yields 417 profiles (0.2 s) which extrude and join to
  the plate in 6.6 s — the same construction `plate_mesh` uses, and it matches.
- **Fusion API notes** that cost time: `ExtrudeFeatureInput.participantBodies`
  wants a Python list, not an `ObjectCollection`; the root component's name
  cannot be set (it follows the document); a Join whose profile touches nothing
  makes a second body regardless of the operation, so order joins so each one
  touches (the ring had to be built hub → spokes → band); an annulus profile is
  the one with `profileLoops.count == 2`.

### Two measurements the model surfaced

- **`print3d.py`'s `GEO` is not the serpentine written up in CLAUDE.md.** Its
  2026-08-08 `__ct.dump()` traces **82.4″ of scale** over ext 0–15.5; CLAUDE.md's
  recorded serpentine numbers trace exactly **58.0″**, matching that document.
  Both were computed with the same solver. So the printed model — and now the
  Fusion model — is of a later tuning than the preset section describes. Nothing
  was changed; flagging it because the two documents currently disagree.
- **Parts swing off the plate edge over part of the stroke.** The plate is sized
  from the Q path + mounts + margin only, so nothing bounds where the other
  joints go. Joint centre plus link half-width, past the plate edge, over all
  141 poses:

  | joint | edge | past by | at ext |
  |---|---|--:|--:|
  | P | x+ | 31.27 mm | 9.30″ |
  | R | y− | 4.38 mm | 15.50″ |
  | D | x+ | 2.28 mm | 8.19″ |
  | B | y− | 1.96 mm | 15.50″ |

  The P overhang carries the 44 mm sleeve, so that column is cantilevered in
  mid-air for a stretch of the stroke. Not a collision and not a transcription
  error — it is what the generator produces — but it is the one thing a viewer
  will notice, and widening `plate_2d` to bound the joint traces (as
  `buildBBox` already does on the page) would fix it. **Unresolved; owner's
  call.** By contrast the ring's outer edge exactly reaches the plate's top edge
  at mid-stroke (0.000 mm), which is `MARGIN + POST_OD/2 = RING_OUT` by
  construction.

### Method note

`numpy`/`shapely`/`trimesh` are not installed on this machine, so the 141-point
Q path needed for the ridge could not come from `print3d.py`. Rather than
install, `pose()` was reimplemented in pure Python from CLAUDE.md's description
and **validated against all 18 published checkpoint values to 0.6 µm** before
use. Verification throughout was by driving the live Fusion document and reading
occurrence transforms back, the same pattern as the page's headless tests.
