"""3D-printable benchtop model of the default index.html design (serpentine).

The flat mechanism is extended into 3D: a back plate carries posts of differing
lengths at the fixed mounts; each moving link rides its own plane parallel to the
plate; sleeves couple joints across planes. A level-assignment search picks which
link goes on which plane so nothing collides anywhere in the full excursion —
verified by sweeping all 141 poses, same sampling as index.html's rangeValid().

The actuator is replaced by a hand drive that reproduces the same constraint:
a bar pivoting on the anchor post with a slot along its axis; a shuttle rides the
slot and pins to the crank's R hole. Push the shuttle knob — R stays on the
anchor line exactly like lenOf(), and the slot ends are stops at ext 0 / 15.5.

    python3 tools/print3d.py [dump.json] [outdir]     # default: embedded geo, print/

Outputs STLs (mm) + PRINT.md (BOM, screw stacks, assembly) into outdir.
Needs shapely + trimesh + mapbox_earcut (pip). Kinematics come from
explore_designs.py, whose port crosscheck_port.py pins to the page at 1e-9.
"""
import itertools, json, math, os, sys

import numpy as np
import trimesh
from shapely.geometry import MultiPoint, Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from explore_designs import from_dict, trace, GEN_LMIN, GEN_EXTMAX

# Dumped from index.html as it opens fresh (serpentine preset, generic actuator),
# via __ct.dump() headless, 2026-08-08. Matches explore_designs.SERPENTINE.
GEO = dict(rA=12.6151, dA=27.6388, anch=-133.1494, gx=12.9, gy=-6.0, L2=11.3701,
           L3=7.7705, L4=7.0142, cu=3.5, cv=11.3, s1=-1, ox=6.9036, oy=-17.4189,
           L5=5.9, L6=14.0, cu2=19.9991, cv2=13.1489, s2=-1)

NSAMP = 141                   # pose samples over the excursion, = rangeValid()
BED = 210.0                   # printable square, mm (220 bed minus skirt margin)

# ---- model constants, mm. The tuning knobs. ----
LINK_T = 4.0                  # link thickness
AIR = 8.0                     # air gap between levels; hardware stubs live here
PITCH = LINK_T + AIR
PLATE_T = 4.0
BASE_GAP = 6.0                # plate top -> level-0 link bottom
LINK_W = 8.0                  # link width (M3 + walls)
M3 = 3.4                      # clearance hole
POST_OD = 8.0
SLEEVE_OD = 6.5
CLEAR = 1.5                   # collision buffer: sampling + print slop
MARGIN = 6.0                  # plate border past mounts+path
BAR_W = 12.0; BAR_T = 4.0
BOSS_OD = 5.0; SLOT_W = 5.4   # shuttle boss sliding in the bar slot
PUCK_OD = 16.0; PUCK_T = 6.0; HEXR = 4.5   # flat shuttle puck, deep hex nut recess
                              # sized so an M3x20 lands nut-engaged, tip sub-flush
NUT_H = 2.4; NUT_AF = 5.5     # M3 nut height / across flats
NUT_R = 3.6                   # nut corner radius + slop = any nut/washer stub
HEAD_R = 3.2; HEAD_H = 2.2    # button/flat head footprint
RING_IN = 8.0; RING_OUT = 10.0; RING_T = 2.5
FOOT_D = 10.0; FOOT_H = 6.0   # feet also hide the under-plate ground nuts
POCKET = 6.5                  # flush-head pocket bore in the laminated crank
M3_STD = [6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 60, 70]

ITEMS = ['crank', 'plate1', 'rocker1', 'plate2', 'rocker2', 'bar']
JOINTS = {'B': ('crank', 'plate1'), 'C': ('plate1', 'rocker1'),
          'P': ('plate1', 'plate2'), 'D': ('plate2', 'rocker2'),
          'R': ('crank', 'bar')}
