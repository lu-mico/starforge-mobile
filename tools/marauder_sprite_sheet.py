#!/usr/bin/env python3
"""
Starforge-mobile — Marauder sprite sheet (32x32 cells, 13 frames).

Heavy marine variant: same 13-frame contract as the Marine
(idle 2 / walk 4 / attack 3 / death 4, right-facing, transparent background),
but a bulkier silhouette, a shoulder cannon instead of a rifle, and a steel
armour ramp instead of the Marine's blue. It reuses the Marine's palette
(global cap: 16 colours) and the same drawing primitives.

Self-contained on purpose: the validated Marine module is never monkey-patched.
"""
import marine_sprite_sheet as M
from marine_sprite_sheet import (CELL, Ops, Grid, T_identity, T_rot, T_shift, T_chain,
                                 fill_poly, render)

# Marine colour codes -> Marauder ramp (steel body, blue trim, orange visor)
REMAP = {
    'B': 'G',   # armour mid      -> gunmetal
    'L': 'T',   # armour light    -> light gunmetal
    'H': 'R',   # armour highlight-> rim light
    'D': 'S',   # armour shadow   -> deep shadow
    'C': 'C',   # mid-dark stays a desaturated blue-grey
    'S': 'K',   # magazine/deep   -> ink
    'K': 'K', 'G': 'G', 'T': 'T', 'N': 'N',
    'V': 'V', 'W': 'W', 'F': 'F', 'X': 'X', 'D2': 'D2',
}


def remap(ops):
    """Return a copy of ops with Marauder colours."""
    out = Ops()
    for kind, data in ops.items:
        if kind == 'poly':
            pts, color = data
            out.items.append(('poly', (pts, REMAP.get(color, color))))
    return out


# ---------------------------------------------------------------- parts

def helmet(g, x, y):
    """Heavy helm with a reinforced brow."""
    g.rect(x + 1, y, x + 8, y + 7, 'B')
    g.rect(x, y + 3, x + 1, y + 7, 'B')
    g.rect(x + 1, y + 3, x + 2, y + 6, 'D')
    g.rect(x + 2, y - 1, x + 7, y, 'L')          # crest
    g.rect(x + 2, y - 1, x + 7, y - 1, 'H')
    g.rect(x + 6, y + 2, x + 8, y + 4, 'V')      # visor
    g.rect(x + 7, y + 2, x + 8, y + 3, 'W')
    g.rect(x + 5, y + 6, x + 8, y + 7, 'D')      # jaw
    g.rect(x + 3, y + 6, x + 4, y + 7, 'C')


def torso(g, x, y):
    """Wide chest block with a layered plate."""
    g.rect(x + 1, y, x + 10, y + 10, 'B')
    g.rect(x, y + 2, x + 1, y + 9, 'D')          # spine shadow
    g.rect(x + 2, y + 1, x + 8, y + 4, 'C')      # upper plate
    g.rect(x + 2, y + 1, x + 8, y + 1, 'L')
    g.rect(x + 3, y + 2, x + 7, y + 2, 'H')
    g.rect(x + 9, y + 4, x + 10, y + 10, 'D')    # front shadow
    g.rect(x + 1, y + 7, x + 10, y + 10, 'D')    # abdomen
    g.rect(x + 2, y + 8, x + 9, y + 8, 'C')
    g.rect(x + 2, y + 5, x + 9, y + 5, 'K')      # waist seam
    g.rect(x + 5, y + 3, x + 6, y + 3, 'K')      # chest vent
    g.rect(x + 3, y + 6, x + 4, y + 7, 'C')      # ammo pouches


def backpack(g, x, y):
    g.rect(x, y, x + 3, y + 7, 'D')
    g.rect(x, y, x + 3, y, 'C')
    g.rect(x + 1, y + 7, x + 3, y + 8, 'S')


