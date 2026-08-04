# Plan: find a wild scale curve that is not at dead center

Written 2026-08-04 for whoever picks this up next. Read `README.md`'s "Dead
center" section first — this plan assumes it.

## What the owner wants

Scale curves shaped like **`example-08`** (their favourite) and **`example-00`**.
Not arcs. Not "a ribbon that comes back up and crosses over itself once". The
eleven `example-*` presets have the right character; the six `clean-*` ones do
not, and the owner has said so twice.

The catch: `example-08` and `example-00` both sit at **0.8°** from dead center.
They are exactly the designs the dead-center section says not to build.

**The question this plan exists to answer: is that shape available at a safe
transmission angle, or is wildness inseparable from the singularity?**

Nobody has actually asked that yet. Read the next section before assuming the
answer is no — the previous runs did not test it.

## What "wild" is, numerically

Measured over the full Joyce stroke with `tools/explore_designs.py`:

| | len″ | loops | rev | wig | **both** | **dens** | trans° | stall |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `example-00` | 218 | 1 | 2 | 2.53 | **7.06** | **3.29** | 0.8 | 0.140 |
| `example-08` ← best | 131 | 2 | 3 | 5.98 | **4.71** | **1.99** | 0.8 | 0.169 |
| `example-07` | 91 | 6 | 3 | 10.70 | 1.71 | 1.51 | 0.1 | 0.093 |
| best `clean-*` | 117 | 1 | 3 | 3.02 | 3.96 | 1.80 | 40.0 | 0.503 |

The two columns that separate them are **`both`** (radians turned each way —
`min(pos, neg)`, so a curve that only ever turns left scores 0) and **`dens`**
(scale length ÷ envelope diagonal — how densely the curve packs its box).
`example-08` turns 4.71 rad *in each direction*; the wildest clean design manages
3.96, and most are near 0. Loop count is a weaker signal than it looks —
`example-07` has six loops and the owner did not pick it.

Note `example-08`'s `stall` is **0.169**, better than four of the six clean
designs. Wild does not mean it stalls. Do not trade that away.

### Why the earlier runs never produced this

Not a search failure — it was never requested. `--character BOTH REV WIG` was run
at `0.4 1 0.3` and `1.5 3 0.8`. `example-08` scores **4.71 3 5.98**. The gate was
set three to ten times below the target, so anything meeting it passed, and the
length and novelty objectives then chose among a field that had no wild designs
left in it. **Gate on the numbers in the table above, not on the old defaults.**

## Do this in order

### 1. Seed from `example-08` and climb the transmission angle (highest value)

The most direct experiment, and it has not been run. Do not start from random
seeds — start *at* the design that already has the shape, and walk uphill in
transmission angle while a penalty holds the shape in place.

Needs two small additions to `tools/explore_designs.py`:

- `--seedfrom FILE` — start the climb from these geometries (jittered, a few
  hundred copies) instead of `sample_box`.
- `--target FILE --targetdist D` — the mirror of the existing `--avoid`: penalise
  shape distance *above* D instead of below it. `shape_dist()` and
  `turning_desc()` already exist and are unit-tested; this is a sign flip and a
  score term, perhaps 15 lines.

Then sweep: for D in 2, 3, 4, 5 (the two original clean families sit 6.3 apart,
so D=3 is "recognisably the same design", D=5 is "same family"), find the highest
`ta` reachable. **Report the frontier, not a single answer.** The useful output is
a table of "shape distance from `example-08` vs best transmission angle".

If that curve reaches 40° at D≤4, the job is done — hand back five designs.

### 2. If it does not reach 40°, report where it does reach

This is a likely outcome and it is **not** a failure — it is the answer to the
question, and the owner should get it as a number rather than a shrug.

`example-08` is at 0.8°. A design with its shape at even 15–20° is **20× further
from the singularity**, and the README's own ladder calls 15° the rebuild line
rather than the danger line. That may be a perfectly good engineering trade for a
garden sculpture, especially with a detent or anti-backdrive gearbox — but it is
the owner's call, not the agent's. Give them the frontier and say plainly what
each point costs.

Do not quietly relax `--tamin` to 20 and present the results as clean. The word
"clean" in this repo means ≥40°; the `verify_export.py` gallery check enforces it
and will fail. Name a lower-angle family something else.

### 3. Widen the parameter box — it is currently binding

`LO`/`HI` in `explore_designs.py` are pinning real designs against the wall:

| param | designs at the edge | current range |
|---|--:|---|
| `cv2` | **9 of 17** | ±20 |
| `L5` | 6 of 17 | 8–24 |
| `cu` | 4 of 17 | 0–24 |
| `L3` | 4 of 17 | 10–26 |

`cv2` is the stage-2 coupler offset — the loop-making parameter — and more than
half the gallery is jammed against its limit. The box was widened once before for
exactly this reason (see the comment above `LO`). Try `cv2` ±32, `cu2` 0–34,
`L5` 8–32, then re-run step 1.

Two cautions: designs found in a wider box are not comparable to older runs, so
say so in the report; and the 48″×48″ envelope cap is a real garden constraint,
so keep it — a bigger box must buy shape, not size.

### 4. Only then, a fresh search with the right gates

If steps 1–3 have not produced it, run the general search with
`--character 4.0 3 4.0` and a new `dens` gate (there is currently no CLI for
`dens`; add one, target ≥2.0). Expect a low yield — budget several runs and merge
them with `--merge`.

## Constraints that are not negotiable

- **Memory.** `--batch` is the killer: peak RSS ≈ `batch × nsamp × 8 × 25` bytes.
  The default 12k is ~0.6 GB. Sixteen parallel runs at 60k OOM'd this machine on
  2026-08-04. Five processes at `--batch 6000` is ~2.5 GB and safe. Launch with
  `setsid` so they survive the session, and watch `free -g`.
- **Verification after any page edit**, all four, all passing:
  `tools/verify_export.py`, `tools/verify_mobile.py`, `tools/sync_core.py`,
  `tools/crosscheck_port.py`. Presets live in the shared core: edit `index.html`,
  then `sync_core.py --apply`. The `<option>` rows are page-specific and must be
  edited in both files by hand.
- **`--selfcheck` must pass**, and extend it if you add metrics.
- **Preset names are never renumbered.** The owner selects by number; gaps in the
  sequence are deliberate.
- **Measure what ships.** The search runs the full 16″ stroke; the page ships
  `extMax 15.5`. Quote page-measured numbers in dropdown labels and docs.
- **Envelope ≤48″×48″**, mount clearance ≥2.5″, `stall` ≥0.07″/°F. The owner
  rejects designs that stall — see the first tuned serpentine in `CLAUDE.md`.

## Hand back

- Five designs, or fewer with an explicit reason.
- For each: scale length, loops, `both`, `dens`, transmission angle, stall, mount
  clearance, and shape distance to `example-08` and to every shipped preset.
- The frontier table from step 1, whatever it shows.
- A contact sheet: `render_designs.py --presets out.png /tmp/x <prefix>`.
- A plain statement of whether the question at the top was answered yes or no.

## One thing to be careful about

An earlier claim in this repo — that loops are absent above 40° — was wrong, and
was committed to the README before being caught. It came from reading the output
of a length-maximising search as if it described the mechanism. A search finds
what its objective rewards; the absence of X in results that never asked for X is
evidence about the objective, not about the geometry. Check that a claim survives
a search that actually looks for the thing before writing it down.
