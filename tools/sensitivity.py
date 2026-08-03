#!/usr/bin/env python3
"""What does each drag handle actually do to the design?

Sweeps every geometry parameter one at a time about a starting design and
reports, for each: how far it can move before the linkage stops assembling, and
what happens to scale length, self-crossings and the slowest degree over that
window. Grouped by the canvas HANDLE that moves it, so it reads as "dragging D
changes L5 and L6, and here is what that costs you".

    python3 tools/sensitivity.py [--geo designs.json:creative:0] [--csv out.csv]

Default start point is index.html's serpentine preset.
"""
import argparse, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import explore_designs as E

# Which canvas handle moves which parameters — index.html's COMPINFO, inverted.
# O2 is delta-based (it shifts the frame under everything) and has no parameter
# of its own, so it does not appear here.
HANDLES = [
    ('R      actuator pin (slides along the arm)', ['rA']),
    ('anchor drive mount', ['dA', 'anch']),
    ('B      coupler pin on the bell crank', ['L2']),
    ('C      rocker-1 pin', ['L3', 'L4']),
    ('O4     rocker-1 ground mount', ['gx', 'gy']),
    ('P      stage-1 coupler point', ['cu', 'cv']),
    ('D      rocker-2 pin', ['L5', 'L6']),
    ('O6     rocker-2 ground mount', ['ox', 'oy']),
    ('Q      the indicator itself', ['cu2', 'cv2']),
]
# index.html's slider clamps, which are also applyDrag's clamps and therefore the
# only bound on the geometry when dragging on mobile.
CLAMP = {'rA': (2, 30), 'dA': (10, 60), 'anch': (-180, 180), 'L2': (2, 30),
         'L3': (2, 40), 'L4': (2, 40), 'gx': (-40, 40), 'gy': (-40, 40),
         'cu': (-30, 40), 'cv': (-30, 30), 'L5': (2, 40), 'L6': (2, 40),
         'ox': (-40, 40), 'oy': (-40, 40), 'cu2': (-30, 40), 'cv2': (-30, 30)}

N = 241                 # samples per parameter sweep
L = E.drive_lengths(1301)


def sweep(g0, key, lo, hi):
    """Vary one parameter across [lo,hi]; return the grid and its metrics."""
    i = E.NAMES.index(key)
    # the start value is spliced into the grid, so "free play" is measured from
    # exactly where the design sits rather than from the nearest sample
    vals = np.unique(np.append(np.linspace(lo, hi, N), np.clip(g0[i] if key != 'anch'
                                                               else math.degrees(g0[i]), lo, hi)))
    G = np.repeat(g0[None, :], len(vals), axis=0)
    G[:, i] = np.radians(vals) if key == 'anch' else vals
    return vals, E.measure(G, L)


def window(vals, ok, v0):
    """The contiguous run of assemblable values containing the start point."""
    if not ok.any():
        return None
    j = int(np.argmin(np.abs(vals - v0)))
    if not ok[j]:
        return None
    a = j
    while a > 0 and ok[a - 1]:
        a -= 1
    b = j
    while b < len(ok) - 1 and ok[b + 1]:
        b += 1
    return a, b, j


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--geo', default='', help='designs.json:SET:INDEX, else the serpentine')
    ap.add_argument('--csv', default='')
    a = ap.parse_args()

    if a.geo:
        path, tag, ix = a.geo.rsplit(':', 2)
        gd = json.load(open(path))[tag][int(ix)]['geo']
        label = f'{os.path.basename(path)} {tag}[{ix}]'
    else:
        gd, label = E.SERPENTINE, 'serpentine preset (index.html)'
    g0 = E.from_dict(gd)

    base = E.measure(g0[None, :], L)
    assert base['ok'][0], 'the starting design does not assemble across the range'
    print(f'start: {label}')
    print(f'  scale {base["plen"][0]:.1f}"   loops {base["cross"][0]:.0f}   '
          f'slowest degree {base["stall"][0]:.3f}"/degF   '
          f'envelope {base["w"][0]:.1f}x{base["h"][0]:.1f}"\n')

    hdr = (f'{"parameter":<10}{"now":>8}{"assembles over":>18}{"free play":>11}'
           f'{"scale len":>18}{"loops":>8}{"stall":>15}')
    rows = []
    for hname, keys in HANDLES:
        print(f'\n{hname}\n{hdr}')
        for k in keys:
            v0 = gd[k]
            lo, hi = CLAMP[k]
            vals, m = sweep(g0, k, lo, hi)
            w = window(vals, m['ok'], v0)
            if w is None:
                print(f'  {k:<8}{v0:>8.2f}   (start point not on the grid)')
                continue
            i0, i1, j = w
            sub = slice(i0, i1 + 1)
            pl, cr, st = m['plen'][sub], m['cross'][sub], m['stall'][sub]
            unit = '°' if k == 'anch' else '"'
            span = f'{vals[i0]:.1f}..{vals[i1]:.1f}{unit}'
            back, fwd = max(0.0, v0 - vals[i0]), max(0.0, vals[i1] - v0)
            play = 'pinned' if back + fwd < 0.05 else f'-{back:.1f}/+{fwd:.1f}'
            print(f'  {k:<8}{v0:>8.2f}{span:>18}{play:>11}'
                  f'{f"{np.nanmin(pl):.0f}-{np.nanmax(pl):.0f}" + chr(34):>18}'
                  f'{f"{np.nanmin(cr):.0f}-{np.nanmax(cr):.0f}":>8}'
                  f'{f"{np.nanmin(st):.3f}-{np.nanmax(st):.3f}":>15}')
            rows.append(dict(handle=hname.split()[0], param=k, now=v0,
                             lo=float(vals[i0]), hi=float(vals[i1]),
                             play_lo=float(back), play_hi=float(fwd),
                             len_lo=float(np.nanmin(pl)), len_hi=float(np.nanmax(pl)),
                             len_at_best=float(vals[sub][int(np.nanargmax(pl))]),
                             cross_hi=float(np.nanmax(cr)),
                             stall_lo=float(np.nanmin(st)), stall_hi=float(np.nanmax(st))))

    print('\n\nWhat this says, ranked by how much scale length each knob can reach:')
    for r in sorted(rows, key=lambda r: -r['len_hi'])[:6]:
        print(f'  {r["param"]:<5} (handle {r["handle"]:<6}) tops out at {r["len_hi"]:6.1f}" '
              f'at {r["param"]}={r["len_at_best"]:.2f}, from {r["now"]:.2f} now')
    print('\nTightest handles — least room before the linkage stops assembling:')
    for r in sorted(rows, key=lambda r: min(r['play_lo'], r['play_hi']))[:6]:
        print(f'  {r["param"]:<5} (handle {r["handle"]:<6}) only '
              f'-{r["play_lo"]:.2f}/+{r["play_hi"]:.2f}{"°" if r["param"] == "anch" else chr(34)}'
              f' before it stops assembling')

    if a.csv:
        import csv
        with open(a.csv, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        print(f'\nwrote {a.csv}')


if __name__ == '__main__':
    main()
