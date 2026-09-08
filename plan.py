#!/usr/bin/env python3
"""Backyard plan drafted from two hand sketches. Model units: metres, origin top-left, y down.
Outputs SVG (1 user unit = 1 cm, page at 1:100) and DXF (metres, y up)."""
import math, os
import ezdxf

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

W = 22.8                   # lot: top (east) width, tape-measured (~22.8)
R = W - 21.6               # shift for features anchored to the south side, drawn originally on a 21.6 m lot
LEFT_H = 10.2              # left (north) side, tape-measured 2026-09-07
DECK_OUT = 0.53            # deck outer edge stands this far east of the house-left wall (tape, photo 28)
SLAB_OUT = 0.98            # existing concrete strip along the house-left wall (tape, photo 28)
DECK_W = 5.8               # deck, house wall to outer edge (tape). 3.2 m of it is outside the roof line
DECK_D = 5.7               # deck depth, tape-measured
DECK_X0 = 7.8              # north fence to house-left wall, tape-measured
HOUSE_R_W = 6.5            # house front right of the deck, tape-measured
DECK_X1 = DECK_X0 + DECK_W               # 13.6
ROOF_EDGE_X = DECK_X1 - 3.2              # 10.4, 3.2 m of deck is outside the roof line
ENTRANCE_W = W - DECK_X1 - HOUSE_R_W     # 2.7 derived (tape said 3.2; drone photo reads ~2.6)
DECK_Y0 = LEFT_H - DECK_OUT             # 9.67, deck outer edge
H = DECK_Y0 + DECK_D                    # 15.37 = house-right wall; the sketch's 15 m right side was never taped
HOUSE_R_X1 = DECK_X1 + HOUSE_R_W
SEAT_W = 0.4               # seat wall width (40-50 cm high, sit-on)
EDGE_W = 0.15              # black paver edging, flush with the paving
FLUSH_X = 9.2              # seat wall ends at tree E (its own circular wall); black edging continues from there

# ---------- geometry helpers ----------
def fillet_path(pts, radii, seg=0.15):
    """pts: corner points; radii[i] radius at interior corner i (0 for ends). Returns dense polyline."""
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        r = radii[i]
        if r <= 0:
            out.append(p1); continue
        v1 = (p0[0] - p1[0], p0[1] - p1[1]); v2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1 = math.hypot(*v1); l2 = math.hypot(*v2)
        u1 = (v1[0] / l1, v1[1] / l1); u2 = (v2[0] / l2, v2[1] / l2)
        ang = math.acos(max(-1, min(1, u1[0] * u2[0] + u1[1] * u2[1])))
        t = r / math.tan(ang / 2)
        a = (p1[0] + u1[0] * t, p1[1] + u1[1] * t)
        b = (p1[0] + u2[0] * t, p1[1] + u2[1] * t)
        bis = (u1[0] + u2[0], u1[1] + u2[1]); lb = math.hypot(*bis)
        d = r / math.sin(ang / 2)
        c = (p1[0] + bis[0] / lb * d, p1[1] + bis[1] / lb * d)
        a0 = math.atan2(a[1] - c[1], a[0] - c[0]); a1 = math.atan2(b[1] - c[1], b[0] - c[0])
        da = a1 - a0
        while da > math.pi: da -= 2 * math.pi
        while da < -math.pi: da += 2 * math.pi
        n = max(2, int(abs(da) * r / seg))
        for k in range(n + 1):
            th = a0 + da * k / n
            out.append((c[0] + r * math.cos(th), c[1] + r * math.sin(th)))
    out.append(pts[-1])
    return out

def offset(path, d):
    """Offset a dense polyline by d to the right of travel (interior for our clockwise wall)."""
    res = []
    n = len(path)
    for i, p in enumerate(path):
        p0 = path[max(0, i - 1)]; p1 = path[min(n - 1, i + 1)]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]; l = math.hypot(dx, dy) or 1
        nx, ny = -dy / l, dx / l
        res.append((p[0] + nx * d, p[1] + ny * d))
    return res

