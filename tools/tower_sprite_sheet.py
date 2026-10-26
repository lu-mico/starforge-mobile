#!/usr/bin/env python3
"""
Starforge-mobile — tower sprites (40x60, 6 images).

brief §2.2: player tower / enemy tower / king tower, each in 2 states
(intact / damaged) = 6 images. Transparent background, hard pixel edges,
same global 16-colour palette as the unit sheets.

Towers are static art (no animation), so this module ships a named list of
images rather than an animation frame table.
"""
import marine_sprite_sheet as M
from marine_sprite_sheet import (Ops, Grid, T_identity, T_rot, T_shift, T_chain,
                                 fill_poly, render)

W, H = 40, 60

# accent colours per side: player = blue, enemy = orange, king = blue + gold-ish rim
ACCENT = {
    "player": ("B", "L", "H"),
    "enemy": ("V", "W", "F"),
    "king": ("B", "L", "R"),
}


def body(g, x0, x1, top, bottom, accent, dark='S'):
    """Tapered tower body with buttresses and a glowing core strip."""
    mid = (x0 + x1) // 2
    g.poly([(x0, bottom), (x0 + 3, top), (x1 - 3, top), (x1, bottom)], 'G')
    g.poly([(x0 + 1, bottom - 1), (x0 + 4, top + 1), (x1 - 4, top + 1), (x1 - 1, bottom - 1)], 'T')
    g.rect(x0, bottom - 2, x1, bottom, dark)          # base shadow
    # side buttresses
    g.rect(x0 - 3, bottom - 14, x0, bottom, 'C')
    g.rect(x1, bottom - 14, x1 + 3, bottom, 'C')
    g.rect(x0 - 3, bottom - 14, x0 - 3, bottom - 12, 'G')
    g.rect(x1 + 3, bottom - 14, x1 + 3, bottom - 12, 'G')
    # core strip
    g.rect(mid - 2, top + 5, mid + 2, bottom - 4, accent[0])
    g.rect(mid - 1, top + 6, mid + 1, bottom - 5, accent[1])
    g.rect(mid - 1, top + 6, mid + 1, top + 7, accent[2])
    # panel seams
    for yy in (top + 12, top + 20, bottom - 8):
        g.rect(x0 + 5, yy, x1 - 5, yy, 'C')


def turret(g, cx, top, accent, barrel=True, tilt=0):
    """Gun turret on top of the tower."""
    if tilt:
        g.poly([(cx - 7, top + 2), (cx + 7, top), (cx + 6, top + 11), (cx - 8, top + 12)], 'G')
        g.poly([(cx - 6, top + 3), (cx + 6, top + 1), (cx + 5, top + 5), (cx - 6, top + 6)], 'T')
    else:
        g.rect(cx - 7, top, cx + 7, top + 11, 'G')
        g.rect(cx - 6, top + 1, cx + 6, top + 4, 'T')
        g.rect(cx - 7, top + 10, cx + 7, top + 11, 'C')
    g.rect(cx - 3, top + 5, cx + 3, top + 8, accent[0])
    g.rect(cx - 2, top + 5, cx + 2, top + 6, accent[1])
    if barrel:
        if tilt:
            g.poly([(cx + 6, top + 3), (cx + 15, top - 1), (cx + 15, top + 3), (cx + 6, top + 6)], 'G')
            g.poly([(cx + 6, top + 3), (cx + 15, top - 1), (cx + 15, top + 1), (cx + 6, top + 4)], 'T')
        else:
            g.rect(cx + 6, top + 2, cx + 15, top + 5, 'G')
            g.rect(cx + 6, top + 2, cx + 15, top + 2, 'T')
            g.rect(cx + 14, top + 1, cx + 16, top + 6, 'C')


def mast(g, cx, top, accent):
    """Antenna mast with a beacon (sits on the shoulder, not floating)."""
    g.rect(cx, top, cx + 1, top + 6, 'C')
    g.rect(cx, top, cx + 1, top + 1, accent[0])
    g.set(cx, top, accent[1])


def crystal(g, cx, top, accent):
    """King tower spire."""
    g.poly([(cx, top - 12), (cx + 5, top - 4), (cx, top + 4), (cx - 5, top - 4)], accent[0])
    g.poly([(cx, top - 10), (cx + 3, top - 4), (cx, top + 2), (cx - 3, top - 4)], accent[1])
    g.set(cx, top - 9, accent[2])


def damage(g, spots):
    """Bites out of the silhouette, cracks and scorch."""
    for x, y, w_, h_ in spots:
        g.rect(x, y, x + w_, y + h_, 'S')
    for x, y in ((12, 34), (24, 42), (16, 48), (26, 28)):
        g.rect(x, y, x + 3, y, 'K')
        g.rect(x + 3, y, x + 3, y + 2, 'K')
    g.rect(18, 20, 21, 22, 'S')


def smoke(g, x, y, n=4):
    for i in range(n):
        g.rect(x + (i % 2) * 2, y - i, x + (i % 2) * 2 + 1, y - i,
               'S' if i < 2 else 'C')


def build_tower(g, side="player", state="intact", king=False):
    accent = ACCENT["king" if king else side]
    if king:
        x0, x1, top, bottom = 6, 33, 20, 56
    else:
        x0, x1, top, bottom = 9, 30, 24, 56
    # plinth
    g.rect(x0 - 4, bottom, x1 + 4, 58, 'C')
    g.rect(x0 - 4, bottom, x1 + 4, bottom + 1, 'G')
    g.rect(x0 - 2, bottom + 2, x1 + 2, 57, 'S')
    body(g, x0, x1, top, bottom, accent)
    if king:
        crystal(g, (x0 + x1) // 2, top, accent)
        turret(g, (x0 + x1) // 2, top + 7, accent)
        mast(g, x1 - 2, top + 9, accent)
    else:
        turret(g, (x0 + x1) // 2, top - 8, accent)
        mast(g, x0 + 1, top + 5, accent)
    if state == "damaged":
        if king:
            damage(g, ((8, 34, 3, 6), (28, 44, 4, 5), (14, 26, 2, 3)))
        else:
            damage(g, ((11, 36, 3, 5), (26, 44, 3, 4), (16, 28, 2, 2)))
        smoke(g, 24, 22, 4)
    return g


def render_tower(**kw):
    o = Ops()
    build_tower(o, **kw)
    return render(o, w=W, h=H)


TOWERS = [
    ("player_tower_intact", dict(side="player", state="intact")),
    ("player_tower_damaged", dict(side="player", state="damaged")),
    ("enemy_tower_intact", dict(side="enemy", state="intact")),
    ("enemy_tower_damaged", dict(side="enemy", state="damaged")),
    ("king_tower_intact", dict(side="player", state="intact", king=True)),
    ("king_tower_damaged", dict(side="player", state="damaged", king=True)),
]


def build_grids():
    out = []
    for name, kw in TOWERS:
        g = render_tower(**kw)
        g.outline()
        out.append(g)
    return out


def build_images():
    return [(name, g.to_image()) for (name, _), g in zip(TOWERS, build_grids())]


# QA shim so tools/sprite_qa.py can validate this module like a unit
FRAME_SPEC = [("tower", i + 1) for i in range(6)]


def build_frames():
    return build_grids()
