# Kinetic Thermometer — Outdoor Garden Sculpture

## What this project is

An outdoor kinetic sculpture that displays temperature. A linear actuator
(driven by a temperature controller — designed in `controller/DESIGN.md`) pushes a bell
crank, which drives a chain of two four-bar linkages. The temperature
indicator is the **coupler point of the second four-bar** — it rides a
non-linear, spline-shaped path. The engraved temperature scale on the
sculpture IS that coupler curve, with tick marks at equal temperature steps
(which are therefore *unequally* spaced along the curve — intentional; part
of the "how does it work?" fascination for viewers).

`index.html` is the interactive design simulator (single self-contained
file, no dependencies, open in any browser). `mobile.html` is the same tool
laid out for a phone in portrait — see "Two pages, one shared core" below.
`ik-demo.html` is an earlier unrelated FABRIK inverse-kinematics demo kept
for reference.

## Hardware constraints (from the owner)

- **Three selectable actuator types** — two since 2026-08-02 (branch `joyce`),
  the third since 2026-08-23 (branch `feature/fixed-actuator`) — chosen by
  `geo.actT` and the "Actuator type" select in the Actuator drive section:
  - **0 = generic pin-to-pin**: retracted length `geo.aLmin` + stroke
    `geo.aStroke`, editable fields, defaults **24″+18″ = 42″ extended** (the
    original assumed hardware). Old saves and both presets mean this.
  - **1 = Joyce QS11940** — the actuator the owner actually owns. Rear mount
    is a split clamp sliding on the Ø2″ tube; its pivot pin sits **2.378″ off
    the tube centerline** (offset clamp). Driven length =
    `√((aClamp+ext)² + off²)`. `geo.aClamp` = c0 = pivot→rod-pin at full
    retraction, adjustable 3.48–24.66″ (drag the tube tail or type it),
    default 23.23″ = as modeled. Stroke **exactly 16″**. All dimensions in
    the `JOYCE` const were MEASURED from the owner's Fusion model
    ("Joyce QS11940 Linear Actuator") via the Fusion MCP link — see
    FABRICATION.md's table and images/joyce-*.png. They are real, not
    placeholders. `JOYCE.side` (pivot ear side) is still a mounting choice.
  - **2 = fixed in the post** — the actuator clamped RIGID so it can be hidden
    inside the mounting post. It cannot rock, so a con-rod `geo.aCon` links the
    rod tip to the crank pin R: a slider-crank. The tip runs along a fixed axis
    `geo.aDir` (degrees) out of the base pin at `(dA, anch)` — the same mount the
    other two types use, reinterpreted, exactly as joyce reinterprets it as the
    clamp pivot — at `geo.aLmin + ext` along it. `geo.aBr` picks the branch, like
    `s1`/`s2`. Retracted length and stroke are the generic `aLmin`/`aStroke`
    fields. **The curve is unaffected**: Q is a function of the crank angle
    alone, so any drive sweeping the same window traces the same engraved scale —
    what changes is where the °F marks land on it. Full rationale, the
    feasibility numbers and the fabrication cost (a guided carriage at the rod
    tip; the screw must not take side load) are in **FIXED-ACTUATOR.md**.
