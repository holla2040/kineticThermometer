#!/usr/bin/env python3
"""Search the linkage parameter space for LONG and for INTERESTING scale curves.

Two objectives over the same geometry box:

  A. longest  — the greatest scale length (arc length of the indicator point Q
     across the excursion) that still assembles everywhere and fits the envelope.
  B. character — scale length >= 80", scored on self-crossings, curvature
     reversals, turning both ways, and curve packed per inch of envelope.

The kinematics are a straight port of index.html's pose() — same margins
(actFits 0.5, circInt none), same branch signs, same collinear R/B crank.
tools/crosscheck_port.py asserts the two agree to 1e-13 against the live page;
run it after touching either solver. tools/search_geometry.py is the original
scalar search that produced the presets and stays as that record.

Everything is vectorized over candidates, including the hill climb and the
self-intersection count, so a run is millions of trials rather than thousands.

Actuator: the Joyce QS11940 the owner owns (16" stroke, offset clamp) at the
as-modeled clamp position, full stroke. Finalists are also reported against the
generic 24"+18" actuator at 0-15.5" so a design can be built either way.

    python3 tools/explore_designs.py --trials 20000000 --out designs.json

Runs are memory-hungry in proportion to --batch; see its comment in main() before
starting several at once.
"""
import argparse, json, math, os, sys, warnings
import numpy as np

# infeasible candidates are all-NaN by construction; the ok mask is what filters them
warnings.filterwarnings('ignore', message='.*All-NaN.*')
warnings.filterwarnings('ignore', message='.*Mean of empty slice.*')
warnings.filterwarnings('ignore', message='.*empty slice.*')

# ---------- actuator (matches index.html JOYCE / lenOf) ----------
JOYCE_OFF, JOYCE_STROKE, ACLAMP = 2.378, 16.0, 23.23
GEN_LMIN, GEN_EXTMAX = 24.0, 15.5      # the generic type as the presets use it


def drive_lengths(nsamp, joyce=True):
    if joyce:
        return np.hypot(ACLAMP + np.linspace(0.0, JOYCE_STROKE, nsamp), JOYCE_OFF)
    return GEN_LMIN + np.linspace(0.0, GEN_EXTMAX, nsamp)


# ---------- parameter box ----------
# The buildable box the original search used, with the coupler offsets widened:
# cu/cv/cu2/cv2 are exactly the knobs that make a coupler curve loop and cusp, and
# the owner's hand-tuned serpentine already sits at cu2=20.0, cv2=13.1 — the old
# box edge. Link lengths and mount positions are unchanged.
NAMES = 'rA dA anch gx gy L2 L3 L4 cu cv s1 ox oy L5 L6 cu2 cv2 s2'.split()
LO = np.array([10, 24, -math.pi, -24, -24,  6, 10,  8,  0, -18, 0, -28, -28,  8,  8,  0, -20, 0], float)
HI = np.array([22, 40,  math.pi,  28,  24, 16, 26, 22, 24,  18, 0,  32,  26, 24, 20, 26,  20, 0], float)
SIGN_IX = [10, 17]                      # s1, s2 come from {-1,+1}, not the box
FREE_IX = np.setdiff1d(np.arange(len(NAMES)), SIGN_IX)
SPAN = np.where(HI - LO > 0, HI - LO, 1.0)
NP_ = len(NAMES)


def sample_box(rng, n):
    G = LO + (HI - LO) * rng.random((n, NP_))
    for i in SIGN_IX:
        G[:, i] = rng.choice(np.array([-1.0, 1.0]), n)
    return G


# ---------- vectorized kinematics ----------
def circ_int(px, py, r0, qx, qy, r1, sign):
    dx, dy = qx - px, qy - py
    d = np.hypot(dx, dy)
    with np.errstate(invalid='ignore', divide='ignore'):
        ok = (d > 1e-9) & (d <= r0 + r1) & (d >= np.abs(r0 - r1))
        a = (r0 * r0 - r1 * r1 + d * d) / (2 * d)
        h2 = r0 * r0 - a * a
        ok &= h2 >= 0
        h = np.sqrt(np.maximum(h2, 0))
        mx, my = px + a * dx / d, py + a * dy / d
        x = mx + sign * h * (-dy / d)
        y = my + sign * h * (dx / d)
    return np.where(ok, x, np.nan), np.where(ok, y, np.nan), ok


