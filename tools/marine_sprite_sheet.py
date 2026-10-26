#!/usr/bin/env python3
"""
Starforge-mobile — armored space marine sprite sheet (deterministic pixel art).

4x4 grid of exactly 32x32 cells on a fully transparent background:
  Row 1: idle1, idle2 (breathing), walk1, walk2
  Row 2: walk3, walk4, attack1 (muzzle flash), attack2 (recoil)
  Row 3: attack3, death1 (stagger), death2 (kneel), death3 (falling)
  Row 4: death4 (on ground), empty, empty, empty

Strict 16-colour palette, hard edges, zero anti-aliasing, no shadows,
no scenery, no grid lines, no text.

Pipeline: figure is authored as vector-ish primitives (rects / thick lines)
in an upright "canonical" space, then rasterised through a transform
(identity / shear / rotate+scale) with hard-edged polygon fill. That keeps
angled frames (recoil, falling, prone) legible instead of pixel-mangled.
"""
from PIL import Image
import math
import os

CELL = 32
GUT = 1
COLS = ROWS = 4
OUT = os.path.dirname(os.path.abspath(__file__))

PAL = {
    '.': None,                 # transparent
    'K': (11, 13, 26),         # outline / ink
    'D': (27, 42, 74),         # armour shadow
    'C': (42, 63, 102),        # armour mid-dark
    'B': (47, 74, 122),        # armour mid
    'L': (79, 124, 192),       # armour light
    'H': (143, 184, 232),      # armour highlight
    'R': (200, 212, 228),      # rim light
    'S': (16, 24, 32),         # deep shadow / boots
    'V': (255, 138, 31),       # visor orange
    'W': (255, 196, 77),       # visor glow
    'G': (107, 114, 128),      # gunmetal
    'T': (170, 179, 194),      # gunmetal light
    'N': (58, 47, 34),         # grip brown
    'F': (255, 224, 138),      # flash yellow
    'X': (255, 255, 255),      # flash white
}
assert len(PAL) == 16


# ---------------------------------------------------------------- ops canvas

class Ops:
    """Collects primitives in canonical space; rendered later via a transform."""

    def __init__(self):
        self.items = []

    def rect(self, x0, y0, x1, y1, c):
        # pixel-inclusive rectangle: lands exactly on pixels x0..x1, y0..y1
        # (polygon spans the pixel-CENTRE box [x0+0.5, x1+0.5]; the even-odd
        #  fill test then keeps exactly those pixel centres).
        self.items.append(('poly', ([(x0, y0), (x1 + 1, y0),
                                     (x1 + 1, y1 + 1), (x0, y1 + 1)], c)))

    def line(self, x0, y0, x1, y1, c, t=2):
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        ux, uy = dx / L, dy / L
        px, py = -uy, ux
        h = t / 2.0
        ex, ey = ux * h, uy * h
        pts = [
            (x0 - ex + px * h, y0 - ey + py * h),
            (x1 + ex + px * h, y1 + ey + py * h),
            (x1 + ex - px * h, y1 + ey - py * h),
            (x0 - ex - px * h, y0 - ey - py * h),
        ]
        self.items.append(('poly', (pts, c)))

    def px(self, x, y, c):
        self.rect(x, y, x, y, c)

    def set(self, x, y, c):
        """Alias of px() so Ops and Grid share one API."""
        self.rect(x, y, x, y, c)

    def poly(self, pts, c):
        self.items.append(('poly', (list(pts), c)))


# ---------------------------------------------------------------- transforms

def T_identity():
    return lambda x, y: (x, y)


def T_shift(dx=0, dy=0):
    return lambda x, y: (x + dx, y + dy)


def T_shear(k, pivot_y):
    """Lean: rows above pivot_y slide horizontally by k * (pivot_y - y)."""
    def f(x, y):
        if y < pivot_y:
            return (x + k * (pivot_y - y), y)
        return (x, y)
    return f