- The usable slice of stroke is configurable ("excursion min/max" fields,
  inches of extension, capped at the selected actuator's stroke) so the build
  can avoid end-stops.
- Large freestanding garden piece; the serpentine preset's overall envelope
  is **40.7″ × 30.8″** square-on for the current serpentine — the path, every
  swept joint, and all four mounts. At the 110° default view it reads
  32.5″ × 43.3″. Measured, not aspirational; re-check after any geometry
  change. (Earlier designs read 37″ × 19″ and 33.6″ × 19.3″.)

## Design requirements established so far

1. Drive: actuator → bell crank (law of cosines triangle: anchor distance
   dA, crank radius rA; must satisfy |dA−rA| < lenOf(extMin) and
   dA+rA > lenOf(extMax) with margin or the triangle can't close somewhere
   in the stroke — for the default generic actuator that is the original
   |dA−rA| < 24 and dA+rA > 42).
2. Two chained four-bars; indicator = stage-2 coupler point Q.
3. **Fabrication rule:** every fixed mount (actuator anchor, bell-crank
   pivot O2, rocker grounds O4 and O6) keeps ≥2.5″ clearance from the path.
   The companion rule — that no straight segment between two mounts may
   cross the path — was DROPPED by the owner on 2026-07-19. Mounts may now
   sit on either side of the path. Both search_geometry.py and
   analyze_geometry.py stopped enforcing/reporting it.
4. The owner's chosen design is the **Serpentine** preset (S-curve with
   end hook), since hand-tuned — see the preset section. Grand Arc is the
   alternate. The original presets were found by random search
   (~10^5–10^6 trials) in Python subject to: assembles across full stroke
   with margin, every temperature step moves visibly (min segment 0.15″,
   max 2.2″, speed ratio ≤7), genuine curvature, and the clearance rule
   above (the search originally also enforced the dropped crossing rule).
5. Coordinate system: O2 (bell-crank pivot) is the origin. Angles in the
   `anch` param are degrees. Canvas y is down (screen), math is consistent
   throughout — don't "fix" the sign.

## Preset geometries (inches, O2-origin)

Serpentine (CHOSEN; `serpentine` in `PRESETS`) → 82.5″ of scale (measured 2026-11-22).
Excursion 0–15.5″ (not 0–17″ — see the ceiling below).

Owner-tuned by dragging, second round, 2026-07-19. Superseded the first
tuned version (dA=29.15 anch=-145.97 L3=10.4 L4=9.6 cv2=3.6 → 41.4″), which
had a cusp at 70°F where the indicator stalled to 0.056″/°F — a dead spot at
typical ambient. This one moves that slow region out to the cold end.

Measured against the original search constraints — it does NOT satisfy them,
same as its predecessor. Recorded honestly so nobody re-derives it:

- 10°F steps run 0.79″ (−20..−10) to 16.36″ (100..110): max-segment rule
  (≤2.2″) and speed-ratio rule (≤7×, actual 20.7×) both exceeded.
- Slowest 1°F step 0.073″ at −17/−18°F, below the 0.15″ min-segment rule.
- Not monotonic: the scale expands to 13.7″ per 10°F at 60–70°F, slows to
  3.0″ at 80–90°F, then expands hard. Sharpest turn is 63° at 85°F.
- **Mount rule (fabrication rule 3) is violated.** O2 clears the curve by
  only 2.06″ (rule: ≥2.5″); O4, O6 and ACT clear it. This is a
  build blocker, not an aesthetic call — unresolved as of this writing.
- Re-measured 2026-11-22 with `tools/analyze_geometry.py` (default 0–15.5″ excursion); re-run it rather than trusting these after any geometry change.
- **Actuator ceiling (GENERIC type): dA+rA=40.25″**, so the drive triangle
  stops closing past ~15.75″ of extension. That is why extMax is 15.5 and
  not 17. The controller must never command past 15.5″ or the linkage jams
  against a pose it cannot reach. ~0.25″ of slack — re-check this if dA, rA,
  or the excursion is touched. **On the Joyce type this ceiling is retired**:
  at the as-modeled clamp position (aClamp=23.23) the driven length runs
  23.35–39.30″ over the full 16″ stroke, inside the window with 0.45″ spare —
  asserted by verify_export.py. Sliding the clamp changes it; re-check.

`tools/analyze_geometry.py <dump.json>` re-runs all of the above against a
`__ct.dump()` capture.

**Serpentine, fixed actuator** (`serp-fixed`) proves the drive swap costs the curve nothing — not a build candidate. Numbers in FIXED-ACTUATOR.md; `verify_export.py` §14 re-measures them.

