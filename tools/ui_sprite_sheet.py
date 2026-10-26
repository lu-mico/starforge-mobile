#!/usr/bin/env python3
"""
Starforge-mobile — UI art batch (docs/ASSET_UI_SPEC.md §3).

  card icons      4 x 64x64   (icon_marine / icon_marauder / icon_hellion / icon_siege_tank)
  card frame      1 x 48x64   9-slice, patch_margin 10px on all sides
  mineral icons   2           (16x16 and 32x32, hand-simplified, not rescaled)
  card badges     3 x 12x12   (cost / count / frame plates, opaque base)

Rules honoured here:
  * icon body height <= 40px and identical across the four icons (§3.1)
  * the 9-slice centre region (28x44) is a single flat colour, the left/right
    bands vary only in x and the top/bottom bands only in y, so stretching
    never produces a seam (§3.2)
  * 16px mineral is drawn by hand, not downscaled (§3.3)
  * badge bases are fully opaque (§3.4)
  * global 16-colour palette, alpha only {0,255}
"""
import marine_sprite_sheet as M
from marine_sprite_sheet import Ops, Grid, T_identity, T_rot, T_shift, T_chain, render

ICON = 64
FRAME_W, FRAME_H = 48, 64
BADGE = 12


# ---------------------------------------------------------------- card frame

def card_frame():
    """48x64 9-slice card frame. patch_margin = 10 on every side -> 28x44 centre."""
    o = Ops()
    o.rect(0, 0, FRAME_W - 1, FRAME_H - 1, 'K')          # outer ink
    o.rect(1, 1, FRAME_W - 2, FRAME_H - 2, 'G')          # metal field
    # left/right bands: horizontal gradient only (safe to stretch vertically)
    for x in range(1, 10):
        col = 'D' if x < 3 else ('G' if x < 6 else 'T')
        o.rect(x, 1, x, FRAME_H - 2, col)
    for x in range(FRAME_W - 10, FRAME_W - 1):
        col = 'D' if x > FRAME_W - 4 else ('G' if x > FRAME_W - 7 else 'T')
        o.rect(x, 1, x, FRAME_H - 2, col)
    # top/bottom bands: vertical gradient only (safe to stretch horizontally)
    for y in range(1, 10):
        col = 'D' if y < 3 else ('G' if y < 6 else 'T')
        o.rect(1, y, FRAME_W - 2, y, col)
    for y in range(FRAME_H - 10, FRAME_H - 1):
        col = 'D' if y > FRAME_H - 4 else ('G' if y > FRAME_H - 7 else 'T')
        o.rect(1, y, FRAME_W - 2, y, col)
    # blue trim hugging the content area
    o.rect(9, 9, FRAME_W - 10, 9, 'B')
    o.rect(9, FRAME_H - 10, FRAME_W - 10, FRAME_H - 10, 'B')
    o.rect(9, 9, 9, FRAME_H - 10, 'B')
    o.rect(FRAME_W - 10, 9, FRAME_W - 10, FRAME_H - 10, 'B')
    # content region: one flat colour (28x44)
    o.rect(10, 10, FRAME_W - 11, FRAME_H - 11, 'C')
    # corner rivets
    for cx, cy in ((3, 3), (FRAME_W - 7, 3), (3, FRAME_H - 7), (FRAME_W - 7, FRAME_H - 7)):
        o.rect(cx, cy, cx + 3, cy + 3, 'T')
        o.rect(cx + 1, cy + 1, cx + 2, cy + 2, 'H')
    return o


# ---------------------------------------------------------------- mineral

def mineral_32():
    """Faceted crystal, 32x32."""
    o = Ops()
    o.poly([(16, 1), (26, 13), (22, 30), (10, 30), (6, 13)], 'G')     # body
    o.poly([(16, 1), (26, 13), (16, 30)], 'T')                       # right facet
    o.poly([(16, 1), (6, 13), (16, 30)], 'H')                        # left facet
    o.poly([(6, 13), (26, 13), (16, 30)], 'C')                       # lower facets
    o.poly([(16, 2), (19, 8), (16, 12), (13, 8)], 'R')               # glint
    o.rect(10, 30, 21, 31, 'S')                                      # base shadow
    return o