def trans_angles(Bx, By, Cx, Cy, gx, gy, L3, L4):
    """Transmission angle at a circle-crossing joint, folded into 0..90 degrees.

    Same definition as index.html's transAngle(): the angle at C between the link
    arriving (C->B) and the link being driven (C->O4). 90 is ideal, 0 is dead
    center. The two norms are the link lengths, so no hypot is needed.
    """
    with np.errstate(invalid='ignore', divide='ignore'):
        dot = (Bx - Cx) * (gx - Cx) + (By - Cy) * (gy - Cy)
        d = np.degrees(np.arccos(np.clip(dot / (L3 * L4), -1, 1)))
    return np.minimum(d, 180 - d)


def trace(G, L, joints=False):
    """G (N,18), L (S,) -> Qx, Qy (N,S), ok (N,).

    ok is True only when the design assembles at EVERY sample — the same thing
    index.html's rangeValid() means. With joints=True the dict also carries `ta`,
    the worse of the two transmission angles at each sample.
    """
    rA = G[:, 0:1]; dA = G[:, 1:2]; anch = G[:, 2:3]
    gx = G[:, 3:4]; gy = G[:, 4:5]; L2 = G[:, 5:6]; L3 = G[:, 6:7]; L4 = G[:, 7:8]
    cu = G[:, 8:9]; cv = G[:, 9:10]; s1 = G[:, 10:11]
    ox = G[:, 11:12]; oy = G[:, 12:13]; L5 = G[:, 13:14]; L6 = G[:, 14:15]
    cu2 = G[:, 15:16]; cv2 = G[:, 16:17]; s2 = G[:, 17:18]
    Lr = L[None, :]

    fits = (Lr >= np.abs(dA - rA) + 0.5) & (Lr <= dA + rA - 0.5)   # actFits
    with np.errstate(invalid='ignore', divide='ignore'):
        c = np.clip((dA * dA + rA * rA - Lr * Lr) / (2 * dA * rA), -1, 1)
    th = anch + np.arccos(c)
    ct, st = np.cos(th), np.sin(th)
    Bx, By = L2 * ct, L2 * st
    Cx, Cy, okC = circ_int(Bx, By, L3, gx, gy, L4, s1)
    ux, uy = (Cx - Bx) / L3, (Cy - By) / L3
    Px, Py = Bx + cu * ux - cv * uy, By + cu * uy + cv * ux
    Dx, Dy, okD = circ_int(Px, Py, L5, ox, oy, L6, s2)
    dl = np.hypot(Dx - Px, Dy - Py)
    with np.errstate(invalid='ignore', divide='ignore'):
        vx, vy = (Dx - Px) / dl, (Dy - Py) / dl
    Qx, Qy = Px + cu2 * vx - cv2 * vy, Py + cu2 * vy + cv2 * vx
    ok = (fits & okC & okD & np.isfinite(Qx) & np.isfinite(Qy)).all(axis=1)
    if joints:
        ta = np.minimum(trans_angles(Bx, By, Cx, Cy, gx, gy, L3, L4),
                        trans_angles(Px, Py, Dx, Dy, ox, oy, L5, L6))
        return Qx, Qy, ok, dict(R=(rA * ct, rA * st), B=(Bx, By), C=(Cx, Cy),
                                P=(Px, Py), D=(Dx, Dy), ta=ta)
    return Qx, Qy, ok


def mounts_of(G):
    """(N,4,2): ACT anchor, O2, O4, O6."""
    ax = G[:, 1] * np.cos(G[:, 2]); ay = G[:, 1] * np.sin(G[:, 2])
    z = np.zeros(len(G))
    return np.stack([np.stack([ax, ay], 1), np.stack([z, z], 1),
                     G[:, 3:5], G[:, 11:13]], 1)


# ---------- vectorized metrics ----------
def scale_length(Qx, Qy):
    return np.hypot(np.diff(Qx, axis=1), np.diff(Qy, axis=1)).sum(axis=1)


JKEYS = ('R', 'B', 'C', 'P', 'D')


def envelope_of(G, Qx, Qy, J):
    """(N,2) width/height of everything the piece sweeps: path, joint traces, mounts."""
    X = [Qx] + [J[k][0] for k in JKEYS] + [mounts_of(G)[:, :, 0]]
    Y = [Qy] + [J[k][1] for k in JKEYS] + [mounts_of(G)[:, :, 1]]
    X = np.concatenate(X, axis=1); Y = np.concatenate(Y, axis=1)
    with np.errstate(invalid='ignore'):
        w = np.nanmax(X, 1) - np.nanmin(X, 1)
        h = np.nanmax(Y, 1) - np.nanmin(Y, 1)
    return np.nan_to_num(w, nan=1e6), np.nan_to_num(h, nan=1e6)