GROUNDS = {'O2': 'crank', 'O4': 'rocker1', 'O6': 'rocker2', 'ANCH': 'bar'}
# Plates are RINGS of capsules, not filled hulls: a filled plate2 sweeps over the
# O2 post at some pose and no stacking exists at all. Hollow triangles sweep far
# less and print just as flat.
EDGES = {'crank': [('O2', 'R')],                   # B lies on the O2-R line
         'plate1': [('B', 'C'), ('C', 'P'), ('P', 'B')],
         'rocker1': [('O4', 'C')],
         'plate2': [('P', 'D'), ('D', 'Q'), ('Q', 'P')],
         'rocker2': [('O6', 'D')]}


def levz(k): return PLATE_T + BASE_GAP + k * PITCH          # level k link bottom


def solve(geo):
    """All joint/world points over the stroke, in sim inches (y down)."""
    G = from_dict(geo)[None, :]
    L = GEN_LMIN + np.linspace(0.0, GEN_EXTMAX, NSAMP)
    Qx, Qy, ok, J = trace(G, L, joints=True)
    assert ok[0], 'design must assemble over the whole excursion'
    ax = geo['dA'] * math.cos(math.radians(geo['anch']))
    ay = geo['dA'] * math.sin(math.radians(geo['anch']))
    pts = {k: np.stack([J[k][0][0], J[k][1][0]], 1) for k in ('R', 'B', 'C', 'P', 'D')}
    pts['Q'] = np.stack([Qx[0], Qy[0]], 1)
    mounts = {'O2': (0.0, 0.0), 'O4': (geo['gx'], geo['gy']),
              'O6': (geo['ox'], geo['oy']), 'ANCH': (ax, ay)}
    return pts, mounts


def pick_scale(pts, mounts):
    """mm per inch: plate (mounts + path + margin) must fit the bed, tidy 0.1 steps."""
    xs = np.concatenate([pts['Q'][:, 0], [m[0] for m in mounts.values()]])
    ys = np.concatenate([pts['Q'][:, 1], [m[1] for m in mounts.values()]])
    span = max(xs.max() - xs.min(), ys.max() - ys.min())
    s = min(5.0, math.floor((BED - 2 * MARGIN - POST_OD) / span * 10) / 10)
    return s


class Model:
    """World-space (y flipped up, mm) footprint of every item at every pose."""

    def __init__(self, geo):
        self.geo = geo
        pts, mounts = solve(geo)
        self.S = pick_scale(pts, mounts)
        f = lambda a: np.asarray(a, float) * [self.S, -self.S]     # sim in -> model mm
        self.pt = {k: f(v) for k, v in pts.items()}
        self.mount = {k: f(v) for k, v in mounts.items()}
        self.lmin, self.lmax = GEN_LMIN * self.S, (GEN_LMIN + GEN_EXTMAX) * self.S
        # tip pulled back to the far stop: a longer tip collided with the P sleeve
        # (worst 7.1mm center distance vs 10.75 needed); the outline's own end cap
        # (BAR_W/2 past this) forms the stop wall, and the whole part stays <210
        self.bar_len = self.lmax + 0.1
        # per-pose outlines: union of edge capsules, buffered to width
        self.poly = {n: [] for n in ITEMS}
        for t in range(NSAMP):
            w = {k: self.pt[k][t] for k in self.pt}
            w.update(self.mount)
            u = (w['R'] - w['ANCH']); u = u / np.linalg.norm(u)
            w['TIP'] = w['ANCH'] + u * self.bar_len
            ed = dict(EDGES, bar=[('ANCH', 'TIP')])
            for n in ITEMS:
                wd = (BAR_W if n == 'bar' else LINK_W) / 2 + CLEAR / 2
                self.poly[n].append(unary_union(
                    [MultiPoint([tuple(w[a]), tuple(w[b])]).convex_hull.buffer(wd, 4)
                     for a, b in ed[n]]))
        self.swept = {n: unary_union(self.poly[n]) for n in ITEMS}

    def circles(self, key, r):
        return [Point(tuple(p)).buffer(r + CLEAR / 2, 4) for p in self.pt[key]]


