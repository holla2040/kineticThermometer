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
  No dependencies, fully self-contained. Design geometry, drag mounts and
  joint pins, tune the scale/excursion, save settings in the browser.
- `tools/search_geometry.py` — the constrained random search that found
  the preset geometries. `python3 tools/search_geometry.py` (a few minutes).
- `CLAUDE.md` — full project context and history. If you work on this
  project with Claude Code, start it in this folder and it reads this
  automatically.
- `ik-demo.html` — unrelated earlier FABRIK inverse-kinematics demo.

## Continuing with Claude Code

```
cd kinetic-thermometer
claude
```

Then just describe what you want ("generate the fabrication document",
"add the .linkage2 export") — CLAUDE.md gives it the design constraints,
chosen preset, code architecture, and open to-do list.