Grand Arc (`grandarc`) is the alternate, 56.0″ of scale (measured 2026-11-22).

**Gallery presets** (`example-*`, `clean-*`, `shape-*`, all Joyce, none a build candidate) and how the design search found them: `tools/CLAUDE.md`. Standing rules: the shape-* family is COMPLETE at six — don't extend it; don't renumber the presets; **check |rA−L2| on any new design** (B and R pivot holes merge below ~24 mm at full size).

**The Joyce rod end is metric (Ø12 mm pin) and dictates the crank** — single-sided crank, single-shear R pin; dimensions and the rod-fouling fix in FABRICATION.md / REPORT.md.

Tool usage (search, verify, explore, the `--batch` memory limit) and the shape-novelty metric: `tools/CLAUDE.md`.

## How the solver works (index.html, ~pose())

Steps 1–2 (temp → extension → driven length → crank angle th) are
`extAt()` / `lenOf()` / `pose()`; read them there. What the code does not say:

2b. **actT 2 (fixed) solves th differently and that is the whole trick.**
   `tipOf(ext)` puts the rod tip on the fixed axis; `pose()` then crosses the
   con-rod circle (aCon about the tip) with the crank circle (rA about O2) —
   `circInt`, the same function the chain uses, branch `geo.aBr` — and reads
   th off the intersection. `fixFits()` is the 0.5″-margin gate, the same
   figure `actFits()` keeps; failing it reports `why:'act'` like the others.
   `p.tip` is null on the rocking types, which is how the render, fitView,
   `buildComps` and `pivotPos` all skip the fixed-drive parts.
   **th is ALL the actuator produces** — step 3 onward is untouched, so the
   two drives are interchangeable at equal crank windows.
3. B = L2 at the same angle th — R and B are COLLINEAR on the crank arm by
   design. A two-arm bell crank (`bAng` between the arms) was built and
   REVERTED the same day (2026-08-02): on screen it read as the linkage
   splitting into a second four-bar and broke too easily. Instead, the R
   handle projects the cursor onto the arm's axis and slides ALONG it,
   range 2–30″ (slider and drag clamp both) — past B or in close to O2,
   but never off the line. Don't rebuild the V. (In actT 2 the con-rod
   absorbs the offset, so dragging R just sets rA, and the collinearity is a
   MODEL choice there, not a physical one — see FIXED-ACTUATOR.md "What it
   unlocks". The model still keeps them collinear.)
   C, P, D and Q follow by circle intersections in `pose()` (branches `s1`,
   `s2`); Q is the indicator.
4. If any intersection fails the pose is invalid.
   Deliberate decision: invalid parts simply aren't drawn (owner chose this
   over a failure-visualization overlay — "leave it").

## Two pages, one shared core (added 2026-07-31)

The owner asked for a mobile version and chose a **separate file** over a
responsive `index.html`, with **full editing parity minus the sliders** —
"rely more on user dragging, remove the placement and length sliders".

`mobile.html` is that page. To stop a 1500-line fork from rotting, the half
that must never differ is fenced in BOTH files:

```
// ==== SHARED CORE START ====      presets, kinematics, fitView, drawing,
...                                 ticks, bbox, DXF, save/load, UI wiring,
// ==== SHARED CORE END ====        undo, COMPINFO, buildComps, applyDrag
```

~1575 of each file's ~2200–2300 lines. **Edit the physics in `index.html`, then
run `python3 tools/sync_core.py --apply`.** `--check` (the default) fails on
any drift and is part of verification. Anything page-specific — hit radii,
gestures, tooltips, the sheet, resize, `__ct` — lives BELOW the END marker
and is meant to differ.

Three things had to move into the core to make this work, and they matter:

- **`VIEWINSET`** replaced `fitView`'s hardcoded `leftEdge=(W>640)?318:24`.
  Each page declares in its prelude how much canvas its UI covers: desktop
  `{left:318|24, bottom:0}`, mobile `{left:0, bottom:peekH}` in portrait and
  `{left:312, bottom:0}` in landscape. `fitView` itself is now identical in
  both. Mobile MEASURES `peekH` from the collapsed sheet in `resize()` rather
  than trusting the CSS constant — the safe-area inset is device-specific.
- **`applyDrag(name, w)`** — the ~50 lines of per-handle geometry mutation,
  lifted out of the desktop's pointermove handler. Its clamps are the same
  numbers as the desktop sliders' min/max, and **on mobile they are the only
  thing bounding the geometry**, since the sliders are gone. Keep them in step.
- **The geometry-slider wiring is null-guarded.** `syncSliders` and the
  `GEOKEYS.forEach` binding loop both `return` on a missing element, so the
  same core runs in a page with no sliders. `updGeoUI` already did.

### What mobile.html does differently

The owner's mobile decisions (sheet, toolbar, gestures, hit radii, drag speed) are in `docs/mobile-ui.md`. Read it before editing below mobile.html's END marker; the standing don'ts are under "UI behaviour" below.

## UI behaviour — read before changing either page

The full decision log for every built feature (actuator-type UI, drag handles, drag-regions overlay, undo, Reset, zoom/pan/rotate, path divisions, label thinning, bounding box, saves, DXF export) is in `docs/ui-decisions.md`; mobile-only behaviour is in `docs/mobile-ui.md`; settled reverts are in TODO.md "Settled — do not redo". Read the relevant section before touching that feature. The owner's standing "don'ts":
- Don't rebuild the drag validity gate — drags are free-form; the "Drag regions" overlay only advises.
- Don't reintroduce a drop shadow, tick strokes, or 1° sub-ticks. Divisions cut ACROSS the path; only 10° labels are drawn.
- The DXF never thins labels; the screen does. That is the one allowed screen/DXF disagreement.
- `rotRad()` is the only place the rotation sign is negated — never a bare `cfg.rot*DEG`. Verify drags MID-drag; release refits and hides bugs.
- tickList positions come from `pose()`, not the 140-sample path, and carry the normal's side forward across cusps. Don't "simplify" either.
- Nothing auto-restores on load except `geo.actT` (`couplerThermometer.actT`).
- Mobile: no geometry sliders (`verify_mobile.py` asserts the id-set difference); `?` stays at the left end of the toolbar; `⟲` stays tinted `--warn` next to undo; a collapsed sheet shows only the pill — don't put the tiles back without asking; range inputs keep `touch-action:pan-y`.

## Verification pattern used throughout

Headless Chromium via Playwright (`executablePath` may need adjusting per
machine). Every feature was verified by driving the page: dispatch real
`input`/`change` events, drag with mouse.move/down/up, reload for
persistence tests, screenshot and inspect. Keep doing this for changes.

**After any change, run all three:**

```
python3 tools/verify_export.py     # index.html, the full desktop suite
python3 tools/sync_core.py         # the two pages' cores are identical
python3 tools/verify_mobile.py     # mobile.html on a 390x844 phone viewport
```

`tools/dxf.py` and the Playwright gotchas `verify_mobile.py` depends on: `tools/CLAUDE.md`.

## Known open items / next steps

Open work is tracked in **TODO.md**; fabrication measurements and the DXF layer reference in **FABRICATION.md** — update those, not this file. Land one change at a time: a five-change bundle was once reverted because the owner couldn't see the wanted change through the unwanted ones. Exports read the CURRENT geo, and the chosen Serpentine still violates the original constraints — re-confirm before cutting metal.

## Owner preferences observed

- Iterative, hands-on; tests features immediately and reports precisely.
- Wants fabrication realism (mount clustering, real actuator envelope).
- Prefers honest behavior over hand-holding (kept the parts-disappear
  behavior when linkage can't assemble).
- Mobile user in this phase; keep touch interactions working.
