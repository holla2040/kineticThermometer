#!/usr/bin/env python3
"""Propose abstract scale-curve SHAPES before any linkage exists.

The reverse of explore_designs.py's parameter-space search, adopted 2026-08-03
after the owner rejected safer-lookalikes of existing presets: draw candidate
curves FIRST, let the owner pick, and only then ask (via explore_designs.py
--targetpts --objective match) how close this mechanism can get to each pick.

Curves are generated in turning-function space — the same representation the
novelty metric lives in: theta'(s) = a random Fourier series plus 0-2 impulse
bumps (hooks), integrated twice at N uniform-arc stations. That yields open,
exactly arc-length-parametrized polylines whose wildness is directly the thing
turn_stats measures.

Every emitted proposal:
  - turns BOTH ways 2.5-7 rad (the wild presets' range; an arc scores ~0),
  - packs 1.2-3.0 arc inches per envelope-diagonal inch (dens),
  - has an envelope aspect within 2.5:1 and visibly separated endpoints,
  - sits >= --novelty (default 7.0) in shape distance from EVERY preset shipped
    in index.html and >= --pairwise (default 5.0) from every other proposal.
    7.0 is the gate the second clean-* run had to clear; the two original
    clean families sit 6.3 apart.

If the requested count cannot be packed at those gates, the tool emits what it
found and says so — it never quietly lowers a gate.

    python3 tools/propose_shapes.py proposals.json proposals.png
    python3 tools/propose_shapes.py --selfcheck
"""
import argparse, json, os, re, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import explore_designs as E

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N_PTS = 1041          # uniform-arc stations per proposal; explore_designs
                      # resamples to ~SHAPE_N+1 for the descriptor either way
ARCLEN = 90.0         # nominal emitted size in inches — the descriptor is
                      # scale-free, this just makes the JSON readable


def shipped_geos():
    """All preset geometries parsed out of index.html itself, so the novelty
    reference can never go stale against what the dropdown actually holds."""
    src = open(os.path.join(HERE, 'index.html')).read()
    out = {}
    for m in re.finditer(r"'?([a-z]+-\d+|serpentine|grandarc)'?\s*:\s*\{([^}]*)\}",
                         src, re.S):
        d = {kv.group(1): float(kv.group(2))
             for kv in re.finditer(r'(\w+):(-?[\d.]+)', m.group(2))}
        if all(k in d for k in E.NAMES):
            out[m.group(1)] = d
    return out


def shipped_descs():
    """Descriptors of the shipped curves AS SHIPPED: joyce drive over the page's
    0-15.5" excursion, not the search's full 16" stroke — example-02 stops
    assembling at exactly 16.0 and the menu never goes there."""
    geos = shipped_geos()
    G = np.array([E.from_dict(g) for g in geos.values()])
    L = np.hypot(E.ACLAMP + np.linspace(0.0, 15.5, E.SHAPE_TRACE), E.JOYCE_OFF)
    Qx, Qy, ok = E.trace(G, L)
    assert ok.all(), [n for n, o in zip(geos, ok) if not o]
    ix = np.linspace(0, E.SHAPE_TRACE - 1, E.SHAPE_N + 1).round().astype(int)
    return list(geos), E.turning_desc(Qx[:, ix], Qy[:, ix])


def gen_curve(rng, n=N_PTS):
    """One random open curve: theta'(s) -> (x, y) at n uniform-arc stations."""
    s = np.linspace(0, 1, n)
    thp = np.zeros(n)
    for k in range(1, 7):
        thp += rng.normal(0, 11.0 / k ** 0.7) * np.cos(k * np.pi * s
                                                       + rng.uniform(0, 2 * np.pi))
    for _ in range(rng.integers(0, 3)):
        c, w = rng.uniform(0.12, 0.88), rng.uniform(0.012, 0.05)
        thp += (rng.normal(0, 2.2) / (w * np.sqrt(2 * np.pi))
                * np.exp(-0.5 * ((s - c) / w) ** 2))     # ~N(0,2.2) rad of hook
    ds = 1.0 / (n - 1)
    th = np.concatenate([[0.0], np.cumsum(0.5 * (thp[1:] + thp[:-1])) * ds])
    x = np.concatenate([[0.0], np.cumsum(np.cos(th[1:])) * ds])
    y = np.concatenate([[0.0], np.cumsum(np.sin(th[1:])) * ds])
    return x * ARCLEN, y * ARCLEN