def mineral_16():
    """Hand-simplified 16x16 crystal: 3 colours, no 1px detail."""
    o = Ops()
    o.poly([(8, 0), (13, 6), (11, 14), (5, 14), (3, 6)], 'G')
    o.poly([(8, 0), (13, 6), (8, 14)], 'T')
    o.poly([(8, 0), (3, 6), (8, 14)], 'H')
    o.rect(4, 15, 11, 15, 'S')
    return o


# ---------------------------------------------------------------- badges

def badge_coin():
    """Cost badge: a metal coin disc, opaque."""
    o = Ops()
    o.rect(1, 0, BADGE - 2, BADGE - 1, 'D')      # round-ish silhouette
    o.rect(0, 1, BADGE - 1, BADGE - 2, 'D')
    o.rect(2, 1, BADGE - 3, BADGE - 2, 'G')
    o.rect(1, 2, BADGE - 2, BADGE - 3, 'G')
    o.rect(3, 2, BADGE - 4, BADGE - 3, 'T')
    o.rect(2, 3, BADGE - 3, BADGE - 4, 'T')
    o.rect(4, 4, BADGE - 5, BADGE - 5, 'W')
    o.rect(5, 5, BADGE - 6, BADGE - 6, 'V')
    return o


def badge_count():
    """Count badge: a square plate with a bright inner field."""
    o = Ops()
    o.rect(0, 0, BADGE - 1, BADGE - 1, 'K')
    o.rect(1, 1, BADGE - 2, BADGE - 2, 'B')
    o.rect(2, 2, BADGE - 3, BADGE - 3, 'L')
    o.rect(3, 3, BADGE - 4, BADGE - 4, 'C')
    return o


def badge_frame():
    """Frame badge: a corner bracket plate, opaque."""
    o = Ops()
    o.rect(0, 0, BADGE - 1, BADGE - 1, 'K')
    o.rect(1, 1, BADGE - 2, BADGE - 2, 'C')
    o.rect(1, 1, BADGE - 2, 2, 'B')
    o.rect(1, 1, 2, BADGE - 2, 'B')
    o.rect(1, 3, 2, 3, 'L')
    o.rect(3, 1, 3, 1, 'L')
    return o


# ---------------------------------------------------------------- card icons

TOP, BOT = 12, 49          # icon body band: 38px tall (<= 40, identical)


def icon_marine():
    """Marine bust: blue helm, orange visor, rifle across the chest."""
    o = Ops()
    # torso
    o.rect(16, 30, 47, BOT, 'B')
    o.rect(16, 30, 47, 32, 'L')
    o.rect(16, 44, 47, BOT, 'D')
    o.rect(19, 34, 30, 42, 'C')
    o.rect(19, 34, 30, 35, 'L')
    # pauldron
    o.rect(38, 26, 50, 33, 'L')
    o.rect(38, 26, 50, 27, 'H')
    o.rect(40, 34, 50, 36, 'B')
    # neck
    o.rect(24, 29, 32, 33, 'D')
    # helm
    o.rect(20, TOP + 2, 40, 30, 'B')
    o.rect(18, TOP + 6, 40, 30, 'B')
    o.rect(22, TOP, 36, TOP + 1, 'L')
    o.rect(22, TOP, 36, TOP, 'H')
    o.rect(31, TOP + 7, 38, TOP + 13, 'V')     # visor
    o.rect(35, TOP + 7, 38, TOP + 9, 'W')
    o.rect(24, 27, 39, 29, 'D')                # jaw
    o.rect(22, 20, 24, 26, 'D')                # back shade
    # rifle across the chest
    o.rect(14, 36, 52, 39, 'G')
    o.rect(14, 36, 52, 36, 'T')
    o.rect(50, 35, 53, 40, 'C')
    o.rect(24, 39, 27, 45, 'N')
    o.rect(30, 39, 33, 43, 'S')
    return o