def conflicts(m):
    """Precomputed pairwise verdicts the level search consumes."""
    pair = {}                                      # same-level link vs link, per pose
    for a, b in itertools.combinations(ITEMS, 2):
        bad = m.swept[a].intersects(m.swept[b]) and \
            any(m.poly[a][t].intersects(m.poly[b][t]) for t in range(NSAMP))
        pair[(a, b)] = pair[(b, a)] = not bad
    post = {}                                      # static post shaft vs item sweep
    for g, xy in m.mount.items():
        c = Point(tuple(xy)).buffer(POST_OD / 2 + CLEAR / 2, 4)
        post[g] = {n: m.swept[n].intersects(c) for n in ITEMS}
    sleeve = {}                                    # joint sleeve vs item, per pose
    for j in JOINTS:
        cs = m.circles(j, SLEEVE_OD / 2)
        sleeve[j] = {n: m.swept[n].intersects(unary_union(cs)) and
                     any(m.poly[n][t].intersects(cs[t]) for t in range(NSAMP))
                     for n in ITEMS}
    # Both stubs are shorter than AIR, so no LINK plane ever meets them — but a
    # sleeve or post shaft passing through a stub's air band still can.
    def near(key, r, xy=None, pts=None):
        d = np.hypot(*((pts if pts is not None else
                        np.asarray(xy)[None, :]) - m.pt[key]).T)
        return d.min() < r + CLEAR
    stub = {}
    for key, r in (('R', PUCK_OD / 2), ('Q', RING_OUT)):
        stub[key] = {
            'sleeve': {j: j != key and near(key, r + SLEEVE_OD / 2, pts=m.pt[j])
                       for j in JOINTS},
            'post': {g: near(key, r + POST_OD / 2, xy=m.mount[g])
                     for g in GROUNDS}}
    # the two stubs themselves share an air band if bar and plate2 share a level
    stubs = np.hypot(*(m.pt['R'] - m.pt['Q']).T).min() < \
        RING_OUT + PUCK_OD / 2 + CLEAR
    return pair, post, sleeve, stub, stubs


def assign_levels(m):
    """Search all stackings; lowest stack wins, then least post+sleeve metal."""
    pair, post, sleeve, stub, stubs = conflicts(m)
    stub_at = {'R': 'bar', 'Q': 'plate2'}          # stub key -> the level it rides
    best = []
    for lv in itertools.product(range(len(ITEMS)), repeat=len(ITEMS)):
        L = dict(zip(ITEMS, lv))
        used = sorted(set(lv))
        if used != list(range(len(used))):
            continue                               # canonical: levels 0..K-1
        if any(L[a] == L[b] for a, b in JOINTS.values()):
            continue                               # joined links can't share a plane
        if any(L[a] == L[b] and not pair[(a, b)]
               for a, b in itertools.combinations(ITEMS, 2)):
            continue
        if any(L[n] < L[it] and post[g][n]
               for g, it in GROUNDS.items() for n in ITEMS):
            continue                               # a post shaft crosses n's plane
        if any(min(L[a], L[b]) < L[n] < max(L[a], L[b]) and sleeve[j][n]
               for j, (a, b) in JOINTS.items() for n in ITEMS):
            continue
        # sleeves / post shafts passing through the air band a stub occupies
        if any(min(L[a], L[b]) <= L[stub_at[k]] < max(L[a], L[b]) and
               stub[k]['sleeve'][j]
               for k in stub_at for j, (a, b) in JOINTS.items()):
            continue
        if any(L[it] > L[stub_at[k]] and stub[k]['post'][g]
               for k in stub_at for g, it in GROUNDS.items()):
            continue
        if stubs and L['bar'] == L['plate2']:
            continue
        metal = sum(BASE_GAP + L[it] * PITCH for it in GROUNDS.values()) + \
            sum((max(L[a], L[b]) - min(L[a], L[b])) * PITCH - LINK_T
                for a, b in JOINTS.values())
        best.append(((len(used), metal), L))
    assert best, 'no collision-free stacking exists — loosen CLEAR or thin the links'
    best.sort(key=lambda x: x[0])
    return [L for _, L in best]


# ---------- meshes ----------
EPS = 0.1                     # sink between stacked sections: overlapping shells
                              # slice cleanly; exactly-touching ones can read leaky


def extrude(poly2d, h, z=0.0):
    mesh = trimesh.creation.extrude_polygon(poly2d, h)
    assert mesh.is_watertight, 'extrusion not watertight'
    mesh.apply_translation([0, 0, z])
    return mesh