def T_rot(deg, ox=16.0, oy=16.0, scale=1.0):
    """Rotate about (ox,oy); positive = clockwise on screen (y down)."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)

    def f(x, y):
        x = (x - ox) * scale
        y = (y - oy) * scale
        return (ox + x * c - y * s, oy + x * s + y * c)
    return f


def T_chain(*fns):
    def f(x, y):
        for fn in fns:
            x, y = fn(x, y)
        return (x, y)
    return f


# ---------------------------------------------------------------- rasteriser

def fill_poly(grid, pts, color):
    """Hard-edged even-odd polygon fill (pixel centres, no anti-aliasing)."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = max(0, int(math.floor(min(xs)))), min(grid.w - 1, int(math.ceil(max(xs))))
    y0, y1 = max(0, int(math.floor(min(ys)))), min(grid.h - 1, int(math.ceil(max(ys))))
    area = 0.0
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[(i + 1) % len(pts)]
        area += xi * yj - xj * yi
    if abs(area) < 0.02:
        # degenerate (1px) shape — fill the bounding box directly
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                grid.set(x, y, color)
        return
    n = len(pts)
    for y in range(y0, y1 + 1):
        cy = y + 0.5
        for x in range(x0, x1 + 1):
            cx = x + 0.5
            inside = False
            j = n - 1
            for i in range(n):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > cy) != (yj > cy):
                    xint = xi + (cy - yi) * (xj - xi) / (yj - yi)
                    if cx < xint:
                        inside = not inside
                j = i
            if inside:
                grid.set(x, y, color)


class Grid:
    def __init__(self, w=CELL, h=CELL):
        self.w, self.h = w, h
        self.px = {}

    def set(self, x, y, c):
        if c == '.' or c not in PAL:
            return
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[(x, y)] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, c)

    def outline(self, c='K'):
        """1px ink border around the silhouette (transparent neighbours only).

        Idempotent: the ink ring is derived from the ORIGINAL silhouette, so
        calling this twice does NOT grow the silhouette by another ring.
        (Calling it on an already-outlined grid used to add a second ring.)
        """
        if getattr(self, '_outlined', False):
            return
        add = {}
        for (x, y) in list(self.px.keys()):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.w and 0 <= ny < self.h and (nx, ny) not in self.px:
                    add[(nx, ny)] = c
        self.px.update(add)
        self._outlined = True

    def to_image(self):
        img = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        p = img.load()
        for (x, y), c in self.px.items():
            p[x, y] = PAL[c] + (255,)
        return img


def render(ops, tf=T_identity(), w=CELL, h=CELL):
    """Rasterise ops into a w x h grid (default 32x32; 48x48 for the tank)."""
    g = Grid(w, h)
    for kind, data in ops.items:
        if kind == 'poly':
            pts, color = data
            fill_poly(g, [tf(x, y) for (x, y) in pts], color)
    return g


# ---------------------------------------------------------------- figure parts

def helmet(g, x, y):
    g.rect(x + 1, y, x + 6, y + 6, 'B')       # dome
    g.rect(x, y + 2, x + 1, y + 6, 'B')       # rear of helm
    g.rect(x + 1, y + 3, x + 2, y + 5, 'D')   # rear shading
    g.rect(x + 2, y - 1, x + 5, y, 'L')       # crest
    g.rect(x + 2, y - 1, x + 5, y - 1, 'H')
    g.rect(x + 5, y + 1, x + 7, y + 3, 'V')   # visor
    g.rect(x + 6, y + 1, x + 7, y + 2, 'W')   # visor glow
    g.rect(x + 4, y + 5, x + 7, y + 6, 'D')   # jaw / respirator
    g.rect(x + 3, y + 5, x + 4, y + 6, 'C')   # neck guard


