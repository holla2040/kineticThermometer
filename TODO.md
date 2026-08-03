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
- [ ] **Actuator headroom is ~0.25″ on the GENERIC actuator.** `dA+rA = 40.25″`
      stops the drive triangle closing past ~15.75″ of extension, and the
      excursion is 15.5″. Re-run `tools/analyze_geometry.py` after touching
      `dA`, `rA` or the excursion — this is the constraint most likely to be
      broken silently. **The Joyce type retires this**: at the as-modeled
      clamp position (c0=23.23″) the full 16″ stroke closes with 0.45″ to
      spare, asserted by `verify_export.py`. Decide which actuator the build
      uses and re-tune the excursion accordingly.
- [ ] **The joyce tube tail is not in the bounding box.** `buildBBox` bounds
      the path, joint traces and mounts; up to ~24.7″ of actuator body sweeps
      behind the clamp and isn't counted in the footprint readout. fitView
      DOES include it (the drawing and the drag handle stay on screen) — this
      is only about the measured w×h. Owner call on whether the envelope
      should include the actuator.

## Fabrication document

- [ ] Pivot hardware: bearing or bushing type, fastener sizes, retention.
- [ ] Actuator mounting-triangle detail — anchor and rod-end brackets. For the
      Joyce: the clamp's pivot pin and rod clevis both take Ø0.472″ (12 mm)
      pins; see the measured table in FABRICATION.md.
- [ ] `JOYCE.side` (which side of the tube the pivot ear points, +1/-1 in the
      code) is a mounting choice — confirm against the sculpture plane before
      welding the clamp mount.
- [ ] temp→extension calibration table for the controller. Mapping is linear
      within the excursion, optionally reversed:
      `ext = extMin + (T−Tmin)/(Tmax−Tmin) × (extMax−extMin)`.

## Nice to have

- [ ] `.linkage2` export — the chosen geometry as XML for David Rector's
      Linkage program (Windows, blog.rectorsquid.com). Not started.
- [ ] `PATHW = 1.0″` (engraved path width, used for the DXF division length)
      is hardcoded in `buildPoints()`. Expose it as a field if it needs tuning
      against real stock.
- [ ] The README GIF predates the bounding box and the current geometry.
      Regenerating costs another ~4.6 MB in git history, so it was left alone.

## Mobile (mobile.html, added 2026-07-31)

- [ ] **Only 6 of the 14 °F labels survive on a phone at 1×.** The thinning
      rule is honest — they genuinely overlap at that scale, and pinching in
      brings the rest back — but the owner has not seen it on real hardware
      yet. If it reads as too sparse, `LBLGAP` in `drawScale` is the knob.
- [ ] **Joint pins sit ~10px apart at the default zoom.** A fingertip covers
      several; nearest-wins picks one, and pinching to ~12× spreads them to
      ~126px. The help says so and `verify_mobile.py` asserts it. Worth
      confirming this is workable in the hand before calling it settled — the
      alternative would be a "zoom to a joint" affordance, which is more UI.
- [ ] Fine numeric entry on a phone is pinch-and-drag only. `?desktop=1`
      reaches the full slider panel on the same device; if that turns out to
      be the thing actually reached for, a numeric-entry sheet for the
      selected handle is the smallest fix.
- [ ] Untested on real iOS/Android hardware — everything so far is headless
      Chromium at a 390×844 phone viewport. The `dvh`, safe-area and
      focus-zoom work is exactly the kind that only fails on the real device.

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
- A responsive `index.html` for mobile — the owner chose a separate
  `mobile.html` instead, with `tools/sync_core.py` holding the shared half
  identical. Don't merge them back without asking.
- Geometry sliders on `mobile.html` — deliberately removed ("rely more on
  user dragging"). All 16 are set by dragging their pin. `?desktop=1` is the
  escape hatch, and `verify_mobile.py` asserts the exact id-set difference,
  so adding one back will fail the suite on purpose.
