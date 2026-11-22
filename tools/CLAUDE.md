# `tools/` — notes for Claude

Moved from the root `CLAUDE.md` on 2026-11-22. The root's "After any change, run all three" still applies.

## Gallery presets and the design search

**Gallery presets.** Three families, all Joyce (`actT:1`), all found by
`tools/explore_designs.py`, none offered as a build candidate:

- `example-00`…`example-10` (2026-08-03) — the length search. All eleven ride
  dead center, 0.06°–5.9° minimum transmission angle, marked `*` in the menu.
- `clean-01`, `clean-03`, `clean-07` (2026-08-04) — the same search under
  `--tamin 40`. No `*`. The run emitted ten; the owner kept these three and cut
  the other seven as **variations on two shapes** — `clean-00..04` were one theme
  and `clean-05..09` another, and 03 and 04 were effectively the same curve.
- `clean-10`…`clean-14` (2026-08-04, same day) — a second run that also had to
  clear `--novelty 7.0` against all ten of the first run plus serpentine and
  Grand Arc. At least 7.3 from every earlier shape and at least 11.0 from each
  other, where the two original families sit 6.3 apart at their closest.
- `shape-01`, `shape-02` (2026-08-03) — SEARCH-PLAN step 1's answer: seeded
  `score_ta` climbs FROM example-08 / example-00 (`--seedfrom --target
  --targetdist 2`), climbing transmission angle while a shape penalty held the
  curve. 13.1° / 16.7° at shape distance 2.0 from their seeds — the owner kept
  these two of twelve candidates and rejected the rest as lookalikes (see
  REPORT.md for the frontier: the shape survives to ~33° at family distance,
  never to 40°). Labels are page-measured at 0–15.5″: 81″ / 138″.
  **shape-01 was respaced on 2026-08-09** and no longer matches the numbers the
  search produced. As found, B and R sat |rA−L2| = **0.1286″** apart on the crank
  arm. That spacing is a **RATIO** — 1.1% of the crank radius — so it is not a
  print-resolution problem and no uniform scaling fixes it: at full size the gap
  is 3.27 mm, and the two pivot holes merge into one slot.
  rA/L2 went 11.2952/11.4238 → **11.0550/12.0000**, opening the gap to
  **0.9450″ = 24.0 mm**. That number is set by METRIC hardware (see the actuator
  note below), not by the hole geometry: 24 mm clears an M12 hex head at R
  against an M12 hex nut at B with a plain washer under each. Chosen by search
  to minimise curve change: 3.7″ max, 2.2″ mean, on a 33″ envelope. Side effects,
  recorded in the label and verify_export §13: transmission angle 13.1° →
  **16.5°** (safer, not worse) and scale 88″ → 81″. Nothing downstream of the
  crank moved. **Check |rA−L2| on any new design** — 7 of the 25 shipped presets
  fail it at bench scale and 3 still fail at full size.