def torso(g, x, y):
    g.rect(x + 1, y, x + 8, y + 9, 'B')
    g.rect(x, y + 1, x + 1, y + 8, 'D')       # spine shadow
    g.rect(x + 2, y + 1, x + 6, y + 3, 'C')   # upper plate
    g.rect(x + 2, y + 1, x + 6, y + 1, 'L')   # plate lip
    g.rect(x + 3, y + 2, x + 6, y + 3, 'B')   # plate face
    g.rect(x + 7, y + 3, x + 8, y + 9, 'D')   # front shadow
    g.rect(x + 1, y + 6, x + 8, y + 9, 'D')   # abdomen
    g.rect(x + 2, y + 7, x + 7, y + 7, 'C')
    g.rect(x + 2, y + 4, x + 7, y + 4, 'C')   # waist seam
    g.rect(x + 4, y + 2, x + 5, y + 2, 'K')   # chest vent


def backpack(g, x, y):
    g.rect(x, y, x + 2, y + 6, 'D')
    g.rect(x, y, x + 2, y, 'C')
    g.rect(x + 1, y + 6, x + 2, y + 7, 'S')


def pauldron(g, x, y):
    g.rect(x, y, x + 3, y + 2, 'L')
    g.rect(x, y, x + 3, y, 'H')
    g.rect(x + 1, y + 3, x + 3, y + 3, 'B')


def arm(g, pts, c='B', t=3):
    for i in range(len(pts) - 1):
        g.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c, t)


def glove(g, x, y):
    g.rect(x, y, x + 1, y + 1, 'S')


def rifle(g, gx, gy, angle=0):
    """Rifle held at grip (gx,gy), barrel to the RIGHT. Returns muzzle (x,y)."""
    rad = math.radians(angle)
    c, s = math.cos(rad), math.sin(rad)

    def rot(px, py):
        return (gx + (px - gx) * c - (py - gy) * s,
                gy + (px - gx) * s + (py - gy) * c)

    def rrect(x0, y0, x1, y1, col):
        g.poly([rot(x0, y0), rot(x1, y0), rot(x1, y1), rot(x0, y1)], col)

    rrect(gx - 3, gy - 1, gx - 1, gy + 1, 'D')    # stock
    rrect(gx - 1, gy - 2, gx + 3, gy + 1, 'G')    # receiver
    rrect(gx + 0, gy - 2, gx + 3, gy - 2, 'T')    # receiver top rail
    rrect(gx + 0, gy - 4, gx + 1, gy - 3, 'C')    # scope
    rrect(gx + 4, gy - 1, gx + 7, gy + 1, 'T')    # barrel
    rrect(gx + 8, gy - 2, gx + 9, gy + 1, 'G')    # muzzle brake
    rrect(gx - 1, gy + 1, gx + 0, gy + 3, 'N')    # grip
    rrect(gx + 1, gy + 1, gx + 2, gy + 3, 'S')    # magazine
    mx, my = rot(gx + 10, gy)
    return int(round(mx)), int(round(my))


def muzzle_flash(g, x, y):
    for dx, dy, c in ((0, 0, 'X'), (-1, 0, 'F'), (1, 0, 'F'), (0, -1, 'F'),
                      (0, 1, 'F'), (2, -1, 'F'), (2, 1, 'F'), (3, 0, 'X'),
                      (-2, -1, 'F'), (-2, 1, 'F'), (1, -2, 'F'), (1, 2, 'F'),
                      (-1, -2, 'F'), (-1, 2, 'F')):
        g.px(x + dx, y + dy, c)


def leg(g, hip, knee, foot, c='B', pad=True, boot_dir=0):
    g.line(hip[0], hip[1], knee[0], knee[1], c, 3)
    g.line(knee[0], knee[1], foot[0], foot[1], c, 3)
    if pad:
        g.rect(knee[0] - 1, knee[1] - 1, knee[0] + 1, knee[1], 'H')
    bx = foot[0] + boot_dir
    g.rect(bx - 1, foot[1], bx + 1, foot[1] + 1, 'C')       # boot
    g.rect(bx - 1, foot[1] + 1, bx + 1, foot[1] + 1, 'K')   # sole


