#!/usr/bin/env python3
"""Screenshot each design in designs.json through index.html itself.

Renders through the real page, so what you see is exactly what the simulator
draws — no second drawing code to drift. Writes one PNG per design plus a
contact sheet.

    python3 tools/render_designs.py designs.json outdir/   # raw search output
    python3 tools/render_designs.py --presets out.png      # the shipped example-* presets
"""
import json, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = 'file://' + os.path.join(HERE, 'index.html')

SETUP = """
(o) => {
  const {geo, rot, ghost, box} = o;
  // VIEWINSET.left is a getter (318 above 640px wide) and __ct does not expose
  // it, so fitView always keeps the drawing clear of the panel. Hide the panel
  // for a clean shot and CLIP to the same region rather than fight the fit.
  document.getElementById('panel').style.display = 'none';
  document.getElementById('hint').style.display = 'none';
  Object.assign(__ct.geo, geo);
  __ct.geo.actT = 1; __ct.geo.aClamp = 23.23;
  Object.assign(__ct.cfg, {extMin: 0, extMax: 16, tmin: -20, tmax: 110, temp: 70,
                           demo: false, ghost, showBox: box, region: false,
                           dims: false, ticks: true, rot});
  __ct.rebuild();
  return {len: __ct.chunks.reduce((a, c) => {
      let d = 0;
      for (let i = 1; i < c.pts.length; i++)
        d += Math.hypot(c.pts[i].x - c.pts[i-1].x, c.pts[i].y - c.pts[i-1].y);
      return a + d; }, 0),
    box: __ct.bbox ? {w: __ct.bbox.w, h: __ct.bbox.h} : null};
}
"""


def render(items, outdir, tag, rot=110):
    os.makedirs(outdir, exist_ok=True)
    shots = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1400, 'height': 950},
                        device_scale_factor=1)
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(PAGE); pg.wait_for_timeout(500)
        for i, d in enumerate(items):
            for mode, ghost, box in (('path', False, False), ('mech', True, True)):
                r = pg.evaluate(SETUP, {'geo': d['geo'], 'rot': rot,
                                        'ghost': ghost, 'box': box})
                pg.wait_for_timeout(120)
                f = os.path.join(outdir, f'{tag}-{i+1:02d}-{mode}.png')
                pg.screenshot(path=f, clip={'x': 310, 'y': 0, 'width': 1080, 'height': 950})
                if mode == 'path':
                    shots.append(f)
                    d.setdefault('page', {})['len'] = r['len']
                    d['page']['box'] = r['box']
        assert not errs, errs
        b.close()
    return shots


def sheet(shots, path, cols=5, cell=380, captions=None):
    """Contact sheet without PIL: an HTML page screenshotted by the same browser."""
    caps = captions or [os.path.basename(s)[:-9] for s in shots]
    assert len(caps) == len(shots), 'caption/shot mismatch would silently drop tiles'
    imgs = ''.join(f'<figure><img src="file://{os.path.abspath(s)}">'
                   f'<figcaption>{c}</figcaption></figure>'
                   for s, c in zip(shots, caps))
    html = (f'<style>body{{margin:0;background:#0e1116;font:12px system-ui;color:#9fb0c8}}'
            f'main{{display:grid;grid-template-columns:repeat({cols},{cell}px);gap:6px;padding:6px}}'
            f'figure{{margin:0}}img{{width:{cell}px;display:block;border:1px solid #223}}'
            f'figcaption{{padding:5px 2px;color:#c8d4e4;font-size:13px}}</style>'
            f'<main>{imgs}</main>')
    tmp = path + '.html'
    open(tmp, 'w').write(html)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': cols * (cell + 6) + 14, 'height': 900})
        pg.goto('file://' + os.path.abspath(tmp)); pg.wait_for_timeout(700)
        pg.screenshot(path=path, full_page=True)
        b.close()
    os.remove(tmp)


PRESET_SETUP = """
(o) => {
  document.getElementById('panel').style.display = 'none';
  document.getElementById('hint').style.display = 'none';
  const s = document.getElementById('preset');
  s.value = o.name; s.dispatchEvent(new Event('change', {bubbles: true}));
  Object.assign(__ct.cfg, {demo: false, ghost: false, showBox: false, region: false,
                           dims: false, ticks: true, temp: 70, rot: 110});
  __ct.rebuild();
  let d = 0;
  for (const c of __ct.chunks)
    for (let i = 1; i < c.pts.length; i++)
      d += Math.hypot(c.pts[i].x - c.pts[i-1].x, c.pts[i].y - c.pts[i-1].y);
  return {len: d, chunks: __ct.chunks.length, valid: __ct.rangeValid()};
}
"""


def render_presets(out_png, tmpdir):
    """Shoot every example-* preset exactly as the page ships it.

    Reads the presets from index.html rather than designs.json, so the sheet can
    never show a curve the dropdown does not actually produce.
    """
    os.makedirs(tmpdir, exist_ok=True)
    shots, rows = [], []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1400, 'height': 950}, device_scale_factor=1)
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(PAGE); pg.wait_for_timeout(500)
        names = pg.eval_on_selector_all(
            '#preset option', "e => e.map(o => o.value).filter(v => v.startsWith('example-'))")
        assert names, 'no example-* presets in the dropdown'
        for n in names:
            r = pg.evaluate(PRESET_SETUP, {'name': n})
            assert r['valid'] and r['chunks'] == 130, (n, r)
            pg.wait_for_timeout(140)
            f = os.path.join(tmpdir, f'{n}.png')
            pg.screenshot(path=f, clip={'x': 310, 'y': 0, 'width': 1080, 'height': 950})
            shots.append((f, f'{n}  —  {r["len"]:.0f}\u2033 scale'))
            rows.append((n, r['len']))
        assert not errs, errs
        b.close()
    sheet([s for s, _ in shots], out_png, cols=4, cell=430,
          captions=[c for _, c in shots])
    for n, l in rows:
        print(f'  {n}  {l:6.1f}"')
    print(f'{len(rows)} presets -> {out_png}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    if sys.argv[1] == '--presets':
        render_presets(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '/tmp/ct-presets')
        sys.exit(0)
    data = json.load(open(sys.argv[1]))
    outdir = sys.argv[2]
    allshots = []
    for tag in ('longest', 'creative'):
        if tag not in data:
            continue
        s = render(data[tag], outdir, tag)
        allshots += s
        print(f'{tag}: {len(s)} rendered')
    sheet(allshots, os.path.join(outdir, 'contact.png'))
    # The page's own chunk-derived length must agree with the search's. It reads
    # a shade LOW by construction: buildChunks samples 781 points where the search
    # re-measures finalists at 1301, and a coarser polyline always cuts corners.
    # So: within 1%, and never over.
    worst = 0.0
    for tag in ('longest', 'creative'):
        for i, d in enumerate(data.get(tag, [])):
            a, b = d['metrics']['plen'], d['page']['len']
            assert b <= a + 1e-6, f'{tag}[{i}] page {b:.2f} exceeds dense {a:.2f}'
            assert (a - b) / a < 0.01, f'{tag}[{i}] search {a:.2f} vs page {b:.2f}'
            worst = max(worst, (a - b) / a)
    print(f'search and page agree on every scale length (worst gap {worst*100:.2f}%)')
    json.dump(data, open(sys.argv[1], 'w'), indent=1)
    print('contact sheet:', os.path.join(outdir, 'contact.png'))
