# Fabrication notes

Everything a shop needs to cut this piece, plus the measured facts about the
current design. Numbers come from `tools/analyze_geometry.py`; re-run it after
**any** geometry change, because they go stale the moment the preset moves:

```
python3 tools/analyze_geometry.py dump.json     # dump.json = copy(__ct.dump())
```

## Hardware, fixed

- Linear actuator: **24″ retracted, 18″ stroke, 42″ extended**, pin to pin.
  Hard physical constants (`ACT={lmin:24, stroke:18}`).
- Usable slice of that stroke is configurable (excursion min/max, inches of
  extension) so the build can stay off the end stops. Currently **0–15.5″**.

## Current geometry — Serpentine, owner-tuned

All coordinates inches, origin at **O2** (the bell-crank pivot).

```
rA=12.6151  dA=27.6388  anch=-133.1494°
stage 1: gx=12.9  gy=-6.0  L2=11.3701  L3=7.7705  L4=7.0142  cu=3.5  cv=11.3  s1=-1
stage 2: ox=6.9036  oy=-17.4189  L5=5.9  L6=14.0  cu2=19.9991  cv2=13.1489  s2=-1
```

- **82.5″** of path, from an 18″ stroke.
- Assembles across the whole 0–15.5″ excursion.
- Footprint square-on: **40.7″ × 30.8″** — the path, every swept joint, and
  all four mounts, i.e. the envelope the mechanism actually occupies. At the
  110° default view angle it reads 32.5″ × 43.3″; rotate the view to your
  mounting angle and the box reports the footprint at that angle.

## Open concerns — read before cutting

### 1. O2 fails the mount clearance rule

Every fixed mount must clear the path by **≥2.5″**. Measured:

| mount | clearance | |
|---|---|---|
| O2 (bell-crank pivot) | **2.06″** | under the rule |
| O6 (rocker-2 ground) | 5.28″ | ok |
| ACT (actuator anchor) | 15.77″ | ok |
| O4 (rocker-1 ground) | 16.11″ | ok |

The mount-to-mount crossing rule was dropped by the owner, so mounts may sit
on either side of the path. Clearance still stands, and O2 is short by 0.44″.

### 2. The actuator has ~0.25″ of headroom

`dA + rA = 40.25″`, so the drive triangle stops closing past about **15.75″**
of extension. That is why the excursion is 15.5″ and not 17″.

- The controller must **never** command past 15.5″. Beyond the limit the
  linkage cannot reach a valid pose — the actuator stalls against geometry it
  physically cannot satisfy.
- Re-check this figure if `dA`, `rA`, or the excursion is touched at all.

### 3. The scale is very non-linear, with a near-cusp

10°F steps along the path:

| band | length | | band | length |
|---|---|---|---|---|
| −20..−10 | 0.79″ | | 50..60 | 12.12″ |
| −10..0 | 1.30″ | | 60..70 | 13.69″ |
| 0..10 | 2.07″ | | 70..80 | 8.04″ |
| 10..20 | 2.94″ | | 80..90 | 3.04″ |
| 20..30 | 3.92″ | | 90..100 | 8.25″ |
| 30..40 | 4.81″ | | 100..110 | **16.36″** |
| 40..50 | 5.14″ | | | |

- Spread **20.7×** (the original search rule was ≤7×, max segment ≤2.2″).
- Slowest single degree **0.073″** at −20°F, against a 0.15″ rule.
- Not monotonic: it slows at 40–50°F and again at 80–90°F.
- **Near-cusp at 43.5°F**: the indicator slows to 0.111 in/°F and the path
  swings 10°. A tight corner to engrave, and a spot where the reading barely
  moves.

None of this is a defect — the uneven scale is the point of the piece. It is
recorded so nobody assumes the search constraints still hold. They do not.

## What the DXF export gives you

Two buttons in the simulator panel. ASCII DXF (R12), units **inches**, Y flipped
to CAD convention. Curves are line segments, not splines — fit a spline in
Fusion if you want a single entity.

### Parts DXF — the five links, laid flat

One layer per part, spaced so they do not overlap:

| layer | holes | driven by |
|---|---|---|
| `CRANK` | O2, B, R (collinear) | `L2`, `rA` |
| `PLATE1` | B, C, P | `L3`, `cu`, `cv` |
| `ROCKER1` | O4, C | `L4` |
| `PLATE2` | P, D, Q | `L5`, `cu2`, `cv2` |
| `ROCKER2` | O6, D | `L6` |

Each part is drawn in its own local frame: first hole at the origin, second
along +X. Outlines are the convex hull of equal-radius circles at each hole, so
two-hole links come out as capsules and the coupler plates as rounded
triangles. Sized by the **Pivot hole ⌀** and **Link width** fields (0.375″ and
1.5″ by default).

### Points DXF — the assembly frame

| layer | contents |
|---|---|
| `SCALE_CURVE` | the path, as line segments |
| `PATH_DIVISIONS` | one mark per whole degree, cut **across** the path |
| `LABELS` | °F every 10°, and the mount names |
| `MOUNTS` | the four fixed mount holes |
| `POINTS` | snap targets at every 10° mark and every mount |

Divisions are `PATHW = 1.0″` long, centred on the path. That constant lives in
`buildPoints()` in `index.html` — it is the one dimension the simulator cannot
infer, because canvas widths are in pixels. Change it there if the engraved
path width differs.

There are deliberately **no tick strokes beside the path**. The indicator is a
ring the viewer reads the temperature *through*, so anything alongside the path
would sit underneath it and be invisible.

## Still to produce

- Pivot hardware selection (bearing/bushing type, fastener sizes, retention).
- Actuator mounting-triangle detail — the anchor and rod-end brackets.
- The temp→extension calibration table for the controller. The mapping is
  linear within the excursion, with optional reversal:
  `extension = extMin + (T − Tmin)/(Tmax − Tmin) × (extMax − extMin)`.
- `.linkage2` export for David Rector's Linkage program, if wanted.