def icon_marauder():
    """Marauder bust: steel armour, shoulder cannon."""
    o = Ops()
    o.rect(14, 30, 48, BOT, 'G')
    o.rect(14, 30, 48, 32, 'T')
    o.rect(14, 44, 48, BOT, 'S')
    o.rect(17, 34, 29, 42, 'C')
    o.rect(17, 34, 29, 35, 'T')
    o.rect(38, 24, 52, 33, 'T')                # big pauldron
    o.rect(38, 24, 52, 25, 'R')
    o.rect(40, 34, 52, 37, 'G')
    o.rect(24, 29, 32, 33, 'S')
    o.rect(20, TOP + 2, 40, 30, 'G')
    o.rect(18, TOP + 6, 40, 30, 'G')
    o.rect(22, TOP, 36, TOP + 1, 'T')
    o.rect(22, TOP, 36, TOP, 'R')
    o.rect(31, TOP + 7, 38, TOP + 13, 'V')
    o.rect(35, TOP + 7, 38, TOP + 9, 'W')
    o.rect(24, 27, 39, 29, 'S')
    # shoulder cannon over the right shoulder
    o.rect(44, 16, 62, 23, 'G')
    o.rect(44, 16, 62, 16, 'T')
    o.rect(58, 14, 63, 25, 'C')
    o.rect(42, 18, 46, 22, 'D')
    return o


def icon_hellion():
    """Hellion bust: skimmer hull + gunner + chin gun."""
    o = Ops()
    # hull wedge
    o.rect(8, 32, 54, 46, 'G')
    o.rect(8, 32, 54, 34, 'T')
    o.poly([(54, 32), (60, 38), (60, 46), (54, 46)], 'G')
    o.poly([(54, 32), (60, 38), (60, 40), (54, 34)], 'T')
    o.rect(8, 43, 60, 46, 'S')
    o.rect(12, 35, 40, 37, 'B')
    o.rect(12, 35, 40, 35, 'L')
    # gunner
    o.rect(20, 12, 36, 32, 'B')
    o.rect(20, 12, 36, 14, 'L')
    o.rect(24, 16, 36, 26, 'G')
    o.rect(26, 18, 36, 24, 'V')
    o.rect(33, 18, 36, 20, 'W')
    o.rect(22, 28, 34, 31, 'D')
    # chin gun
    o.rect(36, 29, 60, 32, 'G')
    o.rect(36, 29, 60, 29, 'T')
    o.rect(58, 27, 61, 34, 'C')
    # hover pods
    o.rect(12, 47, 22, 49, 'G')
    o.rect(38, 47, 48, 49, 'G')
    return o


def icon_siege_tank():
    """Siege Tank bust: turret + heavy barrel + hull front."""
    o = Ops()
    # hull
    o.rect(6, 34, 58, 46, 'G')
    o.rect(6, 34, 58, 36, 'T')
    o.rect(6, 43, 58, 46, 'S')
    o.rect(10, 38, 34, 40, 'B')
    o.rect(10, 38, 34, 38, 'L')
    # turret
    o.rect(14, 16, 44, 36, 'G')
    o.rect(14, 16, 44, 20, 'T')
    o.rect(14, 32, 44, 36, 'C')
    o.rect(18, 24, 30, 29, 'C')
    o.rect(18, 24, 30, 25, 'T')
    o.rect(20, 12, 32, 17, 'C')        # cupola
    o.rect(20, 12, 32, 12, 'T')
    # barrel
    o.rect(40, 22, 62, 27, 'G')
    o.rect(40, 22, 62, 22, 'T')
    o.rect(58, 20, 63, 29, 'C')
    # track
    o.rect(8, 46, 56, 49, 'S')
    for x in range(12, 56, 8):
        o.rect(x, 45, x + 3, 48, 'G')
    return o


# ---------------------------------------------------------------- registry

UI_ITEMS = [
    ("icon_marine", icon_marine, ICON, ICON),
    ("icon_marauder", icon_marauder, ICON, ICON),
    ("icon_hellion", icon_hellion, ICON, ICON),
    ("icon_siege_tank", icon_siege_tank, ICON, ICON),
    ("card_frame", card_frame, FRAME_W, FRAME_H),
    ("icon_mineral_32", mineral_32, 32, 32),
    ("icon_mineral_16", mineral_16, 16, 16),
    ("card_badge_cost", badge_coin, BADGE, BADGE),
    ("card_badge_count", badge_count, BADGE, BADGE),
    ("card_badge_frame", badge_frame, BADGE, BADGE),
]


def build_images():
    out = []
    for name, fn, w, h in UI_ITEMS:
        g = render(fn(), w=w, h=h)
        g.outline()
        out.append((name, g.to_image(), w, h))
    return out


def build_grids():
    out = []
    for name, fn, w, h in UI_ITEMS:
        g = render(fn(), w=w, h=h)
        g.outline()
        out.append(g)
    return out