def capsule_part(holes, edges=None, w=LINK_W):
    """Flat link: capsules along the edges (default: one through all points),
    M3 at every hole. Matches the collision model's slim per-pose shape."""
    pts = [np.asarray(p, float) for p in holes]
    if edges is None:
        edges = [(i, i + 1) for i in range(len(pts) - 1)]
    outer = unary_union([MultiPoint([tuple(pts[a]), tuple(pts[b])])
                         .convex_hull.buffer(w / 2, 16) for a, b in edges])
    return outer.difference(unary_union(
        [Point(tuple(p)).buffer(M3 / 2, 16) for p in pts]))


def tube(od, idm, h):
    return extrude(Point(0, 0).buffer(od / 2, 24)
                   .difference(Point(0, 0).buffer(idm / 2, 24)), h)


def hexagon(af):
    r = af / math.sqrt(3)
    return Polygon([(r * math.cos(a), r * math.sin(a))
                    for a in np.arange(6) * math.pi / 3 + math.pi / 6])


def bar_2d(m):
    """Pivot hole at origin, +X toward R; slot ends are the stroke stops."""
    outer = MultiPoint([(0, 0), (m.bar_len, 0)]).convex_hull.buffer(BAR_W / 2, 16)
    slot = MultiPoint([(m.lmin, 0), (m.lmax, 0)]).convex_hull.buffer(SLOT_W / 2, 16)
    return outer.difference(slot).difference(Point(0, 0).buffer(M3 / 2, 16))


def shuttle_mesh():
    """Flat puck the thumb pushes: boss riding in the slot, wide flange on the
    bar, M3 nut sunk in a hex recess. Total stub stays under AIR by design.
    Sections overlap by EPS so the slicer sees one solid."""
    z1 = BAR_T + 0.4                              # boss top / flange bottom
    solid = Point(0, 0).buffer(PUCK_OD / 2, 24) \
        .difference(Point(0, 0).buffer(M3 / 2, 16))
    pocket = Point(0, 0).buffer(PUCK_OD / 2, 24).difference(hexagon(NUT_AF + 0.3))
    return trimesh.util.concatenate([
        tube(BOSS_OD, M3, z1),
        extrude(solid, PUCK_T - HEXR + EPS, z1 - EPS),
        extrude(pocket, HEXR, z1 + PUCK_T - HEXR)])


def ring_2d():
    """Indicator: M3 hub tied by three spokes to a ring the viewer reads through."""
    hub = Point(0, 0).buffer(3.5, 16)
    band = Point(0, 0).buffer(RING_OUT, 32).difference(Point(0, 0).buffer(RING_IN, 32))
    spokes = [MultiPoint([(0, 0), (RING_IN * math.cos(a), RING_IN * math.sin(a))])
              .convex_hull.buffer(0.8) for a in (0.5, 2.6, 4.7)]
    return unary_union([hub, band] + spokes).difference(Point(0, 0).buffer(M3 / 2, 16))


def plate_2d(m):
    xs = np.concatenate([m.pt['Q'][:, 0], [v[0] for v in m.mount.values()]])
    ys = np.concatenate([m.pt['Q'][:, 1], [v[1] for v in m.mount.values()]])
    r = box(xs.min() - MARGIN - POST_OD / 2, ys.min() - MARGIN - POST_OD / 2,
            xs.max() + MARGIN + POST_OD / 2, ys.max() + MARGIN + POST_OD / 2)
    holes = unary_union([Point(tuple(v)).buffer(M3 / 2, 16) for v in m.mount.values()])
    return r.difference(holes), r.bounds


def plate_mesh(m):
    p2d, bnd = plate_2d(m)
    parts = [extrude(p2d, PLATE_T)]
    path = unary_union([MultiPoint([tuple(m.pt['Q'][t]), tuple(m.pt['Q'][t + 1])])
                        .convex_hull for t in range(NSAMP - 1)]).buffer(0.6, 4)
    parts.append(extrude(path, 1.2 + EPS, PLATE_T - EPS))   # the scale curve, raised
    for cx, cy in itertools.product(bnd[0::2], bnd[1::2]):
        fx = cx + (FOOT_D / 2 + 2) * (1 if cx == bnd[0] else -1)
        fy = cy + (FOOT_D / 2 + 2) * (1 if cy == bnd[1] else -1)
        parts.append(extrude(Point(fx, fy).buffer(FOOT_D / 2, 16),
                             FOOT_H + EPS, -FOOT_H))
    return trimesh.util.concatenate(parts), bnd