def pauldron(g, x, y):
    """Oversized shoulder plate."""
    g.rect(x, y, x + 4, y + 3, 'L')
    g.rect(x, y, x + 4, y, 'H')
    g.rect(x + 1, y + 4, x + 4, y + 4, 'B')
    g.rect(x, y + 1, x + 1, y + 3, 'C')


def arm(g, pts, c='B', t=4):
    for i in range(len(pts) - 1):
        g.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c, t)


def glove(g, x, y):
    g.rect(x, y, x + 1, y + 1, 'S')


def cannon(g, gx, gy, angle=0, muzzle=False):
    """Shoulder cannon: boxy receiver, short heavy barrel. Returns muzzle x."""
    import math
    rad = math.radians(angle)
    c, s = math.cos(rad), math.sin(rad)

    def rot(px, py):
        return (gx + (px - gx) * c - (py - gy) * s,
                gy + (px - gx) * s + (py - gy) * c)

    def rrect(x0, y0, x1, y1, col):
        g.poly([rot(x0, y0), rot(x1, y0), rot(x1, y1), rot(x0, y1)], col)

    rrect(gx - 3, gy - 1, gx + 1, gy + 2, 'D')    # breech
    rrect(gx - 1, gy - 2, gx + 2, gy + 2, 'G')    # receiver
    rrect(gx - 1, gy - 2, gx + 2, gy - 2, 'T')    # top rail
    rrect(gx + 2, gy - 1, gx + 4, gy + 1, 'G')    # barrel
    rrect(gx + 5, gy - 2, gx + 6, gy + 2, 'G')    # muzzle brake
    rrect(gx + 5, gy - 2, gx + 6, gy - 2, 'T')
    mx, my = rot(gx + 7, gy)
    if muzzle:
        for dx, dy, col in ((0, 0, 'X'), (-1, 0, 'F'), (1, 0, 'F'), (0, -1, 'F'),
                            (0, 1, 'F'), (2, -1, 'F'), (2, 1, 'F')):
            g.set(int(round(mx)) + dx, int(round(my)) + dy, col)
    return int(round(mx)), int(round(my))


def muzzle_flash(g, x, y):
    for dx, dy, col in ((0, 0, 'X'), (-1, 0, 'F'), (1, 0, 'F'), (0, -1, 'F'),
                        (0, 1, 'F'), (2, -1, 'F'), (2, 1, 'F'), (-1, -2, 'F'),
                        (-1, 2, 'F'), (1, -2, 'F'), (1, 2, 'F')):
        g.set(x + dx, y + dy, col)


def leg(g, hip, knee, foot, c='B', pad=True, boot_dir=0):
    g.line(hip[0], hip[1], knee[0], knee[1], c, 4)
    g.line(knee[0], knee[1], foot[0], foot[1], c, 4)
    if pad:
        g.rect(knee[0] - 1, knee[1] - 1, knee[0] + 2, knee[1] + 1, 'H')
    bx = foot[0] + boot_dir
    g.rect(bx - 1, foot[1], bx + 1, foot[1] + 1, 'C')
    g.rect(bx - 1, foot[1] + 1, bx + 1, foot[1] + 1, 'K')


def build_base(g, *, body_dx=0, body_dy=0, head_dx=0, head_dy=0,
               leg_back=None, leg_front=None, arm_front=None, arm_back=None,
               cannon_pos=None, cannon_angle=0, flash=False, pack=True):
    body_dx, body_dy = body_dx, body_dy
    torso_x, torso_y = 8 + body_dx, 8 + body_dy
    helm_x, helm_y = 10 + body_dx + head_dx, 1 + body_dy + head_dy

    if pack:
        backpack(g, 5 + body_dx, 11 + body_dy)
    if arm_back:
        arm(g, arm_back, 'D', 4)
    if leg_back:
        leg(g, leg_back[0], leg_back[1], leg_back[2], 'D', False, -1)
    torso(g, torso_x, torso_y)
    g.rect(torso_x + 4, torso_y - 2, torso_x + 6, torso_y, 'D')   # neck
    if leg_front:
        leg(g, leg_front[0], leg_front[1], leg_front[2], 'B', True, 1)
    helmet(g, helm_x, helm_y)
    pauldron(g, 15 + body_dx, 9 + body_dy)
    mx = my = None
    if cannon_pos:
        mx, my = cannon(g, cannon_pos[0], cannon_pos[1], cannon_angle)
    if arm_front:
        arm(g, arm_front, 'B', 4)
        glove(g, arm_front[-1][0], arm_front[-1][1])
    if cannon_pos and flash:
        muzzle_flash(g, mx - 1, my)
    return g