def build_base(g, *, body_dx=0, body_dy=0, head_dx=0, head_dy=0,
               leg_back=None, leg_front=None, arm_front=None, arm_back=None,
               rifle_pos=None, rifle_angle=0, flash=False, pack=True):
    body_dx, body_dy = body_dx, body_dy
    torso_x, torso_y = 9 + body_dx, 9 + body_dy
    helm_x, helm_y = 11 + body_dx + head_dx, 1 + body_dy + head_dy

    if pack:
        backpack(g, 6 + body_dx, 11 + body_dy)
    if arm_back:
        arm(g, arm_back, 'D', 3)
    if leg_back:
        leg(g, leg_back[0], leg_back[1], leg_back[2], 'D', False, -1)
    torso(g, torso_x, torso_y)
    # neck
    g.rect(torso_x + 3, torso_y - 2, torso_x + 5, torso_y, 'D')
    if leg_front:
        leg(g, leg_front[0], leg_front[1], leg_front[2], 'B', True, 1)
    helmet(g, helm_x, helm_y)
    pauldron(g, 16 + body_dx, 9 + body_dy)
    if rifle_pos:
        mx, my = rifle(g, rifle_pos[0], rifle_pos[1], rifle_angle)
    if arm_front:
        arm(g, arm_front, 'C', 3)
        glove(g, arm_front[-1][0], arm_front[-1][1])
    if rifle_pos:
        if flash:
            muzzle_flash(g, mx - 1, my)
    return g


def make_ops(**kw):
    o = Ops()
    build_base(o, **kw)
    return o


# ---------------------------------------------------------------- poses

def pose_idle1():
    return render(make_ops(
        leg_back=((11, 18), (11, 23), (9, 28)),
        leg_front=((14, 18), (14, 23), (15, 28)),
        arm_back=((11, 12), (14, 15), (18, 16)),
        arm_front=((17, 11), (19, 14), (20, 15)),
        rifle_pos=(20, 15),
    ))


def pose_idle2():
    """Subtle breathing: torso + helm drop 1px, arms sag 1px."""
    return render(make_ops(
        body_dy=1,
        leg_back=((11, 19), (11, 24), (9, 28)),
        leg_front=((14, 19), (14, 24), (15, 28)),
        arm_back=((11, 13), (14, 16), (18, 17)),
        arm_front=((17, 12), (19, 15), (20, 16)),
        rifle_pos=(20, 16),
    ))


def pose_walk(phase):
    head_dy = 0
    if phase == 1:      # contact — front leg forward, back leg trailing
        dy = 0
        front, back = ((14, 18), (16, 23), (17, 28)), ((11, 18), (10, 23), (8, 28))
        af, ab = ((17, 11), (19, 14), (20, 16)), ((11, 12), (14, 15), (18, 16))
        rp = (20, 15)
    elif phase == 2:    # passing — legs together, body rises (head stays level)
        dy = -1
        head_dy = 1
        front, back = ((14, 17), (13, 22), (12, 27)), ((11, 17), (12, 22), (13, 27))
        af, ab = ((17, 10), (20, 13), (21, 15)), ((11, 11), (13, 14), (17, 15))
        rp = (21, 14)
    elif phase == 3:    # contact — opposite stride
        dy = 0
        front, back = ((14, 18), (12, 23), (11, 28)), ((11, 18), (12, 23), (14, 28))
        af, ab = ((17, 11), (19, 14), (20, 16)), ((11, 12), (14, 15), (18, 16))
        rp = (20, 15)
    else:              # passing — legs together, body rises (head stays level)
        dy = -1
        head_dy = 1
        front, back = ((14, 17), (15, 22), (16, 27)), ((11, 17), (10, 22), (9, 27))
        af, ab = ((17, 10), (19, 13), (20, 15)), ((11, 11), (13, 14), (17, 15))
        rp = (20, 14)
    return render(make_ops(body_dy=dy, head_dy=head_dy, leg_back=back,
                           leg_front=front, arm_back=ab, arm_front=af,
                           rifle_pos=rp))


def pose_attack1():
    """Muzzle flash, arms extended, weight forward."""
    return render(make_ops(
        body_dx=1,
        leg_back=((11, 18), (10, 23), (8, 28)),
        leg_front=((14, 18), (15, 23), (17, 28)),
        arm_back=((11, 12), (14, 15), (18, 15)),
        arm_front=((18, 11), (20, 13), (21, 14)),
        rifle_pos=(19, 14),
        flash=True,
    ))


