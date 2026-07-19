# Kinetic Thermometer

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

- `index.html` — the interactive design simulator. Open in any browser.
  No dependencies, fully self-contained. Drag the mounts and joint pins to
  reshape the linkage, tune the scale range and actuator excursion, undo
  with Ctrl/Cmd+Z, pan by right-dragging, rotate the view in 10° steps, and
  save named designs in the browser. A dashed bounding box gives the piece's
  overall size in inches. Exports DXF for Fusion — see below.
- `tools/search_geometry.py` — the constrained random search that found
  the preset geometries. `python3 tools/search_geometry.py` (a few minutes).
- `tools/analyze_geometry.py` — measures a saved design against the
  fabrication constraints: assembly across the stroke, scale length, per-10°F
  step lengths, cusps and kinks, mount clearance, and the actuator-triangle
  ceiling. Feed it a `__ct.dump()` capture (see below).
- `tools/verify_export.py` — drives the page headless and checks the whole
  UI and both DXF exports. Run it after changing `index.html`.
- `CLAUDE.md` — full project context and history. If you work on this
  project with Claude Code, start it in this folder and it reads this
  automatically.
- `ik-demo.html` — unrelated earlier FABRIK inverse-kinematics demo.

## Exporting for CAD

Two buttons in the panel write ASCII DXF in inches:

- **Parts DXF** — the five fabricated links, each laid flat in its own local
  frame on its own layer, spaced out so they don't overlap. Outlines are
  sized by the pivot-hole and link-width fields.
- **Points DXF** — the assembly frame: the path, its 5°/10° ticks with
  labels, the four mounts, and POINT entities to snap to.

Curves come out as line segments, not splines — fit a spline in Fusion if
you want one entity. Note the export does not yet carry the 1° path
divisions the simulator draws.

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

Then just describe what you want ("generate the fabrication document",
"add the .linkage2 export") — CLAUDE.md gives it the design constraints,
chosen preset, code architecture, and open to-do list.