- `shape-03`…`shape-06` (2026-08-03, later the same day) — the REVERSE
  pipeline: abstract curves drawn first (`tools/propose_shapes.py`, novelty
  ≥7 vs everything shipped), owner picked five; `--targetpts --objective
  match` found each drawing's closest mechanism curve, then ta-lift ladders
  walked each match toward safety. The owner picked these four off the tagged
  verdict sheet (tiles #4, #7, #11, #14) at their stated 6° criterion:
  7.5° / 6.9° / 14.0° / 25.3°, labels 71″/43″/35″/36″ page-measured at
  0–15.5″. Two things this settled, recorded in REPORT.md: a drawn wild shape
  is always MATCHED at dead center and buying safety costs shape drift at a
  measured rate; and two of the five picked drawings (prop-11's double
  spiral, prop-08's grand ribbon) are beyond this mechanism outright.
  **The family is COMPLETE at six** (owner, 2026-08-03) — don't extend it.
  NOT clean — none reaches 40°; `verify_export.py` §13 pins each preset's
  angle to its label value ±0.5° inside [6°, 40°).


The six clean: 40.0°–50.1°, scale 55″–111″, mount clearance 2.89″–10.37″ (all
clear the 2.5″ rule the serpentine misses; the six shape-* clear it too at
2.6″–9.4″). Numbering is deliberately non-contiguous — the names are the ones
the owner picked by, so don't renumber them.

**A wrong finding, recorded so it is not re-derived:** the first run's output made
it look like loops and cusps simply ARE the singularity and vanish above 40°.
They do not. That was an artefact of a length-maximising objective, which does not
go looking in that part of the space. Under a novelty objective the same gate
returns curves crossing themselves 1–3 times at 40°–53°. Loops cost even movement,
not safety: the self-crossing designs are the slowest of the kept six at 0.074″ and
0.092″/°F against clean-01's 0.50″ — but the ranges overlap, since loop-free
clean-07 also stalls to 0.092″ (the serpentine itself is 0.075).

Still true: 94% of assemblable random geometries clear 10°, but 2.4M random trials
produced ZERO at 40° with a 70″ scale, so the clean set exists only because the
hill climb reaches it. Don't retry this with random sampling.

**Shape novelty** (`--avoid FILE --novelty N`) reduces each curve to its turning
function — turn per unit arc at `SHAPE_K` equal-arc stations — and requires a
minimum distance from every shape in the avoid file. Two things there are measured,
not chosen: `SHAPE_K=10` is the coarsest resolution that still reproduces the
owner's own two-family grouping (by K=12 within-family spread exceeds cross-family,
because it starts measuring local wiggle), and the descriptor compares INCREMENTS
because reversing a cumulative turning profile is not an isometry — that version's
distance was asymmetric. `--selfcheck` asserts symmetry and the invariances.

## Search, verify and explore tools

`tools/search_geometry.py` reproduces the constrained random search.
`tools/verify_export.py` drives the page headless and checks the named-save
flow plus both DXF exports (`python3 tools/verify_export.py [outdir]`).

`tools/explore_designs.py` measures the transmission angle at C and D exactly as
index.html's `transAngle()` does; `crosscheck_port.py` asserts the two agree to
1e-9 along with the path itself. Gates are `--tamin`, `--minlen` and
`--character BOTH REV WIG`. **Watch `--batch`**: peak RSS is roughly
`batch × nsamp × 8 × 25` bytes, so the old 60k default was >3 GB per process and
eight in parallel OOM'd this machine on 2026-08-04. Default is now 12k.

## The `window.__ct` test hook

- Debug hook for tests: `window.__ct` = {pivotScreen(name), geo, cfg, pose,
  pan, zoom, rotPt, screen (=TX), dir (=rotDir), rebuild(), ticks, chunks,
  bbox, pathJ, undoDepth(), buildParts(), buildPoints(),
  lenOf(ext), extAt(t), strokeOf(), actGeom(p,t), JOYCE, dump()}. mobile.html
  adds {peek, sheetOpen, setSheet(), pick(x,y,type)}. The builders return DXF
  text so tests can assert on the export without a download. `dump()` returns
  geo+cfg as JSON — this is how the owner hands over a hand-tuned design:
  `copy(__ct.dump())` in the console.

## verify scripts

`tools/dxf.py` holds the shared DXF reader — its own module because
`verify_export.py` runs its whole suite at import time.

Two things `verify_mobile.py` has to do that the desktop one does not, both
worth knowing before you edit it:

- Playwright's touchscreen API taps only; it cannot express a pinch or tag a
  drag with a `pointerType`. It dispatches raw `PointerEvent`s instead.
- Those carry pointer ids that are not real active pointers, so
  `setPointerCapture` throws `NotFoundError`. `ready(pg)` stubs it out after
  every load — call it after every `reload()`, along with stopping the sweep.

## Other tools (each file's docstring has the detail)

- `benchmodel.py` — dependency-free port of print3d.py's level search + fastener policy.
- `export_trace.py` — export a design from the page as a trace: geometry plus sampled kinematics.
- `make_diagrams.py` — generates the SVG diagrams the README's dead-center section uses.
- `print3d.py` — 3D-printable benchtop model of the default (serpentine) design; output in `print/` (see `print/PRINT.md`).
- `render_designs.py` — screenshots each design in `designs.json` through index.html.
- `sensitivity.py` — what each drag handle actually does to the design.
- `propose_shapes.py` — proposes abstract scale-curve shapes before any linkage exists.