def envelope(G, L):
    Qx, Qy, ok, J = trace(G, L, joints=True)
    return envelope_of(G, Qx, Qy, J)


def turn_stats(Qx, Qy):
    """Signed turning: total left, total right, reversal count, and wiggle.

    wiggle is the coefficient of variation of CURVATURE (turn per unit arc). A
    circular arc — the shape a pure length objective converges on — has constant
    curvature and scores 0 no matter how long it is. That is the whole point of
    the metric: it separates "long" from "interesting".
    """
    seg = np.hypot(np.diff(Qx, axis=1), np.diff(Qy, axis=1))
    ang = np.arctan2(np.diff(Qy, axis=1), np.diff(Qx, axis=1))
    d = np.diff(ang, axis=1)
    d = (d + math.pi) % (2 * math.pi) - math.pi
    pos = np.where(d > 0, d, 0).sum(1)
    neg = np.where(d < 0, -d, 0).sum(1)
    with np.errstate(invalid='ignore', divide='ignore'):
        kap = d / np.maximum(0.5 * (seg[:, :-1] + seg[:, 1:]), 1e-9)
        wig = np.nanstd(kap, 1) / (np.nanmean(np.abs(kap), 1) + 1e-9)
    # a reversal is a sign change between consecutive non-negligible turns.
    # Sentinel-fill the small ones so the comparison stays vectorized.
    s = np.where(np.abs(d) > 0.02, np.sign(d), np.nan)
    filled = np.zeros_like(s)
    cur = np.zeros(len(s))
    for j in range(s.shape[1]):                 # forward-fill, one pass over samples
        cur = np.where(np.isnan(s[:, j]), cur, s[:, j])
        filled[:, j] = cur
    rev = (np.diff(filled, axis=1) != 0).sum(1).astype(float)
    return pos, neg, rev, np.nan_to_num(wig)


def crossings(Qx, Qy, step=4):
    """(N,) self-intersections of each polyline, non-adjacent segments only."""
    x, y = Qx[:, ::step], Qy[:, ::step]
    ax, ay = x[:, :-1], y[:, :-1]
    rx, ry = np.diff(x, axis=1), np.diff(y, axis=1)
    # pairwise over segments: i (rows) vs j (cols)
    px = ax[:, :, None]; py = ay[:, :, None]
    qx = ax[:, None, :]; qy = ay[:, None, :]
    r1x = rx[:, :, None]; r1y = ry[:, :, None]
    s1x = rx[:, None, :]; s1y = ry[:, None, :]
    denom = r1x * s1y - r1y * s1x
    qpx, qpy = qx - px, qy - py
    with np.errstate(invalid='ignore', divide='ignore'):
        t = (qpx * s1y - qpy * s1x) / denom
        u = (qpx * r1y - qpy * r1x) / denom
    n = ax.shape[1]
    far = np.abs(np.arange(n)[:, None] - np.arange(n)[None, :]) > 1
    hit = (np.abs(denom) > 1e-12) & (t > 0) & (t < 1) & (u > 0) & (u < 1) & far[None]
    return np.nan_to_num(hit).sum(axis=(1, 2)) / 2.0        # each pair counted twice


def mount_clear(G, Qx, Qy, step=3):
    """(N,) smallest distance from any fixed mount to the path (rule: >= 2.5")."""
    M = mounts_of(G)                                        # (N,4,2)
    x, y = Qx[:, ::step], Qy[:, ::step]
    dx = x[:, None, :] - M[:, :, 0:1]
    dy = y[:, None, :] - M[:, :, 1:2]
    with np.errstate(invalid='ignore'):
        return np.nanmin(np.hypot(dx, dy), axis=(1, 2))


SHAPE_N = 200          # shape metrics always read at this resolution, so a coarse
                       # search sample and a dense re-measure describe one curve


