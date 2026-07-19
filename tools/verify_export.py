"""Drives index.html headless and checks the simulator end to end.

    pip install playwright && playwright install chromium
    python3 tools/verify_export.py [outdir]

Covers: named saves and recall, both DXF exports (geometry asserted against the
live `geo` values, all three save-dialog outcomes), drag stopping auto-cycle,
undo, panning, the tick layout and its behaviour across the path's cusp, the
envelope bounding box and its checkbox, and view rotation.

Writes parts.dxf / points.dxf to outdir (default /tmp) so you can eyeball them.
Run this after any change to index.html.
"""
import math, os, sys, tempfile
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "file://" + os.path.join(HERE, "index.html")
OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir()

def parse_dxf(txt):
    """Minimal DXF group-code reader -> list of entities in ENTITIES section."""
    lines = txt.split("\r\n")
    assert lines[-1] == "", "file must end with a line terminator"
    pairs = [(int(lines[i]), lines[i+1]) for i in range(0, len(lines)-1, 2)]
    ents, cur, inent = [], None, False
    for code, val in pairs:
        if code == 2 and val == "ENTITIES":
            inent = True; continue
        if not inent: continue
        if code == 0:
            if cur: ents.append(cur)
            if val in ("ENDSEC", "EOF"): cur = None; inent = False; continue
            cur = {"type": val}
        elif cur is not None:
            cur.setdefault(code, []).append(val)
    return ents

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console."+m.type+": "+m.text) if m.type == "error" else None)
    pg.goto(PAGE)
    pg.wait_for_timeout(600)
    assert not errs, errs

    # ---- 1. named saves -------------------------------------------------
    # a save with no name is refused -- there is no auto-restore slot to write
    pg.fill("#sname", "")
    pg.click("#save"); pg.wait_for_timeout(150)
    assert pg.eval_on_selector_all("#sload option", "els=>els.length") == 1, "nameless save stored nothing"
    assert "Type a name" in pg.inner_text("#smsg"), pg.inner_text("#smsg")
    print("nameless save refused:", pg.inner_text("#smsg"))

    pg.fill("#sname", "bench test A")
    pg.evaluate("__ct.geo.L3 = 12.34")
    pg.click("#save")
    pg.wait_for_timeout(150)
    opts = pg.eval_on_selector_all("#sload option", "els=>els.map(e=>e.value)")
    assert opts == ["", "bench test A"], opts
    assert pg.input_value("#sname") == "", "name field clears after a named save"
    assert pg.input_value("#sload") == "bench test A", "dropdown holds the record instead"
    print("save list:", opts, "| name field cleared |", pg.inner_text("#smsg"))

    # a second, different design
    pg.fill("#sname", "bench test B")
    pg.evaluate("__ct.geo.L3 = 20.0")
    pg.click("#save")
    pg.wait_for_timeout(150)
    opts = pg.eval_on_selector_all("#sload option", "els=>els.map(e=>e.value)")
    assert opts == ["", "bench test A", "bench test B"], opts

    # reload: the saved-design list survives, but NOTHING is auto-restored -- the page
    # must come up on the defaults compiled into index.html
    defaults = pg.evaluate("({L3: __ct.geo.L3, rot: __ct.cfg.rot, ghost: __ct.cfg.ghost})")
    pg.reload(); pg.wait_for_timeout(500)
    assert not errs, errs
    opts = pg.eval_on_selector_all("#sload option", "els=>els.map(e=>e.value)")
    assert opts == ["", "bench test A", "bench test B"], opts
    fresh = pg.evaluate("({L3: __ct.geo.L3, rot: __ct.cfg.rot, ghost: __ct.cfg.ghost})")
    assert abs(fresh["L3"] - 7.7705) < 1e-9, f"reload must give the default L3, got {fresh['L3']}"
    assert fresh["rot"] == 110 and fresh["ghost"] is False, fresh
    print("reload gives defaults, not the last save:", fresh)

    # load the older one by name
    pg.select_option("#sload", "bench test A")
    pg.wait_for_timeout(200)
    got = pg.evaluate("__ct.geo.L3")
    assert abs(got - 12.34) < 1e-9, f"loading 'bench test A' gave L3={got}"
    assert pg.input_value("#sname") == "", "recall must NOT populate the name field"
    print("loaded named design ->", pg.inner_text("#smsg"))

    # delete -- keys off the name field, which recall no longer fills, so type it
    pg.fill("#sname", "bench test A")
    pg.click("#del"); pg.wait_for_timeout(150)
    opts = pg.eval_on_selector_all("#sload option", "els=>els.map(e=>e.value)")
    assert opts == ["", "bench test B"], opts
    print("after delete:", opts)

    # ---- 2. DXF export --------------------------------------------------
    # back to the chosen preset, through the UI so the path cache rebuilds
    pg.select_option("#preset", "serpentine")
    pg.wait_for_timeout(200)
    assert abs(pg.evaluate("__ct.geo.cu2") - 19.9991) < 1e-9
    pg.fill("#hole", "0.375"); pg.dispatch_event("#hole", "change")
    pg.fill("#lwid", "1.5");   pg.dispatch_event("#lwid", "change")

    parts = pg.evaluate("__ct.buildParts()")
    pts   = pg.evaluate("__ct.buildPoints()")
    open(os.path.join(OUT,"parts.dxf"), "w", newline="").write(parts)
    open(os.path.join(OUT,"points.dxf"), "w", newline="").write(pts)

    for nm, txt in (("parts", parts), ("points", pts)):
        assert txt.startswith("0\r\nSECTION"), nm
        assert txt.rstrip().endswith("EOF"), nm
        # every group code line must be an integer -> catches odd/misaligned pairs
        ls = txt.split("\r\n")[:-1]
        assert len(ls) % 2 == 0, (nm, "odd number of lines")
        for i in range(0, len(ls), 2):
            int(ls[i])
        print(nm, "DXF parsed,", len(ls)//2, "group pairs")

    pe = parse_dxf(parts)
    types = {}
    for e in pe: types[e["type"]] = types.get(e["type"], 0) + 1
    print("parts entities:", types)
    layers = sorted({e[8][0] for e in pe})
    print("parts layers:", layers)
    assert layers == ["CRANK", "LABELS", "PLATE1", "PLATE2", "ROCKER1", "ROCKER2"], layers

    # geometry check: PLATE1's three holes must reproduce L3 / cu / cv
    geo = pg.evaluate("({...__ct.geo})")
    holes = [(float(e[10][0]), float(e[20][0])) for e in pe
             if e["type"] == "CIRCLE" and e[8][0] == "PLATE1"]
    assert len(holes) == 3, holes
    B, C, P = holes
    d = lambda a, b: math.hypot(a[0]-b[0], a[1]-b[1])
    assert abs(d(B, C) - geo["L3"]) < 1e-6, (d(B, C), geo["L3"])
    # P offset along BC (u) and perpendicular (v); y was flipped, so cv flips too
    ux, uy = (C[0]-B[0])/geo["L3"], (C[1]-B[1])/geo["L3"]
    du, dv = P[0]-B[0], P[1]-B[1]
    u, v = du*ux + dv*uy, -du*uy + dv*ux
    assert abs(u - geo["cu"]) < 1e-6, (u, geo["cu"])
    assert abs(v + geo["cv"]) < 1e-6, (v, geo["cv"])          # flipped
    print(f"PLATE1 holes: L3={d(B,C):.4f} u={u:.4f} v={v:.4f}  (geo L3={geo['L3']} cu={geo['cu']} cv={geo['cv']})")

    # hole diameter honoured
    rads = {round(float(e[40][0]), 6) for e in pe if e["type"] == "CIRCLE"}
    assert rads == {0.1875}, rads

    # outlines: every hole must sit >= w inside its own part outline.
    # Check by sampling the outline arcs' radius = w = 0.75
    arcs = [e for e in pe if e["type"] == "ARC"]
    assert arcs and {round(float(a[40][0]), 6) for a in arcs} == {0.75}, "corner arcs = half link width"
    # parts must not overlap: x-ranges disjoint per layer
    def xr(layer):
        xs = []
        for e in pe:
            if e[8][0] != layer: continue
            for c in (10, 11):
                if c in e: xs += [float(v) for v in e[c]]
        return min(xs), max(xs)
    ranges = [xr(l) for l in ["CRANK", "PLATE1", "ROCKER1", "PLATE2", "ROCKER2"]]
    for (a0, a1), (b0, b1) in zip(ranges, ranges[1:]):
        assert a1 < b0, f"parts overlap: {a1} !< {b0}"
    print("part x-ranges (no overlap):", [(round(a,2), round(b,2)) for a, b in ranges])

    po = parse_dxf(pts)
    play = sorted({e[8][0] for e in po})
    ptypes = {}
    for e in po: ptypes[e["type"]] = ptypes.get(e["type"], 0) + 1
    print("points layers:", play, ptypes)
    assert "POINTS" in play and "SCALE_CURVE" in play and "MOUNTS" in play, play
    npt = sum(1 for e in po if e["type"] == "POINT")
    assert npt >= 4 + 13, npt      # 4 mounts + one per 10F tick over -20..110
    # mounts land where the sim says they do (y flipped)
    mount_pts = [(float(e[10][0]), float(e[20][0])) for e in po if e["type"] == "POINT"]
    assert (0.0, 0.0) in [(round(x,6), round(y,6)) for x, y in mount_pts], "O2 at origin"
    assert (round(geo["gx"],6), round(-geo["gy"],6)) in [(round(x,6), round(y,6)) for x, y in mount_pts], "O4"
    print("mount points ok; total POINT entities:", npt)

    # ---- 3. save-dialog path --------------------------------------------
    # headless has showSaveFilePicker but no dialog to resolve it, so stub the three outcomes
    print("showSaveFilePicker present:", pg.evaluate("!!window.showSaveFilePicker"))

    # 3a. picker accepted -> file written through the handle, not via <a download>
    pg.evaluate("""() => {
      window.__cap = {};
      window.showSaveFilePicker = async (o) => {
        window.__cap.suggested = o.suggestedName;
        window.__cap.accept = JSON.stringify(o.types);
        return { name: 'chosen-by-user.dxf', createWritable: async () => ({
          write: async b => { window.__cap.bytes = b.size; window.__cap.text = await b.text(); },
          close: async () => { window.__cap.closed = true; } }) };
      };
    }""")
    pg.fill("#sname", "serpentine v3")
    pg.click("#expParts"); pg.wait_for_timeout(300)
    cap = pg.evaluate("window.__cap")
    assert cap["suggested"] == "serpentine_v3-parts.dxf", cap["suggested"]
    assert cap["closed"] and cap["bytes"] > 1000, cap
    assert cap["text"].startswith("0\r\nSECTION") and cap["text"].rstrip().endswith("EOF")
    assert ".dxf" in cap["accept"], cap["accept"]
    print("picker path: suggested=%s written=%d bytes -> msg: %s"
          % (cap["suggested"], cap["bytes"], pg.inner_text("#emsg")))

    # 3b. user cancels -> no download, no success message
    pg.evaluate("""() => { const m=document.getElementById('emsg'); m.className=''; m.textContent='';
      window.showSaveFilePicker = async () => { const e=new Error('x'); e.name='AbortError'; throw e; }; }""")
    pg.click("#expPoints"); pg.wait_for_timeout(400)
    assert pg.text_content("#emsg") == "", "cancel must stay silent"
    print("cancel path: silent, no file")

    # 3c. no picker (Firefox/Safari) -> <a download> fallback
    pg.evaluate("() => { delete window.showSaveFilePicker; }")
    with pg.expect_download() as dl:
        pg.click("#expPoints")
    d = dl.value
    assert d.suggested_filename == "serpentine_v3-points.dxf", d.suggested_filename
    pg.wait_for_timeout(200)
    print("fallback path: downloaded", d.suggested_filename)
    print("export msg:", pg.inner_text("#emsg"))

    # ---- 4. drag: stops auto-cycle, is undoable --------------------------
    pg.select_option("#preset", "serpentine"); pg.wait_for_timeout(200)
    pg.evaluate("__ct.cfg.demo = true; document.getElementById('demo').checked = true")
    before = pg.evaluate("__ct.geo.gx")
    depth0 = pg.evaluate("__ct.undoDepth()")   # preset switches push too, so measure deltas
    o4 = pg.evaluate("__ct.pivotScreen('O4')")
    pg.mouse.move(o4["x"], o4["y"]); pg.mouse.down()
    pg.mouse.move(o4["x"] + 60, o4["y"] + 25, steps=6); pg.mouse.up()
    pg.wait_for_timeout(200)
    assert pg.evaluate("__ct.cfg.demo") is False, "drag must stop auto-cycle"
    assert pg.is_checked("#demo") is False, "demo checkbox must follow"
    moved = pg.evaluate("__ct.geo.gx")
    assert abs(moved - before) > 0.5, (before, moved)
    assert pg.evaluate("!document.getElementById('undo').disabled"), "undo should be armed"
    assert pg.evaluate("__ct.undoDepth()") == depth0 + 1, "one drag = exactly one undo state"
    print(f"drag O4: gx {before:.2f} -> {moved:.2f}, auto-cycle off, undo armed")

    pg.click("#undo"); pg.wait_for_timeout(200)
    assert abs(pg.evaluate("__ct.geo.gx") - before) < 1e-9, "undo must restore gx"
    assert pg.input_value("#preset") == "serpentine", "undo relabels the preset from the geometry"
    assert pg.evaluate("__ct.undoDepth()") == depth0
    print("undo restored gx and the preset label")

    # grab-and-release without moving must not push a junk undo state
    pg.mouse.move(o4["x"], o4["y"]); pg.mouse.down(); pg.mouse.up()
    pg.wait_for_timeout(150)
    assert pg.evaluate("__ct.undoDepth()") == depth0, "no-op grab must not push undo"
    print("grab without move leaves the undo stack alone")

    # Ctrl+Z path
    pg.mouse.move(o4["x"], o4["y"]); pg.mouse.down()
    pg.mouse.move(o4["x"] - 40, o4["y"], steps=5); pg.mouse.up()
    pg.wait_for_timeout(150)
    pg.keyboard.press("Control+z"); pg.wait_for_timeout(200)
    assert abs(pg.evaluate("__ct.geo.gx") - before) < 1e-9, "Ctrl+Z must undo the drag"
    print("Ctrl+Z undo works")

    # undo must restore the range/excursion too, not just geo -- loading a saved design
    # changes both, so a geo-only undo would leave the curve reshaped
    pg.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
    pg.select_option("#preset", "serpentine"); pg.wait_for_timeout(150)
    pg.fill("#extMax", "12"); pg.dispatch_event("#extMax", "change"); pg.wait_for_timeout(150)
    pg.select_option("#preset", "grandarc"); pg.wait_for_timeout(150)   # snapshots extMax=12
    pg.fill("#extMax", "9"); pg.dispatch_event("#extMax", "change"); pg.wait_for_timeout(150)
    pg.click("#undo"); pg.wait_for_timeout(200)
    assert pg.evaluate("__ct.cfg.extMax") == 12, pg.evaluate("__ct.cfg.extMax")
    assert pg.input_value("#extMax") == "12", "the field must follow too"
    assert pg.input_value("#preset") == "serpentine"
    print("undo restored excursion (9 -> 12) alongside the geometry")

    # ---- 5. panning ------------------------------------------------------
    q0 = pg.evaluate("__ct.pivotScreen('O2')")
    pg.mouse.move(650, 400); pg.mouse.down(button="right")
    pg.mouse.move(750, 460, steps=6); pg.mouse.up(button="right")
    pg.wait_for_timeout(150)
    q1 = pg.evaluate("__ct.pivotScreen('O2')")
    assert abs(q1["x"] - q0["x"] - 100) < 2 and abs(q1["y"] - q0["y"] - 60) < 2, (q0, q1)
    print(f"right-drag panned by ({q1['x']-q0['x']:.0f},{q1['y']-q0['y']:.0f}) px")

    # after panning, a pivot drag must still land where the cursor is (worldOf un-pans)
    gx_pre = pg.evaluate("__ct.geo.gx")
    o4b = pg.evaluate("__ct.pivotScreen('O4')")
    pg.mouse.move(o4b["x"], o4b["y"]); pg.mouse.down()
    pg.mouse.move(o4b["x"] + 30, o4b["y"], steps=4); pg.mouse.up()
    pg.wait_for_timeout(200)
    assert abs(pg.evaluate("__ct.geo.gx") - gx_pre) > 0.1, "pivot still grabbable after pan"
    print("pivot drag still tracks the cursor after a pan")

    # (screen position can't be compared to q0 here — the drag above refit the view)
    assert pg.evaluate("__ct.pan.x") != 0, "still panned"
    pg.dblclick("canvas"); pg.wait_for_timeout(150)
    assert pg.evaluate("__ct.pan.x") == 0 and pg.evaluate("__ct.pan.y") == 0, "dblclick clears pan"
    print("double-click recentred")

    # pan is clamped so the mechanism can't be lost off-screen
    pg.mouse.move(650, 400); pg.mouse.down(button="right")
    pg.mouse.move(9000, 9000, steps=4); pg.mouse.up(button="right")
    pg.wait_for_timeout(150)
    px, py = pg.evaluate("__ct.pan.x"), pg.evaluate("__ct.pan.y")
    vw, vh = pg.evaluate("innerWidth"), pg.evaluate("innerHeight")
    assert px <= vw*0.6 + 1 and py <= vh*0.6 + 1, (px, py, vw, vh)
    print(f"pan clamped at ({px:.0f},{py:.0f}) for a {vw}x{vh} viewport")
    pg.dblclick("canvas"); pg.wait_for_timeout(100)

    # ---- 6. path divisions in the DXF -----------------------------------
    pg.select_option("#preset", "serpentine"); pg.wait_for_timeout(200)
    sub = pg.evaluate("__ct.buildPoints()")
    so = parse_dxf(sub)
    lay = {}
    for e in so:
        if e["type"] == "LINE": lay[e[8][0]] = lay.get(e[8][0], 0) + 1
    print("line counts by layer:", lay)
    # the export must match the screen: divisions across the path, and NO tick strokes
    # beside it -- the indicator ring would cover anything alongside
    assert sorted(lay) == ["PATH_DIVISIONS", "SCALE_CURVE"], sorted(lay)
    assert not any(k.startswith("TICKS") for k in lay), lay
    chunks = pg.evaluate("__ct.chunks.length")
    assert lay["PATH_DIVISIONS"] == chunks == 130, (lay, chunks)

    # every division is centred on the path and exactly one path-width long
    ticks = pg.evaluate("__ct.ticks.map(k=>({t:k.t,x:k.q.x,y:k.q.y,nx:k.nx,ny:k.ny,major:k.major}))")
    ends = pg.evaluate("__ct.chunks.map(c=>c.pts[c.pts.length-1])")
    for e in so:
        if e["type"] != "LINE" or e[8][0] != "PATH_DIVISIONS": continue
        x0, y0, x1, y1 = (float(e[c][0]) for c in (10, 20, 11, 21))
        assert abs(math.hypot(x1-x0, y1-y0) - 1.0) < 1e-6, "division = 1.0in path width"
        mx, my = (x0+x1)/2, (y0+y1)/2
        near = min(math.hypot(mx-q["x"], my+q["y"]) for q in ends)   # y flipped in CAD
        assert near < 1e-6, f"division not centred on a chunk boundary (off {near})"
    print(f"{lay['PATH_DIVISIONS']} divisions, each 1.00in and centred on a whole degree")

    # a division must be perpendicular to the path. Reference tangent comes from pose()
    # either side of the boundary temperature -- independent of the drawing code, and
    # local: a whole-degree chord is a bad proxy where the path turns 63 degrees.
    tangents = pg.evaluate("""__ct.chunks.map(c => {
      const T = c.t + 0.5;                       // c.t is the chunk midpoint
      const a = __ct.pose(T - 0.05), b = __ct.pose(T + 0.05);
      if (!a.valid || !b.valid) return null;
      return {T, x: b.Q.x - a.Q.x, y: -(b.Q.y - a.Q.y)};   // mirrored into CAD space
    })""")
    divs = [e for e in so if e["type"] == "LINE" and e[8][0] == "PATH_DIVISIONS"]
    worst, worst_at = 0.0, None
    for e in divs:
        x0, y0, x1, y1 = (float(e[c][0]) for c in (10, 20, 11, 21))
        mx, my = (x0+x1)/2, (y0+y1)/2
        i = min(range(len(ends)), key=lambda k: math.hypot(mx-ends[k]["x"], my+ends[k]["y"]))
        t = tangents[i]
        if not t: continue
        tl = math.hypot(t["x"], t["y"]) or 1
        dl = math.hypot(x1-x0, y1-y0) or 1
        c = abs(((x1-x0)*t["x"] + (y1-y0)*t["y"]) / (tl*dl))
        if c > worst: worst, worst_at = c, t["T"]
    # Tolerance, not zero: the renderer takes the tangent from the chunk's last sub-step
    # (a backward difference), which diverges from a centred one exactly where the path
    # turns hardest -- there is a near-cusp at 43.5F where it slows to 0.111 in/degF and
    # swings 10 degrees. Typical divisions come in under 0.5 degrees.
    assert worst < 0.15, f"divisions must be perpendicular (worst |cos| {worst} at {worst_at}F)"
    print(f"divisions perpendicular to the path (worst |cos| {worst:.4f} at {worst_at}F)")

    # 10F labels survive, and land clear of the path
    labels = [e for e in so if e["type"] == "TEXT" and e[8][0] == "LABELS"]
    degs = sorted(int(e[1][0][:-1]) for e in labels if e[1][0].endswith("F")
                  and e[1][0][:-1].lstrip("-").isdigit())
    assert [d for d in degs if d % 10 == 0 and -20 <= d <= 110] == list(range(-20, 120, 10)), degs
    print(f"{len(degs)} degree labels: {degs[0]}F..{degs[-1]}F every 10F")

    # ---- 6b. envelope bounding box ---------------------------------------
    pg.select_option("#preset", "serpentine"); pg.wait_for_timeout(250)
    bb = pg.evaluate("__ct.bbox")
    # must contain the path, EVERY moving joint's swept trace, and all four mounts --
    # the envelope the built piece actually occupies. Scanned far finer than the box's
    # own sampling. Tolerance is 5 thou, not zero: the joint traces come from pathJ at
    # 140 samples (~0.93F apart), which clips a smooth extremum by ~2 thou around P@58F.
    # The path itself uses the 6x finer pathChunks and lands within 0.01 thou.
    over = pg.evaluate("""(() => {
      const b = __ct.bbox; let worst = 0, at = null;
      const chk = (p, n) => { if (!p) return;
        const d = Math.max(b.x0-p.x, p.x-b.x1, b.y0-p.y, p.y-b.y1);
        if (d > worst) { worst = d; at = n; } };
      for (let t = __ct.cfg.tmin; t <= __ct.cfg.tmax; t += 0.02) {
        const s = __ct.pose(t); if (!s.valid) continue;
        ['Q','R','B','C','P','D'].forEach(k => chk(__ct.rotPt(s[k]), k+'@'+t.toFixed(2)));
      }
      const p = __ct.pose(__ct.cfg.temp);
      ['O2','O4','O6','anchor'].forEach(k => chk(__ct.rotPt(p[k]), k));
      return {worst, at}; })()""")
    assert over["worst"] < 0.005, over
    print(f"envelope {bb['w']:.2f} x {bb['h']:.2f}in, contains path+joints+mounts "
          f"(worst overshoot {over['worst']*1000:.2f} thou at {over['at']})")

    # must update DURING a drag, not just on release -- buildBBox runs before fitView,
    # which early-returns while dragPivot is set
    o4 = pg.evaluate("__ct.pivotScreen('O4')")
    pg.mouse.move(o4["x"], o4["y"]); pg.mouse.down()
    pg.mouse.move(o4["x"] + 110, o4["y"] + 70, steps=8)
    mid = pg.evaluate("__ct.bbox")
    pg.mouse.up(); pg.wait_for_timeout(200)
    assert abs(mid["w"] - bb["w"]) > 0.5 or abs(mid["h"] - bb["h"]) > 0.5, (bb, mid)
    print(f"tracks live while dragging: {mid['w']:.2f} x {mid['h']:.2f}in mid-drag")
    pg.keyboard.press("Control+z"); pg.wait_for_timeout(250)
    back = pg.evaluate("__ct.bbox")
    assert abs(back["w"] - bb["w"]) < 1e-6 and abs(back["h"] - bb["h"]) < 1e-6, (bb, back)
    print("undo restores the envelope")

    # the Bounding box checkbox. Probes the box's own top edge, which runs through empty
    # background -- a colour match would also hit the steel links and the ghost traces.
    probe = """(() => {
      const s2 = __ct.pivotScreen('O2'), s4 = __ct.pivotScreen('O4'), g = __ct.geo;
      const sc = Math.hypot(s4.x-s2.x, s4.y-s2.y) / Math.hypot(g.gx, g.gy);
      const TX = w => ({x: w.x*sc + s2.x, y: w.y*sc + s2.y});
      const bb = __ct.bbox, a = TX({x: bb.x0, y: bb.y0}), c = TX({x: bb.x1, y: bb.y1});
      const cv = document.getElementById('c'), dpr = cv.width / parseFloat(cv.style.width);
      const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
      let lit = 0;
      for (let f = 0.05; f < 0.45; f += 0.004) {
        const i = ((Math.round(a.y*dpr)) * cv.width + Math.round((a.x + (c.x-a.x)*f) * dpr)) * 4;
        if (0.2126*d[i] + 0.7152*d[i+1] + 0.0722*d[i+2] > 28) lit++;   // background ~19
      }
      return lit; })()"""
    # the probe reconstructs world->screen as a pure scale about O2, so it only holds
    # with the view square. rot defaults to 110, so zero it first.
    pg.evaluate("const e=document.getElementById('rot');e.value=0;e.dispatchEvent(new Event('input'))")
    pg.wait_for_timeout(200)
    assert pg.is_checked("#showBox") is False, "box is OFF by default"
    off = pg.evaluate(probe)
    # the box bounds the swept joints, so ticking it must also tick Inner curves --
    # otherwise it measures things that aren't drawn
    pg.uncheck("#ghost"); pg.wait_for_timeout(100)
    pg.check("#showBox"); pg.wait_for_timeout(300)
    assert pg.is_checked("#ghost") is True and pg.evaluate("__ct.cfg.ghost") is True, \
        "enabling the bounding box must enable inner curves"
    print("enabling Bounding box also enables Inner curves")
    on = pg.evaluate(probe)
    assert on > 25 and off == 0, (on, off)
    pg.uncheck("#showBox"); pg.wait_for_timeout(300)
    assert pg.evaluate(probe) == 0, "unchecking hides it again"
    print(f"Bounding box checkbox: off by default, {on}/100 edge samples lit when on")

    # it rides along in a NAMED design, but a bare reload comes back at the default
    pg.check("#showBox"); pg.fill("#sname", "box on"); pg.click("#save"); pg.wait_for_timeout(200)
    pg.reload(); pg.wait_for_timeout(700)
    assert pg.is_checked("#showBox") is False, "reload must give the default, not the last save"
    pg.select_option("#sload", "box on"); pg.wait_for_timeout(300)
    assert pg.is_checked("#showBox") is True, "recalling the design brings it back"
    pg.fill("#sname", "box on"); pg.click("#del"); pg.wait_for_timeout(150)
    pg.uncheck("#showBox"); pg.wait_for_timeout(150)
    print("box visibility rides in a named design; reload gives the default")

    # ---- 6c. view rotation ------------------------------------------------
    pg.select_option("#preset", "serpentine"); pg.wait_for_timeout(250)
    el = pg.query_selector("#rot")
    assert (el.get_attribute("min"), el.get_attribute("max"), el.get_attribute("step")) \
        == ("0", "360", "10"), "0..360 in 10 degree steps"

    def setrot(a):
        pg.evaluate("a => { const e = document.getElementById('rot');"
                    "e.value = a; e.dispatchEvent(new Event('input')); }", a)
        pg.wait_for_timeout(130)
        return pg.evaluate("__ct.cfg.rot")

    assert setrot(215) == 220 and setrot(7) == 10, "off-step values must snap to 10"

    def o2o4_angle():
        a = pg.evaluate("__ct.pivotScreen('O2')"); c = pg.evaluate("__ct.pivotScreen('O4')")
        return math.degrees(math.atan2(c["y"]-a["y"], c["x"]-a["x"]))

    setrot(0); base = o2o4_angle(); bb0 = pg.evaluate("__ct.bbox")
    for a in (10, 90, 180, 210, 350, 360):
        assert setrot(a) == a
        got = (o2o4_angle() - base + 540) % 360 - 180
        # counterclockwise on screen. atan2 is measured in y-down coords, where a
        # counterclockwise turn DECREASES the angle -- hence -a, not +a.
        want = ((-a + 180) % 360) - 180
        assert abs(((got - want + 540) % 360) - 180) < 0.5, (a, got, want)
    print("rotation turns the view at every step")

    # The box is square to the SCREEN, so its w/h are the footprint at the current
    # orientation and DO change as you rotate -- that is what it is for. At 90 degrees
    # they must simply swap.
    # back to the shipped defaults first. Reset restores geo and rotation but NOT the
    # excursion, and section 4's undo test leaves extMax at 12in -- which shrinks how
    # far every joint sweeps, so the footprint would be measured for the wrong stroke.
    pg.click("#reset"); pg.wait_for_timeout(200)
    pg.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
    pg.fill("#extMin", "0");    pg.dispatch_event("#extMin", "change")
    pg.fill("#extMax", "15.5"); pg.dispatch_event("#extMax", "change")
    pg.wait_for_timeout(250)
    setrot(0);  sq = pg.evaluate("__ct.bbox")
    setrot(90); rot90 = pg.evaluate("__ct.bbox")
    assert abs(rot90["w"] - sq["h"]) < 1e-6 and abs(rot90["h"] - sq["w"]) < 1e-6, (sq, rot90)
    # and at 0 it must equal an independently computed world extent
    manual = pg.evaluate("""(() => {
      let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
      const add=p=>{if(!p)return;
        x0=Math.min(x0,p.x);y0=Math.min(y0,p.y);x1=Math.max(x1,p.x);y1=Math.max(y1,p.y);};
      __ct.chunks.forEach(c => c.pts.forEach(add));          // the path
      const J = __ct.pathJ;                                  // every swept joint
      Object.keys(J).forEach(k => J[k].forEach(add));
      const q = __ct.pose(__ct.cfg.temp);
      ['O2','O4','O6','anchor'].forEach(k => add(q[k]));     // the fixed mounts
      return {w:x1-x0, h:y1-y0}; })()""")
    setrot(0)
    assert abs(sq["w"]-manual["w"]) < 1e-9 and abs(sq["h"]-manual["h"]) < 1e-9, (sq, manual)
    print(f"footprint {sq['w']:.2f} x {sq['h']:.2f}in square-on, swaps to "
          f"{rot90['w']:.2f} x {rot90['h']:.2f}in at 90 degrees")

    # worldOf must invert the rotation, or grabbed pivots drift away from the cursor.
    # Measured MID-drag: releasing refits the view and would mask the result.
    for a in (0, 90, 210):
        setrot(a)
        o4 = pg.evaluate("__ct.pivotScreen('O4')")
        pg.mouse.move(o4["x"], o4["y"]); pg.mouse.down()
        pg.mouse.move(o4["x"]+60, o4["y"]+40, steps=6)
        mid = pg.evaluate("__ct.pivotScreen('O4')")
        pg.mouse.up(); pg.wait_for_timeout(180)
        pg.keyboard.press("Control+z"); pg.wait_for_timeout(180)
        assert abs(mid["x"]-o4["x"]-60) < 2 and abs(mid["y"]-o4["y"]-40) < 2, (a, o4, mid)
    print("grabbed pivots follow the cursor exactly at 0/90/210 degrees")

    setrot(140); pg.fill("#sname", "rot 140"); pg.click("#save"); pg.wait_for_timeout(200)
    pg.reload(); pg.wait_for_timeout(800)
    assert pg.evaluate("__ct.cfg.rot") == 110, "reload gives the 110 default, not the save"
    pg.select_option("#sload", "rot 140"); pg.wait_for_timeout(300)
    assert pg.evaluate("__ct.cfg.rot") == 140, pg.evaluate("__ct.cfg.rot")
    assert pg.input_value("#rot") == "140" and "140" in pg.inner_text("#rotV")
    pg.fill("#sname", "rot 140"); pg.click("#del"); pg.wait_for_timeout(150)
    print("rotation rides in a named design, slider and label follow on recall")

    # Reset preset squares the view back up, and undo puts the rotation back
    setrot(120)
    pg.click("#reset"); pg.wait_for_timeout(250)
    assert pg.evaluate("__ct.cfg.rot") == 0, pg.evaluate("__ct.cfg.rot")
    assert pg.input_value("#rot") == "0" and "0°" in pg.inner_text("#rotV")
    pg.keyboard.press("Control+z"); pg.wait_for_timeout(250)
    assert pg.evaluate("__ct.cfg.rot") == 120, pg.evaluate("__ct.cfg.rot")
    print("Reset zeroes rotation; undo restores it")
    setrot(0)

    # ---- 6d. mouse wheel zoom --------------------------------------------
    pg.mouse.dblclick(700, 500); pg.wait_for_timeout(200)
    assert pg.evaluate("__ct.zoom") == 1
    pg.mouse.move(700, 500); pg.mouse.wheel(0, -300); pg.wait_for_timeout(150)
    zin = pg.evaluate("__ct.zoom")
    assert zin > 1, f"wheel FORWARD must zoom IN, got {zin}"
    pg.mouse.wheel(0, 600); pg.wait_for_timeout(150)
    zout = pg.evaluate("__ct.zoom")
    assert zout < zin, f"wheel back must zoom out, got {zout}"
    print(f"wheel: forward -> {zin:.2f}x in, back -> {zout:.2f}x")

    # zoom is anchored on the cursor: the point under the pointer must not move
    for step in (-240, -240, 180):
        q = pg.evaluate("__ct.pivotScreen('O4')")
        pg.mouse.move(q["x"], q["y"]); pg.mouse.wheel(0, step); pg.wait_for_timeout(120)
        q2 = pg.evaluate("__ct.pivotScreen('O4')")
        d = math.hypot(q2["x"]-q["x"], q2["y"]-q["y"])
        assert d < 1.5, f"cursor anchor drifted {d}px at wheel {step}"
    print("wheel zoom is cursor-anchored (point under pointer holds within 1.5px)")

    pg.mouse.dblclick(700, 500); pg.wait_for_timeout(200)
    assert pg.evaluate("__ct.zoom") == 1 and pg.evaluate("__ct.pan.x") == 0
    print("double-click resets zoom and pan")

    # ---- 7. actuator rod end has an inner curve --------------------------
    assert pg.evaluate("Object.keys(__ct.pathJ)").count("R") == 1
    npts = pg.evaluate("__ct.pathJ.R.filter(Boolean).length")
    assert npts > 100, npts
    print(f"actuator rod end R traced over {npts} samples")

    # ---- 8. nothing regressed -------------------------------------------
    assert not errs, errs
    pg.keyboard.press("Space"); pg.wait_for_timeout(100)
    print("spacebar demo toggle still works:", pg.evaluate("__ct.cfg.demo"))
    pg.screenshot(path=os.path.join(OUT,"panel.png"))
    b.close()
print("\nALL CHECKS PASSED")