def pose_attack2():
    """Recoil: body jolts back and down, weapon kicks up."""
    return render(make_ops(
        body_dx=-1,
        body_dy=1,
        head_dy=-1,
        leg_back=((10, 19), (9, 24), (7, 28)),
        leg_front=((13, 19), (13, 24), (14, 28)),
        arm_back=((10, 13), (13, 16), (17, 16)),
        arm_front=((16, 12), (18, 13), (19, 14)),
        rifle_pos=(19, 14),
        rifle_angle=-12,
    ))


def pose_attack3():
    """Follow-through: weapon drops, weight forward."""
    return render(make_ops(
        body_dx=1,
        leg_back=((11, 18), (11, 23), (9, 28)),
        leg_front=((14, 18), (15, 23), (16, 28)),
        arm_back=((11, 12), (14, 15), (18, 16)),
        arm_front=((18, 11), (20, 14), (21, 17)),
        rifle_pos=(21, 18),
        rifle_angle=8,
    ))


def pose_death1():
    """Stagger: torso thrown back, one leg flung forward, arms thrown out."""
    ops = make_ops(
        body_dx=-2,
        body_dy=1,
        head_dx=-2,
        head_dy=-1,
        leg_back=((9, 19), (8, 24), (6, 28)),
        leg_front=((12, 19), (16, 23), (18, 24)),
        arm_back=((8, 13), (7, 16), (9, 18)),
        arm_front=((14, 12), (12, 15), (13, 18)),
        rifle_pos=(14, 20),
        rifle_angle=62,
    )
    return render(ops, T_shear(0.15, 20))


def pose_death2():
    """Kneeling on one knee, head bowed, weapon dropped on the floor."""
    o = make_ops(
        body_dy=4,
        leg_back=((13, 22), (17, 25), (20, 28)),
        leg_front=((15, 22), (16, 26), (11, 28)),
        arm_back=((11, 16), (12, 19), (14, 21)),
        arm_front=((17, 15), (19, 18), (18, 21)),
        rifle_pos=None,
    )
    # dropped weapon lying on the floor in front
    o.rect(21, 27, 30, 29, 'G')
    o.rect(23, 27, 30, 27, 'T')
    o.rect(21, 28, 22, 29, 'N')
    return render(o)


def pose_death3():
    """Falling backward: whole figure tipped ~40 deg and dropping."""
    ops = make_ops(
        leg_back=((11, 18), (11, 23), (9, 28)),
        leg_front=((14, 18), (14, 23), (15, 28)),
        arm_back=((11, 12), (14, 15), (18, 16)),
        arm_front=((17, 11), (19, 14), (20, 15)),
        rifle_pos=(20, 15),
    )
    tf = T_chain(T_rot(-42, 13.0, 27.0, 0.82), T_shift(1.5, -1.0))
    return render(ops, tf)


def pose_death4():
    """Lying on the ground: body flat, rifle dropped beside it."""
    o = Ops()
    # legs (feet at the left), torso, head at the right — still facing RIGHT
    o.rect(2, 24, 8, 27, 'D')            # back leg
    o.rect(1, 24, 3, 29, 'S')            # boot
    o.rect(6, 23, 12, 27, 'B')           # front leg
    o.rect(5, 23, 7, 24, 'H')            # knee pad
    o.rect(11, 27, 13, 29, 'S')          # boot
    o.rect(12, 20, 19, 26, 'B')          # torso
    o.rect(13, 20, 18, 22, 'L')          # plate
    o.rect(14, 20, 17, 20, 'H')
    o.rect(11, 23, 19, 26, 'D')          # abdomen shadow
    o.rect(17, 18, 20, 21, 'L')          # pauldron
    o.rect(17, 18, 20, 18, 'H')
    # head at the right, visor facing right
    o.rect(20, 18, 27, 25, 'B')
    o.rect(21, 17, 25, 17, 'L')
    o.rect(21, 17, 25, 17, 'H')
    o.rect(25, 19, 27, 22, 'V')          # visor
    o.rect(26, 19, 27, 20, 'W')          # glow
    o.rect(20, 23, 26, 24, 'D')          # jaw
    o.rect(20, 20, 21, 22, 'C')
    # dropped rifle lying on the floor
    o.rect(4, 27, 16, 29, 'G')
    o.rect(8, 27, 16, 27, 'T')
    o.rect(16, 26, 17, 29, 'G')
    o.rect(3, 28, 4, 29, 'N')
    return render(o)


