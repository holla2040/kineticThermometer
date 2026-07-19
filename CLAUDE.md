# Kinetic Thermometer — Outdoor Garden Sculpture

## What this project is

An outdoor kinetic sculpture that displays temperature. A linear actuator
(driven by a temperature controller, not part of this repo) pushes a bell
crank, which drives a chain of two four-bar linkages. The temperature
indicator is the **coupler point of the second four-bar** — it rides a
non-linear, spline-shaped path. The engraved temperature scale on the
sculpture IS that coupler curve, with tick marks at equal temperature steps
(which are therefore *unequally* spaced along the curve — intentional; part
of the "how does it work?" fascination for viewers).

`index.html` is the interactive design simulator (single self-contained
file, no dependencies, open in any browser). `ik-demo.html` is an earlier
unrelated FABRIK inverse-kinematics demo kept for reference.

## Hardware constraints (fixed, from the owner)

- Linear actuator: **24″ retracted, 18″ stroke, 42″ extended** (pin-to-pin).
  These are hard physical constants — `ACT={lmin:24, stroke:18}` in the code.
- The usable slice of stroke is configurable ("excursion min/max" fields,
  inches of extension 0–18) so the build can avoid end-stops.
- Large freestanding garden piece; the serpentine preset's overall envelope
  (scale curve plus all four mounts) is roughly 37″ × 19″.

## Design requirements established so far

1. Drive: actuator → bell crank (law of cosines triangle: anchor distance
   dA, crank radius rA; must satisfy |dA−rA| < 24 and dA+rA > 42 with margin
   or the triangle can't close somewhere in the stroke).
2. Two chained four-bars; indicator = stage-2 coupler point Q.
3. **Fabrication rule:** all four fixed mounts (actuator anchor, bell-crank
   pivot O2, rocker grounds O4 and O6) must sit on ONE side of the scale —
   formally: every mount keeps ≥2.5″ clearance from the curve, and the
   straight segment between any two mounts never crosses the curve.
4. The owner's chosen design is the **Serpentine** preset (S-curve with
   end hook), since hand-tuned — see the preset section. Grand Arc is the
   alternate. The original presets were found by random search
   (~10^5–10^6 trials) in Python subject to: assembles across full stroke
   with margin, every temperature step moves visibly (min segment 0.15″,
   max 2.2″, speed ratio ≤7), genuine curvature, and the mount rule above.
5. Coordinate system: O2 (bell-crank pivot) is the origin. Angles in the
   `anch` param are degrees. Canvas y is down (screen), math is consistent
   throughout — don't "fix" the sign.

## Preset geometries (inches, O2-origin)

Serpentine (CHOSEN): rA=12.8 dA=29.15 anch=-145.97° | stage1: gx=12.9 gy=-6.0
L2=11.4 L3=10.4 L4=9.6 cu=3.5 cv=11.3 s1=-1 | stage2: ox=6.30 oy=-16.71
L5=5.9 L6=14.0 cu2=14.6 cv2=3.6 s2=-1  → 41.4″ of scale, ~32× speed ratio.

Owner-tuned by dragging on 2026-07-19; replaced the earlier search result
(dA=33.1 anch=-127.2 L3=11.2 ox=8.1 oy=-12.0 → 37″, 6.8×). Assembles over
the full excursion (0–17″), but note it does NOT satisfy the original search
constraints: 10°F steps run 1.38″ (at 0–10°F) to 8.07″ (at 80–90°F), so both
the 2.2″ max-segment and ≤7× speed-ratio rules are exceeded. Accepted as a
deliberate aesthetic choice, not a search product — re-confirm before
generating fabrication output.

Grand Arc: rA=20.8 dA=31.7 anch=166.7° gx=-3.8 gy=-0.1 L2=11.9 L3=11.8
L4=12.6 cu=19.6 cv=-5.2 s1=-1 ox=7.7 oy=-7.6 L5=8.5 L6=13.5 cu2=19.3
cv2=-12.0 s2=-1  → ~66″ of scale.

`tools/search_geometry.py` reproduces the constrained random search.
`tools/verify_export.py` drives the page headless and checks the named-save
flow plus both DXF exports (`python3 tools/verify_export.py [outdir]`).

## How the solver works (index.html, ~pose())

1. temp → fraction of scale (optionally reversed via `tdir`) → extension
   within [extMin, extMax] → pin-to-pin length l ∈ [24+extMin, 24+extMax].
2. Crank angle th = anch + acos((dA²+rA²−l²)/(2·dA·rA)).
3. B = L2 at angle th. C = circle-circle intersection of (B, L3) and
   (O4, L4), branch sign s1. P = B + cu·û + cv·perp(û) where û is unit BC.
4. D = intersection of (P, L5) and (O6, L6), branch s2. Q = P + cu2·v̂ +
   cv2·perp(v̂) where v̂ is unit PD. Q is the indicator.