def local_frames(m, t):
    """Each part's local->world 2D frame (origin point, +X unit) at pose t."""
    w = {k: m.pt[k][t] for k in m.pt}; w.update(m.mount)
    def fr(a, b):
        u = (w[b] - w[a]) / np.linalg.norm(w[b] - w[a]); return w[a], u
    return {'crank': fr('O2', 'B'), 'plate1': fr('B', 'C'), 'rocker1': fr('O4', 'C'),
            'plate2': fr('P', 'D'), 'rocker2': fr('O6', 'D'), 'bar': fr('ANCH', 'R')}


def part_2ds(m):
    """Local outlines: first hole at origin, second along +X (partDefs order)."""
    g, S = m.geo, m.S
    tri = [(0, 1), (1, 2), (2, 0)]                 # closed ring, hollow middle
    return {'plate1': capsule_part([(0, 0), (g['L3'] * S, 0),
                                    (g['cu'] * S, -g['cv'] * S)], tri),
            'rocker1': capsule_part([(0, 0), (g['L4'] * S, 0)]),
            'plate2': capsule_part([(0, 0), (g['L5'] * S, 0),
                                    (g['cu2'] * S, -g['cv2'] * S)], tri),
            'rocker2': capsule_part([(0, 0), (g['L6'] * S, 0)]),
            'bar': bar_2d(m)}


def crank_mesh(m):
    """Two 2mm laminates: flush-head pockets at B (opening up) and R (opening
    down) — B and R sit only |rA-L2| apart, so heads beside the neighbouring
    sleeve don't fit. Flat-head M3 sinks fully into a 2mm pocket."""
    g, S = m.geo, m.S
    holes = [(0, 0), (g['L2'] * S, 0), (g['rA'] * S, 0)]
    base = capsule_part(holes, [(0, 2)])
    bot = base.difference(Point(holes[2]).buffer(POCKET / 2, 16))   # R from below
    top = base.difference(Point(holes[1]).buffer(POCKET / 2, 16))   # B from above
    return trimesh.util.concatenate(
        [extrude(bot, LINK_T / 2), extrude(top, LINK_T / 2 + EPS, LINK_T / 2 - EPS)])


def place(mesh, origin, u, z):
    T = np.eye(4)
    T[:2, 0] = u; T[:2, 1] = [-u[1], u[0]]; T[:2, 3] = origin; T[2, 3] = z
    return mesh.copy().apply_transform(T)


# ---------- fastener policy & hardware verification ----------
# Orientation, chosen so protrusions land in bands with room (see verify_hardware,
# which proves it for the actual geometry):
# - grounds: screw DOWN from the link top (small head stub up), nut hidden under
#   the plate inside the feet height, excess absorbed there.
# - B and R: FLUSH heads in pockets of the laminated crank — B and R sit only
#   |rA-L2| apart on the crank arm and a head beside the other joint's sleeve
#   does not fit. B's nut goes under plate1, R's nut into the puck recess.
# - C, P, D: head under the lower link, nut atop the upper, washers under the
#   head trim the standard-length excess.
# - Q: head atop the ring, nut under plate2.

def std_len(grip, tipmax):
    """Smallest standard M3 covering grip+nut, plus washers to keep the tip
    protrusion past the nut at or under tipmax. -> (std, washers)"""
    std = next(l for l in M3_STD if l >= grip + NUT_H + 0.5)
    wash = max(0.0, math.ceil((std - grip - NUT_H - tipmax) / 0.5) * 0.5)
    return std, wash


