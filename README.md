# Kinetic Thermometer

**[Live demo →](https://holla2040.github.io/kineticThermometer/)** ·
**[Phone version →](https://holla2040.github.io/kineticThermometer/mobile.html)**

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
  angle. Double-click recenters and resets zoom. Exports DXF for Fusion —
  see below.
- `mobile.html` — the same simulator, portrait-first for a phone, served at
  <https://holla2040.github.io/kineticThermometer/mobile.html>. A narrow
  touch screen opening the live demo lands here automatically; add
  `?desktop=1` to force the desktop page instead. The controls hide behind
  the pill at the bottom of the screen — tap or drag it to bring the sheet
  up, and collapsed it gives the whole screen to the drawing. **There are no
  geometry sliders**: every
  length and mount position is set by dragging its pin, with the values you
  are changing shown at the top of the screen. Pinch to zoom (also how you
  get fine control — at 12× a pixel is about a hundredth of an inch),
  double-tap to recenter, and use the ▶ ↶ ⌖ buttons in place of the
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

## Dead center — the thing to understand before you build one

If you only read one section of this repository before committing metal to a
design of your own, make it this one. It is the difference between a sculpture
that tells the time of day in degrees and one that quietly lies to you.

You do not need any mechanism theory to follow it. Start with a bicycle.

### The bicycle pedal

![A crank at dead center gets no turning force from a straight-down push: on the
left the pedal is at the top of its circle and the push produces no rotation; on
the right, a quarter turn later, the same push has full leverage](images/dead-center-pedal.svg)

When the pedal is at the very top, your foot, the crank and the axle are in one
straight line. Push straight down as hard as you like — the crank does not turn.
Which way it eventually goes is decided by your other foot, or by the bike
rocking, not by how hard you pushed.

That position has a name: **dead center**. Any linkage can reach one, and this
sculpture has two places where it can happen.

### Why a linkage has the same problem

The joints this mechanism has to *solve* for are found the same way: by
crossing two circles. (The others come straight off the crank angle.)

Take pin **D**. It has to sit exactly `L5` away from point P, and exactly `L6`
away from the ground mount O6. Draw a circle of each radius and D is where they
cross.

![Two circles cross at two points, so there are two valid ways to assemble the
linkage — the simulator picks one branch and stays on it](images/dead-center-two-branches.svg)

Two circles normally cross at **two** points. Both are perfectly valid
assemblies — that is exactly what the "assembly branch" flips in the panel
switch between. The mechanism sits on one and stays there.

Now push the circles apart until they only just touch:

![When the two circles are tangent the two solutions merge into one and the
linkage is at dead center, with both links in a straight line](images/dead-center-tangent.svg)

The two crossings have merged into one. The two links are in a straight line —
the pedal at the top of its circle. Push a hair further and the circles do not
touch at all: there is no solution, and the simulator simply stops drawing the
linkage. That is the red "can't assemble" warning.

### Where it can happen here

![The drive chain from actuator through bell crank, B, C, P and D to the
indicator Q, showing that only C and D are found by crossing circles](images/dead-center-chain.svg)

Motion runs one way along that chain, and only **C** and **D** are found by
crossing circles. They are the only two joints that can go dead. The actuator's
own triangle could in principle do the same, but the code already keeps a hard
0.5″ margin there, so it never gets close.

### The number that measures it: transmission angle

![Transmission angle at a joint: 65 degrees is healthy, 22 degrees is getting
tight, 4 degrees is effectively dead center](images/dead-center-angle.svg)

At each of those joints, measure the angle between the link arriving and the
link being driven. That is the **transmission angle**.

- **90°** — perfect. All of the push goes into moving the next link.
- **above ~40°** — normal engineering practice.
- **near 0°** — dead center. The links are in a line and the push goes nowhere.

It is not a matter of opinion or of guessing which link pushes which. The angle
is fixed by the triangle formed by the two link lengths and the distance between
their anchor points, and it hits zero at exactly the moment the two circles stop
crossing. Same event, two ways of describing it.

### How the presets measure up

![Where each preset falls on the transmission-angle scale: the eleven search
examples all sit in the red zone below 6 degrees, serpentine reaches 7.7 degrees
and Grand Arc 33.9 degrees](images/dead-center-ruler.svg)

Every preset in the dropdown, worst case across its whole temperature range.
The jump column is what one press of the ↑ key does — 0.1″ of actuator travel:

| preset | closest approach to dead center | worst jump per 0.1″ of actuator |
|---|--:|--:|
| the six `clean-*` | **40.0° – 50.1°** | **0.7″ – 1.9″** |
| Grand Arc | 33.9° | 0.5″ |
| the six `shape-*` | 6.9° – 25.3° | 0.4″ – 3.2″ |
| Serpentine | 7.7° | 2.3″ |
| `example-00` … `example-10` | **0.06° – 5.9°** | **4.6″ – 28.9″** |

The two hand-tuned designs clear the danger zone. **All eleven `example-*`
presets sit inside it** — which is why each is marked with a `*` in the menu.

That is not bad luck. Those eleven came out of a numerical search told to make
the scale as long as possible, and near dead center the indicator sweeps furthest
for the least input — so "make it long" and "ride the singularity" turn out to be
the same instruction. The search walked straight to the edge and sat on it. They
are wonderful to watch and a perfect illustration of what to check for.

![The eleven example presets, each showing the curve its indicator traces and
the scale length in inches: spirals, loops, hooks and S-curves ranging from 91
to 201 inches](contact-sheet.png)

All eleven, as the dropdown draws them. Pick any one and watch it sweep — then
watch pins C and D. Regenerate this sheet with
`python3 tools/render_designs.py --presets contact-sheet.png`, which reads the
presets out of `index.html` rather than a saved file, so it cannot show a curve
the menu does not actually produce.

### The same search, told to stay away from the edge

The `clean-*` presets are the answer to the obvious follow-up question: if the
search only found those eleven because nothing stopped it, what does it find when
something does? `tools/explore_designs.py` now measures the transmission angle at
C and D exactly the way the page does, and `--tamin 40` refuses any design that
drops below the 40° figure this section recommends.

That first run produced ten, of which the owner kept three: the other seven were
variations on two shapes rather than seven designs. A second run then had to be
told what "a different shape" means — see "Asking for a shape you have not seen
yet" below — and produced the remaining three.

![The six clean presets, each showing the curve its indicator traces and the
scale length in inches: open C-curves, nested arcs, an S and two self-crossing
curves, from 61 to 111 inches](contact-sheet-clean.png)

    python3 tools/explore_designs.py --tamin 40 --minlen 60 --trials 3000000
    python3 tools/render_designs.py --presets contact-sheet-clean.png /tmp/x clean-

Three things that run of the search settled, all of them worth knowing before you
draw a curve you like and then go looking for a linkage that traces it:

- **Healthy is common; healthy *and* long is not.** 94% of assemblable random
  geometries keep 10° or better. But in 2.4 million random trials, not one reached
  40° with even a 70″ scale. Every one of these ten had to be hill-climbed to.
- **A length-maximising search finds no loops above 40°, but they are there.**
  This is worth stating carefully, because the first run made it look like a law
  of the mechanism: every design it returned at 40° was an arc or an open spiral,
  and the obvious conclusion was that crossings and cusps simply *are* the
  singularity and cannot be had safely. That conclusion was wrong. Told to hunt
  for unfamiliar shapes instead of long ones, the same search returns curves that
  cross themselves once to three times at 40°–53°. What loops actually cost is
  even movement. Among the six kept, the two self-crossing designs sit at the
  bottom of the range at 0.074″ and 0.092″ per °F, while the loop-free ones reach
  0.50″ — though they overlap, since loop-free `clean-07` also stalls to 0.092″.
  That is a readability problem, not a branch-flip problem, and 0.075″ is what the
  owner's own serpentine manages.
- **You pay for it in scale length, and less than you would think.** The kept
  designs run 61″–111″ against the examples' 91″–201″, and get a linkage that
  cannot flip branch in a gust of wind.

They come out ahead on the fabrication rule too, which was not asked of them:
each keeps its mounts **2.89″–10.37″** off the engraved path, clearing the 2.5″
rule that the chosen serpentine misses at 2.06″. That is luck, not design — a
design far from dead center is not automatically buildable, and `clean-*` still
needs the rest of `analyze_geometry.py` run over it before anyone cuts metal.

### The same shapes, walked away from the edge

The `shape-*` presets answer a third question: not "what does the search find
when fenced off" but "can a shape chosen for its looks be moved to safety?"
Two provenances, one method — hold a target curve's shape while the search
climbs transmission angle:

- `shape-01` / `shape-02` hold the shapes of example-08 and example-00 at
  **13.1°** and **16.7°** — sixteen to twenty times the 0.8° margin those two
  seeds ride, at the cost of some scale length (88″ vs 129″, 138″ vs 201″ as
  shipped).
- `shape-03`…`shape-06` began as freehand drawings that never came from any
  linkage (`tools/propose_shapes.py`). An approximate-path-synthesis search
  (`explore_designs.py --targetpts --objective match`) found each drawing's
  closest mechanism curve, then climbed away from dead center holding that
  shape. The owner picked these four from a tagged sheet of every candidate;
  they land at **6.9°–25.3°**.

None reaches the 40° this section recommends, which is why the family is
named `shape-*` and not `clean-*`: how far from the singularity is far enough
is a judgment call, and every label carries its true minimum angle so nobody
has to re-derive it. The full frontier — what each increment of shape drift
buys in transmission angle, and which drawn shapes turned out to be
unreachable outright — is in `REPORT.md`.

### Asking for a shape you have not seen yet

Re-running the search with a new random seed does not give you a new shape. It
gives you another member of whichever family the objective favours, which is how
the first ten came back as two families wearing ten names. To get something
genuinely different the search has to be told what "different" means.

`--avoid designs.json --novelty N` does that. Each curve is reduced to its
**turning function** — how much it has turned, measured at ten equal-arc-length
stations, as turn per unit length. A circle is flat at 2π, a half circle flat at
π, an S changes sign, a spiral sits high. Position, rotation and size fall out by
construction, and mirroring the curve or running it backwards are folded out in
the comparison, so nothing scores as novel for being the same curve hung the
other way round. `--novelty` is then the distance, in radians, a design must keep
from every shape in the avoid file.

Two things about it are not adjustable to taste:

- **Ten stations, not twenty.** The resolution was calibrated against the owner's
  own grouping of the first ten designs into two families. At ten stations or
  fewer the closest cross-family pair is further apart than the widest
  within-family pair; by twelve that has inverted, because the measure has
  started describing local wiggle rather than overall shape.
- **It compares increments, not cumulative turning.** Running a cumulative
  profile backwards mixes its endpoint value into every difference, so it is not
  an isometry and the distance came out asymmetric — A was 1.9 from B while B was
  2.7 from A. On increments both symmetries are isometries and the distance is a
  metric. `--selfcheck` asserts it.

For scale: the two original families sit 6.3 apart at their closest. The designs
from the second run are at least 7.3 from every earlier shape, and at least 11.0
from *each other* — further apart, pairwise, than the two families they were told
to avoid.

### What goes wrong, part one: the scale becomes unreadable

![Near dead center the one-degree scale marks bunch up and then a single degree
jumps the whole width of the sculpture](images/dead-center-scale.svg)

The scale is engraved with a mark every degree. Near dead center the indicator
is moving enormously fast for a small actuator movement, so consecutive degrees
land far apart — while just before it, they pile on top of each other.

On one design the search found (kept out of the menu for this reason), a single
degree moved the indicator **39.7 inches** — over three feet of engraved curve
between two marks. Elsewhere on the same curve, the slowest degree moves it
**0.195 inches**. That is a 200:1 spread across one temperature scale.

### What goes wrong, part two: it can start reading the wrong temperature

This is the serious one.

![After a snap-through the linkage settles on the mirror branch, putting the
indicator somewhere different for the same actuator position](images/dead-center-branch-flip.svg)

Remember that the two circles cross at two points, and the mechanism lives on
one of them. At dead center there is only one point — so nothing at all
determines which branch it comes off onto. Momentum, friction, a gust of wind,
gravity, or a few thousandths of slop in a pivot will decide.

If it comes off on the other branch, your sculpture is now assembled the mirror
way round. Nothing is bent. Nothing is broken. Nothing looks wrong. The
indicator is simply in a different place for the same temperature, and it stays
that way until something knocks it back through.

Outdoors, unattended, with wind and thermal cycling, that is not a hypothetical.

### What the simulator shows you

Three things, all live:

- **`*` in the preset menu** — this design passes within 6° of dead center
  somewhere in its range.
- **Pins C and D turn red** whenever their own transmission angle drops below
  6°. Run the sweep and watch: you will see exactly which joint, and at what
  temperature, the mechanism is in trouble.
- **The inner curve for that pin turns red too**, over the whole stretch of its
  travel that is inside the danger zone — so you can see the size of the problem
  with the animation paused. Turn on **Inner curves** in the Display section.

Load `example-05` and then `clean-08` and watch the difference: the first flashes
red at C and D and throws the ring across the piece, the second never colours at
all.

### If you are building one of these

1. **Watch the whole sweep before you cut anything.** Play the animation end to
   end with Inner curves on. If a pin flashes red, the design has a dead center
   in its working range.
2. **Aim for 40° minimum** transmission angle at both C and D. If you want a
   number to design to, that is the one.
3. **Treat anything under about 15° as a rebuild**, not a tweak. Dragging a
   handle a little will not fix it — the geometry wants to be there.
4. **A long scale is not automatically a good scale.** Length bought by
   approaching a singularity comes with both failure modes above. The chosen
   serpentine gives up length for a mechanism that behaves.
5. **Check the mount clearances separately.** Dead center is about the linkage;
   whether a mount lands on top of the engraved path is a different question, and
   `tools/analyze_geometry.py` reports it.
6. **Remember the simulator is frictionless and has no slop.** It will happily
   drive through a pose that real bearings, real wind loading and a real gearbox
   would jam, stall or snap through.

The eleven `example-*` presets are in the menu precisely so you can see all of
this happening in something real, rather than take it on trust — and the
`clean-*` ones so you can see what the same search produces when rule 2 is
enforced instead of hoped for.

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
