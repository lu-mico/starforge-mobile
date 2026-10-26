#!/usr/bin/env python3
"""
Starforge-mobile — Hellion sprite sheet (32x32 cells, 13 frames).

Fast hover scout: a small open-frame skimmer with a gunner, a chin-mounted
gun and thruster pods. Same 13-frame contract as the other units
(idle 2 / walk 4 / attack 3 / death 4, right-facing, transparent background),
same global 16-colour palette, same primitives.

"walk" for a hover unit = thruster pulse + chassis bob (no treads).
"""
import marine_sprite_sheet as M
from marine_sprite_sheet import (CELL, Ops, Grid, T_identity, T_rot, T_shift, T_chain,
                                 fill_poly, render)

STATE_FPS = {"idle": 2, "walk": 6, "attack": 8, "death": 4}
STATE_LOOP = {"idle": True, "walk": True, "attack": False, "death": False}


# ---------------------------------------------------------------- parts

def thruster(g, x, y, hot=False):
    """Rear thruster nozzle."""
    g.rect(x, y, x + 2, y + 3, 'C')
    g.rect(x, y + 3, x + 2, y + 4, 'S')
    if hot:
        g.rect(x, y + 4, x + 2, y + 5, 'V')
        g.set(x + 1, y + 4, 'W')


def pod(g, x, y, hot=False):
    """Hover pod under the chassis."""
    g.rect(x, y, x + 4, y + 2, 'G')
    g.rect(x, y, x + 4, y, 'T')
    g.rect(x + 1, y + 2, x + 3, y + 3, 'S')
    if hot:
        g.rect(x + 1, y + 3, x + 3, y + 3, 'F')


def hull(g, x0, x1, top, bottom):
    """Chassis with a sloped nose (right)."""
    g.rect(x0, top, x1 - 3, bottom, 'G')
    g.rect(x0 + 1, top + 1, x1 - 3, top + 2, 'T')
    g.poly([(x1 - 3, top), (x1, top + 2), (x1, bottom), (x1 - 3, bottom)], 'G')
    g.poly([(x1 - 3, top), (x1, top + 2), (x1, top + 3), (x1 - 3, top + 1)], 'T')
    g.rect(x0, bottom - 1, x1 - 3, bottom, 'S')          # belly shadow
    g.rect(x0, top + 2, x1 - 4, top + 3, 'B')             # player stripe
    g.rect(x0, top + 2, x1 - 4, top + 2, 'L')
    g.rect(x0 - 1, top, x0, bottom, 'C')                  # rear plate
    for i in range(3):                                    # vents
        vx = x0 + 3 + i * 5
        g.rect(vx, top + 1, vx + 1, top + 1, 'C')


def canopy(g, x0, x1, top, bottom):
    """Gunner compartment."""
    g.rect(x0, top, x1, bottom, 'C')
    g.rect(x0 + 1, top + 1, x1 - 1, top + 1, 'G')
    g.rect(x0, bottom, x1, bottom, 'S')


def head(g, x, y):
    """Gunner helm, small, with an orange visor."""
    g.rect(x + 1, y, x + 4, y + 4, 'B')
    g.rect(x, y + 1, x + 1, y + 4, 'B')
    g.rect(x + 1, y, x + 4, y, 'L')
    g.rect(x + 3, y + 1, x + 4, y + 3, 'V')
    g.set(x + 4, y + 1, 'W')
    g.rect(x + 1, y + 4, x + 4, y + 4, 'D')


def gun(g, x0, x1, y, dy=0, muzzle=False):
    """Chin gun pointing RIGHT; returns muzzle x."""
    y += dy
    g.rect(x0, y, x1, y + 1, 'G')
    g.rect(x0, y, x1, y, 'T')
    g.rect(x1, y - 1, x1 + 1, y + 2, 'C')
    mx = x1 + 2
    if muzzle:
        for dx, dy2, col in ((0, 0, 'X'), (-1, 0, 'F'), (1, 0, 'F'), (0, -1, 'F'),
                             (0, 1, 'F'), (2, -1, 'F'), (2, 1, 'F')):
            g.set(mx + dx, y + dy2, col)
    return mx