5. If any intersection fails → pose invalid; the range-level warning in the
   panel distinguishes actuator-triangle failure from chain failure.
   Deliberate decision: invalid parts simply aren't drawn (owner chose this
   over a failure-visualization overlay — "leave it").

## UI features already built (don't regress these)

- Presets dropdown (serpentine / grandarc / custom), Reset preset.
- Temperature reading slider + numeric Scale min/max °F fields (≥10° span).
- Reverse scale checkbox (retract = hot). Excursion min/max fields (≥1″).
- Auto-cycle with speed slider **0.05×–1×**; **spacebar toggles** auto-cycle
  globally (guarded so focused buttons don't re-fire; resumes from current
  temperature via phase sync — see syncDemoPhase()).
- Draggable canvas handles: all 4 mounts AND all joint pins (R sets rA,
  B sets L2, C sets L3+L4, P sets cu/cv, D sets L5+L6, Q sets cu2/cv2).
  View refit is suppressed during drag; sliders track live; any edit
  switches preset to "custom".
- Hover: component highlight + tooltip naming the part + its sliders, and
  the matching slider rows highlight in the panel (COMPINFO / hlSliders).
- Collapsible <details> sections for Stage 1 / Stage 2 / Actuator drive.
- Scale ticks every 10° labeled, 5° minors. "Inner curves" checkbox traces
  all four moving joints (B, C, P, D) as dashed paths.
- Settings persist to localStorage key `couplerThermometer.v2` (guarded
  try/catch — degrades to in-memory where storage is blocked). Save /
  Clear saved buttons; auto-restore on load.
- **Named designs**: type a name before Save and it also goes into the map
  under `couplerThermometer.saves`; the "Load a saved design…" dropdown
  restores one, Delete removes the named entry. Saving with the name field
  empty still updates the auto-restore slot. "Clear saved" only clears
  auto-restore — it leaves named designs alone.
- **DXF export for Fusion** (two buttons, R12 ASCII, inches, y flipped to
  CAD convention). `showSaveFilePicker` gives a real Save dialog where the
  browser has one, else it falls back to an `<a download>`:
  - *Parts DXF* — the 5 fabricated links, each flat in its own local frame
    on its own layer (CRANK / PLATE1 / ROCKER1 / PLATE2 / ROCKER2), laid
    out side by side without overlap. Outline = convex hull of equal-radius
    circles at each hole (offset edges + corner arcs), so 2-hole links come
    out as capsules and 3-hole plates as rounded triangles. Driven by the
    "Pivot hole ⌀" and "Link width" fields (`cfg.hole` / `cfg.lwid`).
  - *Points DXF* — the assembly frame: scale curve as line segments, 5°/10°
    ticks with °F labels, the 4 mounts, and POINT entities at every 10°
    tick and mount to snap to.
  Curves are line segments, not splines — fit a spline in Fusion if wanted.
- Public view: uncheck "Show mechanism" — only scale + indicator bead.
- Debug hook for tests: `window.__ct` = {pivotScreen(name), geo, cfg,
  buildParts(), buildPoints()} — the two builders return DXF text, so tests
  can assert on the export without going through the download.

## Verification pattern used throughout

Headless Chromium via Playwright (`executablePath` may need adjusting per
machine). Every feature was verified by driving the page: dispatch real
`input`/`change` events, drag with mouse.move/down/up, reload for
persistence tests, screenshot and inspect. Keep doing this for changes.

## Known open items / next steps

1. **Fabrication document** (owner has asked for this "when design is
   final"): the DXF export now covers the drawing side — link outlines and
   mount coordinates on a common frame. Still missing: pivot hardware
   suggestions, actuator mounting-triangle detail, and the temp→extension
   calibration table for the controller. Note the exports read the CURRENT
   geo, and the chosen Serpentine preset still violates the original search
   constraints (see the preset section) — re-confirm before cutting metal.
2. **.linkage2 export** — write the chosen geometry as XML for David
   Rector's Linkage program (Windows; blog.rectorsquid.com). Not started.
3. Unresolved question: owner once asked for "beginning and ending point
   control for actuator"; clarification returned "no preference". The
   excursion fields may already satisfy it. Re-confirm before building
   anything (candidates were: XY fields for actuator mounts, absolute
   length endpoints, or crank start/end angles).
4. Possible polish: auto-thin tick labels where the non-linear scale
   crowds them (owner was told this is available on request).
5. Real-world drive: temperature sensor → controller → actuator position;
   the sim's temp→extension mapping (linear within excursion, optional
   reverse) is the spec the controller must implement.

## Owner preferences observed

- Iterative, hands-on; tests features immediately and reports precisely.
- Wants fabrication realism (mount clustering, real actuator envelope).
- Prefers honest behavior over hand-holding (kept the parts-disappear
  behavior when linkage can't assemble).
- Mobile user in this phase; keep touch interactions working.