def screw_table(lv):
    """-> rows (name, desc, grip, std, washers) and stub registry for the
    verifier: (name, trace key, radius, band) one entry per protrusion."""
    # The flush-pocket policy below is directional: B assumes plate1 sits under
    # the crank, R assumes the bar sits over it. A stacking that flips either
    # would put the stub in the wrong band and verify the wrong thing.
    assert lv['plate1'] < lv['crank'] < lv['bar'], \
        'fastener policy needs plate1 < crank < bar — re-derive orientations'
    rows, stubs = [], []
    for g, it in GROUNDS.items():
        post = BASE_GAP + lv[it] * PITCH
        grip = PLATE_T + post + (BAR_T if it == 'bar' else LINK_T)
        std, wash = std_len(grip, FOOT_H - NUT_H - 0.5)
        rows.append((g, f'{it} + post {post:g} + plate, nut under plate', grip, std, wash))
        stubs.append((g + '.head', g, NUT_R if wash else HEAD_R, lv[it]))
    for j, (a, b) in JOINTS.items():
        lo, hi = sorted((lv[a], lv[b]))
        sl = (hi - lo) * PITCH - LINK_T
        if j == 'R':
            grip = (LINK_T - 2) + sl + BAR_T + 0.4 + (PUCK_T - HEXR)
            std, wash = std_len(grip, HEXR - NUT_H - 0.2)
            assert wash == 0, 'R excess must fit the puck pocket — deepen HEXR'
            rows.append((j, f'flush head in crank + sleeve {sl:g} + shuttle, '
                         'nut in puck recess', grip, std, 0))
        elif j == 'B':
            grip = (LINK_T - 2) + sl + LINK_T
            std, wash = std_len(grip, 1.5)
            rows.append((j, f'flush head in crank + sleeve {sl:g} + plate1, '
                         'nut+washers below', grip, std, wash))
            stubs.append(('B.nut', j, NUT_R, lo - 1))
        else:
            grip = LINK_T + sl + LINK_T
            std, wash = std_len(grip, 1.5)
            rows.append((j, f'{a} + sleeve {sl:g} + {b}', grip, std, wash))
            stubs.append((j + '.head', j, NUT_R if wash else HEAD_R, lo - 1))
            stubs.append((j + '.nut', j, NUT_R, hi))
    grip = RING_T + LINK_T
    std, wash = std_len(grip, 1.5)
    rows.append(('Q', 'ring + plate2, nut+washers below', grip, std, wash))
    stubs.append(('Q.nut', 'Q', NUT_R, lv['plate2'] - 1))
    # every stub height is bounded by construction: nut+tip <= 3.9, head+washers
    # <= 4.7, puck 6.4 — all under AIR-1.5
    return rows, stubs


def verify_hardware(m, lv, stubs):
    """Everything living in the air bands — post shafts, sleeves, the puck, the
    ring, every nut/head stub — checked pairwise per pose wherever two share a
    band. The level search cleared the LINKS; this clears the hardware."""
    occ = []                                       # (label, trace, radius, lo, hi)
    for g, it in GROUNDS.items():
        occ.append((g + '.post', g, POST_OD / 2, -1, lv[it] - 1))
    for j, (a, b) in JOINTS.items():
        lo, hi = sorted((lv[a], lv[b]))
        occ.append((j + '.sleeve', j, SLEEVE_OD / 2, lo, hi - 1))
    occ.append(('puck', 'R', PUCK_OD / 2, lv['bar'], lv['bar']))
    occ.append(('ring', 'Q', RING_OUT, lv['plate2'], lv['plate2']))
    occ += [(lb, k, r, b, b) for lb, k, r, b in stubs]

    def tr(k):
        return m.pt[k] if k in m.pt else np.asarray(m.mount[k])[None, :]
    worst = []
    for (l1, k1, r1, a1, b1), (l2, k2, r2, a2, b2) in \
            itertools.combinations(occ, 2):
        if k1 == k2 or b1 < a2 or b2 < a1:
            continue                               # coaxial, or no shared band
        # moving pairs ride the same pose — compare same-t only, never cross-time
        d = np.hypot(*(tr(k1) - tr(k2)).T).min() - r1 - r2
        worst.append((round(float(d), 2), l1, l2))
    worst.sort()
    bad = [w for w in worst if w[0] < 0.5]
    return worst, bad


