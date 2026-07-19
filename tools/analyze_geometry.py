"""Measure a candidate geometry against the constraints CLAUDE.md records.

    python3 tools/analyze_geometry.py dump.json

where dump.json is what `copy(__ct.dump())` puts on your clipboard in the
browser console. Reports assembly, scale length, per-10F step lengths, cusps
and kinks, mount clearance, and the actuator-triangle ceiling.
"""
import json, math, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "file://" + os.path.join(HERE, "index.html")
CAND = json.load(open(sys.argv[1]))

JS = """
(cand) => {
  Object.assign(__ct.geo, cand.geo);
  Object.assign(__ct.cfg, cand.cfg);
  __ct.cfg.demo = false;
  __ct.rebuild();
  const g = __ct.geo, c = __ct.cfg;

  // sample the indicator path densely in temperature
  const N = 1300, pts = [];
  let bad = 0;
  for (let i = 0; i <= N; i++) {
    const t = c.tmin + (c.tmax - c.tmin) * i / N;
    const p = __ct.pose(t);
    if (!p.valid) { bad++; pts.push(null); continue; }
    pts.push({t, x: p.Q.x, y: p.Q.y});
  }
  const ok = pts.filter(Boolean);

  // arc length, and per-10F segment lengths
  let total = 0;
  const seg10 = [];
  for (let lo = Math.ceil(c.tmin/10)*10; lo + 10 <= c.tmax; lo += 10) {
    let d = 0, prev = null;
    for (let k = 0; k <= 100; k++) {
      const t = lo + 10*k/100;
      const p = __ct.pose(t);
      if (!p.valid) { prev = null; continue; }
      if (prev) d += Math.hypot(p.Q.x-prev.x, p.Q.y-prev.y);
      prev = p.Q;
    }
    seg10.push({lo, len: d});
  }
  for (let i = 1; i < ok.length; i++)
    total += Math.hypot(ok[i].x-ok[i-1].x, ok[i].y-ok[i-1].y);

  // per-degree steps -> cusp / dead-spot detection
  const steps = [];
  for (let t = Math.ceil(c.tmin); t + 1 <= c.tmax; t++) {
    const a = __ct.pose(t), b = __ct.pose(t+1);
    if (a.valid && b.valid)
      steps.push({t, d: Math.hypot(b.Q.x-a.Q.x, b.Q.y-a.Q.y)});
  }

  // tick normals: how sharply does the curve turn?
  const tk = __ct.ticks;
  let minDot = 1, minAt = null;
  for (let i = 1; i < tk.length; i++) {
    const d = tk[i].nx*tk[i-1].nx + tk[i].ny*tk[i-1].ny;
    if (d < minDot) { minDot = d; minAt = tk[i].t; }
  }

  // mounts: clearance from the curve, and do mount-to-mount lines cross it
  const p0 = __ct.pose(c.temp);
  const mounts = {O2: p0.O2, O4: p0.O4, O6: p0.O6, ACT: p0.anchor};
  const clear = {};
  for (const k in mounts) {
    let m = 1e9;
    for (const q of ok) m = Math.min(m, Math.hypot(q.x-mounts[k].x, q.y-mounts[k].y));
    clear[k] = m;
  }
  const seg = (a,b,c2,d) => {
    const s=(p,q,r)=>(r.x-p.x)*(q.y-p.y)-(q.x-p.x)*(r.y-p.y);
    const d1=s(a,b,c2), d2=s(a,b,d), d3=s(c2,d,a), d4=s(c2,d,b);
    return ((d1>0)!==(d2>0)) && ((d3>0)!==(d4>0));
  };
  const names = Object.keys(mounts), crossings = [];
  for (let i=0;i<names.length;i++) for (let j=i+1;j<names.length;j++) {
    let hit = 0;
    for (let k=1;k<ok.length;k++)
      if (seg(mounts[names[i]], mounts[names[j]], ok[k-1], ok[k])) hit++;
    if (hit) crossings.push(names[i]+"-"+names[j]+" ("+hit+")");
  }

  // actuator travel actually used
  const lmin = 24 + c.extMin, lmax = 24 + c.extMax;
  return {bad, total, seg10, steps, minDot, minAt, clear, crossings,
          lmin, lmax, dAmrA: Math.abs(g.dA-g.rA), dApluslA: g.dA+g.rA};
}
"""

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(PAGE)
    pg.wait_for_timeout(500)
    r = pg.evaluate(JS, CAND)
    assert not errs, errs
    b.close()

print(f"assembles everywhere: {'YES' if r['bad']==0 else 'NO — ' + str(r['bad']) + ' invalid samples'}")
print(f"scale length:        {r['total']:.1f}\"")
print(f"actuator triangle:   |dA-rA|={r['dAmrA']:.2f} (must be < {r['lmin']:.1f})"
      f"   dA+rA={r['dApluslA']:.2f} (must be > {r['lmax']:.1f})")
print()
print("per-10F segment lengths:")
lens = [s["len"] for s in r["seg10"]]
for s in r["seg10"]:
    bar = "#" * int(s["len"] * 6)
    print(f"  {s['lo']:4}..{s['lo']+10:<4} {s['len']:6.2f}\"  {bar}")
print(f"  -> min {min(lens):.2f}\"  max {max(lens):.2f}\"  ratio {max(lens)/min(lens):.1f}x"
      f"   (search rule: max<=2.2\", ratio<=7)")
print()
st = sorted(r["steps"], key=lambda s: s["d"])
print(f"slowest 1F steps:  " + ", ".join(f"{s['t']}F={s['d']:.3f}\"" for s in st[:5]))
print(f"fastest 1F steps:  " + ", ".join(f"{s['t']}F={s['d']:.3f}\"" for s in st[-3:]))
print(f"  -> per-degree speed ratio {st[-1]['d']/st[0]['d']:.1f}x"
      f"   (search rule: min step >= 0.15\")")
print(f"sharpest turn: adjacent tick normals dot={r['minDot']:.3f} at {r['minAt']}F"
      f"   ({math.degrees(math.acos(max(-1,min(1,r['minDot'])))):.0f} deg)")
print()
print("mount clearance from the scale curve (rule: >= 2.5\"):")
for k, v in r["clear"].items():
    print(f"  {k:5} {v:6.2f}\"  {'OK' if v >= 2.5 else '** TOO CLOSE **'}")
print("mount-to-mount lines crossing the curve:",
      ", ".join(r["crossings"]) if r["crossings"] else "none - OK")
