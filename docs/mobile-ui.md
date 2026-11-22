# mobile.html — what it does differently

Moved from `CLAUDE.md` on 2026-11-22. The shared-core rule (edit physics in `index.html`, then `python3 tools/sync_core.py --apply`) is in `CLAUDE.md`.


- **No geometry sliders** — all 16 (`L2 L3 L4 gx gy cu cv L5 L6 ox oy cu2
  cv2 rA dA anch`) are gone; the 10 canvas handles set them. Kept: excursion
  min/max, both stage flips, rotation, temperature range, display toggles,
  presets, saves and both DXF exports. `verify_mobile.py` asserts the id-set
  difference against index.html EXACTLY, so a forgotten control and an
  over-eager deletion both fail.
- **Bottom sheet** (`#sheet`, `.peek` 44px / `.open` 72dvh) instead of the
  left panel; tap or drag the grab pill. The fit is pinned to the COLLAPSED
  height on purpose — opening must not make the drawing jump. In landscape a
  media query turns it into a 300px left drawer.
  Collapsed it shows **only the pill**: `.peek` drops the background, border
  and shadow, so the 44px strip is still there to be thumbed but nothing is
  painted over the drawing. The owner asked for this after seeing a 168px
  peek that carried the readout tiles and the reading slider — the numeric
  °F now lives behind the pill, and the ring on the path is what you read at
  a glance. Don't put the tiles back without asking.
- **`touch-action` sits on the canvas, not on `html,body`.** index.html's
  body-level `touch-action:none` is exactly what makes a scrolling panel
  impossible on a phone; the sheet body is `pan-y` with `overscroll-behavior:
  contain`.
- **Every range input is `touch-action:pan-y` as well**, and that one rule is
  load-bearing. A slider spans the full width of the sheet and claims the
  touch the moment a gesture starts on it, so scrolling the sheet dragged
  whichever slider the thumb crossed. `pan-y` hands vertical movement back to
  the scroller and leaves the slider only the horizontal — the one direction
  that ever meant to move it. It must sit on the input; `#sheetbody`'s own
  `pan-y` does not reach it. The test asserts the computed value on all three,
  because touch-action is enforced by the compositor and synthetic pointer
  events bypass it — the mechanism is what can be checked, and the mechanism
  is the fix.
- **Gestures**: a `Map` of live pointers. Two fingers = pinch + two-finger
  pan, anchored on the midpoint, and it outranks any in-flight drag. Double
  tap (<320ms, <40px, and only if the release didn't move) recenters.
  `zoomAt(sx,sy,f)` is shared by pinch and wheel.
- **Hit radius 30px for a non-mouse pointer**, 20 for a mouse. Note the real
  constraint: at 1× the whole 40″ piece is ~270px wide, so the joint pins sit
  **~10px apart** and a fingertip covers several. Nearest-wins picks
  something sensible, but picking a SPECIFIC joint means pinching in first —
  at 12× they are ~126px apart. The help text says so and the test asserts it.
  This is geometry, not a bug to fix.
- **The drag tooltip carries VALUES, not slider names** — `gx 9.7″  gy −3.4″`,
  pinned to the top of the canvas because your finger is on the part. It
  reuses `COMPINFO[id].sliders` as a parameter list through `fmtGeo`. With the
  sliders gone this is the only place those numbers appear live.
- **Floating toolbar: ONE ROW across the top** — `?` at the far left (pushed
  there by `margin-right:auto`), then `▶/⏸ ↶ ⟲ ⌖` at the right. Settled by the
  owner on 2026-08-01, after a right-hand column and a help button inside the
  sheet were both tried and rejected. Things that are load-bearing here:
  - `?` sits apart from the action group on purpose, so reaching for help can
    never be a mis-tap on Reset. It must stay at the LEFT end.
  - `↶` and `⟲` are adjacent and read alike at 19px, and one of them wipes
    everything — so `⟲` is tinted `--warn`. The glyphs alone are not enough.
  - Undo belongs next to Reset precisely *because* Reset is the destructive
    one. It was briefly moved out of the toolbar and the owner asked for it
    back.
  - The drag tooltip moved BELOW the row (`top:64px`), since the row now spans
    the full width and there is no space left at either end. In landscape both
    the row and the tip start clear of the drawer at 324px.
  - The play glyph and undo's disabled state are refreshed in a two-line rAF
    tick — `cfg.demo` and the undo stack are changed from half a dozen places
    and making each one announce itself would be more code, not less.
- **A drag does not pause the sweep — it winds it up to 1×**, `DRAGSPEED`
  (owner's call, 2026-08-01: "users can see the full excursion of their
  change"; 2× was tried first and read as too fast). `frame()`
  reads `speedOverride||cfg.speed`, and `cfg.speed` is never written, so the
  slider keeps the user's value and release just clears the override. Every
  exit from a drag goes through `endPointer`, which clears it unconditionally
  — a boost left switched on would be permanent. Consequence worth knowing:
  the four ground mounts hold still while animating, so dragging those is
  exactly the intended experience, but R, B, C, P, D and Q ride the mechanism
  and move under your finger. Pause with ⏸ to pin one down.
- **A tap does not pause either.** index.html stops the sweep on pointerdown;
  here the touch radius is 30px over pins ~10px apart, so almost any tap in
  the middle of the drawing lands on a handle and would silently stop
  playback. The boost waits for real movement (`dragMoved`), so a stray tap
  costs nothing — same gate that arms undo.
- **All typed controls are ≥16px**, or iOS zooms the page on focus. Tap
  targets ≥44px. `100dvh`, `env(safe-area-inset-*)`, `viewport-fit=cover`.
- **resize** is rAF-debounced and also bound to `orientationchange` and
  `visualViewport.resize` — the mobile URL bar fires `resize` continuously.
- `index.html` redirects a narrow touch screen here (3 lines in `<head>`);
  **`?desktop=1` escapes it**, and that is the documented way to get the
  sliders back on a phone.
