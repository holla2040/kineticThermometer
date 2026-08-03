"""Drives mobile.html headless on a phone viewport and checks the portrait build.

    pip install playwright && playwright install chromium
    python3 tools/verify_mobile.py [outdir]

Covers what the desktop harness cannot: the bottom sheet, touch-sized hit radii, pinch
zoom, two-finger and one-finger pan, double-tap, the drag tooltip that replaces the
deleted geometry sliders, control parity against index.html, iOS font-size floors, the
landscape drawer, and both DXF exports from the phone page.

Run tools/verify_export.py as well — that one covers the shared core against index.html.
"""
import math, os, sys, tempfile
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dxf import parse_dxf                                # shared with verify_export.py

MOBILE = "file://" + os.path.join(HERE, "mobile.html")
DESKTOP = "file://" + os.path.join(HERE, "index.html")
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir()

# the 16 sliders mobile.html drops, and the handle that sets each one instead.
# O2 is the frame origin: dragging it shifts every other mount the opposite way.
DRAG_OWNS = {
    "O4": ["gx", "gy"], "O6": ["ox", "oy"], "anchor": ["dA", "anch"],
    "R": ["rA"], "B": ["L2"], "C": ["L3", "L4"], "P": ["cu", "cv"],
    "D": ["L5", "L6"], "Q": ["cu2", "cv2"],
    "O2": ["gx", "gy", "ox", "oy", "dA", "anch"],
}
GEO_SLIDERS = {k for v in DRAG_OWNS.values() for k in v}
assert len(GEO_SLIDERS) == 16, GEO_SLIDERS

# --- synthetic pointer events -------------------------------------------------
# Playwright's touchscreen API taps only; it cannot express a two-finger pinch or a
# pointerType-tagged drag. The page listens to pointer events, so dispatch those.
PTR = """([type, id, x, y, ptype]) => {
  const c = document.getElementById('c');
  c.dispatchEvent(new PointerEvent(type, {
    pointerId: id, pointerType: ptype, isPrimary: id === 1,
    clientX: x, clientY: y, button: 0, buttons: type === 'pointerup' ? 0 : 1,
    bubbles: true, cancelable: true
  }));
}"""


def ptr(pg, type_, id_, x, y, ptype="touch"):
    pg.evaluate(PTR, [type_, id_, x, y, ptype])


def drag(pg, x0, y0, x1, y1, steps=6, ptype="touch", id_=1):
    ptr(pg, "pointerdown", id_, x0, y0, ptype)
    for i in range(1, steps + 1):
        ptr(pg, "pointermove", id_, x0 + (x1 - x0) * i / steps,
            y0 + (y1 - y0) * i / steps, ptype)
    ptr(pg, "pointerup", id_, x1, y1, ptype)


def pinch(pg, cx, cy, d0, d1, steps=8):
    """Two fingers spreading (d1>d0) or closing, centred on cx,cy."""
    ptr(pg, "pointerdown", 1, cx - d0 / 2, cy)
    ptr(pg, "pointerdown", 2, cx + d0 / 2, cy)
    for i in range(1, steps + 1):
        d = d0 + (d1 - d0) * i / steps
        ptr(pg, "pointermove", 1, cx - d / 2, cy)
        ptr(pg, "pointermove", 2, cx + d / 2, cy)
    ptr(pg, "pointerup", 1, cx - d1 / 2, cy)
    ptr(pg, "pointerup", 2, cx + d1 / 2, cy)


def double_tap(pg, x, y):
    """Both taps in ONE round trip -- the page allows 320ms between them."""
    pg.evaluate("""([x, y]) => {
      const c = document.getElementById('c');
      const fire = t => c.dispatchEvent(new PointerEvent(t, {
        pointerId: 1, pointerType: 'touch', isPrimary: true, clientX: x, clientY: y,
        button: 0, buttons: t === 'pointerup' ? 0 : 1, bubbles: true, cancelable: true}));
      fire('pointerdown'); fire('pointerup');
      fire('pointerdown'); fire('pointerup');
    }""", [x, y])


def ready(pg, animate=False):
    """After every load: neutralise pointer capture (synthetic pointer ids are not real
    active pointers, so setPointerCapture throws NotFoundError) and stop the sweep."""
    pg.evaluate("""([animate]) => {
      document.getElementById('c').setPointerCapture = () => {};
      document.getElementById('grab').setPointerCapture = () => {};
      if (!animate) { __ct.cfg.demo = false; document.getElementById('demo').checked = false; }
    }""", [animate])


