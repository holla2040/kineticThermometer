#!/usr/bin/env python3
"""Constrained random search for the kinetic-thermometer linkage geometry.

Finds two-stage four-bar geometries driven by a 24-42" linear actuator
(18" stroke) such that:
  - the chain assembles across the entire stroke (with margin),
  - every temperature step produces visible indicator motion,
  - the coupler curve genuinely curves (serpentine: turns both ways),
  - ALL four fixed mounts sit on one side of the scale curve:
      * every mount keeps >= 2.5" clearance from the curve, and
      * no straight segment between two mounts crosses the curve.

This reproduces the search that produced the presets baked into index.html.
Parameter tuple order:
  (rA, dA, anch, gx, gy, L2, L3, L4, cu, cv, s1, ox, oy, L5, L6, cu2, cv2, s2)
Angles in radians here; index.html stores anch in degrees.
"""
import math, random

LMIN, STROKE = 24.0, 18.0
LMAX = LMIN + STROKE


def circ_int(p0, r0, p1, r1, sign, margin=0.5):
    dx, dy = p1[0]-p0[0], p1[1]-p0[1]
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return None
    if d > r0+r1-margin or d < abs(r0-r1)+margin:
        return None
    a = (r0*r0 - r1*r1 + d*d) / (2*d)
    h2 = r0*r0 - a*a
    if h2 < 0:
        return None
    h = math.sqrt(h2)
    mx, my = p0[0]+a*dx/d, p0[1]+a*dy/d
    return (mx + sign*h*(-dy/d), my + sign*h*(dx/d))


def make_path(g, samples=61):
    (rA, dA, anch, gx, gy, L2, L3, L4, cu, cv, s1,
     ox, oy, L5, L6, cu2, cv2, s2) = g
    if dA+rA < LMAX+1.5 or abs(dA-rA) > LMIN-1.5:
        return None                      # actuator triangle can't close
    O4, O6 = (gx, gy), (ox, oy)
    pts = []
    for i in range(samples):
        l = LMIN + STROKE*i/(samples-1)
        c = (dA*dA + rA*rA - l*l) / (2*dA*rA)
        if abs(c) > 0.999:
            return None
        th = anch + math.acos(c)
        B = (L2*math.cos(th), L2*math.sin(th))
        C = circ_int(B, L3, O4, L4, s1)
        if C is None:
            return None
        ux, uy = (C[0]-B[0])/L3, (C[1]-B[1])/L3
        P = (B[0]+cu*ux-cv*uy, B[1]+cu*uy+cv*ux)
        D = circ_int(P, L5, O6, L6, s2)
        if D is None:
            return None
        dl = math.hypot(D[0]-P[0], D[1]-P[1])
        vx, vy = (D[0]-P[0])/dl, (D[1]-P[1])/dl
        pts.append((P[0]+cu2*vx-cv2*vy, P[1]+cu2*vy+cv2*vx))
    return pts


def seg_int(a, b, c, d):
    def ccw(p, q, r):
        return (r[1]-p[1])*(q[0]-p[0]) > (q[1]-p[1])*(r[0]-p[0])
    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def pt_seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx-ax, by-ay
    L2s = dx*dx + dy*dy
    if L2s < 1e-12:
        return math.hypot(px-ax, py-ay)
    t = max(0, min(1, ((px-ax)*dx + (py-ay)*dy) / L2s))
    return math.hypot(px-ax-t*dx, py-ay-t*dy)


def grounds_of(g):
    rA, dA, anch = g[0], g[1], g[2]
    return [(dA*math.cos(anch), dA*math.sin(anch)), (0.0, 0.0),
            (g[3], g[4]), (g[11], g[12])]


def mounts_same_side(g, pts, clearance=2.5, max_rg=28.0):
    G = grounds_of(g)
    cx = sum(p[0] for p in G)/4; cy = sum(p[1] for p in G)/4
    if max(math.hypot(p[0]-cx, p[1]-cy) for p in G) > max_rg:
        return False
    for m in G:
        for i in range(1, len(pts)):
            if pt_seg_dist(m, pts[i-1], pts[i]) < clearance:
                return False
    for i in range(4):
        for j in range(i+1, 4):
            for k in range(1, len(pts)):
                if seg_int(G[i], G[j], pts[k-1], pts[k]):
                    return False
    return True


def metrics(pts):
    segs = [math.hypot(pts[i][0]-pts[i-1][0], pts[i][1]-pts[i-1][1])
            for i in range(1, len(pts))]
    if min(segs) < 0.15 or max(segs) > 2.2:
        return None
    ratio = max(segs)/min(segs)
    if ratio > 7:
        return None
    plen = sum(segs)
    pos = neg = 0.0
    for i in range(1, len(pts)-1):
        a1 = math.atan2(pts[i][1]-pts[i-1][1], pts[i][0]-pts[i-1][0])
        a2 = math.atan2(pts[i+1][1]-pts[i][1], pts[i+1][0]-pts[i][0])
        d = (a2-a1+math.pi) % (2*math.pi) - math.pi
        if d > 0:
            pos += d
        else:
            neg -= d
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    bbox = math.hypot(max(xs)-min(xs), max(ys)-min(ys))
    endd = math.hypot(pts[-1][0]-pts[0][0], pts[-1][1]-pts[0][1])
    return dict(plen=plen, pos=pos, neg=neg, bbox=bbox, ratio=ratio, endd=endd)


def rand_g(rng):
    return (rng.uniform(10, 22), rng.uniform(24, 40),
            rng.uniform(-math.pi, math.pi),
            rng.uniform(-24, 28), rng.uniform(-24, 24),
            rng.uniform(6, 16), rng.uniform(10, 26), rng.uniform(8, 22),
            rng.uniform(4, 20), rng.uniform(-12, 12),
            rng.choice([-1, 1]),
            rng.uniform(-28, 32), rng.uniform(-28, 26),
            rng.uniform(8, 24), rng.uniform(8, 20),
            rng.uniform(4, 20), rng.uniform(-14, 14),
            rng.choice([-1, 1]))


def serpentine_ok(m):
    return (m['plen'] >= 22 and m['pos'] >= 0.8 and m['neg'] >= 0.8
            and m['endd'] >= 0.4*m['bbox'])


def serpentine_score(m):
    return m['plen'] + 10*min(m['pos'], m['neg']) + 0.5*m['bbox']


if __name__ == '__main__':
    rng = random.Random(3)
    best, cnt = None, 0
    for trial in range(600000):
        g = rand_g(rng)
        pts = make_path(g)
        if pts is None:
            continue
        m = metrics(pts)
        if m is None or not serpentine_ok(m):
            continue
        if not mounts_same_side(g, pts):
            continue
        cnt += 1
        s = serpentine_score(m)
        if best is None or s > best[0]:
            best = (s, g, m)
    print('valid candidates:', cnt)
    if best:
        s, g, m = best
        names = 'rA dA anch gx gy L2 L3 L4 cu cv s1 ox oy L5 L6 cu2 cv2 s2'.split()
        out = {n: (round(v, 1) if isinstance(v, float) else v)
               for n, v in zip(names, g)}
        out['anch'] = round(math.degrees(g[2]), 1)
        print('score %.1f  len %.1f  ratio %.1f' % (s, m['plen'], m['ratio']))
        print(out)