def spline(pts, seg=0.12):
    """Catmull-Rom through pts, densified to about seg spacing."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(2, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / seg))
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out

def circle_pts(c, r, n=48):
    return [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]

# ---------- design geometry ----------
# seat wall: traced from the owner's red line. Runs east of the big fence tree, past F on its west side,
# then along the east edge to tree E, which gets its own circular seat wall like F.
# seat wall: traced from the owner's red line (S-curve up the west side, shallow wave along the east side),
# ending tangentially on E's ring at its north-west point. Ring centreline radius = 0.5 + SEAT_W/2 = 0.7.
E_C = (9.2, 2.0); RC = 0.5 + SEAT_W / 2
tp = (E_C[0] - RC * math.cos(math.pi / 4), E_C[1] - RC * math.sin(math.pi / 4))   # (8.7, 1.5), tangent direction (1, -1)
SEAT_CTRL = [(2.0, LEFT_H - SLAB_OUT), (2.75, 7.4), (2.6, 5.5), (2.4, 4.2), (2.8, 3.3), (3.6, 2.8), (4.5, 2.85),
             (5.6, 3.2), (6.8, 3.1), (7.6, 2.6)]
# override from the 3D viewer's edit mode: seat_ctrl.json holds the dragged control points
if os.path.exists(os.path.join(OUT, "seat_ctrl.json")):
    import json as _json
    SEAT_CTRL = [tuple(pt) for pt in _json.load(open(os.path.join(OUT, "seat_ctrl.json")))["pts"]]
seat_pts = spline(SEAT_CTRL + [(tp[0] - 0.35, tp[1] + 0.35), tp])
# black paver edging: 1.5 m off the east fence, 1.2 m off the south fence (to its outer face)
EDGE_E = 1.5 + EDGE_W / 2; EDGE_S = W - 1.2 - EDGE_W / 2
ex0 = E_C[0] + math.sqrt(max(0.0, (0.5 + SEAT_W) ** 2 - (EDGE_E - E_C[1]) ** 2))   # where the edge leaves the ring's outer face
edge_pts = fillet_path([(ex0, EDGE_E), (EDGE_S, EDGE_E), (EDGE_S, 15.2), (W - 0.2, 15.2)], [0, 2.2, 1.0, 0])
wall_c = seat_pts + edge_pts   # seat part ends on the ring's NW; edge part leaves the ring's east side
wall_out = offset(wall_c, -SEAT_W / 2)
wall_in = offset(wall_c, SEAT_W / 2)
edge_out = offset(wall_c, -EDGE_W / 2)
edge_in = offset(wall_c, EDGE_W / 2)
# split bed at FLUSH_X along the top run
si = len(seat_pts) - 1
seat_wall = wall_out[:si + 1] + list(reversed(wall_in[:si + 1]))
black_edge = edge_out[si:] + list(reversed(edge_in[si:]))
inner = wall_in[:si + 1] + edge_in[si:]      # paving boundary
outer = wall_out[:si + 1] + edge_out[si:]

patio = list(inner) + [(W, H), (DECK_X1, H), (DECK_X1, DECK_Y0), (DECK_X0, DECK_Y0), (DECK_X0, LEFT_H - SLAB_OUT), (inner[0][0], LEFT_H - SLAB_OUT)]

lawn = [(0, 0), (W, 0), (W, outer[-1][1])] + list(reversed(outer)) + [(0, LEFT_H)]

gravel_L = [(0, 2.5), (1.0, 2.5), (1.0, LEFT_H), (0, LEFT_H)]
gravel_R = [(20.6 + R, 5.5), (W, 5.5), (W, 14.2), (20.6 + R, 14.2)]
concrete = [(10.3 + R/2, 0.0), (16.8 + R/2, 0.0), (16.8 + R/2, 1.5), (10.3 + R/2, 1.5)]   # 6.5 x 1.5, hard against the east fence
slab_strip = [(0, LEFT_H - SLAB_OUT), (DECK_X0, LEFT_H - SLAB_OUT), (DECK_X0, LEFT_H), (0, LEFT_H)]   # existing concrete strip
deck = [(DECK_X0, DECK_Y0), (DECK_X1, DECK_Y0), (DECK_X1, H), (DECK_X0, H)]
house_L = [(1.0, LEFT_H), (DECK_X0, LEFT_H), (DECK_X0, H), (1.0, H)]
drive = [(0, LEFT_H), (1.0, LEFT_H), (1.0, H), (0, H)]
house_R = [(DECK_X0, H), (HOUSE_R_X1, H), (HOUSE_R_X1, H + 1.5), (DECK_X0, H + 1.5)]
entrance = [(HOUSE_R_X1, H), (W, H), (W, H + 1.5), (HOUSE_R_X1, H + 1.5)]
lot = [(0, 0), (W, 0), (W, H), (0, H)]

# existing trees, positions and canopy radii read off the rectified drone photo (photo/base_grid.jpg)
# kind: "broad" round canopy, "conifer" tall narrow column (south fence row)
trees = [((4.5, 1.15), 1.4, "broad"),
         ((0.7, 4.5), 0.8, "broad"), ((1.68, 7.8), 1.5, "broad"),
         ((20.8 + R, 6.0), 1.2, "conifer"), ((20.8 + R, 8.3), 1.0, "conifer"), ((20.8 + R, 10.6), 1.1, "conifer"),
         ((21.0 + R, 12.9), 1.0, "conifer"), ((20.8 + R, 14.8), 0.8, "conifer")]
ringed = []
tree_walls = [((5.2, 8.0), 1.2, 0.5), ((9.2, 2.0), 0.6, 0.5)]   # F and E: circular seat walls, inner radius 0.5 m, SEAT_W wide   # kept trees given a paved surround (centre, canopy r, surround r)
topiary = ((19.0, 0.8), 0.6)
# existing tree to be removed (from the rectified drone photo)
remove_trees = [((4.0, 4.3), 0.8), ((1.5, 1.2), 1.3), ((7.3, 1.2), 0.9), ((3.5, 6.7), 0.5)]   # + C, A, B

# facade features read from photos 12, 17, 26, 27 (positions approximate, ±0.3 m)
# openings: (wall, a, b, sill, head, kind) — wall "S" is the y=15 wall facing north (a,b = x range),
#           wall "W" is the x=7.8 wall facing east (a,b = y range)
openings = [
    # wall "S": the y=H wall facing the yard (photos 3, 26). From the south end: terrace door, bay, small window.
    ("S", 18.6, 19.6, 0.0, 2.1, "door"),      # French door at the top of the balustrade steps
    ("S", 15.3, 17.3, 0.9, 2.1, "bay"),       # kitchen bay window, projects 0.5 m
    ("S", 14.0, 14.8, 1.0, 2.0, "window"),    # small window beside the deck
    ("S", 16.0, 17.8, 4.2, 5.3, "window"),    # upstairs, arched, above the bay
    ("S", 18.7, 19.7, 4.2, 5.3, "window"),    # upstairs, above the terrace door
    # wall "W": the x=7.8 wall at the back of the deck (photo 27)
    ("W", 13.6, 14.5, 0.0, 2.1, "door"),      # door onto the deck, under the porch roof
    # wall "N": the west wing's yard-facing wall at y=LEFT_H (photo 8)
    ("N", 3.9, 5.3, 1.0, 2.2, "window"),      # large arched window, centred on the wing
]
porch = {"x0": DECK_X0, "x1": ROOF_EDGE_X, "y0": DECK_Y0, "y1": H, "height": 2.9}   # house roof continues over the west 2.6 m of the deck
DECK_H = 0.35                                # two steps of ~17 cm, photo 26

labels = [  # (x, y, text, size)
    (2.3, 1.1, "草地 LAWN", 0.32),
    (13.55 + R/2, 0.75, "水泥铺 CONCRETE PAD 6.5×1.5", 0.28),
    (20.9, 0.8, "草地", 0.26),
    (0.5, 5.9, "小石头", 0.22), (0.5, 6.25, "1 m", 0.22),
    (21.1 + R, 9.2, "小石头", 0.22), (21.1 + R, 9.55, "1 m", 0.22),
    (3.4, 5.2, "座墙 SEAT WALL", 0.22), (3.4, 5.55, "H 40–50 cm", 0.2),
    (11.0, 7.0, "铺石砖 STONE PAVERS", 0.42),
    (18.9, 2.2, "黑色收边 BLACK PAVER EDGE, flush", 0.22),
    (12.0, 10.9, "木平台 DECK +0.35", 0.28), (12.0, 11.35, "5.8 × 5.7", 0.26), (9.1, 12.6, "roof over", 0.2), (9.1, 12.9, "3.2 open", 0.2),
    (4.3, 12.6, "房子 HOUSE", 0.34), (4.6, 9.45, "existing concrete strip 0.98", 0.18),
    (0.5, 12.3, "通道", 0.24),
    (DECK_X1 + 3.2, 16.1, "屋 HOUSE", 0.30),
    (W - 1.35, 16.1, "入口", 0.24),
    (19.0, 0.8, "花球", 0.2),
    (5.2, 9.2, "F  座墙 r0.5", 0.2), (9.2, 0.75, "E  座墙 r0.5", 0.2),
    (6.2, 3.95, "座墙 SEAT WALL → E", 0.22),
]
label_rot = {}

dims = [  # (p1, p2, offset, text) offset: positive = away to the outside side
    ((0, 0), (W, 0), -0.8, "22.8 m"),
    ((W, 0), (W, H), 0.9, "15.37 m*"),
    ((0, 0), (0, LEFT_H), -0.9, "10.2 m"),
    ((0, LEFT_H), (DECK_X0, LEFT_H), -0.45, "7.8 m"),
    ((DECK_X0, H), (DECK_X1, H), 0.6, "5.8 m"),
    ((DECK_X1, H), (HOUSE_R_X1, H), 0.6, "6.5 m"),
    ((HOUSE_R_X1, H), (W, H), 0.6, "2.7*"),
    ((DECK_X1, DECK_Y0), (DECK_X1, H), -0.6, "5.7 m"), ((DECK_X1 + 1.2, DECK_Y0), (DECK_X1 + 1.2, LEFT_H), 0.0, "0.53"),
]

# ---------- SVG ----------
S = 100.0  # cm per m
def f(v): return f"{v * S:.1f}"
def poly(pts, close=True):
    return " ".join(f"{f(x)},{f(y)}" for x, y in pts)

svg = []
svg.append('<?xml version="1.0" encoding="UTF-8"?>')
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="270mm" height="205mm" viewBox="-150 -150 2700 2050" '
           'font-family="PingFang SC, Helvetica Neue, Arial, sans-serif">')
svg.append('<rect x="-150" y="-150" width="2700" height="2050" fill="#ffffff"/>')
svg.append('<g id="lawn"><polygon points="%s" fill="#cfe5b8" stroke="none"/></g>' % poly(lawn))
svg.append('<g id="gravel" fill="#e6e1d6" stroke="#a89f90" stroke-width="2"><polygon points="%s"/><polygon points="%s"/></g>'
           % (poly(gravel_L), poly(gravel_R)))
svg.append('<g id="concrete"><polygon points="%s" fill="#d9d9d9" stroke="#8c8c8c" stroke-width="2"/></g>' % poly(concrete))
svg.append('<g id="slab-strip"><polygon points="%s" fill="#d9d9d9" stroke="#8c8c8c" stroke-width="2"/></g>' % poly(slab_strip))
svg.append('<g id="patio"><polygon points="%s" fill="#f1d3bd" stroke="none"/></g>' % poly(patio))
svg.append('<g id="seat-wall"><polygon points="%s" fill="#8a8a8a" stroke="#333" stroke-width="2"/></g>' % poly(seat_wall))
svg.append('<g id="black-edge"><polygon points="%s" fill="#1a1a1a" stroke="none"/></g>' % poly(black_edge))
# deck with boards
svg.append('<g id="deck"><polygon points="%s" fill="#dcb98a" stroke="#6b4a1e" stroke-width="3"/>' % poly(deck))
y = DECK_Y0 + 0.3
while y < H:
    svg.append(f'<line x1="{f(DECK_X0)}" y1="{f(y)}" x2="{f(DECK_X1)}" y2="{f(y)}" stroke="#b08a55" stroke-width="1.5"/>')
    y += 0.3
svg.append('</g>')
svg.append('<defs><pattern id="hatch" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
           '<line x1="0" y1="0" x2="0" y2="20" stroke="#9a9a9a" stroke-width="2"/></pattern></defs>')
svg.append('<g id="house" stroke="#222" stroke-width="3">')
for p in (house_L, house_R, entrance):
    svg.append('<polygon points="%s" fill="url(#hatch)"/>' % poly(p))
svg.append('<polygon points="%s" fill="#bfbfbf" stroke-width="2"/>' % poly(drive))
svg.append('</g>')
svg.append('<g id="openings" stroke="#1f5fa8" stroke-width="4" fill="none">')
for wall, a, b, sill, head, kind in openings:
    if sill >= 3: continue   # upstairs, not on the plan
    if wall == "S":
        y0 = H
        if kind == "door":
            r = b - a
            svg.append(f'<path d="M {f(a)} {f(y0)} L {f(a)} {f(y0-r)} A {f(r)} {f(r)} 0 0 1 {f(b)} {f(y0)}" stroke-width="3"/>')
        elif kind == "bay":
            svg.append(f'<polyline points="{f(a)},{f(y0)} {f(a+0.3)},{f(y0-0.5)} {f(b-0.3)},{f(y0-0.5)} {f(b)},{f(y0)}"/>')
        else:
            svg.append(f'<line x1="{f(a)}" y1="{f(y0-0.06)}" x2="{f(b)}" y2="{f(y0-0.06)}"/><line x1="{f(a)}" y1="{f(y0+0.06)}" x2="{f(b)}" y2="{f(y0+0.06)}"/>')
    elif wall == "N":
        svg.append(f'<line x1="{f(a)}" y1="{f(LEFT_H-0.06)}" x2="{f(b)}" y2="{f(LEFT_H-0.06)}"/><line x1="{f(a)}" y1="{f(LEFT_H+0.06)}" x2="{f(b)}" y2="{f(LEFT_H+0.06)}"/>')
    else:
        x0 = DECK_X0
        if kind == "door":
            r = b - a
            svg.append(f'<path d="M {f(x0)} {f(a)} L {f(x0+r)} {f(a)} A {f(r)} {f(r)} 0 0 1 {f(x0)} {f(b)}" stroke-width="3"/>')
        else:
            svg.append(f'<line x1="{f(x0-0.06)}" y1="{f(a)}" x2="{f(x0-0.06)}" y2="{f(b)}"/><line x1="{f(x0+0.06)}" y1="{f(a)}" x2="{f(x0+0.06)}" y2="{f(b)}"/>')
svg.append(f'<rect x="{f(porch["x0"])}" y="{f(porch["y0"])}" width="{f(porch["x1"]-porch["x0"])}" height="{f(porch["y1"]-porch["y0"])}" stroke="#6b4a1e" stroke-width="2" stroke-dasharray="12 8"/>')
svg.append(f'<circle cx="{f(porch["x1"])}" cy="{f(porch["y0"])}" r="8" fill="#6b4a1e" stroke="none"/>')
svg.append('</g>')
svg.append('<g id="lot"><polygon points="%s" fill="none" stroke="#000" stroke-width="5"/></g>' % poly(lot))
# trees
svg.append('<g id="trees">')
for c, r, kind in trees:
    svg.append(f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(r)}" fill="#7db36a" stroke="#2f5d25" stroke-width="2"/>'
               f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="6" fill="#2f5d25"/>')
for c, r, rs in ringed:
    svg.append(f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(rs)}" fill="#e6e1d6" stroke="#666" stroke-width="3"/>'
               f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(r)}" fill="#7db36a" stroke="#2f5d25" stroke-width="2"/>'
               f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="6" fill="#2f5d25"/>')
for c, r, ri in tree_walls:
    svg.append(f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(ri + SEAT_W/2)}" fill="none" stroke="#8a8a8a" stroke-width="{f(SEAT_W)}"/>'
               f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(ri)}" fill="#c9a97a" stroke="#333" stroke-width="2"/><circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(ri + SEAT_W)}" fill="none" stroke="#333" stroke-width="2"/>'
               f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(r)}" fill="#7db36a" fill-opacity="0.55" stroke="#2f5d25" stroke-width="2"/><circle cx="{f(c[0])}" cy="{f(c[1])}" r="6" fill="#2f5d25"/>')
c, r = topiary
svg.append(f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(r)}" fill="#a3cf8f" stroke="#2f5d25" stroke-width="2" stroke-dasharray="6 4"/>')
for c, r in []:   # removal marks kept off the sheet (they stay on the DXF layer TREES_REMOVE)
    svg.append(f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(r)}" fill="none" stroke="#c0392b" stroke-width="3" stroke-dasharray="10 6"/>'
               f'<line x1="{f(c[0]-r*.6)}" y1="{f(c[1]-r*.6)}" x2="{f(c[0]+r*.6)}" y2="{f(c[1]+r*.6)}" stroke="#c0392b" stroke-width="3"/>'
               f'<line x1="{f(c[0]-r*.6)}" y1="{f(c[1]+r*.6)}" x2="{f(c[0]+r*.6)}" y2="{f(c[1]-r*.6)}" stroke="#c0392b" stroke-width="3"/>'
               f'<text x="{f(c[0])}" y="{f(c[1]+r+0.35)}" font-size="20" fill="#c0392b" text-anchor="middle">移除 REMOVE</text>')
svg.append('</g>')
# labels
svg.append('<g id="labels" fill="#222" text-anchor="middle">')
for x, y_, t, sz in labels:
    svg.append(f'<text x="{f(x)}" y="{f(y_)}" font-size="{f(sz)}" dominant-baseline="middle">{t}</text>')
svg.append('</g>')
# dims
svg.append('<g id="dims" stroke="#c0392b" stroke-width="2" fill="#c0392b" font-size="28" text-anchor="middle">')
for p1, p2, off, txt in dims:
    horiz = abs(p1[1] - p2[1]) < 1e-6
    if horiz:
        yy = p1[1] + off
        svg.append(f'<line x1="{f(p1[0])}" y1="{f(yy)}" x2="{f(p2[0])}" y2="{f(yy)}"/>')
        for x in (p1[0], p2[0]):
            svg.append(f'<line x1="{f(x)}" y1="{f(yy - 0.15)}" x2="{f(x)}" y2="{f(yy + 0.15)}"/>')
            svg.append(f'<line x1="{f(x)}" y1="{f(p1[1])}" x2="{f(x)}" y2="{f(yy)}" stroke-width="1" stroke-dasharray="4 4"/>')
        svg.append(f'<text x="{f((p1[0] + p2[0]) / 2)}" y="{f(yy - 0.12)}" stroke="none">{txt}</text>')
    else:
        xx = p1[0] + off
        svg.append(f'<line x1="{f(xx)}" y1="{f(p1[1])}" x2="{f(xx)}" y2="{f(p2[1])}"/>')
        for y_ in (p1[1], p2[1]):
            svg.append(f'<line x1="{f(xx - 0.15)}" y1="{f(y_)}" x2="{f(xx + 0.15)}" y2="{f(y_)}"/>')
            svg.append(f'<line x1="{f(p1[0])}" y1="{f(y_)}" x2="{f(xx)}" y2="{f(y_)}" stroke-width="1" stroke-dasharray="4 4"/>')
        cy = (p1[1] + p2[1]) / 2
        svg.append(f'<text x="{f(xx)}" y="{f(cy)}" stroke="none" transform="rotate(-90 {f(xx)} {f(cy)})" dy="-10">{txt}</text>')
svg.append('</g>')
# title + scale bar
svg.append('<g id="title" fill="#222"><text x="0" y="1720" font-size="40" font-weight="bold">后院平面图 · BACKYARD PLAN</text>'
           '<text x="0" y="1760" font-size="24">Scale 1:100 · 1 SVG unit = 1 cm · '
           'Top is east · Lot, deck and house tape-measured 2026-09-07 · *entrance 2.7 derived from 22.8 − 7.8 − 5.8 − 6.5 (tape said 3.2); 15.37 derived from 10.2 + 0.53 + 5.7</text>'
           '<text x="0" y="1795" font-size="24">Trees placed from the rectified drone photo · Doors, windows, porch roof and steps from the ground photos (±0.3 m)</text>'
           '<rect x="2050" y="1700" width="500" height="14" fill="none" stroke="#222" stroke-width="2"/>'
           '<rect x="2050" y="1700" width="100" height="14" fill="#222"/><rect x="2250" y="1700" width="100" height="14" fill="#222"/>'
           '<rect x="2450" y="1700" width="100" height="14" fill="#222"/>'
           '<text x="2050" y="1745" font-size="22">0</text><text x="2300" y="1745" font-size="22" text-anchor="middle">2.5 m</text>'
           '<text x="2550" y="1745" font-size="22" text-anchor="end">5 m</text></g>')
svg.append('</svg>')
with open(os.path.join(OUT, "backyard_plan.svg"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(svg))

# ---------- DXF (metres, y up) ----------
doc = ezdxf.new("R2010")
doc.header["$INSUNITS"] = 6
msp = doc.modelspace()
layers = {"LOT": 7, "HOUSE": 8, "DECK": 30, "SEAT_WALL": 251, "BLACK_EDGE": 250,
          "PATIO": 41, "CONCRETE": 9, "LAWN": 3, "GRAVEL": 253, "TREES": 92, "TREES_REMOVE": 1, "TEXT": 7, "DIMS": 1}
for name, col in layers.items():
    doc.layers.add(name, color=col)
def Y(y): return -y
def P(pts): return [(x, Y(y)) for x, y in pts]
def lw(pts, layer, close=True, width=0.0):
    msp.add_lwpolyline(P(pts), close=close, dxfattribs={"layer": layer, "const_width": width})
def hatch(pts, layer, pattern="SOLID", scale=1.0, color=None):
    h = msp.add_hatch(dxfattribs={"layer": layer})
    if pattern == "SOLID": h.set_solid_fill(color=color if color is not None else 256)
    else: h.set_pattern_fill(pattern, scale=scale, color=color if color is not None else 256)
    h.paths.add_polyline_path(P(pts), is_closed=True)

lw(lot, "LOT", width=0.05)
lw(lawn, "LAWN"); hatch(lawn, "LAWN", "GRASS", 0.5)
for g in (gravel_L, gravel_R): lw(g, "GRAVEL"); hatch(g, "GRAVEL", "GRAVEL", 0.3)
lw(concrete, "CONCRETE"); hatch(concrete, "CONCRETE", "AR-CONC", 0.05)
lw(slab_strip, "CONCRETE"); hatch(slab_strip, "CONCRETE", "AR-CONC", 0.05)
lw(patio, "PATIO"); hatch(patio, "PATIO", "AR-B816", 0.05)
lw(seat_wall, "SEAT_WALL"); hatch(seat_wall, "SEAT_WALL", "ANSI37", 0.3)
lw(black_edge, "BLACK_EDGE"); hatch(black_edge, "BLACK_EDGE", "SOLID")
lw(deck, "DECK", width=0.02)
y = DECK_Y0 + 0.3
while y < H:
    msp.add_line((DECK_X0, Y(y)), (DECK_X1, Y(y)), dxfattribs={"layer": "DECK"}); y += 0.3
for p in (house_L, house_R, entrance): lw(p, "HOUSE", width=0.03); hatch(p, "HOUSE", "ANSI31", 0.5)
lw(drive, "HOUSE")
doc.layers.add("OPENINGS", color=5)
for wall, a, b, sill, head, kind in openings:
    if sill >= 3: continue
    if wall == "S":
        if kind == "door":
            msp.add_line((a, Y(H)), (a, Y(H - (b - a))), dxfattribs={"layer": "OPENINGS"}); msp.add_arc((a, Y(H)), b - a, 0, 90, dxfattribs={"layer": "OPENINGS"})
        elif kind == "bay":
            msp.add_lwpolyline(P([(a, H), (a+0.3, H-0.5), (b-0.3, H-0.5), (b, H)]), dxfattribs={"layer": "OPENINGS"})
        else:
            msp.add_line((a, Y(H-0.06)), (b, Y(H-0.06)), dxfattribs={"layer": "OPENINGS"}); msp.add_line((a, Y(H+0.06)), (b, Y(H+0.06)), dxfattribs={"layer": "OPENINGS"})
    elif wall == "N":
        msp.add_line((a, Y(LEFT_H-0.06)), (b, Y(LEFT_H-0.06)), dxfattribs={"layer": "OPENINGS"}); msp.add_line((a, Y(LEFT_H+0.06)), (b, Y(LEFT_H+0.06)), dxfattribs={"layer": "OPENINGS"})
    else:
        if kind == "door":
            r = b - a
            msp.add_line((DECK_X0, Y(a)), (DECK_X0 + r, Y(a)), dxfattribs={"layer": "OPENINGS"})
            msp.add_arc((DECK_X0, Y(a)), r, 270, 360, dxfattribs={"layer": "OPENINGS"})
        else:
            msp.add_line((DECK_X0-0.06, Y(a)), (DECK_X0-0.06, Y(b)), dxfattribs={"layer": "OPENINGS"}); msp.add_line((DECK_X0+0.06, Y(a)), (DECK_X0+0.06, Y(b)), dxfattribs={"layer": "OPENINGS"})
msp.add_lwpolyline(P([(porch["x0"], porch["y0"]), (porch["x1"], porch["y0"]), (porch["x1"], porch["y1"]), (porch["x0"], porch["y1"])]), close=True, dxfattribs={"layer": "OPENINGS", "linetype": "DASHED"} if "DASHED" in doc.linetypes else {"layer": "OPENINGS"})
for c, r, kind in trees:
    msp.add_circle((c[0], Y(c[1])), r, dxfattribs={"layer": "TREES"})
    msp.add_circle((c[0], Y(c[1])), 0.06, dxfattribs={"layer": "TREES"})
for c, r, rs in ringed:
    msp.add_circle((c[0], Y(c[1])), rs, dxfattribs={"layer": "TREES"})
    msp.add_circle((c[0], Y(c[1])), r, dxfattribs={"layer": "TREES"})
    msp.add_circle((c[0], Y(c[1])), 0.06, dxfattribs={"layer": "TREES"})
for c, r, ri in tree_walls:
    msp.add_circle((c[0], Y(c[1])), ri, dxfattribs={"layer": "SEAT_WALL"}); msp.add_circle((c[0], Y(c[1])), ri + SEAT_W, dxfattribs={"layer": "SEAT_WALL"})
    msp.add_circle((c[0], Y(c[1])), r, dxfattribs={"layer": "TREES"}); msp.add_circle((c[0], Y(c[1])), 0.06, dxfattribs={"layer": "TREES"})
c, r = topiary
msp.add_circle((c[0], Y(c[1])), r, dxfattribs={"layer": "TREES", "linetype": "DASHED"} if "DASHED" in doc.linetypes else {"layer": "TREES"})
for c, r in remove_trees:
    msp.add_circle((c[0], Y(c[1])), r, dxfattribs={"layer": "TREES_REMOVE"})
    msp.add_line((c[0]-r*.6, Y(c[1]-r*.6)), (c[0]+r*.6, Y(c[1]+r*.6)), dxfattribs={"layer": "TREES_REMOVE"})
    msp.add_line((c[0]-r*.6, Y(c[1]+r*.6)), (c[0]+r*.6, Y(c[1]-r*.6)), dxfattribs={"layer": "TREES_REMOVE"})
    msp.add_text("REMOVE TREE", dxfattribs={"layer": "TREES_REMOVE", "height": 0.2}).set_placement((c[0], Y(c[1]+r+0.3)), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
for x, y_, t, sz in labels:
    msp.add_text(t.replace("▼ ", ""), dxfattribs={"layer": "TEXT", "height": sz * 0.8}).set_placement((x, Y(y_)), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
doc.styles.new("DIM", dxfattribs={"font": "arial.ttf"}) if "DIM" not in doc.styles else None
dimstyle = doc.dimstyles.new("PLAN", dxfattribs={"dimtxt": 0.28, "dimasz": 0.2, "dimexo": 0.1, "dimdec": 1, "dimlfac": 1, "dimtxsty": "DIM"})
for p1, p2, off, txt in dims:
    horiz = abs(p1[1] - p2[1]) < 1e-6
    if horiz:
        d = msp.add_linear_dim(base=(p1[0], Y(p1[1] + off)), p1=(p1[0], Y(p1[1])), p2=(p2[0], Y(p2[1])),
                               dimstyle="PLAN", dxfattribs={"layer": "DIMS"})
    else:
        d = msp.add_linear_dim(base=(p1[0] + off, Y(p1[1])), p1=(p1[0], Y(p1[1])), p2=(p2[0], Y(p2[1])),
                               angle=90, dimstyle="PLAN", dxfattribs={"layer": "DIMS"})
    d.render()
msp.add_text("BACKYARD PLAN 后院平面图 — units: metres — from hand sketch", dxfattribs={"layer": "TEXT", "height": 0.4}).set_placement((0, Y(H + 2.2)))
doc.saveas(os.path.join(OUT, "backyard_plan.dxf"))

# ---------- geometry JSON + 3D viewer ----------
import json
geom = {
    "W": W, "H": H, "LEFT_H": LEFT_H,
    "areas": {
        "lawn": lawn, "gravelL": gravel_L, "gravelR": gravel_R, "concrete": concrete, "patio": patio,
        "seatWall": seat_wall, "blackEdge": black_edge,
        "deck": deck, "slabStrip": slab_strip, "houseL": house_L, "houseR": house_R, "entrance": entrance, "drive": drive, "lot": lot,
    },
    "trees": [{"c": c, "r": r, "kind": k} for c, r, k in trees],
    "ringed": [{"c": c, "r": r, "rs": rs} for c, r, rs in ringed],
    "topiary": {"c": topiary[0], "r": topiary[1]},
    "treeWalls": [{"c": c, "r": r, "ri": ri, "w": SEAT_W} for c, r, ri in tree_walls],
    "seatCtrl": SEAT_CTRL, "seatW": SEAT_W, "edgeW": EDGE_W, "E_C": E_C, "RC": RC, "SLAB_OUT": SLAB_OUT,
    "edgeIn": edge_in, "edgeOut": edge_out,
    "patioTail": [(W, H), (DECK_X1, H), (DECK_X1, DECK_Y0), (DECK_X0, DECK_Y0), (DECK_X0, LEFT_H - SLAB_OUT)],
    "removeTrees": [{"c": c, "r": r} for c, r in remove_trees],
    "openings": [{"wall": w, "a": a, "b": b, "sill": si, "head": he, "kind": k} for w, a, b, si, he, k in openings],
    "porch": porch, "deckH": DECK_H, "deckX0": DECK_X0, "deckX1": DECK_X1, "deckY0": DECK_Y0,
    "labels": [
        {"p": (5.0, 1.2, 0.0), "t": "草地 Lawn"}, {"p": (13.55 + R/2, 0.75, 0.0), "t": "水泥铺 Concrete pad"},
        {"p": (2.1, 6.0, 0.45), "t": "座墙 Seat wall 45 cm"}, {"p": (18.9, 2.2, 0.0), "t": "黑色收边 Black paver edge"},
        {"p": (10.5, 6.5, 0.0), "t": "铺石砖 Stone pavers"}, {"p": (12.0, 12.2, 0.35), "t": "木平台 Wood deck"},
        {"p": (4.0, 12.2, 3.2), "t": "房子 House"}, {"p": (W - 1.35, 15.5, 0.0), "t": "入口 Entrance"},
        {"p": (0.5, 6.0, 0.0), "t": "小石头 Gravel 1 m"}, {"p": (21.1 + R, 9.3, 0.0), "t": "小石头 Gravel 1 m"},
        {"p": (19.0, 0.8, 1.3), "t": "花球 Topiary"},
    ],
}
import base64
photo_path = os.path.join(OUT, "photo", "base_rectified.jpg")
geom["photo"] = None
if os.path.exists(photo_path):
    from PIL import Image as _I
    im = _I.open(photo_path).convert("RGB"); im.thumbnail((1600, 1600))
    import io; buf = io.BytesIO(); im.save(buf, "JPEG", quality=72)
    geom["photo"] = {"uri": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), "w": W, "h": im.height / im.width * W}
tpl_path = os.path.join(OUT, "viewer_template.html")
if os.path.exists(tpl_path):
    tpl = open(tpl_path, encoding="utf-8").read().replace("__GEOM__", json.dumps(geom))
    open(os.path.join(OUT, "backyard_3d.html"), "w", encoding="utf-8").write(tpl.replace("__SHARE__", "false"))
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(tpl.replace("__SHARE__", "true"))   # view-only copy: GitHub Pages root and the shareable Claude link
with open(os.path.join(OUT, "backyard_geom.json"), "w") as fh: json.dump(geom, fh)
print("wrote", OUT)
