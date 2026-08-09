"""Dependency-free port of tools/print3d.py's level search + fastener policy.

Consumes a trace exported from the page (joint positions at NSAMP poses, in sim
inches, y down) instead of re-deriving the kinematics, so it is correct for BOTH
actuator types — print3d.py hardwires the generic 24..39.5 drive length and is
wrong for a joyce design. Every collision test in print3d is between capsules
and discs, so shapely's polygon ops reduce to exact segment-distance algebra.

Emits the same fusion-data.json shape, plus the Q path for the scale ridge.
"""
import itertools, json, math, sys

NSAMP = 141
BED = 210.0
LINK_T = 4.0
AIR = 8.0
PITCH = LINK_T + AIR
PLATE_T = 4.0
BASE_GAP = 6.0
LINK_W = 8.0
M3 = 3.4
POST_OD = 8.0
SLEEVE_OD = 6.5
CLEAR = 1.5
MARGIN = 6.0
BAR_W = 12.0
BAR_T = 4.0
BOSS_OD = 5.0
SLOT_W = 5.4
PUCK_OD = 16.0
PUCK_T = 6.0
HEXR = 4.5
NUT_H = 2.4
NUT_AF = 5.5
NUT_R = 3.6
HEAD_R = 3.2
HEAD_H = 2.2
RING_IN = 8.0
RING_OUT = 10.0
RING_T = 2.5
FOOT_D = 10.0
FOOT_H = 6.0
POCKET = 6.5
M3_STD = [6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 60, 70]

ITEMS = ['crank', 'plate1', 'rocker1', 'plate2', 'rocker2', 'bar']
JOINTS = {'B': ('crank', 'plate1'), 'C': ('plate1', 'rocker1'),
          'P': ('plate1', 'plate2'), 'D': ('plate2', 'rocker2'),
          'R': ('crank', 'bar')}
GROUNDS = {'O2': 'crank', 'O4': 'rocker1', 'O6': 'rocker2', 'ANCH': 'bar'}
EDGES = {'crank': [('O2', 'R')], 'plate1': [('B', 'C'), ('C', 'P'), ('P', 'B')],
         'rocker1': [('O4', 'C')], 'plate2': [('P', 'D'), ('D', 'Q'), ('Q', 'P')],
         'rocker2': [('O6', 'D')]}


def levz(k):
    return PLATE_T + BASE_GAP + k * PITCH


def _clamp01(v):
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def pt_seg(p, a, b):
    """Distance from point p to segment ab."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0.0 else _clamp01(((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2)
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def seg_seg(a, b, c, d):
    """Distance between segments ab and cd (0 if they cross)."""
    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    d1, d2 = cross(c, d, a), cross(c, d, b)
    d3, d4 = cross(a, b, c), cross(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))


def pick_scale(Q, mounts):
    xs = [p[0] for p in Q] + [m[0] for m in mounts.values()]
    ys = [p[1] for p in Q] + [m[1] for m in mounts.values()]
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    return min(5.0, math.floor((BED - 2 * MARGIN - POST_OD) / span * 10) / 10)


class Model:
    """World-space (y flipped up, mm) footprint of every item at every pose."""

    def __init__(self, trace):
        J = trace['joints']
        mounts_in = trace['mounts']
        self.n = trace['nsamp']
        self.S = pick_scale(J['Q'], mounts_in)
        f = lambda xy: (xy[0] * self.S, -xy[1] * self.S)
        self.pt = {k: [f(p) for p in J[k]] for k in ('R', 'B', 'C', 'P', 'D', 'Q')}
        self.mount = {k: f(v) for k, v in mounts_in.items()}
        self.lmin, self.lmax = (trace['lenOf'][0] * self.S, trace['lenOf'][1] * self.S)
        self.bar_len = self.lmax + 0.1
        self.rad = {n: ((BAR_W if n == 'bar' else LINK_W) / 2 + CLEAR / 2) for n in ITEMS}
        # per-pose edge segments; the bar's outline runs anchor -> trimmed tip
        self.seg = {n: [] for n in ITEMS}
        for t in range(self.n):
            w = {k: self.pt[k][t] for k in self.pt}
            w.update(self.mount)
            ax, ay = w['ANCH']
            ux, uy = w['R'][0] - ax, w['R'][1] - ay
            L = math.hypot(ux, uy)
            w['TIP'] = (ax + ux / L * self.bar_len, ay + uy / L * self.bar_len)
            ed = dict(EDGES, bar=[('ANCH', 'TIP')])
            for n in ITEMS:
                self.seg[n].append([(w[a], w[b]) for a, b in ed[n]])

    def hits_pt(self, n, t, p, r):
        """Does item n's outline at pose t reach within r of point p?"""
        return any(pt_seg(p, a, b) <= self.rad[n] + r for a, b in self.seg[n][t])


