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
    print("save list:", opts, "|", pg.inner_text("#smsg"))

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
    assert pg.input_value("#sname") == "bench test A"
    print("loaded named design ->", pg.inner_text("#smsg"))

    # delete
    pg.click("#del"); pg.wait_for_timeout(150)
    opts = pg.eval_on_selector_all("#sload option", "els=>els.map(e=>e.value)")
    assert opts == ["", "bench test B"], opts
    print("after delete:", opts)

    # ---- 2. DXF export --------------------------------------------------
    # back to the chosen preset, through the UI so the path cache rebuilds
    pg.select_option("#preset", "serpentine")
    pg.wait_for_timeout(200)
    assert abs(pg.evaluate("__ct.geo.L3") - 10.4) < 1e-9
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

    # ---- 4. nothing regressed -------------------------------------------
    assert not errs, errs
    pg.keyboard.press("Space"); pg.wait_for_timeout(100)
    print("spacebar demo toggle still works:", pg.evaluate("__ct.cfg.demo"))
    pg.screenshot(path=os.path.join(OUT,"panel.png"))
    b.close()
print("\nALL CHECKS PASSED")