# ---------------------------------------------------------------- poses

def pose_idle_1():
    o = Ops()
    build_base(o,
               leg_back=((10, 18), (10, 23), (8, 28)),
               leg_front=((14, 18), (14, 23), (15, 28)),
               arm_back=((10, 13), (13, 16), (17, 17)),
               arm_front=((17, 12), (19, 15), (20, 16)),
               cannon_pos=(19, 10))
    return render(remap(o), w=CELL, h=CELL)


def pose_idle_2():
    o = Ops()
    build_base(o, body_dy=1,
               leg_back=((10, 19), (10, 24), (8, 28)),
               leg_front=((14, 19), (14, 24), (15, 28)),
               arm_back=((10, 14), (13, 17), (17, 18)),
               arm_front=((17, 13), (19, 16), (20, 17)),
               cannon_pos=(19, 11))
    return render(remap(o), w=CELL, h=CELL)


def pose_walk(phase):
    if phase == 1:
        dy, head_dy = 0, 0
        front, back = ((14, 18), (16, 23), (17, 28)), ((10, 18), (9, 23), (7, 28))
        af, ab = ((17, 12), (19, 15), (20, 17)), ((10, 13), (13, 16), (17, 17))
        cp = (18, 9)
    elif phase == 2:
        dy, head_dy = -1, 1
        front, back = ((14, 17), (13, 22), (12, 27)), ((10, 17), (11, 22), (12, 27))
        af, ab = ((17, 11), (19, 14), (20, 16)), ((10, 12), (12, 15), (16, 16))
        cp = (18, 8)
    elif phase == 3:
        dy, head_dy = 0, 0
        front, back = ((14, 18), (12, 23), (11, 28)), ((10, 18), (11, 23), (13, 28))
        af, ab = ((17, 12), (19, 15), (20, 17)), ((10, 13), (13, 16), (17, 17))
        cp = (18, 9)
    else:
        dy, head_dy = -1, 1
        front, back = ((14, 17), (15, 22), (16, 27)), ((10, 17), (9, 22), (8, 27))
        af, ab = ((17, 11), (19, 14), (20, 16)), ((10, 12), (12, 15), (16, 16))
        cp = (18, 8)
    o = Ops()
    build_base(o, body_dy=dy, head_dy=head_dy, leg_back=back, leg_front=front,
               arm_back=ab, arm_front=af, cannon_pos=cp)
    return render(remap(o), w=CELL, h=CELL)


def pose_attack_1():
    o = Ops()
    build_base(o, body_dx=1,
               leg_back=((10, 18), (9, 23), (7, 28)),
               leg_front=((14, 18), (15, 23), (17, 28)),
               arm_back=((10, 13), (13, 16), (17, 16)),
               arm_front=((17, 12), (19, 14), (20, 15)),
               cannon_pos=(20, 10), flash=True)
    return render(remap(o), w=CELL, h=CELL)


def pose_attack_2():
    o = Ops()
    build_base(o, body_dx=-1, body_dy=1, head_dy=-1,
               leg_back=((9, 19), (8, 24), (6, 28)),
               leg_front=((13, 19), (13, 24), (14, 28)),
               arm_back=((9, 14), (12, 17), (16, 17)),
               arm_front=((16, 13), (18, 15), (19, 16)),
               cannon_pos=(19, 9), cannon_angle=-14)
    return render(remap(o), w=CELL, h=CELL)