def conflicts(m):
    pair = {}
    for a, b in itertools.combinations(ITEMS, 2):
        bad = any(seg_seg(p0, p1, q0, q1) <= m.rad[a] + m.rad[b]
                  for t in range(m.n)
                  for p0, p1 in m.seg[a][t] for q0, q1 in m.seg[b][t])
        pair[(a, b)] = pair[(b, a)] = not bad
    post = {}
    for g, xy in m.mount.items():
        r = POST_OD / 2 + CLEAR / 2
        post[g] = {n: any(m.hits_pt(n, t, xy, r) for t in range(m.n)) for n in ITEMS}
    sleeve = {}
    for j in JOINTS:
        r = SLEEVE_OD / 2 + CLEAR / 2
        sleeve[j] = {n: any(m.hits_pt(n, t, m.pt[j][t], r) for t in range(m.n))
                     for n in ITEMS}

    def near(key, r, xy=None, pts=None):
        src = pts if pts is not None else [xy] * m.n
        return min(math.hypot(src[t][0] - m.pt[key][t][0],
                              src[t][1] - m.pt[key][t][1]) for t in range(m.n)) < r + CLEAR

    stub = {}
    for key, r in (('R', PUCK_OD / 2), ('Q', RING_OUT)):
        stub[key] = {
            'sleeve': {j: j != key and near(key, r + SLEEVE_OD / 2, pts=m.pt[j])
                       for j in JOINTS},
            'post': {g: near(key, r + POST_OD / 2, xy=m.mount[g]) for g in GROUNDS}}
    stubs = min(math.hypot(m.pt['R'][t][0] - m.pt['Q'][t][0],
                           m.pt['R'][t][1] - m.pt['Q'][t][1])
                for t in range(m.n)) < RING_OUT + PUCK_OD / 2 + CLEAR
    return pair, post, sleeve, stub, stubs


def puck_band(L):
    """The shuttle rides the face of the bar AWAY from the crank, so its air
    band follows the crank/bar order. print3d.py assumes crank<bar and asserts
    it; deriving it instead is what lets a flipped stacking build."""
    return L['bar'] if L['crank'] < L['bar'] else L['bar'] - 1


def stub_band(L, k):
    return puck_band(L) if k == 'R' else L['plate2']


def pocket_dirs(L):
    """Flush head sinks into the crank from the face away from the mating part."""
    return {'B': 'down' if L['plate1'] > L['crank'] else 'up',
            'R': 'down' if L['bar'] > L['crank'] else 'up'}


def assign_levels(m):
    pair, post, sleeve, stub, stubs = conflicts(m)
    stub_at = {'R': 'bar', 'Q': 'plate2'}
    best = []
    for lv in itertools.product(range(len(ITEMS)), repeat=len(ITEMS)):
        L = dict(zip(ITEMS, lv))
        used = sorted(set(lv))
        if used != list(range(len(used))):
            continue
        if any(L[a] == L[b] for a, b in JOINTS.values()):
            continue
        if any(L[a] == L[b] and not pair[(a, b)]
               for a, b in itertools.combinations(ITEMS, 2)):
            continue
        if any(L[n] < L[it] and post[g][n]
               for g, it in GROUNDS.items() for n in ITEMS):
            continue
        if any(min(L[a], L[b]) < L[n] < max(L[a], L[b]) and sleeve[j][n]
               for j, (a, b) in JOINTS.items() for n in ITEMS):
            continue
        if any(min(L[a], L[b]) <= stub_band(L, k) < max(L[a], L[b]) and stub[k]['sleeve'][j]
               for k in stub_at for j, (a, b) in JOINTS.items()):
            continue
        if any(L[it] > stub_band(L, k) and stub[k]['post'][g]
               for k in stub_at for g, it in GROUNDS.items()):
            continue
        if stubs and stub_band(L, 'R') == stub_band(L, 'Q'):
            continue
        metal = sum(BASE_GAP + L[it] * PITCH for it in GROUNDS.values()) + \
            sum((max(L[a], L[b]) - min(L[a], L[b])) * PITCH - LINK_T
                for a, b in JOINTS.values())
        best.append(((len(used), metal), L))
    assert best, 'no collision-free stacking exists — loosen CLEAR or thin the links'
    best.sort(key=lambda x: x[0])
    return [L for _, L in best]


