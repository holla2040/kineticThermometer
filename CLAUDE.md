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
- Large freestanding garden piece; the serpentine preset spans roughly 4–5 ft.

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
   end hook). Grand Arc is the alternate. Both were found by random search
   (~10^5–10^6 trials) in Python subject to: assembles across full stroke
   with margin, every temperature step moves visibly (min segment 0.15″,
   max 2.2″, speed ratio ≤7), genuine curvature, and the mount rule above.
5. Coordinate system: O2 (bell-crank pivot) is the origin. Angles in the
   `anch` param are degrees. Canvas y is down (screen), math is consistent
   throughout — don't "fix" the sign.

## Preset geometries (inches, O2-origin)

Serpentine (CHOSEN): rA=12.8 dA=33.1 anch=-127.2° | stage1: gx=12.9 gy=-6.0
L2=11.4 L3=11.2 L4=9.6 cu=3.5 cv=11.3 s1=-1 | stage2: ox=8.1 oy=-12.0
L5=5.9 L6=14.0 cu2=14.6 cv2=3.6 s2=-1  → 37″ of scale, ~6.8× speed ratio.

Grand Arc: rA=20.8 dA=31.7 anch=166.7° gx=-3.8 gy=-0.1 L2=11.9 L3=11.8
L4=12.6 cu=19.6 cv=-5.2 s1=-1 ox=7.7 oy=-7.6 L5=8.5 L6=13.5 cu2=19.3
cv2=-12.0 s2=-1  → ~66″ of scale.

`tools/search_geometry.py` reproduces the constrained random search.

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
- Public view: uncheck "Show mechanism" — only scale + indicator bead.
- Debug hook for tests: `window.__ct` = {pivotScreen(name), geo, cfg}.

## Verification pattern used throughout

Headless Chromium via Playwright (`executablePath` may need adjusting per
machine). Every feature was verified by driving the page: dispatch real
`input`/`change` events, drag with mouse.move/down/up, reload for
persistence tests, screenshot and inspect. Keep doing this for changes.

## Known open items / next steps

1. **Fabrication document** (owner has asked for this "when design is
   final"): dimensioned drawing data — mount coordinates on a common frame,
   link lengths, coupler-plate geometry (B/C/P and P/D/Q triangles with
   cu/cv offsets), actuator mounting triangle, pivot hardware suggestions,
   plus the temp→extension calibration table for the controller.
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