def pose_attack_3():
    o = Ops()
    build_base(o, body_dx=1,
               leg_back=((10, 18), (10, 23), (8, 28)),
               leg_front=((14, 18), (15, 23), (16, 28)),
               arm_back=((10, 13), (13, 16), (17, 17)),
               arm_front=((17, 12), (19, 15), (20, 17)),
               cannon_pos=(20, 12), cannon_angle=8)
    return render(remap(o), w=CELL, h=CELL)


def pose_death_1():
    o = Ops()
    build_base(o, body_dx=-2, body_dy=1, head_dx=-1, head_dy=-1,
               leg_back=((9, 19), (8, 24), (6, 28)),
               leg_front=((13, 19), (16, 24), (17, 25)),
               arm_back=((8, 14), (7, 17), (9, 19)),
               arm_front=((14, 13), (12, 16), (13, 19)),
               cannon_pos=(14, 12), cannon_angle=40)
    return render(remap(o), M.T_shear(0.14, 20), w=CELL, h=CELL)


def pose_death_2():
    """Down on one knee, cannon dropped."""
    o = Ops()
    build_base(o, body_dy=4, head_dy=1,
               leg_back=((13, 22), (17, 25), (20, 28)),
               leg_front=((15, 22), (16, 26), (11, 28)),
               arm_back=((10, 16), (12, 19), (15, 20)),
               arm_front=((16, 15), (18, 18), (19, 20)),
               cannon_pos=None)
    g = render(remap(o), w=CELL, h=CELL)
    # dropped cannon on the floor
    o2 = Ops()
    o2.rect(21, 27, 29, 28, 'G')
    o2.rect(21, 27, 26, 27, 'T')
    o2.rect(21, 28, 22, 29, 'N')
    g2 = render(remap(o2), w=CELL, h=CELL)
    for (x, y), c in g2.px.items():
        g.set(x, y, c)
    return g


def pose_death_3():
    """Falling backward."""
    o = Ops()
    build_base(o,
               leg_back=((10, 18), (10, 23), (8, 28)),
               leg_front=((14, 18), (14, 23), (15, 28)),
               arm_back=((10, 13), (13, 16), (17, 17)),
               arm_front=((17, 12), (19, 15), (20, 16)),
               cannon_pos=(19, 10))
    tf = T_chain(T_rot(-40, 12.0, 27.0, 0.80), T_shift(2.0, 0.0))
    return render(remap(o), tf, w=CELL, h=CELL)


def pose_death_4():
    """On the ground."""
    o = Ops()
    o.rect(6, 24, 20, 28, 'B')          # torso on the floor
    o.rect(7, 23, 18, 24, 'C')
    o.rect(6, 27, 20, 28, 'D')
    o.rect(3, 22, 9, 27, 'B')            # helm
    o.rect(4, 22, 8, 22, 'L')
    o.rect(3, 24, 4, 26, 'V')            # visor
    o.rect(3, 24, 3, 25, 'W')
    o.rect(19, 25, 25, 27, 'D')          # legs
    o.rect(20, 27, 22, 28, 'C')
    o.rect(24, 26, 27, 28, 'G')         # dropped cannon
    o.rect(24, 26, 27, 26, 'T')
    return render(remap(o), w=CELL, h=CELL)


def build_frames():
    return [pose_idle_1(), pose_idle_2(), pose_walk(1), pose_walk(2),
            pose_walk(3), pose_walk(4), pose_attack_1(), pose_attack_2(),
            pose_attack_3(), pose_death_1(), pose_death_2(), pose_death_3(),
            pose_death_4()]


FRAME_SPEC = [
    ('idle', 1), ('idle', 2),
    ('walk', 1), ('walk', 2), ('walk', 3), ('walk', 4),
    ('attack', 1), ('attack', 2), ('attack', 3),
    ('death', 1), ('death', 2), ('death', 3), ('death', 4),
]
