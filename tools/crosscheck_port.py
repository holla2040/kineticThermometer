#!/usr/bin/env python3
"""Assert tools/explore_designs.py's numpy kinematics match index.html's pose().

Feeds random geometries (and the serpentine preset) to both and compares the
indicator path point-for-point. If this drifts, every design the search finds is
measured against a solver the page does not have.
"""
import json, math, os, sys
import numpy as np
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import explore_designs as E

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = 'file://' + os.path.join(HERE, 'index.html')
NS = 141

JS = """
(cands) => cands.map(g => {
  Object.assign(__ct.geo, g);
  __ct.geo.actT = 1; __ct.geo.aClamp = 23.23;
  __ct.cfg.extMin = 0; __ct.cfg.extMax = 16;
  __ct.cfg.tmin = -20; __ct.cfg.tmax = 110; __ct.cfg.demo = false;
  const N = 140, xs = [], ys = [];
  let ok = true, len = 0, prev = null;
  for (let i = 0; i <= N; i++) {
    const p = __ct.pose(-20 + 130 * i / N);
    if (!p.valid) { ok = false; break; }
    xs.push(p.Q.x); ys.push(p.Q.y);
    if (prev) len += Math.hypot(p.Q.x - prev.x, p.Q.y - prev.y);
    prev = p.Q;
  }
  return {ok, len, xs, ys};
})
"""

rng = np.random.default_rng(11)
L = E.drive_lengths(NS)
G = E.sample_box(rng, 4000)
Qx, Qy, ok = E.trace(G, L)
G = G[ok][:60]
assert len(G) >= 20, f'only {len(G)} feasible seeds'
Qx, Qy, _ = E.trace(G, L)
plen = E.scale_length(Qx, Qy)

cands = [E.to_dict(g) for g in G]
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(PAGE); pg.wait_for_timeout(400)
    res = pg.evaluate(JS, cands)
    assert not errs, errs
    b.close()

worst_pt = worst_len = 0.0
for i, r in enumerate(res):
    assert r['ok'], f'candidate {i}: page says unassemblable, python says fine'
    d = np.hypot(np.array(r['xs']) - Qx[i], np.array(r['ys']) - Qy[i]).max()
    worst_pt = max(worst_pt, d)
    worst_len = max(worst_len, abs(r['len'] - plen[i]))
print(f'{len(res)} geometries compared')
print(f'worst point disagreement : {worst_pt:.3e} in')
print(f'worst length disagreement: {worst_len:.3e} in')
assert worst_pt < 1e-9 and worst_len < 1e-9, 'PORT DOES NOT MATCH THE PAGE'
print('port matches index.html pose() exactly')
