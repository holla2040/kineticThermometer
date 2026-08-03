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
file, no dependencies, open in any browser). `mobile.html` is the same tool
laid out for a phone in portrait — see "Two pages, one shared core" below.
`ik-demo.html` is an earlier unrelated FABRIK inverse-kinematics demo kept
for reference.

## Hardware constraints (from the owner)

- **Two selectable actuator types** since 2026-08-02 (branch `joyce`), chosen
  by `geo.actT` and the "Actuator type" select in the Actuator drive section:
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

Serpentine (CHOSEN): rA=12.8 dA=27.3506 anch=-135.3211° | stage1: gx=12.9
gy=-6.0 L2=11.4 L3=7.7705 L4=7.0142 cu=3.5 cv=11.3 s1=-1 | stage2: ox=6.30
oy=-16.71 L5=5.9 L6=14.0 cu2=14.665 cv2=9.6354 s2=-1  → 58″ of scale.
Excursion 0–15.5″ (not 0–17″ — see the ceiling below).

Owner-tuned by dragging, second round, 2026-07-19. Superseded the first
tuned version (dA=29.15 anch=-145.97 L3=10.4 L4=9.6 cv2=3.6 → 41.4″), which
had a cusp at 70°F where the indicator stalled to 0.056″/°F — a dead spot at
typical ambient. This one moves that slow region out to the cold end.

Measured against the original search constraints — it does NOT satisfy them,
same as its predecessor. Recorded honestly so nobody re-derives it:

- 10°F steps run 1.02″ (−20..−10) to 10.95″ (100..110): max-segment rule
  (≤2.2″) and speed-ratio rule (≤7×, actual 10.8×) both exceeded.
- Slowest 1°F step 0.089″ at −20°F, below the 0.15″ min-segment rule.
- Not monotonic: the scale expands, then slows at 40–50°F and again at
  80–90°F, then expands hard. Sharpest kink is a 65° turn at 48°F.
- **Mount rule (fabrication rule 3) is violated.** O6 clears the curve by
  only 0.97″ and O2 by 2.41″ (rule: ≥2.5″), and four mount-to-mount lines
  cross the scale: O2–O4, O2–O6, O4–O6, O4–ACT. The curve now weaves
  between the mounts instead of staying on one side of them. This is a
  build blocker, not an aesthetic call — unresolved as of this writing.
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

Grand Arc: rA=20.8 dA=31.7 anch=166.7° gx=-3.8 gy=-0.1 L2=11.9 L3=11.8
L4=12.6 cu=19.6 cv=-5.2 s1=-1 ox=7.7 oy=-7.6 L5=8.5 L6=13.5 cu2=19.3
cv2=-12.0 s2=-1  → ~66″ of scale.

`tools/search_geometry.py` reproduces the constrained random search.
`tools/verify_export.py` drives the page headless and checks the named-save
flow plus both DXF exports (`python3 tools/verify_export.py [outdir]`).

## How the solver works (index.html, ~pose())

1. temp → fraction of scale (optionally reversed via `tdir`) → extension
   within [extMin, extMax] (`extAt`) → driven length l = `lenOf(ext)`:
   generic `aLmin+ext` pin-to-pin, joyce `√((aClamp+ext)²+JOYCE.off²)` from
   the clamp pivot to the rod pin. `strokeOf()` is the selected stroke.
2. Crank angle th = anch + acos((dA²+rA²−l²)/(2·dA·rA)). The fixed drive
   pivot (dA, anch about O2) is the rear pin for generic, the CLAMP pivot
   for joyce — pose() is identical either way. `actGeom(p,t)` adds the
   joyce tube frame (direction u, clamp foot F, tube front/rear) for the
   drawing, the hover seg and the tail drag handle; fitView includes the
   tube's swept body at both stroke extremes so the tail stays on screen.