def stats_of(x, y):
    pos, neg, rev, wig = (v[0] for v in E.turn_stats(x[None, :], y[None, :]))
    w = x.max() - x.min()
    h = y.max() - y.min()
    diag = float(np.hypot(w, h))
    arc = float(np.hypot(np.diff(x), np.diff(y)).sum())
    end = float(np.hypot(x[-1] - x[0], y[-1] - y[0]))
    cross = float(E.crossings(x[None, ::5], y[None, ::5])[0])
    return dict(both=float(min(pos, neg)), rev=float(rev), wig=float(wig),
                dens=arc / diag, aspect=max(w, h) / max(min(w, h), 1e-9),
                endsep=end / diag, arc=arc, cross=cross)


def plausible(st):
    """Stay inside what the mechanism has ever been seen to draw — proposing
    the impossible would make every synthesis run a foregone failure."""
    return (2.5 <= st['both'] <= 7.0 and 1.2 <= st['dens'] <= 3.0
            and st['aspect'] <= 2.5 and st['endsep'] >= 0.12)


def desc_of(x, y):
    ix = np.linspace(0, len(x) - 1, min(len(x), E.SHAPE_N + 1)).round().astype(int)
    return E.turning_desc(x[None, ix], y[None, ix])


def propose(count, novelty, pairwise, seed, tries=40000):
    names, refs = shipped_descs()
    rng = np.random.default_rng(seed)
    kept, tried, feas = [], 0, 0
    while len(kept) < count and tried < tries:
        tried += 1
        x, y = gen_curve(rng)
        st = stats_of(x, y)
        if not plausible(st):
            continue
        feas += 1
        d = desc_of(x, y)
        dref = float(E.shape_dist(d, refs).min())
        if dref < novelty:
            continue
        dpair = min((float(E.shape_dist(d, k['desc']).min()) for k in kept),
                    default=1e9)
        if dpair < pairwise:
            continue
        kept.append(dict(id=f'prop-{len(kept)+1:02d}', x=x, y=y, desc=d, st=st,
                         nearest=names[int(E.shape_dist(d, refs).argmin())],
                         dref=dref, dpair=min(dpair, 99.0)))
    print(f'{tried} drawn, {feas} plausible, {len(kept)} kept '
          f'(novelty >= {novelty} vs {len(names)} shipped, pairwise >= {pairwise})')
    if len(kept) < count:
        print(f'NOTE: could not pack {count} proposals at these gates; '
              f'emitting {len(kept)}. Loosen --novelty/--pairwise consciously '
              f'or accept the smaller set — do not lower gates silently.')
    return kept


def write_json(kept, path):
    out = [dict(id=k['id'], pts=[[round(float(a), 4), round(float(b), 4)]
                                 for a, b in zip(k['x'], k['y'])],
                stats={kk: round(vv, 3) for kk, vv in k['st'].items()},
                nearest_shipped=[k['nearest'], round(k['dref'], 2)])
           for k in kept]
    json.dump(out, open(path, 'w'))
    print(f'wrote {path} ({len(out)} proposals)')


