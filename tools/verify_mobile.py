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
    peek = pg.evaluate("__ct.peek")
    assert 120 < peek < 260, f"peek height {peek} looks wrong"
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
    pg.tap("#grab"); pg.wait_for_timeout(350)
    print(f"sheet body scrolls, touch-action {ta}")

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
                    "tbUndo", "tbFit", "tbPlay"}
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

    # ---- 5. drag stops the sweep, arms undo, and shows live values ------
    pg.reload(); pg.wait_for_timeout(600); ready(pg, animate=True)
    assert pg.evaluate("__ct.cfg.demo") is True, "Animate is on by default"
    pg.evaluate("__ct.cfg.temp = 70")           # pin the pose; the sweep is still running
    s = pg.evaluate("__ct.pivotScreen('O4')")
    gx0 = pg.evaluate("__ct.geo.gx")
    ptr(pg, "pointerdown", 1, s["x"], s["y"])
    assert pg.evaluate("__ct.cfg.demo") is False, "grabbing a handle must stop Animate"
    assert pg.eval_on_selector("#tip", "e => getComputedStyle(e).display") == "block", \
        "the drag tooltip must appear on grab"
    ptr(pg, "pointermove", 1, s["x"] + 30, s["y"] + 18)
    tiptext = pg.eval_on_selector("#tip .s", "e => e.textContent")
    gx1 = pg.evaluate("__ct.geo.gx")
    assert abs(gx1 - gx0) > 1e-9, "the drag changed nothing"
    assert "gx" in tiptext and f"{gx1:.1f}" in tiptext, \
        f"tooltip {tiptext!r} does not carry the live gx value {gx1:.1f}"
    ptr(pg, "pointerup", 1, s["x"] + 30, s["y"] + 18)
    assert pg.eval_on_selector("#tip", "e => getComputedStyle(e).display") == "none", \
        "the tooltip must clear on release"
    print(f"drag tip carried the values the sliders used to: {tiptext!r}")

    assert pg.evaluate("__ct.undoDepth()") == 1
    pg.wait_for_timeout(80)                     # the toolbar mirrors #undo on the next frame
    assert pg.eval_on_selector("#tbUndo", "e => !e.disabled"), "toolbar undo should be armed"
    pg.tap("#tbUndo"); pg.wait_for_timeout(200)
    assert abs(pg.evaluate("__ct.geo.gx") - gx0) < 1e-9, "toolbar undo did not restore gx"
    assert pg.eval_on_selector("#preset", "e => e.value") == "serpentine", \
        "undo relabels the preset from the geometry"
    print("toolbar undo restored gx and the preset label")

    # a grab with no movement must not push an undo entry
    pg.evaluate("__ct.rebuild()")
    depth = pg.evaluate("__ct.undoDepth()")
    s = pg.evaluate("__ct.pivotScreen('O6')")
    ptr(pg, "pointerdown", 1, s["x"], s["y"])
    ptr(pg, "pointerup", 1, s["x"], s["y"])
    assert pg.evaluate("__ct.undoDepth()") == depth, "a grab-and-release pushed an undo entry"
    print("grab without move leaves the undo stack alone")

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
    pg.evaluate("__ct.pan.x = 55; __ct.pan.y = -22")
    pg.tap("#tbFit"); pg.wait_for_timeout(120)
    assert pg.evaluate("__ct.pan.x") == 0 and pg.evaluate("__ct.zoom") == 1
    print("toolbar play/pause and recentre work; glyph tracks cfg.demo")

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
        "#sheet button, #tools button, #sheet .chk, #sheet summary",
        "els => els.map(e => ({what: e.id || e.className || e.tagName,"
        " h: Math.round(e.getBoundingClientRect().height)}))")
    smallhit = [f"{h['what']}@{h['h']}" for h in hits if h["h"] < 30]
    assert not smallhit, f"touch targets under 30px: {smallhit} (of {len(hits)} checked)"
    print(f"all {len(hits)} tap targets are >=30px tall "
          f"(smallest {min(h['h'] for h in hits)}px)")
    pg.evaluate("__ct.setSheet(false)")

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