def std_len(grip, tipmax):
    std = next(l for l in M3_STD if l >= grip + NUT_H + 0.5)
    wash = max(0.0, math.ceil((std - grip - NUT_H - tipmax) / 0.5) * 0.5)
    return std, wash


def screw_table(lv):
    pk = pocket_dirs(lv)
    rows, stubs = [], []
    for g, it in GROUNDS.items():
        post = BASE_GAP + lv[it] * PITCH
        grip = PLATE_T + post + (BAR_T if it == 'bar' else LINK_T)
        std, wash = std_len(grip, FOOT_H - NUT_H - 0.5)
        rows.append((g, '%s + post %g + plate, nut under plate' % (it, post), grip, std, wash))
        stubs.append((g + '.head', g, NUT_R if wash else HEAD_R, lv[it]))
    for j, (a, b) in JOINTS.items():
        lo, hi = sorted((lv[a], lv[b]))
        sl = (hi - lo) * PITCH - LINK_T
        if j == 'R':
            grip = (LINK_T - 2) + sl + BAR_T + 0.4 + (PUCK_T - HEXR)
            std, wash = std_len(grip, HEXR - NUT_H - 0.2)
            assert wash == 0, 'R excess must fit the puck pocket — deepen HEXR'
            rows.append((j, 'flush head in crank + sleeve %g + shuttle, nut in puck recess' % sl,
                         grip, std, 0))
        elif j == 'B':
            grip = (LINK_T - 2) + sl + LINK_T
            std, wash = std_len(grip, 1.5)
            side = 'below' if lv['plate1'] < lv['crank'] else 'above'
            rows.append((j, 'flush head (%s) in crank + sleeve %g + plate1, nut+washers %s'
                         % (pk['B'], sl, side), grip, std, wash))
            stubs.append(('B.nut', j, NUT_R, lo - 1 if side == 'below' else hi))
        else:
            grip = LINK_T + sl + LINK_T
            std, wash = std_len(grip, 1.5)
            rows.append((j, '%s + sleeve %g + %s' % (a, sl, b), grip, std, wash))
            stubs.append((j + '.head', j, NUT_R if wash else HEAD_R, lo - 1))
            stubs.append((j + '.nut', j, NUT_R, hi))
    grip = RING_T + LINK_T
    std, wash = std_len(grip, 1.5)
    rows.append(('Q', 'ring + plate2, nut+washers below', grip, std, wash))
    stubs.append(('Q.nut', 'Q', NUT_R, lv['plate2'] - 1))
    return rows, stubs


def verify_hardware(m, lv, stubs, modeled_only=False):
    """modeled_only: keep just the parts a CAD assembly actually contains —
    posts, sleeves, puck, ring — and drop the nut/head stubs, which exist only
    in the physical build. A design can pass one and fail the other."""
    occ = []
    for g, it in GROUNDS.items():
        occ.append((g + '.post', g, POST_OD / 2, -1, lv[it] - 1))
    for j, (a, b) in JOINTS.items():
        lo, hi = sorted((lv[a], lv[b]))
        occ.append((j + '.sleeve', j, SLEEVE_OD / 2, lo, hi - 1))
    pb = puck_band(lv)
    occ.append(('puck', 'R', PUCK_OD / 2, pb, pb))
    occ.append(('ring', 'Q', RING_OUT, lv['plate2'], lv['plate2']))
    if not modeled_only:
        occ += [(lb, k, r, b, b) for lb, k, r, b in stubs]

    def tr(k):
        return m.pt[k] if k in m.pt else [m.mount[k]] * m.n
    worst = []
    for (l1, k1, r1, a1, b1), (l2, k2, r2, a2, b2) in itertools.combinations(occ, 2):
        if k1 == k2 or b1 < a2 or b2 < a1:
            continue
        A, B = tr(k1), tr(k2)
        d = min(math.hypot(A[t][0] - B[t][0], A[t][1] - B[t][1]) for t in range(m.n)) - r1 - r2
        worst.append((round(d, 2), l1, l2))
    worst.sort()
    return worst, [w for w in worst if w[0] < 0.5]


