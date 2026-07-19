# TODO

Open work and known concerns. Fabrication measurements and the DXF layer
reference live in [FABRICATION.md](FABRICATION.md); design constraints and code
architecture in [CLAUDE.md](CLAUDE.md).

## Blocking fabrication

- [ ] **O2 clears the path by only 2.06″** — the rule is ≥2.5″, so it is short
      by 0.44″. Every other mount is comfortable (O6 5.28″, ACT 15.77″,
      O4 16.11″). Either move O2 or accept the clearance and record why.
      The mount-to-mount *crossing* rule was dropped on 2026-07-19; only
      clearance still applies.
- [ ] **Actuator headroom is ~0.25″.** `dA+rA = 40.25″` stops the drive
      triangle closing past ~15.75″ of extension, and the excursion is 15.5″.
      Re-run `tools/analyze_geometry.py` after touching `dA`, `rA` or the
      excursion — this is the constraint most likely to be broken silently.

## Fabrication document

- [ ] Pivot hardware: bearing or bushing type, fastener sizes, retention.
- [ ] Actuator mounting-triangle detail — anchor and rod-end brackets.
- [ ] temp→extension calibration table for the controller. Mapping is linear
      within the excursion, optionally reversed:
      `ext = extMin + (T−Tmin)/(Tmax−Tmin) × (extMax−extMin)`.

## Nice to have

- [ ] `.linkage2` export — the chosen geometry as XML for David Rector's
      Linkage program (Windows, blog.rectorsquid.com). Not started.
- [ ] Auto-thin the °F labels where the scale crowds them. At the cold end
      −20..10 the labels nearly touch; at the hot end they are far apart.
- [ ] `PATHW = 1.0″` (engraved path width, used for the DXF division length)
      is hardcoded in `buildPoints()`. Expose it as a field if it needs tuning
      against real stock.
- [ ] The README GIF predates the bounding box and the current geometry.
      Regenerating costs another ~4.6 MB in git history, so it was left alone.

## Design decisions to re-confirm

- [ ] The scale is very uneven — 10°F steps run 0.79″ to 16.36″ (20.7×), and
      the slowest degree covers 0.073″. Both are well outside the original
      search constraints. Accepted as an aesthetic choice; worth one more look
      before it is cut, since it cannot be changed afterwards.
- [ ] **Near-cusp at 43.5°F**: the indicator slows to 0.111 in/°F and the path
      turns 10°. A tight corner to engrave and a spot where the reading barely
      moves.
- [ ] Owner once asked for "beginning and ending point control for actuator";
      the clarification came back "no preference". The excursion fields may
      already cover it. Confirm before building anything else.

## Settled — do not redo

These were tried and deliberately reverted or removed. The reasons are in
CLAUDE.md; listed here so they do not get "fixed" again.

- Sub-ticks at 1° — built, then removed. The path divisions say the same thing.
- White tick strokes beside the path — removed. The indicator ring covers
  anything alongside the path.
- The groove drop-shadow — deleted. It was what made the divisions appear only
  where the path climbs.
- Auto-restoring settings from localStorage on load — removed. The page always
  opens on the defaults in `index.html`; saved designs are opt-in only.
- The mount-to-mount crossing rule — dropped by the owner.
