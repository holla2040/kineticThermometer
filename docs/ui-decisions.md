# UI decisions — features already built (don't regress these)

Moved from `CLAUDE.md` on 2026-11-22. Applies to both `index.html` and `mobile.html` (the shared core). TODO.md "Settled — do not redo" lists the reverts; the reasons are here.


- Presets dropdown (25 presets + custom), Reset preset.
- Temperature reading slider + numeric Scale min/max °F fields (≥10° span).
- Reverse scale checkbox (retract = hot). Excursion min/max fields (≥1″,
  capped at the selected actuator's stroke — `clampExcursion()` re-clamps on
  type/stroke edits).
- **Actuator type select + per-type fields** (both pages, ids shared so the
  mobile parity test is untouched): `#actT`, generic row `#actGen`
  (`#aLmin`/`#aStroke`, shown for the fixed type too), joyce row `#actJoy`
  (`#aClamp`), fixed row `#actFix` (`#aDir`/`#aCon`) plus a **Flip drive**
  checkbox `#aBrc` beside the two stage flips. All four are
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
  Fixed mode adds ONE handle, `tip` — grab the rod tip / carriage to aim the
  axis and set how far out the body sits (`aDir` and `aLmin` together; aLmin is
  the tip distance at ZERO extension, so the current extension is backed out or
  the tip walks away under the finger). Verify tracking MID-drag; releasing
  refits the view.
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
- **Drag feasibility overlay ("Drag regions"), dragging itself unrestricted**
  (2026-08-03/04, branch `drag-area`, both pages via the shared core).
  Grabbing a handle — pointerdown, before any movement — tints the NO-GO
  region faint red under the drawing: every screen cell where dropping the
  cursor would leave a design that can't assemble somewhere in the range.
  The untinted holes are where the handle may go. Advisory only:
  - **A validity gate was built first and REMOVED the next day at the owner's
    request** ("keeping you within the good region was a mistake"). It pinned
    drags to range-valid designs with a slide-to-the-wall binary search. The
    owner wants free-form dragging: into the red and back, with the overlay
    (and the red box) doing the informing. Don't rebuild the hard block.
  - The **"Drag regions" checkbox** (Display section, `cfg.region`, default
    ON, id `region` in both pages) switches the overlay. It rides in
    CFGDEFAULTS/UNDOCFG/saves like every display toggle.
  - Mechanics: `applyDrag` = `mutateDrag(name,w)` (pure per-handle mutation;
    returns touched keys or null when the branch declines — keep the split,
    the overlay depends on it) + `updGeoUI`. `startDragRegion`/
    `stepDragRegion` scan a screen grid (~27px cells) in 5ms rAF slices from
    `frame()`, `mutateDrag` + coarse `rangeValid(24)` per cell, restoring geo
    after each sample and freezing cfg.temp per slice (mobile's sweep runs
    during drags). `drawDragRegion` merges each row's bad runs into single
    rects — per-cell fills doubled alpha at seams and read as a checkerboard.
  - Computed ONCE per grab: every handle except O2 maps the cursor to
    geometry absolutely, so its region is drag-invariant. O2 is delta-based
    and gets no overlay. Cells beyond the slider clamps read GOOD on purpose
    — the mutation saturates there, so the cursor may go there.
  - Cleared on release, and on mobile when a second finger outranks the drag.
    Approximate by design ("close, not exact" — owner's words); the red
    range warning is the authority.
  - `rangeValid(n)` (defaults to the same 141 samples as rebuildPath) and
    `dropNoopUndo` (pops the undo snapshot of a drag that netted zero change,
    e.g. shoving a handle already pinned at its clamp) live in the core.
    `__ct` gains `rangeValid` and a `dragRegion` getter on both pages.
  - Numbers worth knowing (asserted in verify_export §12, mobile §11c): at
    serpentine defaults O4 has ~0.03″ of valid travel up-right and ~2″
    down-left (14 good cells of 1296), R can slide in only ~0.6″ before the
    range fails (dA+rA has ~0.25″ slack), and BOTH joyce tail extremes jam
    the linkage. The overlay is how a user discovers this; nothing stops
    them any more.
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
  `scale()`; fitView centers using `scale()` too, or a refit would jump the
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
  - It rotates about the UNROTATED content center (`view.cx/cy`, set by
    fitView from the unrotated bounds). Using the rotated center would walk
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
  center dot) so the path and its divisions read straight through it — the
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
  its name. A save with the name empty is refused with a warning (there is no auto-restore slot).
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
