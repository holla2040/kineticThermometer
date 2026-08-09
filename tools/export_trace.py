"""Export a design from the page as a trace: geometry PLUS sampled kinematics.

    python3 tools/export_trace.py [--url U] [--preset NAME | --design FILE] [out.json]

`__ct.dump()` gives geo+cfg, which is what print3d.py eats. That is enough only
because print3d re-derives the kinematics in Python. A trace carries the joint
positions the PAGE computed, so anything downstream transcribes instead of
re-deriving — the project's rule everywhere else — and is therefore correct for
both actuator types. print3d.py hardwires the generic 24..39.5in drive length and
is wrong for a joyce design (shape-01 runs 23.351..38.803); a trace cannot be.

Coordinates are the page's own: inches, y DOWN. Consumers flip and scale.
Needs playwright (pip install playwright && playwright install chromium).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_URL = 'file://' + os.path.join(os.path.dirname(HERE), 'index.html')

JS = """(N) => {
  const g = __ct.geo, c = __ct.cfg;
  const ext = [], J = {R:[], B:[], C:[], P:[], D:[], Q:[]};
  for (let i = 0; i < N; i++) {
    ext.push(c.extMin + (c.extMax - c.extMin) * i / (N - 1));
    const p = __ct.pose(c.tmin + (c.tmax - c.tmin) * i / (N - 1));
    for (const k of ['R','B','C','P','D','Q'])
      J[k].push(p && p[k] ? [p[k].x, p[k].y] : null);
  }
  const ax = g.dA * Math.cos(g.anch * Math.PI / 180),
        ay = g.dA * Math.sin(g.anch * Math.PI / 180);
  return {geo: JSON.parse(JSON.stringify(g)), cfg: JSON.parse(JSON.stringify(c)),
          nsamp: N, ext: ext, joints: J,
          mounts: {O2:[0,0], O4:[g.gx,g.gy], O6:[g.ox,g.oy], ANCH:[ax,ay]},
          lenOf: [__ct.lenOf(c.extMin), __ct.lenOf(c.extMax)],
          stroke: __ct.strokeOf(), rangeValid: __ct.rangeValid()};
}"""


def export(url, preset=None, design=None, nsamp=141):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1400, 'height': 950})
        pg.goto(url, wait_until='load')
        pg.wait_for_function('window.__ct !== undefined')
        if design:
            with open(design) as f:
                d = json.load(f)
            pg.evaluate('(g) => { Object.assign(__ct.geo, g.geo);'
                        ' Object.assign(__ct.cfg, g.cfg); __ct.rebuild(); }', d)
            name = os.path.basename(design).rsplit('.', 1)[0]
        else:
            pg.select_option('#preset', preset or 'serpentine')
            name = preset or 'serpentine'
        pg.wait_for_timeout(400)
        tr = pg.evaluate(JS, nsamp)
        b.close()
    tr['preset'] = name
    return tr


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('out', nargs='?', help='output json (default: <name>-trace.json)')
    ap.add_argument('--url', default=DEFAULT_URL, help='page to drive')
    ap.add_argument('--preset', help='preset name from the dropdown')
    ap.add_argument('--design', help='a saved design json (geo+cfg) to apply instead')
    ap.add_argument('--nsamp', type=int, default=141, help='pose samples (default 141)')
    a = ap.parse_args()
    tr = export(a.url, a.preset, a.design, a.nsamp)
    out = a.out or '%s-trace.json' % tr['preset']
    with open(out, 'w') as f:
        json.dump(tr, f)
    g = tr['geo']
    print('%s: actT=%d  lenOf %.4f..%.4f in  stroke %g  assembles %s'
          % (tr['preset'], g['actT'], tr['lenOf'][0], tr['lenOf'][1],
             tr['stroke'], tr['rangeValid']))
    if not tr['rangeValid']:
        print('WARNING: this design does not assemble across its own range', file=sys.stderr)
    print('wrote %s (%d poses)' % (out, tr['nsamp']))


if __name__ == '__main__':
    main()