def smoke(g, x, y, n=4):
    for i in range(n):
        g.rect(x + (i % 2) * 2, y - i, x + (i % 2) * 2 + 1, y - i,
               'S' if i < 2 else 'C')


def fire(g, spots):
    for x, y in spots:
        g.rect(x, y, x + 1, y + 1, 'V')
        g.set(x, y, 'W')


# ---------------------------------------------------------------- unit

def build_hellion(g, *, dx=0, dy=0, phase=0, hot=False, muzzle=False,
                   gun_dy=0, tilt=0, dead=False, wreck=False):
    x = dx
    y = dy
    if not wreck:
        pod(g, 8 + x, 24 + y, hot=hot and phase % 2 == 0)
        pod(g, 17 + x, 24 + y, hot=hot and phase % 2 == 1)
        hull(g, 6 + x, 27 + x, 18 + y, 23 + y)
        canopy(g, 12 + x, 19 + x, 12 + y, 18 + y)
        head(g, 14 + x, 8 + y)
        thruster(g, 4 + x, 15 + y, hot=hot)
        mx = gun(g, 19 + x, 26 + x, 12 + y + gun_dy, muzzle=muzzle)
    else:
        # flattened wreck
        g.rect(5, 24, 22, 28, 'G')
        g.rect(6, 24, 19, 25, 'T')
        g.rect(5, 27, 22, 28, 'S')
        g.rect(9, 22, 14, 24, 'C')       # broken canopy
        g.rect(23, 25, 28, 26, 'G')      # gun flung clear
        g.rect(23, 25, 28, 25, 'T')
        g.rect(6, 25, 8, 26, 'V')
        g.rect(6, 25, 6, 25, 'W')
    return g


def render_hellion(**kw):
    o = Ops()
    build_hellion(o, **kw)
    return render(o, w=CELL, h=CELL)


# ---------------------------------------------------------------- frames

def f_idle_1():
    return render_hellion(phase=0, hot=False)


def f_idle_2():
    return render_hellion(dy=-1, phase=1, hot=True)


def f_walk(phase):
    dy = -1 if phase in (1, 3) else 0
    return render_hellion(dy=dy, phase=phase, hot=True)


def f_attack_1():
    return render_hellion(dx=-1, phase=0, muzzle=True)


def f_attack_2():
    return render_hellion(dx=-2, dy=1, gun_dy=-1, phase=1)


def f_attack_3():
    return render_hellion(dx=1, dy=1, gun_dy=1, phase=2)


def f_death_1():
    """Lurching back, gun drooping."""
    o = Ops()
    build_hellion(o, dx=-2, dy=1, phase=0, gun_dy=2)
    smoke(o, 8, 12, 3)
    return render(o, w=CELL, h=CELL)


def f_death_2():
    """Tipping over, gunner thrown clear."""
    o = Ops()
    build_hellion(o, dx=1, dy=1, phase=1, gun_dy=3)
    smoke(o, 10, 11, 4)
    return render(o, w=CELL, h=CELL)


def f_death_3():
    """Burning hulk."""
    o = Ops()
    build_hellion(o, dx=0, dy=1, phase=2, gun_dy=3)
    smoke(o, 12, 11, 5)
    fire(o, ((7, 20), (14, 19), (20, 21)))
    return render(o, w=CELL, h=CELL)


def f_death_4():
    """Wreck on the ground."""
    o = Ops()
    build_hellion(o, wreck=True)
    return render(o, w=CELL, h=CELL)


def build_frames():
    return [f_idle_1(), f_idle_2(), f_walk(0), f_walk(1), f_walk(2), f_walk(3),
            f_attack_1(), f_attack_2(), f_attack_3(),
            f_death_1(), f_death_2(), f_death_3(), f_death_4()]


FRAME_SPEC = [
    ('idle', 1), ('idle', 2),
    ('walk', 1), ('walk', 2), ('walk', 3), ('walk', 4),
    ('attack', 1), ('attack', 2), ('attack', 3),
    ('death', 1), ('death', 2), ('death', 3), ('death', 4),
]
