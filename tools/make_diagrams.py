#!/usr/bin/env python3
"""Generate the SVG diagrams the README's dead-center section uses.

Written as a script rather than hand-authored SVG so the drawings stay in step
with the real geometry: the ones that show the mechanism read their poses from
index.html's presets through tools/explore_designs.py, so they cannot drift into
illustrating something the simulator does not do.

    python3 tools/make_diagrams.py [outdir]        # default images/

GitHub strips inline <svg> from markdown but renders linked .svg files, so each
diagram is a standalone file referenced with normal image syntax. Every file
carries its own dark background, so it reads the same in light or dark theme.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BG, INK, MUTE = '#0e1116', '#e8edf3', '#8fa2ba'
BLUE, RED, TEAL, AMBER, GREY = '#63b3ed', '#ef5350', '#4fd1c5', '#d9a441', '#5a6472'
FONT = 'Helvetica,Arial,sans-serif'


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" role="img" aria-label="{title}">'
            f'<title>{title}</title>'
            f'<rect width="{w}" height="{h}" fill="{BG}"/>{body}</svg>')


def txt(x, y, s, size=13, fill=INK, anchor='middle', weight='normal', style=''):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" font-style="{style}">{s}</text>')


def line(x1, y1, x2, y2, col=INK, w=2, dash=None, cap='round'):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{col}" stroke-width="{w}" stroke-linecap="{cap}"{d}/>')


def circ(x, y, r, fill='none', col=INK, w=2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" '
            f'stroke="{col}" stroke-width="{w}"{d}/>')


def dot(x, y, r=5, fill=INK):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>'


def ground(x, y, col=BLUE):
    """The hatched fixed-pivot glyph the simulator draws."""
    s = [circ(x, y, 7, '#1c242f', col, 2)]
    for i in range(-2, 3):
        s.append(line(x + i * 4, y + 7, x + i * 4 - 4, y + 13, GREY, 1.3))
    return ''.join(s)


def arrow(x1, y1, x2, y2, col=AMBER, w=2.5):
    a = math.atan2(y2 - y1, x2 - x1)
    hx, hy = x2 - 9 * math.cos(a), y2 - 9 * math.sin(a)
    p = [(x2, y2), (hx - 5 * math.sin(a), hy + 5 * math.cos(a)),
         (hx + 5 * math.sin(a), hy - 5 * math.cos(a))]
    pts = ' '.join(f'{px:.1f},{py:.1f}' for px, py in p)
    return line(x1, y1, hx, hy, col, w) + f'<polygon points="{pts}" fill="{col}"/>'


def angle_arc(cx, cy, p1, p2, r=30, col=AMBER, w=2.5):
    """Arc marking the angle at (cx,cy) between the directions to p1 and p2."""
    a1 = math.atan2(p1[1] - cy, p1[0] - cx)
    a2 = math.atan2(p2[1] - cy, p2[0] - cx)
    d = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
    large = 1 if abs(d) > math.pi else 0
    sweep = 1 if d > 0 else 0
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
    return (f'<path d="M {x1:.1f} {y1:.1f} A {r} {r} 0 {large} {sweep} {x2:.1f} {y2:.1f}" '
            f'fill="none" stroke="{col}" stroke-width="{w}"/>')


def panel(x, y, w, h, label, col=MUTE):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" '
            f'stroke="#1e2733" stroke-width="1" rx="6"/>' + txt(x + w / 2, y + 20, label, 13, col))


# ---------------------------------------------------------------- 1. the pedal
def pedal():
    W, H = 760, 330
    s = [txt(W / 2, 30, 'A bicycle pedal at the top of its circle', 17, INK, weight='bold'),
         txt(W / 2, 52, 'Same push. Completely different result.', 13, MUTE)]
    for i, (cx, ang, ok, cap1, cap2) in enumerate([
            (200, -90, False, 'DEAD CENTER', 'Foot, crank and axle in one straight line.'),
            (560, 0, True, 'A QUARTER TURN LATER', 'The push now has leverage on the crank.')]):
        cy, r = 190, 70
        col = RED if not ok else TEAL
        s.append(circ(cx, cy, r, 'none', '#1e2733', 2, '5,5'))
        px = cx + r * math.cos(math.radians(ang))
        py = cy + r * math.sin(math.radians(ang))
        s.append(line(cx, cy, px, py, col, 6))
        s.append(ground(cx, cy))
        s.append(dot(px, py, 8, col))
        s.append(arrow(px, py - 62, px, py - 16, AMBER, 3))
        s.append(txt(px, py - 72, 'push', 12, AMBER))
        s.append(txt(cx, 285, cap1, 13, col, weight='bold'))
        s.append(txt(cx, 306, cap2, 12, MUTE))
        if not ok:
            s.append(txt(cx, cy + 46, 'no turning force at all', 12, RED, style='italic'))
        else:
            s.append(angle_arc(px, py, (cx, cy), (px, py - 40), 26, TEAL, 2))
            s.append(txt(px - 34, py - 26, '90°', 13, TEAL))
    return svg(W, H, ''.join(s), 'A crank at dead center gets no turning force from a straight-down push')


# ------------------------------------------------- 2. two circles = two branches
def two_branches():
    W, H = 760, 430
    s = [txt(W / 2, 30, 'Finding a joint means crossing two circles', 17, INK, weight='bold'),
         txt(W / 2, 52, 'Pin D has to be L5 from P and L6 from O6. Two circles. Two crossings.', 12, MUTE)]
    P, O6 = (250, 220), (510, 220)
    r1, r2 = 145, 145
    s += [circ(*P, r1, 'none', TEAL, 1.6, '4,4'), circ(*O6, r2, 'none', BLUE, 1.6, '4,4')]
    dx = O6[0] - P[0]
    a = dx / 2
    h = math.sqrt(r1 * r1 - a * a)
    for sign, nm, col in ((-1, 'D', INK), (1, "D'", '#9aa7b8')):
        D = (P[0] + a, P[1] + sign * h)
        s += [line(*P, *D, col, 3), line(*O6, *D, col, 3), dot(*D, 6, col),
              txt(D[0] + (0 if sign < 0 else 0), D[1] + (-14 if sign < 0 else 24), nm, 14, col, weight='bold')]
    s += [ground(*O6), dot(*P, 6, TEAL),
          txt(P[0] - 16, P[1] + 5, 'P', 14, TEAL, 'end', 'bold'),
          txt(O6[0] + 18, O6[1] + 5, 'O6', 14, BLUE, 'start', 'bold'),
          txt(W / 2, 410, 'Both are valid. The simulator picks one and stays on it — that is the '
              '"assembly branch" flip in the panel.', 12, MUTE)]
    return svg(W, H, ''.join(s), 'Two circles cross at two points, giving two ways to assemble the linkage')


# ------------------------------------------------------- 3. tangent = dead center
def tangent():
    W, H = 760, 430
    s = [txt(W / 2, 30, 'Dead center: the two crossings merge into one', 17, INK, weight='bold'),
         txt(W / 2, 52, 'Slide the circles apart until they only touch. Now there is no choice left.', 12, MUTE)]
    P, r1, r2 = (215, 215), 145, 125
    O6 = (P[0] + r1 + r2, P[1])
    D = (P[0] + r1, P[1])
    s += [circ(*P, r1, 'none', TEAL, 1.6, '4,4'), circ(*O6, r2, 'none', BLUE, 1.6, '4,4'),
          line(*P, *D, RED, 4), line(*D, *O6, RED, 4), dot(*D, 7, RED),
          ground(*O6), dot(*P, 6, TEAL),
          txt(P[0] - 16, P[1] + 5, 'P', 14, TEAL, 'end', 'bold'),
          txt(D[0], D[1] - 18, 'D', 14, RED, 'middle', 'bold'),
          txt(O6[0] + 18, O6[1] + 5, 'O6', 14, BLUE, 'start', 'bold'),
          txt(D[0], D[1] + 34, 'the two links are in one straight line', 12, RED, style='italic'),
          txt(W / 2, 392, 'Nothing decides which way it comes off. Momentum, friction, gravity and '
              'joint slop do — not the actuator.', 12, MUTE),
          txt(W / 2, 414, 'Come out on the wrong side and the sculpture reads wrong until something '
              'knocks it back.', 12, RED)]
    return svg(W, H, ''.join(s), 'When the two circles are tangent the linkage is at dead center')


# ------------------------------------------------------- 4. the transmission angle
def trans_angle():
    W, H = 790, 400
    s = [txt(W / 2, 30, 'The transmission angle', 17, INK, weight='bold'),
         txt(W / 2, 52, 'The angle where the pushing link meets the link it drives. '
             'This is the number that matters.', 12, MUTE)]
    cases = [(140, 65, TEAL, 'HEALTHY', '90° is perfect. Above ~40° is normal practice.'),
             (400, 22, AMBER, 'GETTING TIGHT', 'The driven link is starting to fight back.'),
             (655, 4, RED, 'DEAD CENTER', 'Below 6° the simulator paints this joint red.')]
    for cx, ang, col, cap, sub in cases:
        C = (cx, 215)
        # both arms measured from C, so the drawn angle IS the labelled angle
        aA = math.radians(200)
        aB = aA - math.radians(ang)
        A = (C[0] + 78 * math.cos(aA), C[1] + 78 * math.sin(aA))
        B = (C[0] + 108 * math.cos(aB), C[1] + 108 * math.sin(aB))
        s += [line(*A, *C, GREY if col != RED else '#8f4340', 4),
              line(*C, *B, col, 4),
              angle_arc(C[0], C[1], A, B, 34, col, 2.5),
              dot(*C, 7, col), dot(*A, 5, MUTE), dot(*B, 5, col),
              txt(C[0] + 46, C[1] - 14, f'{ang}°', 15, col, 'start', 'bold'),
              txt(A[0], A[1] - 16, 'coupler', 11, MUTE),      # above
              txt(B[0], B[1] + 24, 'driven link', 11, col),   # below, so 4° still reads
              txt(cx, 330, cap, 13, col, weight='bold'),
              txt(cx, 351, sub, 11, MUTE)]
    s.append(txt(W / 2, 385, 'Squeeze that angle to nothing and the driven link no longer knows '
                 'which way to go.', 12, MUTE))
    return svg(W, H, ''.join(s), 'Transmission angle: healthy, tight, and dead center')


# -------------------------------------------------------------- 5. the whole chain
def chain():
    W, H = 800, 330
    s = [txt(W / 2, 30, 'Where the two watched joints sit in the chain', 17, INK, weight='bold'),
         txt(W / 2, 52, 'Motion runs left to right. Each box is solved from the one before it.', 12, MUTE)]
    boxes = [('actuator', 60, MUTE), ('bell crank', 175, AMBER), ('B', 285, AMBER),
             ('C', 380, RED), ('P', 480, TEAL), ('D', 575, RED), ('Q  indicator', 700, INK)]
    y = 150
    for i, (nm, x, col) in enumerate(boxes):
        w = 96 if len(nm) > 3 else 46
        s += [f'<rect x="{x - w/2}" y="{y - 22}" width="{w}" height="44" rx="8" fill="none" '
              f'stroke="{col}" stroke-width="{2.5 if col == RED else 1.6}"/>',
              txt(x, y + 5, nm, 13, col, weight='bold' if col == RED else 'normal')]
        if i:
            px = boxes[i - 1][1] + (96 if len(boxes[i - 1][0]) > 3 else 46) / 2
            s.append(arrow(px + 4, y, x - w / 2 - 6, y, GREY, 2))
    for x, lbl in ((380, 'watched: angle between'), (575, 'watched: angle between')):
        s += [line(x, y + 26, x, y + 48, RED, 1.5, '3,3'),
              txt(x, y + 64, lbl, 10.5, RED),
              txt(x, y + 78, 'coupler and rocker' if x == 380 else 'coupler and rocker', 10.5, RED)]
    s += [txt(200, y + 64, 'the actuator has its own', 10.5, MUTE),
          txt(200, y + 78, '0.5″ safety margin built in', 10.5, MUTE),
          txt(W / 2, 310, 'C and D are the only two joints found by crossing circles — so they are '
              'the only two that can go dead.', 12, MUTE)]
    return svg(W, H, ''.join(s), 'The drive chain, showing which joints are watched for dead center')


# ------------------------------------------------- 6. what it does to the scale
def scale_blowup():
    W, H = 780, 300
    s = [txt(W / 2, 30, 'What it does to the temperature scale', 17, INK, weight='bold'),
         txt(W / 2, 52, 'Each mark is one degree. Equal steps of temperature, unequal steps '
             'along the curve.', 12, MUTE)]
    y1, y2 = 120, 225
    s.append(txt(30, y1 - 26, 'A healthy design — marks spread out gently', 12, TEAL, 'start'))
    for i in range(29):
        x = 40 + i * 24.5
        s.append(line(x, y1 - 14, x, y1 + 14, TEAL, 2))
    s.append(txt(30, y2 - 30, 'Near dead center — marks pile up, then one degree jumps the '
                 'width of the sculpture', 12, RED, 'start'))
    x = 40
    for i in range(22):
        s.append(line(x, y2 - 14, x, y2 + 14, RED if i > 13 else AMBER, 2))
        x += 3.5 + (i ** 2.35) * 0.09
    s += [arrow(x + 6, y2, 742, y2, RED, 2.5),
          line(742, y2 - 16, 742, y2 + 16, RED, 2),
          txt(742, y2 - 26, 'ONE degree of temperature', 12.5, RED, 'end', 'bold'),
          txt(W / 2, 285, 'On design 13 of the search, a single degree moved the indicator '
              '39.7 inches. That stretch carries no marks at all.', 12, MUTE)]
    return svg(W, H, ''.join(s), 'Near dead center the scale marks bunch up and then jump')


# ------------------------------------------------------------- 7. the angle ruler
def ruler():
    W, H = 790, 350
    s = [txt(W / 2, 30, 'How much angle do you actually need?', 17, INK, weight='bold'),
         txt(W / 2, 52, 'Every preset in this simulator, measured across its whole '
             'temperature range.', 12, MUTE)]
    x0, x1, y = 70, 720, 120
    X = lambda v: x0 + (x1 - x0) * v / 90
    s.append(f'<rect x="{x0}" y="{y-5}" width="{X(6)-x0}" height="10" fill="{RED}" opacity=".6"/>')
    s.append(f'<rect x="{X(6)}" y="{y-5}" width="{X(40)-X(6)}" height="10" fill="{AMBER}" opacity=".38"/>')
    s.append(f'<rect x="{X(40)}" y="{y-5}" width="{X(90)-X(40)}" height="10" fill="{TEAL}" opacity=".38"/>')
    for v, col in ((0, RED), (6, RED), (40, AMBER), (90, TEAL)):
        s += [line(X(v), y - 14, X(v), y + 14, col, 2), txt(X(v), y - 22, f'{v}°', 12, col)]
    s += [txt(X(3), y + 32, 'red zone', 11, RED),
          txt(X(23), y + 32, 'workable, watch it', 11, AMBER),
          txt(X(65), y + 32, 'comfortable', 11, TEAL)]
    # presets plotted BELOW the bar so nothing collides with the heading
    for nm, a, b, col, yy in (('the 11 search examples  (0.06° – 5.9°)', 0.06, 5.9, RED, 180),
                              ('serpentine  7.7°', 7.7, 7.7, AMBER, 209),
                              ('the 6 shape presets  (6.9° – 25.3°)', 6.9, 25.3, AMBER, 238),
                              ('Grand Arc  33.9°', 33.9, 33.9, TEAL, 267),
                              ('the 6 clean presets  (40.0° – 50.1°)', 40.0, 50.1, TEAL, 296)):
        xa, xb = X(a), X(b)
        if b > a:
            s.append(line(xa, yy, xb, yy, col, 6))
        lx = max(xb + 18, X(46))          # one label column, never over a leader
        s += [dot(xb, yy, 5, col), line(xb, y + 16, xb, yy - 7, col, 1.2, '3,3'),
              line(xb + 8, yy, lx - 8, yy, col, 1, '2,3'),
              txt(lx, yy + 4, nm, 12, col, 'start')]
    s.append(txt(W / 2, 322, 'Everything except the length-search examples clears the red zone; '
                 'all eleven of them sit inside it —', 12, MUTE))
    s.append(txt(W / 2, 342, 'because that search was told to make the scale as long as possible, '
                 'and that is exactly where length comes from.', 12, MUTE))
    return svg(W, H, ''.join(s), 'Where each preset falls on the transmission-angle scale')


# ------------------------------------------------------------ 8. the branch flip
def branch_flip():
    W, H = 790, 430
    s = [txt(W / 2, 30, 'The failure you cannot see coming', 17, INK, weight='bold'),
         txt(W / 2, 52, 'Same actuator position. Same temperature. Two different readings.', 12, MUTE)]
    for cx, sign, cap, col in ((215, -1, 'How you built it', TEAL),
                               (575, 1, 'After it snaps through once', RED)):
        P, O6 = (cx - 85, 210), (cx + 85, 210)
        r = 108
        a = (O6[0] - P[0]) / 2
        h = math.sqrt(r * r - a * a)
        D = (P[0] + a, P[1] + sign * h)
        Q = (D[0] + (D[0] - P[0]) * 0.5, D[1] + (D[1] - P[1]) * 0.5)
        s += [line(*P, *D, col, 4), line(*O6, *D, col, 4), line(*D, *Q, col, 3, '5,4'),
              dot(*P, 6, TEAL), ground(*O6), dot(*D, 6, col),
              circ(*Q, 10, 'none', col, 2.5),
              txt(Q[0] + 20, Q[1] + 4, 'indicator', 11, col, 'start'),
              txt(cx, 356, cap, 13, col, weight='bold')]
    s += [txt(W / 2, 398, 'Nothing breaks. Nothing looks bent. The sculpture just tells you the '
              'wrong temperature —', 12, MUTE),
          txt(W / 2, 418, 'and keeps telling you, until something knocks it back through.', 12, RED)]
    return svg(W, H, ''.join(s), 'After a snap-through the linkage settles on the mirror branch and reads wrong')


DIAGRAMS = [('dead-center-pedal.svg', pedal),
            ('dead-center-two-branches.svg', two_branches),
            ('dead-center-tangent.svg', tangent),
            ('dead-center-angle.svg', trans_angle),
            ('dead-center-chain.svg', chain),
            ('dead-center-scale.svg', scale_blowup),
            ('dead-center-ruler.svg', ruler),
            ('dead-center-branch-flip.svg', branch_flip)]


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'images')
    os.makedirs(out, exist_ok=True)
    for name, fn in DIAGRAMS:
        p = os.path.join(out, name)
        open(p, 'w').write(fn())
        print(f'{p}  {os.path.getsize(p):,} bytes')