3. B = L2 at angle th + bAng·DEG (`geo.bAng`, degrees, default 0 = the two
   crank arms collinear as originally). The bell crank is a real two-arm
   plate: R is the actuator arm (angle th solved by the triangle), B the
   coupler arm. Dragging B places it ANYWHERE on the plate (sets L2+bAng, B
   lands under the cursor); dragging R changes rA and auto-compensates bAng
   so B — and the whole chain — holds still (the attachment point is
   independent of the coupler pin, owner request 2026-08-02). The CRANK DXF
   part carries the bent arm with the same y-flip chirality as PLATE1's
   cu/cv. C = circle-circle intersection of (B, L3) and
   (O4, L4), branch sign s1. P = B + cu·û + cv·perp(û) where û is unit BC.
4. D = intersection of (P, L5) and (O6, L6), branch s2. Q = P + cu2·v̂ +
   cv2·perp(v̂) where v̂ is unit PD. Q is the indicator.
5. If any intersection fails → pose invalid; the range-level warning in the
   panel distinguishes actuator-triangle failure from chain failure.
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

~1050 of each file's ~1550 lines. **Edit the physics in `index.html`, then
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

- **No geometry sliders** — all 16 (`L2 L3 L4 gx gy cu cv L5 L6 ox oy cu2
  cv2 rA dA anch`) are gone; the 10 canvas handles set them. Kept: excursion
  min/max, both stage flips, rotation, temperature range, display toggles,
  presets, saves and both DXF exports. `verify_mobile.py` asserts the id-set
  difference against index.html EXACTLY, so a forgotten control and an
  over-eager deletion both fail.
- **Bottom sheet** (`#sheet`, `.peek` 44px / `.open` 72dvh) instead of the
  left panel; tap or drag the grab pill. The fit is pinned to the COLLAPSED
  height on purpose — opening must not make the drawing jump. In landscape a
  media query turns it into a 300px left drawer.
  Collapsed it shows **only the pill**: `.peek` drops the background, border
  and shadow, so the 44px strip is still there to be thumbed but nothing is
  painted over the drawing. The owner asked for this after seeing a 168px
  peek that carried the readout tiles and the reading slider — the numeric
  °F now lives behind the pill, and the ring on the path is what you read at
  a glance. Don't put the tiles back without asking.
- **`touch-action` sits on the canvas, not on `html,body`.** index.html's
  body-level `touch-action:none` is exactly what makes a scrolling panel
  impossible on a phone; the sheet body is `pan-y` with `overscroll-behavior:
  contain`.
- **Every range input is `touch-action:pan-y` as well**, and that one rule is
  load-bearing. A slider spans the full width of the sheet and claims the
  touch the moment a gesture starts on it, so scrolling the sheet dragged
  whichever slider the thumb crossed. `pan-y` hands vertical movement back to
  the scroller and leaves the slider only the horizontal — the one direction
  that ever meant to move it. It must sit on the input; `#sheetbody`'s own
  `pan-y` does not reach it. The test asserts the computed value on all three,
  because touch-action is enforced by the compositor and synthetic pointer
  events bypass it — the mechanism is what can be checked, and the mechanism
  is the fix.