def ids_of(pg):
    return set(pg.eval_on_selector_all("[id]", "els => els.map(e => e.id)"))


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3,
                        is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errs.append("console." + m.type + ": " + m.text)
          if m.type == "error" else None)
    pg.goto(MOBILE)
    pg.wait_for_timeout(600)
    assert not errs, errs
    ready(pg)
    print("loaded 390x844 @3x with no console errors")

    # ---- 1. the sheet ---------------------------------------------------
    assert pg.evaluate("__ct.sheetOpen") is False, "sheet must start collapsed"
    # collapsed, the sheet is the grab strip and nothing else
    peek = pg.evaluate("__ct.peek")
    assert 40 <= peek < 70, f"peek height {peek} should be just the grab strip"
    assert pg.eval_on_selector("#sheet", "e => getComputedStyle(e).backgroundColor")\
        in ("rgba(0, 0, 0, 0)", "transparent"), "the collapsed sheet must not paint a panel"
    assert pg.eval_on_selector("#grab", "e => e.getBoundingClientRect().height") >= 44, \
        "the grab strip is the only tap target in peek; keep it thumb-sized"
    gbox = pg.eval_on_selector("#grab", "e => e.getBoundingClientRect().toJSON()")
    pg.tap("#grab"); pg.wait_for_timeout(350)
    assert pg.evaluate("__ct.sheetOpen") is True, "tapping the grab bar must open the sheet"
    opened = pg.eval_on_selector("#sheet", "e => e.offsetHeight")
    pg.tap("#grab"); pg.wait_for_timeout(350)
    assert pg.evaluate("__ct.sheetOpen") is False, "tapping again must collapse it"
    assert opened > peek + 200, f"open sheet {opened} is barely taller than peek {peek}"
    print(f"sheet toggles {peek}px peek <-> {opened}px open")

    # a drag on the grab bar snaps the way it was heading
    ymid = gbox["y"] + gbox["height"] / 2
    pg.evaluate("""([y]) => {
      const g = document.getElementById('grab');
      g.dispatchEvent(new PointerEvent('pointerdown', {pointerId: 1, clientY: y, bubbles: true}));
      g.dispatchEvent(new PointerEvent('pointerup', {pointerId: 1, clientY: y - 60, bubbles: true}));
    }""", [ymid])
    pg.wait_for_timeout(300)
    assert pg.evaluate("__ct.sheetOpen") is True, "dragging the grab bar up must open it"
    pg.tap("#grab"); pg.wait_for_timeout(350)
    print("grab-bar drag snaps open; tap collapses")

    # the body is finger-scrollable -- index.html's body-level touch-action:none is
    # exactly what stops this, so assert the property, not just that it exists
    ta = pg.eval_on_selector("#sheetbody", "e => getComputedStyle(e).touchAction")
    assert ta == "pan-y", f"#sheetbody touch-action is {ta!r}, must be pan-y"
    assert pg.eval_on_selector("#c", "e => getComputedStyle(e).touchAction") == "none"
    pg.tap("#grab"); pg.wait_for_timeout(350)
    pg.eval_on_selector("#sheetbody", "e => e.scrollTop = 400")
    assert pg.eval_on_selector("#sheetbody", "e => e.scrollTop") > 200, "sheet body will not scroll"
    pg.eval_on_selector("#sheetbody", "e => e.scrollTop = 0")

    # Every range input must hand vertical movement back to the scroller, or a thumb
    # swiping up the sheet drags whichever slider it happens to cross. touch-action is
    # enforced by the compositor and synthetic pointer events bypass it, so this asserts
    # the mechanism rather than the gesture -- but the mechanism IS the fix.
    bad = pg.eval_on_selector_all(
        "#sheet input[type=range]",
        "els => els.filter(e => getComputedStyle(e).touchAction !== 'pan-y')"
        ".map(e => e.id + '@' + getComputedStyle(e).touchAction)")
    assert not bad, f"sliders that will steal a vertical scroll: {bad}"
    nr = pg.eval_on_selector_all("#sheet input[type=range]", "e => e.length")
    pg.tap("#grab"); pg.wait_for_timeout(350)
    print(f"sheet body scrolls (touch-action {ta}); all {nr} sliders are pan-y, "
          f"so a vertical swipe scrolls instead of dragging them")

    # ---- 2. the drawing clears the collapsed sheet ----------------------
    clear = pg.evaluate("""() => {
      const names = ['O2','O4','O6','anchor','R','B','C','P','D','Q'];
      const t0 = __ct.cfg.tmin, t1 = __ct.cfg.tmax, keep = __ct.cfg.temp;
      let worst = -1e9, at = null;
      for (let i = 0; i <= 140; i++) {
        __ct.cfg.temp = t0 + (t1 - t0) * i / 140;
        for (const n of names) {
          const s = __ct.pivotScreen(n);
          if (!s || !isFinite(s.y)) continue;
          if (s.y > worst) { worst = s.y; at = n; }
        }
      }
      __ct.cfg.temp = keep;
      return {worst, at, limit: innerHeight - __ct.peek};
    }""")
    assert clear["worst"] <= clear["limit"], \
        f"{clear['at']} reaches y={clear['worst']:.0f}, under the sheet at {clear['limit']}"
    print(f"drawing clears the sheet: lowest point {clear['worst']:.0f} of {clear['limit']}")

    # ---- 3. control parity against index.html ---------------------------
    d = ctx.new_page()
    d.goto(DESKTOP + "?desktop=1")
    d.wait_for_timeout(500)
    desktop_ids, mobile_ids = ids_of(d), ids_of(pg)
    d.close()
    missing = desktop_ids - mobile_ids
    extra = mobile_ids - desktop_ids
    # the sheet replaces panel/hide/toggle, and the hint bar's advice was mouse-only
    expect_missing = (GEO_SLIDERS | {k + "V" for k in GEO_SLIDERS}
                      | {"panel", "hide", "toggle", "hint"})
    expect_extra = {"sheet", "grab", "sheethead", "sheetbody", "tools",
                    "tbReset", "tbFit", "tbPlay", "tbUndo"}
    assert missing == expect_missing, \
        f"unexpected difference\n  only missing should be geometry sliders\n" \
        f"  missing but should not be: {sorted(missing - expect_missing)}\n" \
        f"  should be missing but is not: {sorted(expect_missing - missing)}"
    assert extra == expect_extra, f"unexpected mobile-only ids: {sorted(extra ^ expect_extra)}"
    print(f"control parity: {len(mobile_ids & desktop_ids)} shared ids, "
          f"{len(GEO_SLIDERS)} geometry sliders dropped by design")

    # ---- 4. every dropped slider is still reachable by dragging ---------
    # this is the whole justification for removing them
    at = "([n]) => { try { return __ct.pivotScreen(n); } catch (e) { return null; } }"
    for handle, keys in DRAG_OWNS.items():
        # back to the preset each time: one drag can leave the linkage unassemblable,
        # and then the NEXT handle has no screen position to grab
        pg.eval_on_selector("#reset", "e => e.click()")
        pg.evaluate("__ct.cfg.temp = 70; __ct.rebuild()")
        s = pg.evaluate(at, [handle])
        assert s and math.isfinite(s["x"]), f"{handle} has no screen position at 70F"
        before = pg.evaluate("([ks]) => ks.map(k => __ct.geo[k])", [keys])
        drag(pg, s["x"], s["y"], s["x"] + 26, s["y"] + 22)
        after = pg.evaluate("([ks]) => ks.map(k => __ct.geo[k])", [keys])
        moved = [k for k, a, c in zip(keys, before, after) if abs(a - c) > 1e-9]
        assert moved, f"dragging {handle} changed none of {keys} ({before} -> {after})"
    print(f"all {len(DRAG_OWNS)} handles drive their geometry: " +
          ", ".join(f"{h}->{'+'.join(k)}" for h, k in DRAG_OWNS.items()))

    # ---- 5. only the button pauses; a drag earns it by moving ------------
    # A tap must NOT pause. The touch radius is 30px over pins ~10px apart, so almost
    # any tap in the middle of the drawing lands on a handle -- if touch-down paused,
    # playback would stop every time someone poked the screen.
    pg.reload(); pg.wait_for_timeout(600); ready(pg, animate=True)
    assert pg.evaluate("__ct.cfg.demo") is True, "Animate is on by default"
    pg.evaluate("__ct.cfg.temp = 70")           # pin the pose; the sweep is still running
    s = pg.evaluate("__ct.pivotScreen('O4')")
    gx_tap = pg.evaluate("__ct.geo.gx")
    ptr(pg, "pointerdown", 1, s["x"], s["y"])
    assert pg.evaluate("__ct.cfg.demo") is True, "touching a handle must NOT pause"
    assert pg.eval_on_selector("#tip", "e => getComputedStyle(e).display") == "block", \
        "the drag tooltip must still appear on grab"
    ptr(pg, "pointerup", 1, s["x"], s["y"])
    assert pg.evaluate("__ct.cfg.demo") is True, "a tap that never moved must NOT pause"
    assert abs(pg.evaluate("__ct.geo.gx") - gx_tap) < 1e-9, "a tap must not change geometry"
    assert pg.evaluate("__ct.undoDepth()") == 0, "a tap must not push an undo entry"
    print("a tap on a handle neither pauses nor edits -- pausing is the button's job")

    # A drag does not stop the sweep either -- it winds it up to 1x so the whole
    # excursion of the change plays out, and release puts the speed back. cfg.speed is
    # never written, so the slider keeps whatever the user set.
    s = pg.evaluate("__ct.pivotScreen('O4')")   # a fixed mount, so the pose can't move it
    gx0 = pg.evaluate("__ct.geo.gx")
    speed0 = pg.evaluate("__ct.cfg.speed")
    ptr(pg, "pointerdown", 1, s["x"], s["y"])
    assert pg.evaluate("__ct.sweepSpeed()") == speed0, "touch-down alone must not boost"
    ptr(pg, "pointermove", 1, s["x"] + 30, s["y"] + 18)
    assert pg.evaluate("__ct.cfg.demo") is True, "dragging must NOT stop the sweep"
    assert pg.evaluate("__ct.sweepSpeed()") == 1, \
        f"drag should sweep at 1x, got {pg.evaluate('__ct.sweepSpeed()')}"
    assert pg.evaluate("__ct.cfg.speed") == speed0, "cfg.speed itself must be left alone"
    assert pg.eval_on_selector("#speed", "e => +e.value") == speed0, "the slider must not move"
    tiptext = pg.eval_on_selector("#tip .s", "e => e.textContent")
    gx1 = pg.evaluate("__ct.geo.gx")
    assert abs(gx1 - gx0) > 1e-9, "the drag changed nothing"
    assert "gx" in tiptext and f"{gx1:.1f}" in tiptext, \
        f"tooltip {tiptext!r} does not carry the live gx value {gx1:.1f}"
    ptr(pg, "pointerup", 1, s["x"] + 30, s["y"] + 18)
    assert pg.eval_on_selector("#tip", "e => getComputedStyle(e).display") == "none", \
        "the tooltip must clear on release"
    assert pg.evaluate("__ct.sweepSpeed()") == speed0, \
        "release must restore the speed, or the boost would be permanent"
    print(f"drag sweeps at 1x and restores {speed0}x on release; "
          f"tip carried the values the sliders used to: {tiptext!r}")

    # undo is back in the toolbar row, next to Reset -- which is what it is there for
    assert pg.evaluate("__ct.undoDepth()") == 1
    pg.wait_for_timeout(80)          # the toolbar mirrors #undo on the next frame
    assert pg.eval_on_selector("#tbUndo", "e => !e.disabled"), "toolbar undo should be armed"
    pg.tap("#tbUndo"); pg.wait_for_timeout(200)
    assert abs(pg.evaluate("__ct.geo.gx") - gx0) < 1e-9, "toolbar undo did not restore gx"
    assert pg.eval_on_selector("#preset", "e => e.value") == "serpentine", \
        "undo relabels the preset from the geometry"
    print("undo restored gx and the preset label")

    # a grab with no movement must not push an undo entry
    pg.evaluate("__ct.rebuild()")
    depth = pg.evaluate("__ct.undoDepth()")
    s = pg.evaluate("__ct.pivotScreen('O6')")
    ptr(pg, "pointerdown", 1, s["x"], s["y"])
    ptr(pg, "pointerup", 1, s["x"], s["y"])
    assert pg.evaluate("__ct.undoDepth()") == depth, "a grab-and-release pushed an undo entry"
    print("grab without move leaves the undo stack alone")

    # a drag cut short by a second finger must give the speed back too, or the boost
    # would be left switched on for good
    speed0 = pg.evaluate("__ct.cfg.speed")
    s = pg.evaluate("__ct.pivotScreen('O4')")
    ptr(pg, "pointerdown", 1, s["x"], s["y"])
    ptr(pg, "pointermove", 1, s["x"] + 20, s["y"] + 10)
    assert pg.evaluate("__ct.sweepSpeed()") == 1
    ptr(pg, "pointerdown", 2, s["x"] + 90, s["y"])          # pinch outranks the drag
    assert pg.evaluate("__ct.sweepSpeed()") == speed0, "pinch cancelled the drag but kept the boost"
    ptr(pg, "pointerup", 1, s["x"] + 20, s["y"] + 10)
    ptr(pg, "pointerup", 2, s["x"] + 90, s["y"])
    assert pg.evaluate("__ct.sweepSpeed()") == speed0
    print("a pinch that interrupts a drag restores the speed too")

    # ---- 6. a fingertip gets more room than a cursor --------------------
    pg.reload(); pg.wait_for_timeout(600); ready(pg)
    pg.evaluate("__ct.cfg.temp = 70; __ct.rebuild()")
    # Ask the picker directly -- asserting on a side effect would silently pass if some
    # other handle happened to be nearer. Use the actuator anchor: it is the one handle
    # with clear space around it at 1x (see the crowding check below).
    s = pg.evaluate("__ct.pivotScreen('anchor')")
    assert pg.evaluate("([x, y]) => __ct.pick(x, y, 'touch')", [s["x"] + 26, s["y"]]) == "anchor"
    assert pg.evaluate("([x, y]) => __ct.pick(x, y, 'mouse')", [s["x"] + 26, s["y"]]) is None
    assert pg.evaluate("([x, y]) => __ct.pick(x, y, 'mouse')", [s["x"] + 16, s["y"]]) == "anchor"
    before = pg.evaluate("__ct.geo.dA")
    drag(pg, s["x"] + 26, s["y"], s["x"] + 46, s["y"] + 14)
    assert abs(pg.evaluate("__ct.geo.dA") - before) > 1e-9, "touch grab at 26px did not drag"
    print("hit radius: 26px off a handle picks it by touch, misses by mouse (16px hits both)")

    # At 1x the whole 40in piece is ~270px wide, so the joint pins sit ~17px apart and a
    # fingertip covers three of them. Nearest-wins still returns something sensible, but
    # picking a SPECIFIC joint means zooming in -- which is what the help text says.
    # Assert the workflow actually delivers, or that advice is a lie.
    pg.reload(); pg.wait_for_timeout(600); ready(pg)
    pg.evaluate("__ct.cfg.temp = 70; __ct.rebuild()")
    spread = """() => {
      const ns = ['anchor','O2','O4','O6','R','B','C','P','D','Q'];
      const ps = ns.map(n => { try { return __ct.pivotScreen(n); } catch (e) { return null; } });
      let worst = 1e9;
      for (let i = 0; i < ps.length; i++) for (let j = i + 1; j < ps.length; j++)
        if (ps[i] && ps[j]) worst = Math.min(worst, Math.hypot(ps[i].x - ps[j].x, ps[i].y - ps[j].y));
      return worst;
    }"""
    near1 = pg.evaluate(spread)
    q = pg.evaluate("__ct.pivotScreen('Q')")
    for _ in range(4):
        pinch(pg, q["x"], q["y"], 70, 260)
    zoomed = pg.evaluate("__ct.zoom")
    near2 = pg.evaluate(spread)
    assert near2 > 60, f"even at {zoomed:.1f}x the closest two handles are {near2:.0f}px apart"
    print(f"handle crowding: closest pair {near1:.0f}px at 1x, {near2:.0f}px at "
          f"{zoomed:.1f}x -- pinch is how you pick a specific joint")

    # ---- 7. pinch, two-finger pan, double-tap ---------------------------
    pg.reload(); pg.wait_for_timeout(600); ready(pg)
    assert pg.evaluate("__ct.zoom") == 1

    pinch(pg, 195, 300, 80, 240)
    z = pg.evaluate("__ct.zoom")
    assert 2.5 < z < 3.5, f"spreading 80->240px should zoom ~3x, got {z:.2f}"
    print(f"pinch out: 1.00x -> {z:.2f}x")
    pinch(pg, 195, 300, 240, 80)
    z2 = pg.evaluate("__ct.zoom")
    assert abs(z2 - 1) < 0.1, f"pinching back should return to ~1x, got {z2:.2f}"
    print(f"pinch in:  {z:.2f}x -> {z2:.2f}x")

    for _ in range(6):
        pinch(pg, 195, 300, 60, 300)
    assert pg.evaluate("__ct.zoom") == 12, "zoom must clamp at 12x"
    for _ in range(10):
        pinch(pg, 195, 300, 300, 60)
    assert pg.evaluate("__ct.zoom") == 0.15, "zoom must clamp at 0.15x"
    print("zoom clamps at 0.15x and 12x")

    # the pinch anchor holds: whatever sits under the midpoint stays there
    pg.reload(); pg.wait_for_timeout(600); ready(pg)
    s0 = pg.evaluate("__ct.pivotScreen('Q')")
    pinch(pg, s0["x"], s0["y"], 90, 200)
    s1 = pg.evaluate("__ct.pivotScreen('Q')")
    off = math.hypot(s1["x"] - s0["x"], s1["y"] - s0["y"])
    assert off < 2.0, f"pinch anchor drifted {off:.2f}px"
    print(f"pinch is midpoint-anchored (point under the fingers held within {off:.2f}px)")

    # one-finger pan on empty space, then double-tap to put it all back
    pg.reload(); pg.wait_for_timeout(600); ready(pg)
    drag(pg, 40, 620, 130, 560, steps=5)
    px, py = pg.evaluate("__ct.pan.x"), pg.evaluate("__ct.pan.y")
    assert abs(px - 90) < 2 and abs(py + 60) < 2, f"one-finger pan gave ({px}, {py})"
    pinch(pg, 195, 300, 80, 200)                   # leave a zoom to clear as well
    double_tap(pg, 60, 640)
    assert pg.evaluate("__ct.pan.x") == 0 and pg.evaluate("__ct.pan.y") == 0, "double-tap did not recentre"
    assert pg.evaluate("__ct.zoom") == 1, "double-tap did not reset zoom"
    print("one-finger pan works; double-tap recentres and resets zoom")

    # a release that panned must NOT arm the double-tap, or every drag would
    pg.reload(); pg.wait_for_timeout(600); ready(pg)
    drag(pg, 40, 620, 140, 620, steps=5)
    ptr(pg, "pointerdown", 1, 60, 640); ptr(pg, "pointerup", 1, 60, 640)
    assert pg.evaluate("__ct.pan.x") != 0, "one tap after a pan must not recentre"
    double_tap(pg, 60, 640)
    assert pg.evaluate("__ct.pan.x") == 0, "two clean taps should still recentre"
    print("a dragged release does not count as the first tap")

    # ---- 8. the toolbar replaces the keyboard ---------------------------
    pg.reload(); pg.wait_for_timeout(600)
    assert pg.eval_on_selector("#tbPlay", "e => e.textContent") == "⏸", "should start playing"
    pg.tap("#tbPlay"); pg.wait_for_timeout(120)
    assert pg.evaluate("__ct.cfg.demo") is False
    assert pg.eval_on_selector("#tbPlay", "e => e.textContent") == "▶"
    pg.tap("#tbPlay"); pg.wait_for_timeout(120)
    assert pg.evaluate("__ct.cfg.demo") is True
    assert pg.eval_on_selector("#tbPlay", "e => e.textContent") == "⏸"
    # Play resumes from the temperature on screen rather than jumping back to wherever
    # the phase counter had got to. Pause BEFORE setting the temperature, or frame()
    # overwrites it on the next tick and the check measures nothing.
    pg.tap("#tbPlay"); pg.wait_for_timeout(80)     # pause
    assert pg.evaluate("__ct.cfg.demo") is False
    pg.evaluate("__ct.cfg.temp = 12")
    pg.tap("#tbPlay"); pg.wait_for_timeout(80)     # play again
    assert pg.evaluate("__ct.cfg.demo") is True
    assert abs(pg.evaluate("__ct.cfg.temp") - 12) < 3, \
        f"the sweep jumped to {pg.evaluate('__ct.cfg.temp'):.1f}F instead of resuming near 12F"

    # ⌖ moves the view and nothing else
    pg.evaluate("__ct.pan.x = 55; __ct.pan.y = -22; __ct.cfg.rot = 40")
    pg.tap("#tbFit"); pg.wait_for_timeout(120)
    assert pg.evaluate("__ct.pan.x") == 0 and pg.evaluate("__ct.zoom") == 1
    assert pg.evaluate("__ct.cfg.rot") == 40, "recentre must leave the rotation alone"
    print("toolbar play/pause resumes in place; recentre clears pan+zoom only")

    # ⟲ is the full reset: geometry, every setting, rotation, zoom and pan
    pg.reload(); pg.wait_for_timeout(600); ready(pg)
    pg.evaluate("""() => {
      __ct.geo.L3 = 21.5;
      __ct.cfg.rot = 40; __ct.cfg.tmax = 150; __ct.cfg.extMax = 9;
      __ct.cfg.showBox = true; __ct.cfg.speed = 0.8; __ct.cfg.hole = 1.25;
      __ct.pan.x = 70; __ct.pan.y = -30;
      __ct.rebuild();
    }""")
    pinch(pg, 195, 300, 80, 240)
    assert pg.evaluate("__ct.zoom") > 2
    pg.tap("#tbReset"); pg.wait_for_timeout(250)
    after = pg.evaluate("""({L3: __ct.geo.L3, rot: __ct.cfg.rot, tmax: __ct.cfg.tmax,
      extMax: __ct.cfg.extMax, showBox: __ct.cfg.showBox, speed: __ct.cfg.speed,
      hole: __ct.cfg.hole, ghost: __ct.cfg.ghost, zoom: __ct.zoom,
      panx: __ct.pan.x, pany: __ct.pan.y})""")
    assert abs(after["L3"] - 7.7705) < 1e-9, after
    assert after["rot"] == 110 and after["tmax"] == 110 and after["extMax"] == 15.5, after
    assert after["showBox"] is False and after["speed"] == 0.1 and after["hole"] == 0.375, after
    assert after["ghost"] is True, "inner curves ship on; reset must restore that"
    assert after["zoom"] == 1 and after["panx"] == 0 and after["pany"] == 0, after
    # and the DOM followed, not just cfg
    assert pg.eval_on_selector("#tmax", "e => e.value") == "110"
    assert pg.eval_on_selector("#rot", "e => e.value") == "110"
    assert pg.eval_on_selector("#ghost", "e => e.checked") is True
    assert pg.eval_on_selector("#showBox", "e => e.checked") is False
    print("⟲ restored geometry, every setting, rotation, zoom and pan")

    # one undo step puts the whole thing back -- that is why UNDOCFG covers all of cfg
    pg.eval_on_selector("#undo", "e => e.click()"); pg.wait_for_timeout(250)
    back = pg.evaluate("""({L3: __ct.geo.L3, rot: __ct.cfg.rot, tmax: __ct.cfg.tmax,
      extMax: __ct.cfg.extMax, showBox: __ct.cfg.showBox, speed: __ct.cfg.speed,
      hole: __ct.cfg.hole})""")
    assert abs(back["L3"] - 21.5) < 1e-9, back
    assert back["rot"] == 40 and back["tmax"] == 150 and back["extMax"] == 9, back
    assert back["showBox"] is True and back["speed"] == 0.8 and back["hole"] == 1.25, back
    print("one undo puts every one of them back")

    # the sheet's Reset button is the same action
    pg.evaluate("__ct.cfg.rot = 25; __ct.rebuild()")
    pg.eval_on_selector("#reset", "e => e.click()"); pg.wait_for_timeout(250)
    assert pg.evaluate("__ct.cfg.rot") == 110, "the sheet Reset must match ⟲"
    print("the sheet's Reset button does the same thing")

    # ---- 9. iOS focus-zoom floor ----------------------------------------
    small = pg.eval_on_selector_all(
        "#sheet input:not([type=range]):not([type=checkbox]), #sheet select",
        "els => els.filter(e => parseFloat(getComputedStyle(e).fontSize) < 16)"
        ".map(e => e.id + '@' + getComputedStyle(e).fontSize)")
    assert not small, f"iOS will zoom the page on focus for: {small}"
    n = pg.eval_on_selector_all(
        "#sheet input:not([type=range]):not([type=checkbox]), #sheet select", "e => e.length")
    print(f"all {n} typed/select controls are >=16px, so iOS will not focus-zoom")

    # touch targets. Measure with the sheet OPEN: a closed <details> or a clipped sheet
    # gives its contents a zero-height box, which would read as a tiny tap target.
    pg.evaluate("__ct.setSheet(true)")
    pg.eval_on_selector_all("#sheet details", "els => els.forEach(e => e.open = true)")
    pg.wait_for_timeout(350)
    hits = pg.eval_on_selector_all(
        "#sheet button, #tools button, #help, #sheet .chk, #sheet summary",
        "els => els.map(e => ({what: e.id || e.className || e.tagName,"
        " h: Math.round(e.getBoundingClientRect().height)}))")
    smallhit = [f"{h['what']}@{h['h']}" for h in hits if h["h"] < 30]
    assert not smallhit, f"touch targets under 30px: {smallhit} (of {len(hits)} checked)"
    print(f"all {len(hits)} tap targets are >=30px tall "
          f"(smallest {min(h['h'] for h in hits)}px)")
    pg.evaluate("__ct.setSheet(false)")

    # ? sits upper LEFT, opposite the action toolbar, so reaching for help can never be
    # a mis-tap on Reset -- and the drag tooltip must not sit on top of either of them
    hb = pg.eval_on_selector("#help", "e => e.getBoundingClientRect().toJSON()")
    tb = pg.eval_on_selector("#tools", "e => e.getBoundingClientRect().toJSON()")
    btns = pg.eval_on_selector_all("#tools button",
        "els => els.map(e => ({id: e.id, x: Math.round(e.getBoundingClientRect().x),"
        " y: Math.round(e.getBoundingClientRect().y)}))")
    assert [x["id"] for x in btns] == ["help", "tbPlay", "tbUndo", "tbReset", "tbFit"], btns
    assert len({x["y"] for x in btns}) == 1, f"the toolbar is not one row: {btns}"
    assert hb["x"] < 60 and hb["y"] < 60, f"? is not in the upper left: {hb}"
    assert hb["right"] < min(x["x"] for x in btns if x["id"] != "help"), \
        "? must sit apart at the left end, not next to the action buttons"
    pg.evaluate("__ct.cfg.demo = false")
    s = pg.evaluate("__ct.pivotScreen('O4')")
    ptr(pg, "pointerdown", 1, s["x"], s["y"])
    ptr(pg, "pointermove", 1, s["x"] + 12, s["y"] + 8)
    tp = pg.eval_on_selector("#tip", "e => e.getBoundingClientRect().toJSON()")
    ptr(pg, "pointerup", 1, s["x"] + 12, s["y"] + 8)
    assert tp["y"] >= tb["bottom"], f"the drag tip overlaps the toolbar row ({tp} vs {tb})"
    print(f"toolbar is one row ? .. play/undo/reset/fit; ? at x={hb['x']:.0f}, "
          f"tip sits below at y={tp['y']:.0f}")
    # that drag moved O4 -- put the preset back before anything measures the geometry
    pg.eval_on_selector("#reset", "e => e.click()"); pg.wait_for_timeout(250)

    # ---- 10. both DXF exports still work from the phone page ------------
    pg.evaluate("__ct.rebuild()")
    parts = parse_dxf(pg.evaluate("__ct.buildParts()"))
    points = parse_dxf(pg.evaluate("__ct.buildPoints()"))
    playa = sorted({e[8][0] for e in parts if 8 in e})
    poila = sorted({e[8][0] for e in points if 8 in e})
    assert playa == ["CRANK", "LABELS", "PLATE1", "PLATE2", "ROCKER1", "ROCKER2"], playa
    assert "SCALE_CURVE" in poila and "PATH_DIVISIONS" in poila, poila
    labels = [e for e in points if e["type"] == "TEXT" and e[8][0] == "LABELS"]
    degs = sorted(int(e[1][0][:-1]) for e in labels if e[1][0].endswith("F"))
    assert degs == list(range(-20, 111, 10)), degs
    # the DXF must NOT thin: screen crowding is a screen problem
    assert len(degs) == 14, degs
    open(os.path.join(OUT, "mobile-parts.dxf"), "w").write(pg.evaluate("__ct.buildParts()"))
    open(os.path.join(OUT, "mobile-points.dxf"), "w").write(pg.evaluate("__ct.buildPoints()"))
    print(f"DXF from mobile: {len(parts)} part entities, {len(points)} point entities, "
          f"all {len(degs)} 10F labels present (unthinned)")

    # ---- 11. label thinning is a screen rule that zoom undoes -----------
    # Mirrors drawScale's rule rather than reading pixels back. If the two ever disagree
    # this check is worthless, so keep LBLGAP and the offset here in step with the page.
    pg.reload(); pg.wait_for_timeout(600); ready(pg)
    count = """() => {
      const gap = 34, placed = [];
      __ct.ticks.forEach(k => {
        if (!k.major) return;
        const q = __ct.screen(k.q), nn = __ct.dir(k.nx, k.ny);
        const x = q.x + nn.x * 14, y = q.y + nn.y * 14;
        if (placed.some(p => Math.hypot(x - p.x, y - p.y) < gap)) return;
        placed.push({x, y});
      });
      return placed.length;
    }"""
    total = pg.evaluate("__ct.ticks.filter(k => k.major).length")
    at1 = pg.evaluate(count)
    assert at1 < total, f"nothing was thinned at 1x ({at1} of {total}) -- is the rule live?"
    for _ in range(6):
        pinch(pg, 195, 300, 60, 300)
    assert pg.evaluate("__ct.zoom") == 12
    at_hi = pg.evaluate(count)
    assert at_hi == total, f"at 12x every label should fit, got {at_hi} of {total}"
    print(f"labels thin to {at1}/{total} at 1x and all {at_hi} return at 12x")

    # ---- 11b. joyce actuator: type switch in the sheet, clamp drag ------
    pg.reload(); pg.wait_for_timeout(600); ready(pg)
    pg.evaluate("__ct.setSheet(true)"); pg.wait_for_timeout(350)
    pg.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
    pg.select_option("#actT", "1"); pg.wait_for_timeout(250)
    assert pg.evaluate("__ct.geo.actT") == 1
    assert pg.evaluate("document.getElementById('actJoy').style.display") == "", \
        "the clamp-position field must appear in the sheet"
    pg.evaluate("__ct.setSheet(false)"); pg.wait_for_timeout(350)
    pg.evaluate("__ct.cfg.demo=false; __ct.cfg.temp=70; __ct.rebuild()")
    pg.wait_for_timeout(200)
    c0 = pg.evaluate("__ct.geo.aClamp")
    q = pg.evaluate("__ct.pivotScreen('clamp')")
    assert 0 <= q["x"] <= 390 and 0 <= q["y"] <= 844, \
        f"the tube tail handle must be inside the fitted view, got {q}"
    u = pg.evaluate("() => { const p=__ct.pose(__ct.cfg.temp);"
                    "  const g=__ct.actGeom(p,__ct.cfg.temp);"
                    "  return __ct.dir(g.u.x,g.u.y); }")
    ptr(pg, "pointerdown", 1, q["x"], q["y"])
    for i in range(1, 7):
        ptr(pg, "pointermove", 1, q["x"] + u["x"]*8*i, q["y"] + u["y"]*8*i)
    tipname = pg.eval_on_selector("#tip .n", "e => e.textContent")
    tiptext = pg.eval_on_selector("#tip .s", "e => e.textContent")
    ptr(pg, "pointerup", 1, q["x"] + u["x"]*48, q["y"] + u["y"]*48)
    pg.wait_for_timeout(200)
    c1 = pg.evaluate("__ct.geo.aClamp")
    J = pg.evaluate("__ct.JOYCE")
    assert c1 != c0 and J["c0min"] <= c1 <= J["c0max"], (c0, c1)
    assert "aClamp" in tiptext, f"drag tip must carry the live value, got {tiptext!r}"
    assert "clamp" in tipname.lower(), tipname
    pg.tap("#tbReset"); pg.wait_for_timeout(300)
    assert pg.evaluate("__ct.geo.actT") == 0, "Reset must return to the generic actuator"
    print(f"joyce on the phone: sheet switch, clamp drag {c0} -> {c1} with value tip, Reset restores generic")

    # ---- 12. landscape turns the sheet into a left drawer ---------------
    pg.reload(); pg.wait_for_timeout(600); ready(pg)   # section 11 left a 12x zoom on
    pg.set_viewport_size({"width": 844, "height": 390})
    pg.wait_for_timeout(400)
    r = pg.eval_on_selector("#sheet", "e => e.getBoundingClientRect().toJSON()")
    assert r["x"] < 20 and r["width"] < 340, f"landscape sheet is not a left drawer: {r}"
    assert r["height"] > 300, f"landscape drawer should be full height, got {r['height']}"
    assert pg.eval_on_selector("#grab", "e => getComputedStyle(e).display") == "none"
    left = pg.evaluate("""() => {
      const names = ['O2','O4','O6','anchor','R','B','C','P','D','Q'];
      const t0 = __ct.cfg.tmin, t1 = __ct.cfg.tmax;
      let worst = 1e9;
      for (let i = 0; i <= 140; i++) {
        __ct.cfg.temp = t0 + (t1 - t0) * i / 140;
        for (const n of names) { const s = __ct.pivotScreen(n);
          if (s && isFinite(s.x)) worst = Math.min(worst, s.x); }
      }
      return worst;
    }""")
    assert left >= 312 - 40, f"landscape drawing runs under the drawer (min x {left:.0f})"
    print(f"landscape: {r['width']:.0f}px left drawer, drawing starts at x={left:.0f}")
    pg.set_viewport_size({"width": 390, "height": 844})
    pg.wait_for_timeout(300)

    # ---- 13. index.html redirects a phone here --------------------------
    r2 = ctx.new_page()
    r2.goto(DESKTOP)
    r2.wait_for_timeout(600)
    assert r2.url.endswith("mobile.html"), f"phone was not redirected: {r2.url}"
    r2.goto(DESKTOP + "?desktop=1")
    r2.wait_for_timeout(600)
    assert "index.html" in r2.url, f"?desktop=1 must defeat the redirect: {r2.url}"
    assert r2.eval_on_selector_all("#panel input[type=range]", "e => e.length") >= 16, \
        "the desktop escape hatch must still have its sliders"
    r2.close()
    print("phone viewport redirects to mobile.html; ?desktop=1 escapes it")

    assert not errs, errs
    b.close()

print("\nALL MOBILE CHECKS PASSED")