def plate_bounds(m):
    xs = [p[0] for p in m.pt['Q']] + [v[0] for v in m.mount.values()]
    ys = [p[1] for p in m.pt['Q']] + [v[1] for v in m.mount.values()]
    r = MARGIN + POST_OD / 2
    return [min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r]


def local_frames(m, t):
    w = {k: m.pt[k][t] for k in m.pt}
    w.update(m.mount)
    return w


def build(trace, fasteners=True):
    m = Model(trace)
    lv = rows = worst = None
    fbad = []
    tried = []
    for cand in assign_levels(m):
        try:
            r, stubs = screw_table(cand)
        except AssertionError as e:          # fastener policy can't serve this stacking
            tried.append((cand, [(None, 'screw_table', str(e))], []))
            continue
        w, bad = verify_hardware(m, cand, stubs)
        wm, badm = verify_hardware(m, cand, stubs, modeled_only=True)
        if not bad or (not fasteners and not badm):
            lv, rows, worst, fbad = cand, r, (w if fasteners else wm), bad
            break
        tried.append((cand, bad[:2], badm[:2]))
    assert lv, 'no stacking survives verification: %r' % (tried[:3],)

    g = trace['geo']
    S = m.S
    mid = m.n // 2
    holes = {
        'crank': {'O2': [0, 0], 'B': [round(g['L2'] * S, 3), 0], 'R': [round(g['rA'] * S, 3), 0]},
        'plate1': {'B': [0, 0], 'C': [round(g['L3'] * S, 3), 0],
                   'P': [round(g['cu'] * S, 3), round(-g['cv'] * S, 3)]},
        'rocker1': {'O4': [0, 0], 'C': [round(g['L4'] * S, 3), 0]},
        'plate2': {'P': [0, 0], 'D': [round(g['L5'] * S, 3), 0],
                   'Q': [round(g['cu2'] * S, 3), round(-g['cv2'] * S, 3)]},
        'rocker2': {'O6': [0, 0], 'D': [round(g['L6'] * S, 3), 0]},
        'bar': {'ANCH': [0, 0], 'slot_center_from': [round(m.lmin, 3), 0],
                'slot_center_to': [round(m.lmax, 3), 0]},
    }
    posts = sorted({round(BASE_GAP + lv[it] * PITCH, 1) for it in GROUNDS.values()})
    sleeves = sorted({round(abs(lv[a] - lv[b]) * PITCH - LINK_T, 1)
                      for a, b in JOINTS.values()
                      if abs(lv[a] - lv[b]) * PITCH - LINK_T > 0.05})
    ck = {}
    for label, t in (('ext0', 0), ('mid', mid), ('ext%g' % trace['ext'][-1], m.n - 1)):
        ck[label] = {k: [round(m.pt[k][t][0], 3), round(m.pt[k][t][1], 3)]
                     for k in ('R', 'B', 'C', 'P', 'D', 'Q')}
    out = {
        'units': 'mm', 'scale_mm_per_inch': S,
        'source': {'preset': trace.get('preset'), 'actT': g['actT'],
                   'lenOf_in': trace['lenOf'], 'stroke_in': trace['stroke'],
                   'ext_in': [trace['ext'][0], trace['ext'][-1]], 'nsamp': m.n},
        'levels': lv,
        'level_z_link_bottom': {str(k): levz(k) for k in sorted(set(lv.values()))},
        'mounts_model_mm': {k: [round(v[0], 3), round(v[1], 3)] for k, v in m.mount.items()},
        'part_local_holes': holes,
        'bar': {'width': BAR_W, 'thick': BAR_T,
                'outline_capsule_axis_len': round(m.bar_len, 3),
                'physical_len': round(m.bar_len + BAR_W, 3), 'slot_width': SLOT_W},
        'screws': [{'joint': j, 'stack': d, 'grip_mm': gr, 'screw': 'M3x%g' % st,
                    'washers_mm': wa} for j, d, gr, st, wa in rows],
        'posts_mm': posts, 'sleeves_mm': sleeves,
        'post_by_ground': {g_: BASE_GAP + lv[it] * PITCH for g_, it in GROUNDS.items()},
        'sleeve_by_joint': {j: abs(lv[a] - lv[b]) * PITCH - LINK_T
                            for j, (a, b) in JOINTS.items()},
        'consts': {'LINK_T': LINK_T, 'AIR': AIR, 'PITCH': PITCH, 'PLATE_T': PLATE_T,
                   'BASE_GAP': BASE_GAP, 'LINK_W': LINK_W, 'M3': M3, 'POST_OD': POST_OD,
                   'SLEEVE_OD': SLEEVE_OD, 'BAR_W': BAR_W, 'BAR_T': BAR_T,
                   'BOSS_OD': BOSS_OD, 'SLOT_W': SLOT_W, 'PUCK_OD': PUCK_OD,
                   'PUCK_T': PUCK_T, 'HEXR': HEXR, 'NUT_AF': NUT_AF, 'RING_IN': RING_IN,
                   'RING_OUT': RING_OUT, 'RING_T': RING_T, 'FOOT_D': FOOT_D,
                   'FOOT_H': FOOT_H, 'POCKET': POCKET, 'CLEAR': CLEAR, 'MARGIN': MARGIN},
        'assembly': {
            'crank_pockets': pocket_dirs(lv),
            'shuttle_side': 'above' if lv['crank'] < lv['bar'] else 'below',
            'shuttle_z_base': levz(lv['bar']) if lv['crank'] < lv['bar']
                              else levz(lv['bar']) + LINK_T,
            'ring_z': levz(lv['plate2']) + LINK_T,
            'link_z': {n: levz(lv[n]) for n in ITEMS},
            'post_z0': PLATE_T,
            'sleeve_z0_by_joint': {j: levz(min(lv[a], lv[b])) + LINK_T
                                   for j, (a, b) in JOINTS.items()},
            'sleeve_rigid_to': {j: (a if lv[a] < lv[b] else b)
                                for j, (a, b) in JOINTS.items()},
            'policy_matches_print3d': lv['plate1'] < lv['crank'] < lv['bar'],
        },
        'plate_bounds_model_mm': [round(v, 3) for v in plate_bounds(m)],
        'pose_checkpoints': ck,
        'q_path_model_mm': [[round(p[0], 4), round(p[1], 4)] for p in m.pt['Q']],
        'mid_frames': {k: [round(v[0], 4), round(v[1], 4)]
                       for k, v in local_frames(m, mid).items()},
        'tightest_hardware_mm': worst[:5],
        'fastener_conflicts': [[d, a, b_] for d, a, b_ in fbad],
        'physically_buildable': not fbad,
    }
    return m, lv, out