- **Gestures**: a `Map` of live pointers. Two fingers = pinch + two-finger
  pan, anchored on the midpoint, and it outranks any in-flight drag. Double
  tap (<320ms, <40px, and only if the release didn't move) recentres.
  `zoomAt(sx,sy,f)` is shared by pinch and wheel.
- **Hit radius 30px for a non-mouse pointer**, 20 for a mouse. Note the real
  constraint: at 1× the whole 40″ piece is ~270px wide, so the joint pins sit
  **~10px apart** and a fingertip covers several. Nearest-wins picks
  something sensible, but picking a SPECIFIC joint means pinching in first —
  at 12× they are ~126px apart. The help text says so and the test asserts it.
  This is geometry, not a bug to fix.
- **The drag tooltip carries VALUES, not slider names** — `gx 9.7″  gy −3.4″`,
  pinned to the top of the canvas because your finger is on the part. It
  reuses `COMPINFO[id].sliders` as a parameter list through `fmtGeo`. With the
  sliders gone this is the only place those numbers appear live.
- **Floating toolbar: ONE ROW across the top** — `?` at the far left (pushed
  there by `margin-right:auto`), then `▶/⏸ ↶ ⟲ ⌖` at the right. Settled by the
  owner on 2026-08-01, after a right-hand column and a help button inside the
  sheet were both tried and rejected. Things that are load-bearing here:
  - `?` sits apart from the action group on purpose, so reaching for help can
    never be a mis-tap on Reset. It must stay at the LEFT end.
  - `↶` and `⟲` are adjacent and read alike at 19px, and one of them wipes
    everything — so `⟲` is tinted `--warn`. The glyphs alone are not enough.
  - Undo belongs next to Reset precisely *because* Reset is the destructive
    one. It was briefly moved out of the toolbar and the owner asked for it
    back.
  - The drag tooltip moved BELOW the row (`top:64px`), since the row now spans
    the full width and there is no space left at either end. In landscape both
    the row and the tip start clear of the drawer at 324px.
  - The play glyph and undo's disabled state are refreshed in a two-line rAF
    tick — `cfg.demo` and the undo stack are changed from half a dozen places
    and making each one announce itself would be more code, not less.
- **A drag does not pause the sweep — it winds it up to 1×**, `DRAGSPEED`
  (owner's call, 2026-08-01: "users can see the full excursion of their
  change"; 2× was tried first and read as too fast). `frame()`
  reads `speedOverride||cfg.speed`, and `cfg.speed` is never written, so the
  slider keeps the user's value and release just clears the override. Every
  exit from a drag goes through `endPointer`, which clears it unconditionally
  — a boost left switched on would be permanent. Consequence worth knowing:
  the four ground mounts hold still while animating, so dragging those is
  exactly the intended experience, but R, B, C, P, D and Q ride the mechanism
  and move under your finger. Pause with ⏸ to pin one down.
- **A tap does not pause either.** index.html stops the sweep on pointerdown;
  here the touch radius is 30px over pins ~10px apart, so almost any tap in
  the middle of the drawing lands on a handle and would silently stop
  playback. The boost waits for real movement (`dragMoved`), so a stray tap
  costs nothing — same gate that arms undo.
- **All typed controls are ≥16px**, or iOS zooms the page on focus. Tap
  targets ≥44px. `100dvh`, `env(safe-area-inset-*)`, `viewport-fit=cover`.
- **resize** is rAF-debounced and also bound to `orientationchange` and
  `visualViewport.resize` — the mobile URL bar fires `resize` continuously.
- `index.html` redirects a narrow touch screen here (3 lines in `<head>`);
  **`?desktop=1` escapes it**, and that is the documented way to get the
  sliders back on a phone.

## UI features already built (don't regress these)

- Presets dropdown (serpentine / grandarc / custom), Reset preset.
- Temperature reading slider + numeric Scale min/max °F fields (≥10° span).
- Reverse scale checkbox (retract = hot). Excursion min/max fields (≥1″,
  capped at the selected actuator's stroke — `clampExcursion()` re-clamps on
  type/stroke edits).
- **Actuator type select + per-type fields** (both pages, ids shared so the
  mobile parity test is untouched): `#actT`, generic row `#actGen`
  (`#aLmin`/`#aStroke`), joyce row `#actJoy` (`#aClamp`). All four are
  numeric geo keys so presets/saves/undo/applyData carry them for free; a
  pre-actuator-types save loads as generic 24/18 via an applyData migration.
  Editing any of them flips the preset to "custom". `syncActUI()` (called
  from syncSliders) fills fields and toggles row visibility, null-guarded
  like the slider wiring. The joyce render draws the tube at real scale
  (Ø2″ tube, Ø1.378″ rod, motor pod, blue clamp glyph at the pivot foot);
  in joyce mode the 4th DXF mount point is labelled ACT_CLAMP instead of
  ACT_ANCHOR.
- Auto-cycle with speed slider **0.05×–1×**; **spacebar toggles** auto-cycle
  globally (guarded so focused buttons don't re-fire; resumes from current
  temperature via phase sync — see syncDemoPhase()).
- Draggable canvas handles: all 4 mounts AND all joint pins (R sets rA,
  B sets L2, C sets L3+L4, P sets cu/cv, D sets L5+L6, Q sets cu2/cv2).
  View refit is suppressed during drag; sliders track live; any edit
  switches preset to "custom". On DESKTOP, grabbing a handle pauses the
  auto-cycle for the duration of the drag and release resumes it (via
  syncDemoPhase, so it picks up from the current temperature) — if the
  sweep was off before the grab it stays off. Mobile is different on
  purpose: a drag never pauses, it winds the sweep to 1× (DRAGSPEED).
  Joyce mode adds TWO more handles (both return undefined in generic mode,
  which is how the pickers skip them), giving three distinct drive drags:
  - `tail` (tube rear end): slides the TUBE through a fixed clamp — only
    aClamp changes. Cursor projects onto the tube axis, pins [c0min,c0max].
  - `clamp` (the clamp body at the foot F): slides the CLAMP along a FIXED
    tube — aClamp and the pivot mount (dA/anch) change together so the pose
    at the current temperature does not move at all (tested to 1e-9). The
    pivot displacement is exactly slide×u along the tube axis.
  - `anchor` (the pivot pin): unchanged — moves the whole drive mount;
    aClamp stays put and the actuator re-aims as pose() solves.
- **Undo** (button + Ctrl/Cmd+Z, 60 deep) for wholesale geo changes: drags,
  preset switches, Reset, loading a saved design. Snapshots geo plus UNDOCFG,
  which is now **all of `cfg` except `temp` and `demo`** — widened on
  2026-08-01 when Reset became a full reset, so that one undo puts every
  setting back. The two exclusions are the point: a drag must not have its
  playback state restored under it. A drag snapshots once, on first movement,
  so a grab-and-release pushes nothing. The preset label is re-derived from
  the restored geometry (presetOf) rather than snapshotted — the dropdown has
  already moved by the time its change event fires.
- **Reset (`resetAll`, shared core) = the page as it first opened**: geometry
  back to the selected preset, every `cfg` value back to `CFGDEFAULTS`, and
  the view squared up — rotation, zoom AND pan. Both pages use it, so the
  button means the same thing in both. It used to restore geometry and zero
  the rotation; it now returns rotation to the 110° default like every other
  setting, because "reset" means the page as it opened, not "square up the
  view". Pan and zoom are not undoable, but they never were — transient
  nudges, not part of the design.
- **Zoom**: mouse wheel, cursor-anchored — the point under the pointer stays
  put. Wheel FORWARD zooms IN. `zoom` multiplies the fitted scale via
  `scale()`; fitView centres using `scale()` too, or a refit would jump the
  view whenever zoom != 1. Clamped 0.15–12. Not saved, same as pan.
- **Pan**: right-drag anywhere, or drag empty canvas (so it works on touch).
  Double-click recenters AND resets zoom. `pan` is added on top of the auto-fit in TX() and
  subtracted back out in worldOf(), so a refit keeps it and pivot dragging
  still tracks the cursor. clampPan() keeps it within ±0.6 viewport scaled by
  zoom, so nothing gets lost. Pan and zoom are the view settings that are NOT
  saved — they're transient nudges. Rotation IS saved.
- **Rotate view** slider, `cfg.rot`, 0–360 in 10° steps, **counterclockwise**.
  Everything on the canvas goes through TX(), so rotating there turns the
  lot. Four things this had to get right, none of them optional:
  - Canvas y points DOWN, so the plain rotation matrix reads *clockwise* on
    screen. `rotRad()` negates the angle in ONE place; rotPt/rotDir/worldOf
    all go through it. Don't reintroduce a bare `cfg.rot*DEG`.
  - It rotates about the UNROTATED content centre (`view.cx/cy`, set by
    fitView from the unrotated bounds). Using the rotated centre would walk
    the drawing across the screen as you turn it.
  - fitView fits the ROTATED bounds, so a turned design still fits the
    viewport. It computes unrotated bounds first (for the pivot), then
    rotated bounds (for the fit).
  - worldOf() inverts the rotation, or a grabbed pivot drifts off the
    cursor. Verify this MID-drag: releasing refits the view and hides it.
  Reset restores the DEFAULT rotation (110°), not zero — see resetAll above —
  and so calls syncUI, not syncSliders.
  Rotation never alters a real dimension. The bounding box footprint DOES
  change with it, but that is a different measurement, not the piece changing.
- Hover: component highlight + tooltip naming the part + its sliders, and
  the matching slider rows highlight in the panel (COMPINFO / hlSliders).
- Collapsible <details> sections for Stage 1 / Stage 2 / Actuator drive.
- **The path and its divisions.** The owner calls the traced curve the
  **path**. It runs tmin→tmax and its colour goes blue → orange → red
  (tempColor). It is drawn as one chunk per whole degree (buildChunks,
  CHUNKSUB=6 sub-samples each, cached in pathChunks by rebuildPath), and a
  short black **division** is stroked ACROSS the path at every chunk
  boundary — 10 divisions between labelled marks, every major and minor
  tick landing exactly on one.
  History worth not repeating: the divisions used to be an accident. The
  path was stroked in 140 sample segments, each painting a drop shadow that
  overpainted the previous segment, and that overpaint showed as the black
  line. The shadow was offset in +y ONLY, so divisions appeared where the
  path climbs and vanished entirely where it descends — none at all between
  60 and 80°F. Both the shadow and that mechanism are gone. Divisions are
  explicit now; do not reintroduce a drop shadow.
- **Labels thin where they crowd** (added 2026-07-31, closing a TODO item).
  A 10° label is drawn only if it clears every label already placed by
  `LBLGAP=34` SCREEN px — against ALL of them, not just the previous one,
  because this path folds back and 110° comes to rest beside 60°: the two
  printed as one blot. Measured in screen px, so **zooming in brings the
  skipped ones back**; it is a legibility rule, not a change to the scale.
  6 of 14 survive on a phone at 1×, 9 of 14 on a 1280px desktop, all 14 at
  12×. **The DXF deliberately does NOT thin** — the engraving is at real
  size where nothing crowds, and it must carry every 10° mark. That is the
  one place screen and DXF are allowed to disagree, and the tests assert
  both halves.
- **No tick strokes.** tickList() still runs every 5° (major on the 10s,
  cached in tickCache) but ONLY the 10° labels are drawn, sat 14px off
  their own division. The white major/minor comb beside the path was
  removed at the owner's request — it repeated what the divisions already
  say. 1° sub-ticks were built and removed too. Don't bring either back.
  The DXF matches: it emits no tick strokes either, only PATH_DIVISIONS and
  the 10° labels.
  tickList positions come from pose() directly, NOT from indexing the
  140-sample path: several ticks land on one sample and the spacing — the
  whole point of this scale — comes out wrong. tickList also carries the
  normal's side forward from tick to tick, because a coupler curve can cusp
  and flip the tangent 180°, which would throw the rest of the comb to the
  far side of the line. Don't "simplify" either of those away.
- **The indicator is a transparent ring** (r=9, 2px outline, no fill, no
  centre dot) so the path and its divisions read straight through it — the
  viewer counts the marks the ring is sitting on. The real sculpture's
  indicator will be a ring with a hole for exactly this reason. It no
  longer carries the temperature colour; the path underneath does.
- **"Inner curves"** (`cfg.ghost`, **default ON** since 2026-08-01 at the
  owner's request) traces every moving joint (R, B, C, P, D) as dashed
  paths — R is the actuator rod end.
- **Bounding box** ("Bounding box" checkbox, `cfg.showBox`, default off): a
  dashed rectangle round the whole design labelled with its overall size in
  inches — 40.7″ × 30.8″ square-on for the current serpentine. A sense of the
  real scale of the piece. Two things to preserve:
  - buildBBox() runs AFTER fitView() in rebuildPath, because rotPt needs the
    pivot fitView sets. It still tracks live during a drag: fitView
    early-returns then, leaving the view frozen, and buildBBox is not gated.
    Rotating calls `fitView(); bbox=buildBBox();` — the footprint changes.
  - It samples `pathChunks`, not `pathQ`. pathQ's 140 samples sit ~0.93°F
    apart and miss the path's extreme at the loop tip near 47°F — three
    points fell outside the box when it was built from pathQ.
  It bounds **everything the piece sweeps**: the path, every moving joint's
  trace (R, B, C, P, D from pathJ), and the four fixed mounts. Ticking the
  box also ticks "Inner curves", so you can see what it is measuring —
  otherwise it bounds things that aren't drawn. Named `showBox` in cfg
  because `bbox` already holds the geometry.
  The joint traces come from pathJ at 140 samples (~0.93°F apart), which
  clips a smooth extremum by ~2 thou; the path itself uses the 6× finer
  pathChunks. Fine for a 40″ piece — don't mistake it for a bug.
  **Measured in ROTATED space**, so its edges stay square to the screen at any
  view angle. That means w/h are the footprint AT THE CURRENT ORIENTATION and
  DO change as you rotate — 40.7″ × 30.8″ square-on, swapping at 90°. That is
  the point: rotate to the mounting angle and read what it occupies. The
  transform is split for this — `TXr()` takes an already-rotated point,
  `TX() = TXr(rotPt())` — and drawBBox uses TXr so it isn't rotated twice.
- **Nothing auto-restores on load** (the old `couplerThermometer.v2`
  auto-restore slot was removed — see TODO.md "Settled"); the page opens on
  the defaults and saved designs are opt-in, with ONE deliberate exception:
  the **actuator choice** (`geo.actT`) persists under localStorage key
  `couplerThermometer.actT` (owner request 2026-08-02 — it is hardware you
  own, not a design edit). Written by `persistActT()` from `rebuildPath()`
  (compare-and-write, so every path that can flip it — select, preset,
  undo, Reset, load — is covered), restored at init, guarded try/catch like
  all storage here. The geometry itself still opens on the preset defaults.
- **Named designs**: type a name before Save and it also goes into the map
  under `couplerThermometer.saves`; the name field then clears and the
  "Load a saved design…" dropdown holds the record. Delete removes the
  entry named in the field. Recalling from the dropdown deliberately does
  NOT refill the name field, so deleting a just-recalled design means typing
  its name. Saving with the name empty still updates the auto-restore slot.
- **DXF export for Fusion** (two buttons, R12 ASCII, inches, y flipped to
  CAD convention). `showSaveFilePicker` gives a real Save dialog where the
  browser has one, else it falls back to an `<a download>`:
  - *Parts DXF* — the 5 fabricated links, each flat in its own local frame
    on its own layer (CRANK / PLATE1 / ROCKER1 / PLATE2 / ROCKER2), laid
    out side by side without overlap. Outline = convex hull of equal-radius
    circles at each hole (offset edges + corner arcs), so 2-hole links come
    out as capsules and 3-hole plates as rounded triangles. Driven by the
    "Pivot hole ⌀" and "Link width" fields (`cfg.hole` / `cfg.lwid`).
  - *Points DXF* — the assembly frame: the path as line segments
    (SCALE_CURVE), a division across it every whole degree
    (PATH_DIVISIONS, `PATHW=1.0″` long), °F labels every 10°, the 4 mounts,
    and POINT entities at every 10° mark and mount to snap to. No tick
    strokes — the indicator ring would cover anything beside the path.
  Curves are line segments, not splines — fit a spline in Fusion if wanted.
- Public view: uncheck "Show mechanism" — only the path + indicator ring.
- Debug hook for tests: `window.__ct` = {pivotScreen(name), geo, cfg, pose,
  pan, zoom, rotPt, screen (=TX), dir (=rotDir), rebuild(), ticks, chunks,
  bbox, pathJ, undoDepth(), buildParts(), buildPoints(),
  lenOf(ext), extAt(t), strokeOf(), actGeom(p,t), JOYCE, dump()}. mobile.html
  adds {peek, sheetOpen, setSheet(), pick(x,y,type)}. The builders return DXF
  text so tests can assert on the export without a download. `dump()` returns
  geo+cfg as JSON — this is how the owner hands over a hand-tuned design:
  `copy(__ct.dump())` in the console.

## Verification pattern used throughout

Headless Chromium via Playwright (`executablePath` may need adjusting per
machine). Every feature was verified by driving the page: dispatch real
`input`/`change` events, drag with mouse.move/down/up, reload for
persistence tests, screenshot and inspect. Keep doing this for changes.

**After any change, run all three:**

```
python3 tools/verify_export.py     # index.html, 601 lines of checks
python3 tools/sync_core.py         # the two pages' cores are identical
python3 tools/verify_mobile.py     # mobile.html on a 390x844 phone viewport
```

`tools/dxf.py` holds the shared DXF reader — its own module because
`verify_export.py` runs its whole suite at import time.

Two things `verify_mobile.py` has to do that the desktop one does not, both
worth knowing before you edit it:

- Playwright's touchscreen API taps only; it cannot express a pinch or tag a
  drag with a `pointerType`. It dispatches raw `PointerEvent`s instead.
- Those carry pointer ids that are not real active pointers, so
  `setPointerCapture` throws `NotFoundError`. `ready(pg)` stubs it out after
  every load — call it after every `reload()`, along with stopping the sweep.

## Known open items / next steps

Tracked in **TODO.md**; fabrication measurements and the DXF layer
reference in **FABRICATION.md**. Kept in sync — update those, not just here.

1. **Fabrication document** (owner has asked for this "when design is
   final"): the DXF export now covers the drawing side — link outlines and
   mount coordinates on a common frame. Still missing: pivot hardware
   suggestions, actuator mounting-triangle detail, and the temp→extension
   calibration table for the controller. Note the exports read the CURRENT
   geo, and the chosen Serpentine preset still violates the original search
   constraints (see the preset section) — re-confirm before cutting metal.
2. ~~Marks in the path~~ — DONE 2026-07-19. The indicator is a ring the
   viewer reads the temperature *through*, so anything beside the path is
   covered up. Screen and DXF now agree: divisions cut ACROSS the path, one
   per whole degree, no tick strokes alongside, labels every 10°F. The DXF
   emits them on layer PATH_DIVISIONS from the same pathChunks drawScale
   uses, so the two cannot drift apart.
   `PATHW=1.0` in buildPoints is the engraved path width in inches — the one
   number the screen can't supply, since canvas widths are in pixels. Make
   it a field if it needs tuning against real stock.
   Method note from 2026-07-19: an earlier attempt bundled five changes at
   once (band width, restyled tiers, ring indicator, new field) and was
   reverted because the owner couldn't see the wanted change through the
   unwanted ones. Land one change at a time here.
3. **.linkage2 export** — write the chosen geometry as XML for David
   Rector's Linkage program (Windows; blog.rectorsquid.com). Not started.
4. Unresolved question: owner once asked for "beginning and ending point
   control for actuator"; clarification returned "no preference". The
   excursion fields may already satisfy it. Re-confirm before building
   anything (candidates were: XY fields for actuator mounts, absolute
   length endpoints, or crank start/end angles).
5. Possible polish: auto-thin tick labels where the non-linear scale
   crowds them (owner was told this is available on request).
6. Real-world drive: temperature sensor → controller → actuator position;
   the sim's temp→extension mapping (linear within excursion, optional
   reverse) is the spec the controller must implement.

## Owner preferences observed

- Iterative, hands-on; tests features immediately and reports precisely.
- Wants fabrication realism (mount clustering, real actuator envelope).
- Prefers honest behavior over hand-holding (kept the parts-disappear
  behavior when linkage can't assemble).
- Mobile user in this phase; keep touch interactions working.