def build(geo, outdir):
    m = Model(geo)
    lv = rows = None
    for cand in assign_levels(m):                  # links cleared by the search;
        if not cand['plate1'] < cand['crank'] < cand['bar']:
            continue                               # fastener policy is directional
        r, stubs = screw_table(cand)               # hardware must clear too
        worst, bad = verify_hardware(m, cand, stubs)
        if not bad:
            lv, rows = cand, r
            break
        print('stacking', cand, 'rejected: hardware', bad[:3])
    assert lv, 'no stacking survives hardware verification'
    print('hardware clearances (mm, tightest):',
          ', '.join(f'{l1}-{l2} {d:g}' for d, l1, l2 in worst[:4]))
    os.makedirs(outdir, exist_ok=True)
    p2 = part_2ds(m)
    meshes = {n: extrude(p2[n], BAR_T if n == 'bar' else LINK_T)
              for n in ITEMS if n != 'crank'}
    meshes['crank'] = crank_mesh(m)
    meshes['shuttle'] = shuttle_mesh()
    meshes['ring'] = extrude(ring_2d(), RING_T)
    plate, bnd = plate_mesh(m)
    meshes['backplate'] = plate
    posts = sorted({round(BASE_GAP + lv[it] * PITCH, 1) for it in GROUNDS.values()})
    sleeves = sorted({round((abs(lv[a] - lv[b])) * PITCH - LINK_T, 1)
                      for a, b in JOINTS.values() if j_has_sleeve(lv, a, b)})
    for L in posts:
        meshes[f'post_{L:g}mm'] = tube(POST_OD, M3, L)
    for L in sleeves:
        meshes[f'sleeve_{L:g}mm'] = tube(SLEEVE_OD, M3, L)

    for n, mesh in meshes.items():                 # primitives asserted in extrude()
        mesh.export(os.path.join(outdir, n + '.stl'))

    # assembled reference at mid-stroke
    t = NSAMP // 2
    fr = local_frames(m, t)
    asm = [meshes['backplate'].copy()]
    for n in ITEMS:
        z = levz(lv[n])
        asm.append(place(meshes[n], *fr[n], z))
    for g, it in GROUNDS.items():
        asm.append(place(tube(POST_OD, M3, BASE_GAP + lv[it] * PITCH),
                         m.mount[g], np.array([1, 0]), PLATE_T))
    for j, (a, b) in JOINTS.items():
        lo, hi = sorted((lv[a], lv[b]))
        sl = (hi - lo) * PITCH - LINK_T
        asm.append(place(tube(SLEEVE_OD, M3, sl), m.pt[j][t],
                         np.array([1, 0]), levz(lo) + LINK_T))
    asm.append(place(meshes['shuttle'], m.pt['R'][t], np.array([1, 0]),
                     levz(lv['bar']) ))
    asm.append(place(meshes['ring'], m.pt['Q'][t], np.array([1, 0]),
                     levz(lv['plate2']) + LINK_T))
    trimesh.util.concatenate(asm).export(os.path.join(outdir, 'assembly.stl'))

    write_doc(m, lv, rows, bnd, posts, sleeves, outdir)
    return m, lv, bnd


def j_has_sleeve(lv, a, b):
    return abs(lv[a] - lv[b]) * PITCH - LINK_T > 0.05


