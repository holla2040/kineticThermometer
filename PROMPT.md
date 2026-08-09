GOAL
Rebuild the 3D-printable benchtop model of the kineticThermometer serpentine
mechanism natively in Autodesk Fusion 360, through the Fusion MCP connection, as
separate components with joints, so the assembly actually articulates when the
shuttle is dragged. The geometry is already fully solved and verified; do not
re-derive it — transcribe it.

WHERE EVERYTHING LIVES (read-only; do not edit the repo, no git operations)
- Repo: the kineticThermometer checkout this file sits in, branch 3dfab-level.
  All paths below are relative to the repo root.
- tools/print3d.py — the generator. Its constants block and docstring are the
  spec. print/ is committed, so you do NOT need to rerun it; if you want to
  (python3 tools/print3d.py), it needs pip installs: numpy shapely trimesh
  mapbox_earcut, plus tools/explore_designs.py beside it.
- print/fusion-data.json — exact numbers in Fusion-ready mm: mount XY, per-part
  local hole coordinates, level z table, post/sleeve lengths per joint, screw
  table, plate bounds, and Q/R/B/C/P/D pose checkpoints at ext0/mid/ext15.5.
  This file is your primary data source.
- print/PRINT.md — bill of materials, screw/washer table, assembly order.
- print/*.stl — the verified geometry. assembly.stl is everything placed at
  mid-stroke; use it as a visual cross-check (insert as mesh if helpful).

CONNECT FIRST
Invoke the fusion-mcp skill (if present) to connect/verify the AutodeskFusionMCP
add-in before declaring Fusion unreachable — the server is usually fine and only
the session's registration is stale. Create a NEW design document (suggest name
"kineticThermometer-bench-3dfab"), units mm. Never modify the owner's existing
designs (notably "Joyce QS11940 Linear Actuator").

COORDINATES
All numbers are model mm, y already flipped to CAD convention (matches the
repo's Points DXF), z up from the back plate bottom. Scale is 5 mm per real
inch. Sketch parts on XY, extrude +Z.

COMPONENTS TO CREATE (all flat extrusions; no lofts, no booleans needed beyond
holes/pockets)
1. backplate — rectangle from plate_bounds_model_mm (x -104.511..81.928,
   y -24.148..139.587), 4 thick; Ø3.4 through-holes at the four mounts
   (mounts_model_mm: O2, O4, O6, ANCH); four Ø10×6 feet under the corners,
   inset 7 from each edge. The raised path ridge (1.2 wide, 1.2 tall along the
   temperature curve) is cosmetic — either skip it, or pull the 141-point Q
   path by running, from the repo root:
     python3 -c "import sys; sys.path.insert(0,'tools');
     from print3d import *; m=Model(GEO);
     print('\n'.join(f'{p[0]:.3f},{p[1]:.3f}' for p in m.pt['Q']))"
   and loft a 1.2×1.2 profile along a fitted spline on the plate top.
2. crank — capsule 8 wide, axis from (0,0) to (63.075,0), holes Ø3.4 at 0 /
   56.85 (B) / 63.075 (R); 4 thick, with two flush-head pockets Ø6.5×2 deep:
   at B opening UP (+Z face), at R opening DOWN. (The STL is two 2mm laminates
   only because the printing pipeline cannot cut counterbores; in Fusion just
   cut the two counterbores in a single 4mm body.)
3. plate1 — hollow triangle: 8-wide capsules along edges B(0,0)→C(38.852,0),
   C→P(17.5,-56.5), P→B; Ø3.4 at all three points; 4 thick. Do NOT fill the
   triangle — filled plates collide with the posts (proven).
4. rocker1 — capsule (0,0)→(35.071,0), Ø3.4 both ends, 4 thick.
5. plate2 — hollow triangle P(0,0)→D(29.5,0)→Q(99.996,-65.744)→P, same recipe.
6. rocker2 — capsule (0,0)→(70,0), Ø3.4 both ends, 4 thick.
7. bar — capsule 12 wide, 4 thick, axis (0,0)→(197.6,0); Ø3.4 pivot at origin;
   slot 5.4 wide, centerline from x=120.0 to x=197.5 (rounded ends). The slot
   ends are the stroke stops — exact, do not lengthen.
8. shuttle — boss Ø5×4.4 below a Ø16 flange, total height 6.0, Ø3.4 through;
   hex recess across-flats 5.8, depth 4.5, in the top face.
9. ring — flat 2.5 thick: hub Ø7 with Ø3.4 hole, ring band ID16/OD20 centered
   on the hub, three 1.6-wide spokes hub→band.
10. posts — Ø8 tubes, Ø3.4 bore: lengths 6 (O4), 30 (O2), 42 (ANCH), 54 (O6),
    one each (post_by_ground in the json).
11. sleeves — Ø6.5 tubes, Ø3.4 bore: 8 long ×4 (joints B, C, D, R), 44 long ×1
    (joint P) (sleeve_by_joint in the json).
Screws/nuts/washers: optional; model as cylinders or omit. The screw table in
PRINT.md is for the physical build, not the CAD.

Z-STACK (link bottom heights; link tops +4)
level 0 rocker1 z=10 · 1 plate1 z=22 · 2 crank z=34 · 3 bar z=46 ·
4 rocker2 z=58 · 5 plate2 z=70. Plate occupies z 0..4. Posts stand plate top →
their link bottom; sleeves span lower-link top → upper-link bottom at each
joint. Ring sits on plate2's top (z=74); shuttle rides the bar top (z=50).

PLACEMENT AT MID-STROKE (then let joints govern)
Use pose_checkpoints['mid'] from the json. Each part's local frame: first hole
at the listed world point, local +X aimed at the second: crank O2→B, plate1
B→C, rocker1 O4→C, plate2 P→D, rocker2 O6→D, bar ANCH→R. Mounts are fixed at
mounts_model_mm. All rotations are about Z only.

JOINTS (target: exactly 1 degree of freedom)
- Ground the backplate. Rigid-join each post to the backplate at its mount,
  each sleeve may be rigid to either of its two links, ring rigid to plate2 at
  Q.
- Revolute (Z axis) at: O2 backplate↔crank, O4 backplate↔rocker1,
  O6 backplate↔rocker2, ANCH backplate↔bar, B crank↔plate1,
  C plate1↔rocker1, P plate1↔plate2, D plate2↔rocker2.
- Shuttle: revolute shuttle↔crank at R, plus a slider/pin-slot shuttle↔bar
  along the bar's slot axis. If Fusion fights the closed-loop constraint
  system, the pin-slot (rotation + translation in one joint) between shuttle
  and bar is the robust choice. Optionally set joint limits to the slot span
  (120..197.5 from the pivot) — that is the actuator excursion 0..15.5″.

VERIFY (do all three, report results)
1. Drag the shuttle end to end: the mechanism must articulate smoothly and
   stop at both slot ends. If a joint pops, check the placement frame of that
   part against pose_checkpoints['mid'].
2. Measure the ring center (Q) at the two extremes and mid: expected model-mm
   XY — ext0: (-6.909, 110.456), mid: (70.625, 129.587),
   ext15.5: (4.972, 99.501). Tolerance ~0.1mm.
3. Run Fusion's Interference check at ext0, mid, ext15.5. The design was
   cleared per-pose in Python (tightest hardware gap 7.1mm; link planes are
   12mm apart with 8mm air) — any interference means a transcription error,
   not a design error.
Take a screenshot of the finished assembly for the owner.

CAUTIONS
- The hole/slot dimensions carry 3D-print clearances (Ø3.4 for M3, slot 5.4
  over a Ø5 boss, pockets Ø6.5). Keep them exactly — they are the spec.
- The STLs stack sections with 0.1mm overlaps (slicer-friendly EPS); when
  modeling natively, make faces exactly coplanar instead.
- Level order, hollow plates, the trimmed bar tip, and the flush pockets at
  B/R are all load-bearing results of a collision search — do not "improve"
  any of them.
- Ask the owner before any destructive Fusion operation (closing unsaved
  docs, overwriting designs). Do not commit, push, or edit the repo.
