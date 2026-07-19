"""Drives index.html headless to check named saves and the DXF export.

    pip install playwright && playwright install chromium
    python3 tools/verify_export.py [outdir]

Writes parts.dxf / points.dxf to outdir (default /tmp) so you can eyeball them,
and asserts the exported geometry matches the live `geo` values.
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

    # reload: list survives, autoload restored the last save
    pg.reload(); pg.wait_for_timeout(500)
    assert not errs, errs
    opts = pg.eval_on_selector_all("#sload option", "els=>els.map(e=>e.value)")
    assert opts == ["", "bench test A", "bench test B"], opts
    assert abs(pg.evaluate("__ct.geo.L3") - 20.0) < 1e-9, "autoload should give the last save"

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
    assert abs(pg.evaluate("__ct.geo.L3") - 7.7705) < 1e-9
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

    # ---- 6. ticks ---------------------------------------------------
    pg.select_option("#preset", "serpentine"); pg.wait_for_timeout(200)
    sub = pg.evaluate("__ct.buildPoints()")
    so = parse_dxf(sub)
    lay = {}
    for e in so:
        if e["type"] == "LINE": lay[e[8][0]] = lay.get(e[8][0], 0) + 1
    print("tick line counts by layer:", lay)
    # -20..110 every 5 deg -> 27 ticks, 14 of them on the 10s
    assert lay["TICKS_MAJOR"] == 14, lay
    assert lay["TICKS_MINOR"] == 13, lay
    assert "TICKS_SUB" not in lay, "1-degree sub-ticks were removed"
    assert sorted(lay) == ["SCALE_CURVE", "TICKS_MAJOR", "TICKS_MINOR"], sorted(lay)

    # ticks must sit on the same side of the curve as on screen
    ticks = pg.evaluate("__ct.ticks.map(k=>({t:k.t,x:k.q.x,y:k.q.y,nx:k.nx,ny:k.ny,major:k.major}))")
    assert len(ticks) == 27, len(ticks)
    tk = next(k for k in ticks if k["t"] == 70)
    dxf70 = [e for e in so if e["type"] == "LINE" and e[8][0] == "TICKS_MAJOR"]
    match = [e for e in dxf70
             if abs(float(e[10][0]) - (tk["x"] + tk["nx"]*0.25)) < 1e-4
             and abs(float(e[20][0]) - (-tk["y"] + -tk["ny"]*0.25)) < 1e-4]
    assert match, "70F tick normal must mirror as a vector (same side as on screen)"
    print("tick normals mirror consistently into CAD space")

    # the serpentine cusps: the tangent flips 180 there, so the raw left-normal would throw
    # every tick past it onto the far side of the line. Adjacent ticks must stay together.
    flips = [(a["t"], b["t"]) for a, b in zip(ticks, ticks[1:])
             if a["nx"]*b["nx"] + a["ny"]*b["ny"] < 0]
    assert not flips, f"tick side flips between {flips}"
    worst = min(a["nx"]*b["nx"] + a["ny"]*b["ny"] for a, b in zip(ticks, ticks[1:]))
    print(f"no tick-side flips across {len(ticks)} ticks (tightest turn: dot={worst:.3f})")

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