def write_sheet(kept, path, cols=4, cell=380):
    """Inline-SVG grid screenshotted by chromium — same pattern as
    render_designs.sheet(), which needs PNG inputs we don't have."""
    from playwright.sync_api import sync_playwright
    figs = []
    for k in kept:
        x, y, st = k['x'], k['y'], k['st']
        w, h = x.max() - x.min(), y.max() - y.min()
        pad = 0.06 * max(w, h)
        pts = ' '.join(f'{a:.2f},{b:.2f}' for a, b in zip(x[::4], y[::4]))
        figs.append(
            f'<figure><svg viewBox="{x.min()-pad:.2f} {y.min()-pad:.2f} '
            f'{w+2*pad:.2f} {h+2*pad:.2f}" width="{cell}" height="{cell*0.72:.0f}" '
            f'preserveAspectRatio="xMidYMid meet">'
            f'<polyline points="{pts}" fill="none" stroke="#f0954f" '
            f'stroke-width="{max(w,h)/150:.3f}" stroke-linecap="round"/>'
            f'<circle cx="{x[0]:.2f}" cy="{y[0]:.2f}" r="{max(w,h)/80:.3f}" fill="#5aa2e8"/>'
            f'<circle cx="{x[-1]:.2f}" cy="{y[-1]:.2f}" r="{max(w,h)/80:.3f}" fill="#ef5350"/>'
            f'</svg><figcaption>{k["id"]}  ·  turns {st["both"]:.1f} rad each way  ·  '
            f'{st["cross"]:.0f} self-cross  ·  nearest shipped: {k["nearest"]} '
            f'({k["dref"]:.1f})</figcaption></figure>')
    html = (f'<style>body{{margin:0;background:#0e1116;font:12px system-ui}}'
            f'main{{display:grid;grid-template-columns:repeat({cols},{cell}px);'
            f'gap:8px;padding:8px}}figure{{margin:0;background:#131721;'
            f'border:1px solid #223}}figcaption{{padding:6px 8px;color:#c8d4e4;'
            f'font-size:13px}}</style><main>{"".join(figs)}</main>')
    tmp = path + '.html'
    open(tmp, 'w').write(html)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': cols * (cell + 8) + 16, 'height': 900})
        pg.goto('file://' + os.path.abspath(tmp))
        pg.wait_for_timeout(500)
        pg.screenshot(path=path, full_page=True)
        b.close()
    os.remove(tmp)
    print(f'wrote {path}')


def _selfcheck():
    # an arc turns one way only -> both ~ 0 -> must be rejected
    t = np.linspace(0, 1.6 * np.pi, N_PTS)
    st = stats_of(9 * np.cos(t), 9 * np.sin(t))
    assert st['both'] < 0.1 and not plausible(st), st
    # the generator must actually produce keepable curves
    rng = np.random.default_rng(3)
    ok = 0
    for _ in range(400):
        x, y = gen_curve(rng)
        ok += plausible(stats_of(x, y))
    assert ok >= 10, f'only {ok}/400 plausible - generator drifted'
    # descriptor must be stable under 2x decimation of the same curve
    rng = np.random.default_rng(5)
    for _ in range(20):
        x, y = gen_curve(rng)
        if plausible(stats_of(x, y)):
            d = float(E.shape_dist(desc_of(x, y), desc_of(x[::2], y[::2]))[0, 0])
            assert d < 0.35, f'descriptor unstable under resampling: {d}'
    # a proposal is distance 0 from itself and the shipped refs load
    names, refs = shipped_descs()
    assert len(names) >= 21, names
    assert float(E.shape_dist(refs[:1], refs[:1])[0, 0]) < 1e-9
    print('selfcheck ok')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out_json', nargs='?', default='proposals.json')
    ap.add_argument('out_png', nargs='?', default='proposals.png')
    ap.add_argument('--n', type=int, default=16)
    ap.add_argument('--novelty', type=float, default=7.0)
    ap.add_argument('--pairwise', type=float, default=5.0)
    ap.add_argument('--seed', type=int, default=11)
    a = ap.parse_args()
    kept = propose(a.n, a.novelty, a.pairwise, a.seed)
    if not kept:
        sys.exit('nothing to emit')
    for k in kept:
        st = k['st']
        print(f'  {k["id"]}: both {st["both"]:.2f}  dens {st["dens"]:.2f}  '
              f'cross {st["cross"]:.0f}  rev {st["rev"]:.0f}  '
              f'nearest {k["nearest"]} at {k["dref"]:.2f}  pairwise {k["dpair"]:.2f}')
    write_json(kept, a.out_json)
    write_sheet(kept, a.out_png)


if __name__ == '__main__':
    if '--selfcheck' in sys.argv:
        _selfcheck()
    else:
        main()