def measure(G, L, shape_from=None):
    """Everything the scorers and the report need, in one pass.

    Arc length, envelope and mount clearance come from the sampling in L. Shape
    metrics are read off a path decimated to ~SHAPE_N points, so they mean the
    same thing whether L is the 141-sample search grid or the dense re-measure.
    """
    Qx, Qy, ok, J = trace(G, L, joints=True)
    plen = scale_length(Qx, Qy)
    w, h = envelope_of(G, Qx, Qy, J)
    with np.errstate(invalid='ignore'):
        ta = np.nanmin(J['ta'], axis=1)          # worst approach to dead center
    k = max(1, Qx.shape[1] // SHAPE_N)
    Sx, Sy = (Qx, Qy) if k == 1 else (Qx[:, ::k], Qy[:, ::k])
    pos, neg, rev, wig = turn_stats(Sx, Sy)
    cr = crossings(Sx, Sy, step=max(1, Sx.shape[1] // 40))
    diag = np.hypot(w, h)
    seg = np.hypot(np.diff(Qx, axis=1), np.diff(Qy, axis=1))
    with np.errstate(invalid='ignore', divide='ignore'):
        dens = np.where(diag > 1e-6, plen / diag, 0.0)
    # Slowest and fastest 1F step, in inches, at the default -20..110F range: the
    # excursion in 130 equal slices. High curvature variation is what gives a
    # curve character, but it is ALSO what a cusp looks like, and a cusp is a dead
    # spot where the indicator stalls — the exact defect that killed the owner's
    # first tuned serpentine at 70F. Measured whenever the sampling divides by 130.
    n = seg.shape[1]
    if n % 130 == 0:
        per = seg.reshape(len(seg), 130, n // 130).sum(2)
        stall, rush = np.nanmin(per, 1), np.nanmax(per, 1)
    else:
        stall = rush = np.full(len(seg), np.nan)
    return dict(ok=ok, plen=plen, w=w, h=h, pos=pos, neg=neg, rev=rev, wig=wig,
                cross=cr, dens=dens, clear=mount_clear(G, Qx, Qy), ta=np.nan_to_num(ta),
                stall=stall, rush=rush,
                segmin=np.nanmin(seg, 1), segmax=np.nanmax(seg, 1))


# ---------- objectives ----------
BAD = -1e9


STALL_MIN = 0.15       # in/degF, the original search's min-segment rule
STALL_GATE = 0.07      # what the owner's own tuned serpentine manages (0.075)
TA_MIN = 0.0           # degrees; set from --tamin. 0 = the pre-2026-08-03 behaviour


def _quality(m):
    """Shared nudges: clear the mounts, and keep the indicator moving.

    The stall term is heavy on purpose. High curvature variation is what gives a
    curve character — and it is also what a cusp looks like, where the indicator
    parks for several degrees. The owner's first tuned serpentine was thrown out
    for exactly that (0.056"/degF at 70F, a dead spot at typical ambient), so a
    search that rewards character without pricing stalls just rediscovers it.
    """
    stall = np.nan_to_num(m['stall'], nan=STALL_MIN)
    # The dead-center term dominates everything else on purpose. A long scale and a
    # near-singular linkage are the SAME geometry (README, "Dead center"): the
    # indicator sweeps furthest for the least input right where the two assembly
    # branches merge. Any objective that prices length without pricing this walks
    # straight back to the edge — which is exactly how example-00..10 got there.
    # Below the gate the penalty is linear, so the climb still has a gradient home.
    return (3.0 * np.clip(m['clear'] - 2.5, -2.5, 1.0)
            + 300.0 * np.clip(stall - STALL_MIN, -0.15, 0.0)
            + 60.0 * np.clip(m['ta'] - TA_MIN, -TA_MIN, 0.0))


def score_length(m, maxw, maxh):
    s = m['plen'] + _quality(m)
    bad = ~m['ok'] | (m['w'] > maxw) | (m['h'] > maxh)
    return np.where(bad, BAD, s)


# What separates "has personality" from "is a big arc". A pure length objective
# converges on a near-circle; these three are the things a circle cannot do.
G_BOTH, G_REV, G_WIG = 1.5, 3.0, 0.8      # rad turned each way, reversals, curvature CoV
MIN_LEN = 80.0                            # the character set's floor on scale length


def score_character(m, maxw, maxh):
    both = np.minimum(m['pos'], m['neg'])
    stall = np.nan_to_num(m['stall'], nan=0.0)
    # staged, so the climb always has a gradient: reach 80", then clear the
    # character gates, then compete on how much personality there is
    gate = (np.minimum(both / G_BOTH, 1) + np.minimum(m['rev'] / G_REV, 1)
            + np.minimum(m['wig'] / G_WIG, 1) + np.minimum(stall / STALL_GATE, 1)
            + (np.minimum(m['ta'] / TA_MIN, 1) if TA_MIN > 0 else 1.0))
    ch = (500.0
          + 14.0 * np.minimum(m['cross'], 6)
          + 8.0 * np.minimum(both, 4.0)
          + 3.0 * np.minimum(m['rev'], 12)
          + 10.0 * np.minimum(m['wig'], 3.0)
          + 6.0 * np.minimum(m['dens'], 4.0)
          + 2.0 * np.minimum(np.maximum(m['ta'] - TA_MIN, 0.0), 15.0)
          + 0.02 * m['plen'])
    # _quality rides EVERY stage, not just the last. Left out of the length stage it
    # was a trapdoor: the climb maximised raw length with no dead-center pressure at
    # all, arrived at 80" sitting on the singularity, and then had to climb back out
    # of a basin it had just spent 400 iterations digging.
    q = _quality(m)
    s = q + np.where(m['plen'] < MIN_LEN, m['plen'] - 1000.0,
                     np.where(gate < 4.999, 100.0 * gate, ch))
    bad = ~m['ok'] | (m['w'] > maxw) | (m['h'] > maxh)
    return np.where(bad, BAD, s)


def gates_met(m):
    return ((m['plen'] >= MIN_LEN) & (np.minimum(m['pos'], m['neg']) >= G_BOTH)
            & (m['rev'] >= G_REV) & (m['wig'] >= G_WIG)
            & (np.nan_to_num(m['stall'], nan=0.0) >= STALL_GATE)
            & (m['ta'] >= TA_MIN) & m['ok'])


# ---------- vectorized hill climb ----------
def climb(G, L, scorer, rng, iters=1200):
    """All candidates refined simultaneously; step shrinks on a schedule."""
    B = G.copy()
    bs = scorer(measure(B, L))
    step = 0.07
    for i in range(iters):
        C = B.copy()
        # perturb 1-3 free params per candidate
        k = rng.integers(1, 4, len(C))
        mask = np.zeros((len(C), NP_), bool)
        for j in range(3):
            ix = rng.choice(FREE_IX, len(C))
            mask[np.arange(len(C)), ix] |= (k > j)
        C += mask * rng.normal(0, step, C.shape) * SPAN
        C = np.clip(C, LO, HI)
        C[:, SIGN_IX] = B[:, SIGN_IX]
        s = scorer(measure(C, L))
        take = s > bs
        B[take], bs[take] = C[take], s[take]
        if i % 200 == 199:
            step *= 0.66
    return B, bs


# ---------- selection ----------
def pick_distinct(G, order, keep, thresh):
    """Greedy diversity in normalized parameter space."""
    out = []
    for i in order:
        gn = (G[i] - LO) / SPAN
        if all(np.linalg.norm(gn - (G[j] - LO) / SPAN) > thresh for j in out):
            out.append(i)
        if len(out) >= keep:
            break
    return out


def pick_varied(G, m, sc, keep, ok):
    """Designs that LOOK different, not variations of one winner.

    Buckets by (self-crossing count, scale-length band) so the set spans shape
    families; best of each bucket first, then fill from the ranked remainder.
    Both passes keep a parameter-distance guard.
    """
    rank = [i for i in np.argsort(-sc) if ok[i]]
    band = np.digitize(m['plen'], MIN_LEN * np.array([1.2, 1.45, 1.8, 2.4]))
    out, seen = [], set()
    # Self-crossing is the thing the owner named first, so fill from the curves
    # that actually loop before letting a merely-wavy one in. Passes:
    # (min crossings, must open a new shape bucket).
    for floor, new_bucket in ((2, True), (1, True), (1, False), (0, True), (0, False)):
        for i in rank:
            if i in out or m['cross'][i] < floor:
                continue
            key = (int(min(m['cross'][i], 5)), int(band[i]))
            if new_bucket and key in seen:
                continue
            gn = (G[i] - LO) / SPAN
            if any(np.linalg.norm(gn - (G[j] - LO) / SPAN) < 0.30 for j in out):
                continue
            seen.add(key); out.append(i)
            if len(out) >= keep:
                return out
    return out


# The owner's current chosen design, for comparison in the report. index.html's
# serpentine preset, converted to radians.
SERPENTINE = dict(rA=12.6151, dA=27.6388, anch=-133.1494, gx=12.9, gy=-6.0, L2=11.3701,
                  L3=7.7705, L4=7.0142, cu=3.5, cv=11.3, s1=-1, ox=6.9036, oy=-17.4189,
                  L5=5.9, L6=14.0, cu2=19.9991, cv2=13.1489, s2=-1)


def from_dict(d):
    g = np.array([d[n] for n in NAMES], float)
    g[2] = math.radians(g[2])
    return g


DENSE = 1301          # finalists are re-measured this finely; analyze_geometry.py's N


def finalize(g, maxw, maxh, tamin=0.0):
    """Re-measure one finalist densely. The 141-sample search length is a ~1%
    underestimate on a curvy path, and a design valid at 141 samples can still
    drop a chunk at the 781 the page draws with. Returns None if it fails dense.

    The transmission angle is re-checked here too, and this is not a formality: a
    dip toward dead center is narrow in the actuator's travel, so a coarse grid
    can step straight over one.
    """
    L = drive_lengths(DENSE)
    m = measure(g[None, :], L)
    if not m['ok'][0] or m['w'][0] > maxw or m['h'][0] > maxh or m['ta'][0] < tamin:
        return None
    _, _, okg = trace(g[None, :], drive_lengths(DENSE, joyce=False))
    r = row(m, 0)
    r['generic_ok'] = bool(okg[0])
    r['gates'] = bool(gates_met(m)[0])
    return r


def to_dict(g):
    d = {n: float(v) for n, v in zip(NAMES, g)}
    d['anch'] = math.degrees(d['anch'])
    d['s1'] = int(round(d['s1'])); d['s2'] = int(round(d['s2']))
    return d


def row(m, i):
    return {k: (float(m[k][i]) if k != 'ok' else bool(m['ok'][i])) for k in m}


def merge(paths, out, keep_long, keep_creative, maxw, maxh):
    """Re-select across several independent runs.

    Each run emits more candidates than it needs; this pools them, re-measures
    every one densely, and applies the same diversity rules over the union. Eight
    seeds in parallel beat one long run because the climb is greedy and gets stuck.
    """
    items, meta = [], None
    for p in paths:
        d = json.load(open(p))
        meta = meta or d.get('meta')
        items += d.get('longest', []) + d.get('creative', [])
    G = np.array([from_dict(it['geo']) for it in items])
    L = drive_lengths(DENSE)
    m = measure(G, L)
    fit = m['ok'] & (m['w'] <= maxw) & (m['h'] <= maxh)
    sL = np.where(fit, score_length(m, maxw, maxh), BAD)
    sC = np.where(fit, score_character(m, maxw, maxh), BAD)
    ixA = pick_distinct(G, np.argsort(-sL), keep_long, 0.45)
    ixB = pick_varied(G, m, sC, keep_creative, gates_met(m) & fit)
    print(f'merged {len(items)} candidates from {len(paths)} runs; '
          f'{int((gates_met(m) & fit).sum())} clear the character gates')
    res = {'meta': meta, 'baseline': {'geo': SERPENTINE,
                                      'metrics': finalize(from_dict(SERPENTINE), 1e9, 1e9)},
           'longest': [], 'creative': []}
    for tag, ix in (('longest', ixA), ('creative', ixB)):
        for i in ix:
            r = finalize(G[i], maxw, maxh, TA_MIN)
            if r is not None:
                res[tag].append({'geo': to_dict(G[i]), 'metrics': r})
    json.dump(res, open(out, 'w'), indent=1)
    report(res)
    print(f'\nwrote {out}')
    return res


def report(out):
    hdr = (f'{"":4}{"len":>7} {"loops":>5} {"rev":>4} {"wig":>5} {"both":>5} '
           f'{"dens":>5}  envelope  clear  stall  {"trans":>5}  gen')
    for tag in ('baseline', 'longest', 'creative'):
        if tag not in out:
            continue
        print(f'\n=== {tag} ===\n{hdr}')
        for i, d in enumerate([out[tag]] if tag == 'baseline' else out[tag]):
            m = d['metrics']
            print(f'  {i+1:>2}.{m["plen"]:7.1f} {m["cross"]:5.0f} {m["rev"]:4.0f} {m["wig"]:5.2f}'
                  f' {min(m["pos"], m["neg"]):5.2f} {m["dens"]:5.2f}  {m["w"]:4.1f}x{m["h"]:<4.1f}'
                  f' {m["clear"]:5.2f}  {m["stall"]:5.3f}  {m["ta"]:5.1f}  '
                  f'{"y" if m["generic_ok"] else "n"}')


def main():
    global TA_MIN, G_BOTH, G_REV, G_WIG, MIN_LEN
    ap = argparse.ArgumentParser()
    ap.add_argument('--merge', nargs='+', help='pool several run outputs and re-select')
    ap.add_argument('--emit', type=int, default=0, help='candidates per set (0 = 5 and 10)')
    ap.add_argument('--trials', type=int, default=20_000_000)
    # Peak RSS is roughly batch * nsamp * 8 bytes * ~25 live arrays: 12k x 261 is
    # about 0.6 GB, and 60k x 261 is over 3 GB. Multiply by however many runs you
    # start in parallel — eight of those is an out-of-memory kill, not a fast search.
    ap.add_argument('--batch', type=int, default=12_000)
    ap.add_argument('--nsamp', type=int, default=261)      # finer than index.html's
    # 141-sample rangeValid, and 260 segments = exactly 2 per degree F so the search
    # can see a stall; finalists are re-checked at DENSE anyway
    ap.add_argument('--maxw', type=float, default=48.0)    # garden-piece envelope,
    ap.add_argument('--maxh', type=float, default=48.0)    # cf. serpentine 40.7x30.8
    ap.add_argument('--tamin', type=float, default=0.0,
                    help='minimum transmission angle at C and D over the whole range, '
                         'in degrees. README recommends 40; Grand Arc manages 33.9 and '
                         'the serpentine 7.7. 0 reproduces the original search.')
    ap.add_argument('--minlen', type=float, default=MIN_LEN,
                    help='scale-length floor for the character set. Buying length at a '
                         'high --tamin costs shape, so lower this to trade one for the '
                         'other; the serpentine is 82 inches and Grand Arc 56.')
    ap.add_argument('--character', type=float, nargs=3, metavar=('BOTH', 'REV', 'WIG'),
                    default=[G_BOTH, G_REV, G_WIG],
                    help='character gates: radians turned each way, curvature reversals, '
                         'curvature CoV. Reachable together with a high --tamin only if '
                         'lowered — a healthy linkage draws a smoother curve.')
    ap.add_argument('--seeds', type=int, default=600)
    ap.add_argument('--iters', type=int, default=1200)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--out', default='designs.json')
    a = ap.parse_args()
    nA, nB = (a.emit, a.emit) if a.emit else (5, 10)
    TA_MIN = a.tamin
    MIN_LEN = a.minlen
    G_BOTH, G_REV, G_WIG = a.character

    if a.merge:
        merge(a.merge, a.out, nA, nB, a.maxw, a.maxh)
        return

    L = drive_lengths(a.nsamp)
    rng = np.random.default_rng(a.seed)
    print(f'driven length {L[0]:.2f}" .. {L[-1]:.2f}"   envelope cap '
          f'{a.maxw:.0f}x{a.maxh:.0f}"   {a.trials:,} trials', flush=True)

    pool, keys = [], []
    done, nfeas = 0, 0
    while done < a.trials:
        n = min(a.batch, a.trials - done)
        G = sample_box(rng, n); done += n
        Qx, Qy, ok, J = trace(G, L, joints=True)
        if not ok.any():
            continue
        G = G[ok]; nfeas += len(G)
        Qx, Qy = Qx[ok], Qy[ok]
        pl = scale_length(Qx, Qy)
        w, h = envelope_of(G, Qx, Qy, {k: (J[k][0][ok], J[k][1][ok]) for k in JKEYS})
        with np.errstate(invalid='ignore'):
            ta = np.nan_to_num(np.nanmin(J['ta'][ok], axis=1))
        # seeds start at half the gate: the climb can lift a design's transmission
        # angle, but not from 0.5 deg to 40 — those live in a different basin.
        good = ((pl > 45.0) & (w <= a.maxw * 1.4) & (h <= a.maxh * 1.4)
                & (ta >= 0.5 * TA_MIN))
        if good.any():
            pool.append(G[good]); keys.append(pl[good])
        if done % (a.batch * 40) < a.batch:
            tot = sum(len(x) for x in keys)
            print(f'  {done:>11,} trials   feasible {nfeas:>8,}   seeds {tot:>6}', flush=True)

    if not pool:
        print('no feasible candidates'); return
    G = np.concatenate(pool); pl = np.concatenate(keys)
    print(f'\nseed pool {len(G)}   raw best {pl.max():.1f}"', flush=True)

    order = np.argsort(-pl)
    seedsA = G[order[:a.seeds]]
    # character seeds come from a WIDE slice, not just the longest — the longest
    # candidates are all near-circles and climb straight back to being circles
    wide = rng.permutation(len(order))[:a.seeds]
    seedsB = G[order[np.sort(wide)]] if len(order) > a.seeds else G

    print('\nclimbing for LENGTH...', flush=True)
    BA, sA = climb(seedsA, L, lambda m: score_length(m, a.maxw, a.maxh), rng, a.iters)
    mA = measure(BA, L)
    ixA = pick_distinct(BA, np.argsort(-sA), nA, 0.45)

    print('climbing for CHARACTER...', flush=True)
    BB, sB = climb(seedsB, L, lambda m: score_character(m, a.maxw, a.maxh), rng, a.iters)
    mB = measure(BB, L)
    passing = gates_met(mB) & (mB['w'] <= a.maxw) & (mB['h'] <= a.maxh)
    print(f'  {int(passing.sum())}/{len(BB)} cleared the character gates', flush=True)
    ixB = pick_varied(BB, mB, sB, nB, passing)

    out = {'meta': {'actuator': 'joyce QS11940, aClamp 23.23, ext 0-16',
                    'driven_len': [float(L[0]), float(L[-1])],
                    'envelope_cap': [a.maxw, a.maxh], 'trials': a.trials,
                    'gates': {'plen': MIN_LEN, 'bothways': G_BOTH, 'rev': G_REV,
                              'wiggle': G_WIG, 'trans_angle': a.tamin}},
           'baseline': {'geo': SERPENTINE,
                        'metrics': finalize(from_dict(SERPENTINE), 1e9, 1e9)},
           'longest': [], 'creative': []}
    for tag, B, ix in (('longest', BA, ixA), ('creative', BB, ixB)):
        for i in ix:
            r = finalize(B[i], a.maxw, a.maxh, a.tamin)
            if r is None:
                print(f'  dropped a {tag} finalist: fails at dense sampling', flush=True)
                continue
            out[tag].append({'geo': to_dict(B[i]), 'metrics': r})

    with open(a.out, 'w') as f:
        json.dump(out, f, indent=1)
    report(out)
    print(f'\nwrote {a.out}')


def _selfcheck():
    L = drive_lengths(141)
    assert abs(L[0] - math.hypot(23.23, 2.378)) < 1e-9
    assert abs(L[-1] - math.hypot(39.23, 2.378)) < 1e-9
    t = np.linspace(0, math.pi, 200)[None, :]
    x, y = 5 * np.cos(t), 5 * np.sin(t)
    assert abs(scale_length(x, y)[0] - 5 * math.pi) < 0.01
    assert crossings(x, y)[0] == 0
    pos, neg, rev, wig = turn_stats(x, y)
    assert rev[0] == 0 and neg[0] < 1e-9
    t = np.linspace(0, 2 * math.pi, 400)[None, :]
    assert crossings(np.sin(2 * t), np.sin(t), step=2)[0] == 1, 'figure eight'
    # two disjoint lobes that touch nowhere -> no crossings; a spiral -> none either
    t = np.linspace(0, 6 * math.pi, 600)[None, :]
    assert crossings(t * np.cos(t) / 10, t * np.sin(t) / 10)[0] == 0, 'spiral'
    # a circular arc must score zero wiggle and turn only one way — this is the
    # gate that stops the search handing back five big arcs
    t = np.linspace(0, 1.8 * math.pi, 300)[None, :]
    pos, neg, rev, wig = turn_stats(9 * np.cos(t), 9 * np.sin(t))
    assert wig[0] < 1e-6 and neg[0] < 1e-9 and rev[0] == 0, (wig[0], neg[0], rev[0])
    # a sine wave bends both ways, reverses repeatedly, and has varying curvature
    t = np.linspace(0, 6 * math.pi, 300)[None, :]
    pos, neg, rev, wig = turn_stats(t, 3 * np.sin(t))
    assert min(pos[0], neg[0]) > 3 and rev[0] >= 5 and wig[0] > 0.5, (pos[0], neg[0], rev[0], wig[0])
    # mount clearance. All four mounts sit at the origin except ACT, which dA/anch
    # put at (0,3); the sample grid includes x=0, so the nearest mount is exact.
    G = np.zeros((1, NP_)); G[0, 1] = 3.0; G[0, 2] = math.pi / 2
    Qx = np.linspace(-5, 5, 51)[None, :]
    assert abs(mount_clear(G, Qx, np.zeros((1, 51)), step=1)[0]) < 1e-12   # O2 on the path
    assert abs(mount_clear(G, Qx, np.full((1, 51), 4.0), step=1)[0] - 1.0) < 1e-12  # ACT 1" off
    # transmission angle: C at the origin with B up the y axis and O4 out the x axis
    # is the square 90 deg case; swinging O4 round to +y and to -y are both dead
    # center, because 180 deg is as collinear as 0.
    z = np.zeros((1, 1)); one = np.ones((1, 1))
    ang = lambda ox, oy: trans_angles(z, one, z, z, np.array([[ox]], float),
                                      np.array([[oy]], float), one, one)[0, 0]
    assert abs(ang(1, 0) - 90) < 1e-9, ang(1, 0)
    assert abs(ang(0, -1)) < 1e-6, ang(0, -1)
    assert abs(ang(0, 1)) < 1e-6, ang(0, 1)
    assert abs(ang(math.cos(math.radians(30)), -math.sin(math.radians(30))) - 60) < 1e-9
    print('selfcheck ok')


if __name__ == '__main__':
    if '--selfcheck' in sys.argv:
        _selfcheck()
    else:
        main()