if __name__ == '__main__':
    trace = json.load(open(sys.argv[1]))
    trace.setdefault('preset', sys.argv[1].split('/')[-1].replace('-trace.json', ''))
    m, lv, out = build(trace, fasteners='--cad-only' not in sys.argv)
    b = out['plate_bounds_model_mm']
    w, h = b[2] - b[0], b[3] - b[1]
    print('scale %g mm/in  plate %.0fx%.0fmm  bar %.0fmm  (bed %g)'
          % (m.S, w, h, m.bar_len + BAR_W, BED))
    print('levels:', ', '.join('%s:%d' % kv for kv in sorted(lv.items(), key=lambda x: x[1])))
    print('tightest modelled gap:', ', '.join('%s-%s %g' % (a, b_, d) for d, a, b_ in out['tightest_hardware_mm'][:4]))
    print('pockets %s  shuttle %s  print3d-policy %s'
          % (out['assembly']['crank_pockets'], out['assembly']['shuttle_side'],
             out['assembly']['policy_matches_print3d']))
    if out['fastener_conflicts']:
        print('NOT PHYSICALLY BUILDABLE - fastener clashes:')
        for d, a, b_ in out['fastener_conflicts']:
            print('    %-10s <-> %-10s overlap %.2f mm' % (a, b_, -d))
    else:
        print('fasteners clear')
    assert w <= BED and h <= BED, (w, h)
    assert m.bar_len + BAR_W <= BED, m.bar_len
    outs = [a for a in sys.argv[2:] if not a.startswith('--')]
    if outs:
        json.dump(out, open(outs[0], 'w'), indent=1)
        print('wrote', outs[0])