# ---------------------------------------------------------------- assemble

def cell_image(g):
    g.outline()
    return g.to_image()


def build_sheet(cells):
    w = COLS * CELL + (COLS - 1) * GUT
    h = ROWS * CELL + (ROWS - 1) * GUT
    sheet = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for idx, p in enumerate(cells):
        if p is None:
            continue
        c, r = idx % COLS, idx // COLS
        sheet.alpha_composite(cell_image(p), (c * (CELL + GUT), r * (CELL + GUT)))
    return sheet


def verify(sheet):
    """Hard guarantees: alpha 0/255 only, <=16 colours, cells exactly 32x32, tail empty."""
    px = list(sheet.getdata())
    colors = {p for p in px if p[3] != 0}
    alphas = {p[3] for p in px}
    assert alphas <= {0, 255}, f"non-opaque pixels: {sorted(alphas)}"
    assert len(colors) <= 16, f"palette overflow: {len(colors)} colours"
    for idx in range(COLS * ROWS):
        c, r = idx % COLS, idx // COLS
        assert c * (CELL + GUT) + CELL <= sheet.width
        assert r * (CELL + GUT) + CELL <= sheet.height
    for idx in (13, 14, 15):
        c, r = idx % COLS, idx // COLS
        box = (c * (CELL + GUT), r * (CELL + GUT),
               c * (CELL + GUT) + CELL, r * (CELL + GUT) + CELL)
        assert sheet.crop(box).getbbox() is None, f"cell {idx} not empty"
    return len(colors)


def main():
    cells = build_frames()
    sheet = build_sheet(cells)
    n = verify(sheet)
    sheet.save(os.path.join(OUT, 'starforge_marine_sheet.png'))

    tight = Image.new('RGBA', (COLS * CELL, ROWS * CELL), (0, 0, 0, 0))
    for idx, p in enumerate(cells):
        if p is None:
            continue
        c, r = idx % COLS, idx // COLS
        tight.alpha_composite(cell_image(p), (c * CELL, r * CELL))
    tight.save(os.path.join(OUT, 'starforge_marine_sheet_tight.png'))

    sheet.resize((sheet.width * 8, sheet.height * 8), Image.NEAREST).save(
        os.path.join(OUT, 'starforge_marine_sheet_preview.png'))

    # per-frame QA export at 12x
    for idx, p in enumerate(cells):
        if p is None:
            continue
        cell_image(p).resize((CELL * 12, CELL * 12), Image.NEAREST).save(
            os.path.join(OUT, f'_qa_{idx:02d}.png'))
    print(f'ok sheet={sheet.size} palette={n} colours')


# named frames: (state, index) -> cell index in the 4x4 grid
FRAME_SPEC = [
    ('idle', 1), ('idle', 2),
    ('walk', 1), ('walk', 2), ('walk', 3), ('walk', 4),
    ('attack', 1), ('attack', 2), ('attack', 3),
    ('death', 1), ('death', 2), ('death', 3), ('death', 4),
]


def build_frames():
    """13 named marine frames (idle 2 / walk 4 / attack 3 / death 4)."""
    return [
        pose_idle1(), pose_idle2(), pose_walk(1), pose_walk(2),
        pose_walk(3), pose_walk(4), pose_attack1(), pose_attack2(),
        pose_attack3(), pose_death1(), pose_death2(), pose_death3(),
        pose_death4(), None, None, None,
    ]


if __name__ == '__main__':
    main()
