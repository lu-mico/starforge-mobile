#!/usr/bin/env python3
"""
Starforge-mobile — Siege Tank sprite sheet (48x48 cells, 13 frames).

Same delivery contract as the Marine (see docs/ASSET_OUTSOURCING_BRIEF.md §2.1):
  idle 2 / walk 4 / attack 3 / death 4, right-facing only, transparent background,
  hard pixel edges, palette shared with the Marine sheet (max 16 colours total),
  single PNG == strip cell == grid cell (byte-identical, enforced by verify).

Drawing primitives are imported from marine_sprite_sheet so both units share
one pipeline (and one palette).
"""
import math

from marine_sprite_sheet import (CELL, GUT, Ops, PAL, Grid, T_identity, T_rot, T_shift,
                                 T_chain, fill_poly, render)

TCELL = 48
STATE_FPS = {"idle": 2, "walk": 6, "attack": 8, "death": 4}
STATE_LOOP = {"idle": True, "walk": True, "attack": False, "death": False}


# ---------------------------------------------------------------- parts

def track(g, x0, x1, y0, y1, phase=0, wheels=5):
    """Side-view tread band with road wheels and a 4-phase tread pattern."""
    g.rect(x0, y0, x1, y1, 'S')                 # band
    g.rect(x0, y0, x1, y0 + 1, 'G')             # top rail
    g.rect(x0, y1 - 1, x1, y1, 'K')             # bottom shadow
    # road wheels
    span = (x1 - x0)
    for i in range(wheels):
        wx = x0 + 3 + round(i * (span - 6) / max(wheels - 1, 1))
        wy = (y0 + y1) // 2 + 1
        g.rect(wx - 2, wy - 2, wx + 2, wy + 1, 'G')
        g.rect(wx - 1, wy - 1, wx + 1, wy, 'T')
        g.set(wx, wy - 1, 'H')
    # tread notches shift with the walk phase
    step = 6
    for i in range(-1, span // step + 2):
        tx = x0 + (i * step + phase * (step // 4)) % (span)
        g.rect(tx, y0 + 1, tx, y1 - 1, 'K')


def hull(g, x0, x1, top, bottom, dy=0):
    """Main hull with a sloped front (right side)."""
    top += dy
    bottom += dy
    g.rect(x0, top, x1 - 3, bottom, 'G')        # hull body
    g.rect(x0 + 1, top + 1, x1 - 3, top + 2, 'T')   # deck highlight
    g.rect(x0, bottom - 2, x1 - 3, bottom, 'C')     # lower shade
    # sloped glacis
    g.poly([(x1 - 3, top), (x1, top + 4), (x1, bottom), (x1 - 3, bottom)], 'G')
    g.poly([(x1 - 3, top), (x1, top + 4), (x1, top + 5), (x1 - 3, top + 1)], 'T')
    g.rect(x0 - 1, top, x0, bottom, 'C')        # rear plate
    # side skirt / armour ribs
    for i in range(3):
        rx = x0 + 3 + i * 7
        g.rect(rx, top + 3, rx + 1, bottom - 3, 'C')
    # player-blue stripe along the hull side
    g.rect(x0 + 2, top + 4, x1 - 6, top + 5, 'B')
    g.rect(x0 + 2, top + 4, x1 - 6, top + 4, 'L')


def turret(g, x0, x1, base, top, dy=0, tilt=0):
    """Trapezoid turret, wider at the base, with a commander's hatch."""
    base += dy
    top += dy
    if tilt:
        # skewed turret for the death frames
        g.poly([(x0, base), (x1 - 2, base), (x1, top + 2), (x0 + 1, top)], 'G')
        g.poly([(x0 + 1, base - 1), (x1 - 2, base - 1), (x1 - 1, top + 2), (x0 + 2, top + 1)], 'T')
    else:
        g.poly([(x0, base), (x1, base), (x1 - 2, top), (x0 + 2, top)], 'G')
        g.poly([(x0 + 1, base - 1), (x1 - 1, base - 1), (x1 - 2, top + 1), (x0 + 2, top + 1)], 'T')
    g.rect(x0 + 3, top - 2, x0 + 7, top, 'C')    # hatch
    g.rect(x0 + 4, top - 2, x0 + 6, top - 2, 'G')


def gun(g, x0, x1, y, dy=0, muzzle=False):
    """Main cannon barrel pointing RIGHT; returns muzzle x."""
    y += dy
    g.rect(x0, y, x1, y + 2, 'T')
    g.rect(x0, y, x1, y, 'H')
    g.rect(x1 - 1, y - 1, x1 + 1, y + 3, 'G')    # muzzle brake
    if muzzle:
        fx = x1 + 2
        for dx, dy2, c in ((0, 0, 'X'), (-1, 0, 'F'), (1, 0, 'F'), (0, -1, 'F'),
                           (0, 1, 'F'), (2, -1, 'F'), (2, 1, 'F'), (3, 0, 'X')):
            g.px(fx + dx, y + 1 + dy2, c)
        return fx
    return x1


def exhaust(g, x, y, hot=False):
    g.rect(x, y, x + 2, y + 3, 'C')
    if hot:
        g.rect(x, y, x + 2, y + 1, 'V')
        g.rect(x + 1, y, x + 1, y, 'W')


def dust(g, x, y, n=4):
    """Kicked-up grit behind the tracks (drawn as ops so it stays in the cell)."""
    for i in range(n):
        g.set(x + i * 2, y - (i % 2), 'G')


def smoke(g, x, y, n=5):
    """Exhaust smoke column (drawn as ops so it stays in the cell)."""
    for i in range(n):
        g.rect(x + (i % 2) * 2, y - i, x + (i % 2) * 2 + 1, y - i, 'S' if i < 3 else 'C')


def fire(g, spots):
    """Burning patches on the wreck."""
    for x, y in spots:
        g.rect(x, y, x + 1, y + 1, 'V')
        g.set(x, y, 'W')


# ---------------------------------------------------------------- unit

def build_tank(g, *, hull_dx=0, hull_dy=0, turret_dy=0, gun_dy=0, gun_dx=0,
               phase=0, muzzle=False, tread=True, turret_tilt=0,
               hot_exhaust=False, dead=False, gun_broken=False):
    gx = hull_dx
    gy = hull_dy
    if tread:
        track(g, 5 + gx, 43 + gx, 35 + gy, 45 + gy, phase=phase)
    hull(g, 7 + gx, 41 + gx, 27 + gy, 35 + gy, dy=0)
    turret(g, 18 + gx, 30 + gx, 27 + gy, 18 + gy, dy=turret_dy, tilt=turret_tilt)
    exhaust(g, 8 + gx, 23 + gy, hot=hot_exhaust)
    # barrel
    bx0, bx1 = 28 + gx + gun_dx, 41 + gx + gun_dx
    if gun_broken:
        g.rect(bx0, 20 + gun_dy, bx0 + 4, 22 + gun_dy, 'T')
        g.rect(bx0, 20 + gun_dy, bx0 + 4, 20 + gun_dy, 'H')
    else:
        gun(g, bx0, bx1, 20 + gun_dy, muzzle=muzzle)
    if dead:
        # charred wreck details
        g.rect(10 + gx, 29 + gy, 18 + gx, 33 + gy, 'S')
        g.rect(26 + gx, 28 + gy, 30 + gx, 31 + gy, 'S')
    return g


def render_tank(dust_spec=None, smoke_spec=None, fire_spots=None, **kw):
    o = Ops()
    build_tank(o, **kw)
    if smoke_spec:
        smoke(o, *smoke_spec)
    if dust_spec:
        dust(o, *dust_spec)
    if fire_spots:
        fire(o, fire_spots)
    return render(o, w=TCELL, h=TCELL)


# ---------------------------------------------------------------- frames

def f_idle_1():
    return render_tank(phase=0)


def f_idle_2():
    return render_tank(phase=2, turret_dy=-1, hot_exhaust=True)


def f_walk(phase):
    dy = -1 if phase in (1, 3) else 0
    return render_tank(phase=phase, hull_dy=dy, turret_dy=dy)


def f_attack_1():
    g = render_tank(hull_dx=-1, phase=0, muzzle=True)
    return g


def f_attack_2():
    return render_tank(hull_dx=-2, hull_dy=1, turret_dy=-1, gun_dy=-2, phase=1,
                       dust_spec=(6, 42, 4))


def f_attack_3():
    return render_tank(hull_dx=1, hull_dy=1, gun_dy=2, phase=2,
                       dust_spec=(8, 43, 5))


def f_death_1():
    """Turret blown off, hull lurching back."""
    return render_tank(hull_dx=-2, hull_dy=1, gun_broken=True, turret_tilt=1,
                       smoke_spec=(20, 14, 4))


def f_death_2():
    """Hull slumping forward, turret detached."""
    return render_tank(hull_dx=1, hull_dy=1, gun_broken=True, turret_tilt=1,
                       smoke_spec=(22, 12, 5))


def f_death_3():
    """Burning wreck."""
    return render_tank(hull_dx=0, hull_dy=1, gun_broken=True, turret_tilt=1, dead=True,
                       smoke_spec=(24, 12, 6),
                       fire_spots=((14, 30), (20, 28), (27, 31)))


def f_death_4():
    """Flattened wreck on the ground."""
    g = Grid(TCELL, TCELL)
    o = Ops()
    # squashed hull
    o.rect(8, 36, 34, 43, 'G')
    o.rect(9, 36, 32, 37, 'T')
    o.rect(8, 41, 34, 43, 'S')
    o.rect(12, 34, 20, 36, 'C')      # detached turret lying flat
    o.rect(13, 34, 19, 34, 'T')
    o.rect(26, 37, 30, 40, 'S')
    o.rect(15, 39, 18, 40, 'V')
    o.rect(15, 39, 15, 39, 'W')
    o.rect(35, 38, 38, 39, 'T')      # dropped barrel
    o.rect(35, 38, 38, 38, 'H')
    return render(o, w=TCELL, h=TCELL)


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