def write_doc(m, lv, rows, bnd, posts, sleeves, outdir):
    w, h = bnd[2] - bnd[0], bnd[3] - bnd[1]
    stack = [f'| {k} | {lv[k]} |' for k in sorted(lv, key=lv.get)]
    scr = [f'| {n} | {d} | {g:.1f} | M3×{s} | {w_ or ""} |'
           for n, d, g, s, w_ in rows]
    doc = f"""# 3D-printed benchtop model — serpentine (default index.html design)

Generated by `python3 tools/print3d.py`. Scale **{m.S:g} mm per inch**
(1:{25.4 / m.S:.1f}); back plate {w:.0f} × {h:.0f} mm, bar {m.bar_len + BAR_W:.0f} mm
— all within a {BED:g} mm bed. All parts print flat, no supports, PLA/PETG,
0.2 mm layers. Holes are {M3} mm for M3 hardware.

## How it goes together

Every moving link rides its own plane parallel to the back plate so nothing
collides anywhere in the stroke — the level assignment is searched, then every
link pair, post shaft, sleeve, nut, head, and stub is clearance-checked over
{NSAMP} poses. Posts of differing lengths stand the grounded pivots off the
plate; sleeves couple the joints across planes. Level pitch {PITCH:g} mm
({LINK_T:g} link + {AIR:g} air); every fastener protrusion stays inside its own
air band.

| part | level (0 = closest to plate) |
|---|---|
{chr(10).join(stack)}

## Screws (M3; washers column = mm of washers under the head to trim excess)

| joint | stack | grip mm | screw | washers |
|---|---|---|---|---|
{chr(10).join(scr)}

Ground screws (O2/O4/O6/ANCH) drop in from the top; their nuts hide under the
plate inside the feet height. **B and R take FLAT-head (countersunk) M3** —
they sink flush into the crank's pockets (B from above, R from below), because
those two joints sit only {(m.geo['rA'] - m.geo['L2']) * m.S:.1f} mm apart on
the crank arm. Everything else is button/socket head.

## Printed parts

- `backplate.stl` — the scale curve is a raised ridge on top; feet lift it so
  the under-plate nuts clear. Mount holes at O2, O4, O6 and the actuator anchor.
- `crank/plate1/rocker1/plate2/rocker2.stl` — the five links, {LINK_T:g} mm.
  The plates are hollow triangles on purpose: filled ones sweep over the posts
  and no collision-free stacking exists. The crank carries the two flush pockets.
- `bar.stl` — the hand drive: pivots on the anchor post; its slot ends ARE the
  excursion stops (ext 0 and {GEN_EXTMAX:g}″ scaled), so it cannot jam the linkage
  past the actuator ceiling (dA+rA), and its tip is trimmed to clear the P sleeve.
- `shuttle.stl` — a flat puck riding the slot, screwed into the crank's R hole;
  push it along the bar to drive the model. The M3 nut sinks into its hex recess.
- `ring.stl` — indicator at Q: read the raised path through the ring, like the sim.
- `post_*mm.stl` / `sleeve_*mm.stl` — standoffs by length: posts {posts} mm,
  sleeves {sleeves} mm. The filename is the label.

## Assembly

1. Print everything. Drop the four ground screws through their links and posts
   into the plate; nut underneath, snug but free.
2. Build in level order (table above), bottom up.
3. Couple B, C, P, D with sleeves between planes (B's flat head sinks into the
   crank top, nut below plate1).
4. Bar onto the anchor post, shuttle boss into the slot, flat-head screw up
   from under the crank at R, nut into the puck recess.
5. Ring onto Q, nut under plate2. Push the puck end to end — the ring should
   trace the raised path, both slot ends stopping inside the safe stroke.

Tuning knobs are the constants at the top of `tools/print3d.py` (clearances,
thicknesses, bed size). `assembly.stl` shows everything placed at mid-stroke.
Follow-ups not built: temperature divisions/labels on the ridge (needs a font).
// ponytail: flat extrusions only — no boolean CSG anywhere.
"""
    with open(os.path.join(outdir, 'PRINT.md'), 'w') as f:
        f.write(doc)


if __name__ == '__main__':
    args = sys.argv[1:]
    geo = GEO
    if args and args[0].endswith('.json'):
        with open(args[0]) as f:
            d = json.load(f)
        geo = {k: d['geo'][k] for k in GEO}
        args = args[1:]
    outdir = args[0] if args else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'print')
    m, lv, bnd = build(geo, outdir)
    w, h = bnd[2] - bnd[0], bnd[3] - bnd[1]
    assert w <= BED and h <= BED, (w, h)
    assert m.bar_len + BAR_W <= BED, m.bar_len   # + both end caps = real part length
    order = ', '.join(f'{k}:{v}' for k, v in sorted(lv.items(), key=lambda x: x[1]))
    print(f'scale {m.S:g} mm/in  plate {w:.0f}x{h:.0f}mm  bar {m.bar_len:.0f}mm')
    print(f'levels: {order}')
    print(f'wrote {outdir}/ — see PRINT.md')
