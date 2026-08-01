# Kinetic Thermometer

**[Live demo →](https://holla2040.github.io/kineticThermometer/)**

An outdoor garden sculpture that displays temperature: a linear actuator
(24″ retracted / 42″ extended, 18″ stroke) drives a bell crank into two
chained four-bar linkages, and the indicator — the second stage's coupler
point — crawls along the serpentine curve it traces. The temperature scale
is engraved along that curve, with equal temperature steps landing at
unequal spacing. Viewers are meant to puzzle over how it works.

![The design simulator sweeping −20 to 110°F: actuator, bell crank, two
four-bar linkages, and the temperature path traced by the stage-2 coupler
point](images/index.gif)

One frame per degree, so the animation gives every degree equal *time* —
which is why the indicator crawls where the path is compressed and races
where it opens out. That unevenness is the mechanism, not the recording.

## Files

- `index.html` — the interactive design simulator, served live at
  <https://holla2040.github.io/kineticThermometer/> (GitHub Pages, straight
  off `main`, so a push updates it). Or just open the file in any browser.
  No dependencies, fully self-contained. Drag the mounts and joint pins to
  reshape the linkage, tune the scale range and actuator excursion, undo
  with Ctrl/Cmd+Z, pan by right-dragging, zoom with the mouse wheel, rotate
  the view in 10° steps, and save named designs in the browser. A dashed
  bounding box gives the piece's footprint in inches at the current view
  angle. Double-click recentres and resets zoom. Exports DXF for Fusion —
  see below.
- `mobile.html` — the same simulator, portrait-first for a phone. A narrow
  touch screen opening the live demo lands here automatically; add
  `?desktop=1` to force the desktop page instead. The controls live in a
  bottom sheet you drag open, and **there are no geometry sliders**: every
  length and mount position is set by dragging its pin, with the values you
  are changing shown at the top of the screen. Pinch to zoom (also how you
  get fine control — at 12× a pixel is about a hundredth of an inch),
  double-tap to recentre, and use the ▶ ↶ ⌖ buttons in place of the
  keyboard. Turned sideways the sheet becomes a left drawer. Presets, saves
  and both DXF exports all work. See "Two files, one core" below.
- `tools/search_geometry.py` — the constrained random search that found
  the preset geometries. `python3 tools/search_geometry.py` (a few minutes).
- `tools/analyze_geometry.py` — measures a saved design against the
  fabrication constraints: assembly across the stroke, scale length, per-10°F
  step lengths, cusps and kinks, mount clearance, and the actuator-triangle
  ceiling. Feed it a `__ct.dump()` capture (see below).
- `tools/verify_export.py` — drives `index.html` headless and checks the
  whole UI and both DXF exports. Run it after changing `index.html`.
- `tools/verify_mobile.py` — the same for `mobile.html` on a 390×844 phone
  viewport: the sheet, touch hit radii, pinch, double-tap, the drag
  tooltip, control parity against the desktop, and the landscape drawer.
- `tools/sync_core.py` — keeps the two pages' shared half identical.
- `FABRICATION.md` — what a shop needs: the chosen geometry, the measured
  scale behaviour, the DXF layer reference, and the concerns to settle before
  anything is cut.
- `TODO.md` — open work, known concerns, and a list of things already tried
  and deliberately reverted.
- `CLAUDE.md` — full project context and history. If you work on this
  project with Claude Code, start it in this folder and it reads this
  automatically.
- `ik-demo.html` — unrelated earlier FABRIK inverse-kinematics demo.

## Exporting for CAD

Two buttons in the panel write ASCII DXF in inches:

- **Parts DXF** — the five fabricated links, each laid flat in its own local
  frame on its own layer, spaced out so they don't overlap. Outlines are
  sized by the pivot-hole and link-width fields.
- **Points DXF** — the assembly frame: the path, a division across it every
  degree, °F labels every 10°, the four mounts, and POINT entities to snap to.

Curves come out as line segments, not splines — fit a spline in Fusion if
you want one entity. The export carries the same 1° path divisions the
simulator draws, on layer `PATH_DIVISIONS`, so the engraving matches the
screen. Full layer reference in [FABRICATION.md](FABRICATION.md).

## Two files, one core

`index.html` and `mobile.html` are two hand-maintained pages that share one
solver, one DXF writer and one set of presets. That shared half — about 1050
of each file's ~1550 lines — sits between marker comments:

```
// ==== SHARED CORE START ====
// ==== SHARED CORE END ====
```

Edit the physics in `index.html`, then:

```
python3 tools/sync_core.py --apply     # copy it into mobile.html
python3 tools/sync_core.py             # --check: fail if they differ
```

Below the END marker each page keeps its own interaction layer — hit radii,
gestures, tooltips, resize — and that is deliberately different. Run the
`--check` after any change to either file; a silent drift between the two
would mean the phone and the desktop disagree about the geometry you cut.

## Handing a tuned design back

Drag the geometry until you like it, then in the browser console:

```js
copy(__ct.dump())
```

That copies geometry plus settings as JSON. Paste it into
`tools/analyze_geometry.py` to check it against the fabrication rules, or
hand it to Claude Code to make it the new preset.

## Continuing with Claude Code

```
cd kinetic-thermometer
claude
```

Then just describe what you want ("fix the O2 clearance", "add the
.linkage2 export") — CLAUDE.md gives it the design constraints, chosen
preset and code architecture; TODO.md gives it the open work.
