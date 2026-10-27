#!/usr/bin/env python3
"""
Starforge-mobile — UI art batch (docs/ASSET_UI_SPEC.md §3).

  card icons      4 x 64x64   (icon_marine / icon_marauder / icon_hellion / icon_siege_tank)
  card frame      1 x 48x64   9-slice, patch_margin 10px on all sides
  mineral icons   2           (16x16 and 32x32, hand-simplified, not rescaled)
  card badges     3 x 12x12   (cost / count / frame plates, opaque base)

Rules honoured here:
  * icon body height <= 40px and identical across the four icons (§3.1).
    The bodies are authored so that AFTER the 1px ink ring is added the
    opaque bbox is exactly rows 12..51 (40px) and the widths are
    36 / 42 / 46 / 52 px (marine < marauder < hellion < tank), each
    horizontally centred with >= 6px of transparent margin per side.
  * the 9-slice centre region (28x44) is a single flat colour, the left/right
    bands vary only in x and the top/bottom bands only in y, so stretching
    never produces a seam (§3.2)
  * 16px mineral is drawn by hand, not downscaled (§3.3), uses 3 colours
    total (2 facets + the ink ring) and has no 1px-wide/tall detail
  * badge bases are fully opaque and carry a complete ink contour (§3.4)
  * global 16-colour palette, alpha only {0,255}
"""
import marine_sprite_sheet as M
from marine_sprite_sheet import Ops, Grid, T_identity, T_rot, T_shift, T_chain, render

ICON = 64
FRAME_W, FRAME_H = 48, 64
BADGE = 12

# Icon body band, BEFORE the 1px ink ring is added.  The ring grows the
# silhouette by exactly one pixel on every side, so the exported PNG ends up
# with an opaque bbox of rows 12..51 (40px tall, 12px margin top and bottom).
TOP, BOT = 13, 50

# The four card icons are drawn to these exact body widths (pre-ring), which
# makes the exported widths 36 / 42 / 46 / 52 px and keeps the intended
# ordering "Marine < Marauder < Hellion < Tank".
ICON_BODY_W = {
    "icon_marine": 34,
    "icon_marauder": 40,
    "icon_hellion": 44,
    "icon_siege_tank": 50,
}


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


# The 16px crystal is drawn row by row so the silhouette is explicit:
#   * every row is at least 2px tall/wide (no 1px detail survives the ring)
#   * the body sits inside x=2..13 / y=2..13, so the ink ring lands on
#     x=1..14 / y=1..14 and still leaves a transparent 1px margin
#   * only two facet colours are used (H light-blue left, T grey right);
#     with the ink ring that is 3 opaque colours in total
MINERAL_16_ROWS = [
    (2, 7, 8), (3, 6, 9), (4, 5, 10), (5, 4, 11), (6, 3, 12),
    (7, 2, 13), (8, 2, 13), (9, 3, 12), (10, 3, 12),
    (11, 4, 11), (12, 4, 11), (13, 5, 10),
]


def mineral_16():
    """Hand-simplified 16x16 crystal: 3 colours (2 facets + ink), no 1px detail."""
    o = Ops()
    for (y, x0, x1) in MINERAL_16_ROWS:
        o.rect(x0, y, x1, y, 'T')          # body / right facet
        o.rect(x0, y, 7, y, 'H')           # left facet (facet edge at x=7/8)
    return o


# ---------------------------------------------------------------- badges

def badge_coin():
    """Cost badge: a metal coin disc with a gold core, opaque.

    The whole 12x12 plate is first filled with ink, so every pixel on the
    canvas border is part of the contour and the badge can never bleed off
    the card corner.
    """
    o = Ops()
    o.rect(0, 0, BADGE - 1, BADGE - 1, 'K')       # complete ink contour
    o.rect(2, 1, 9, 1, 'D')                        # octagonal rim
    o.rect(1, 2, 10, 9, 'D')
    o.rect(2, 10, 9, 10, 'D')
    o.rect(3, 2, 8, 2, 'G')                        # coin face
    o.rect(2, 3, 9, 8, 'G')
    o.rect(3, 9, 8, 9, 'G')
    o.rect(4, 4, 7, 4, 'T')                        # inner ring
    o.rect(3, 5, 8, 6, 'T')
    o.rect(4, 7, 7, 7, 'T')
    o.rect(5, 5, 6, 6, 'W')                        # gold core
    o.rect(5, 5, 5, 5, 'V')                        # hot centre
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
#
# Every icon below is drawn so that its silhouette (before the ink ring) is
# exactly 38px tall (y = TOP..BOT) and exactly ICON_BODY_W pixels wide, and is
# horizontally centred on the 64px canvas.  Adding the 1px ink ring then
# yields the exported bbox: rows 12..51, widths 36 / 42 / 46 / 52, and
# symmetric margins of at least 6px.

def icon_marine():
    """Marine bust: blue helm, orange visor, rifle across the chest."""
    o = Ops()
    # torso (x 17..44)
    o.rect(17, 30, 44, BOT, 'B')
    o.rect(17, 30, 44, 32, 'L')
    o.rect(17, 44, 44, BOT, 'D')
    o.rect(20, 34, 31, 42, 'C')
    o.rect(20, 34, 31, 35, 'L')
    # pauldron (x 36..47)
    o.rect(36, 26, 47, 33, 'L')
    o.rect(36, 26, 47, 27, 'H')
    o.rect(38, 34, 47, 36, 'B')
    # neck
    o.rect(24, 29, 31, 33, 'D')
    # helm (x 19..39)
    o.rect(21, 15, 39, 30, 'B')
    o.rect(19, 19, 39, 30, 'B')
    o.rect(23, TOP, 35, TOP + 1, 'L')
    o.rect(23, TOP, 35, TOP, 'H')
    o.rect(31, 20, 38, 26, 'V')     # visor (faces right)
    o.rect(35, 20, 38, 22, 'W')
    o.rect(24, 27, 38, 29, 'D')      # jaw
    o.rect(23, 21, 25, 27, 'D')      # back shade
    # rifle across the chest (x 15..48)
    o.rect(15, 36, 45, 39, 'G')
    o.rect(15, 36, 45, 36, 'T')
    o.rect(43, 35, 48, 40, 'C')
    o.rect(23, 39, 26, 45, 'N')
    o.rect(29, 39, 32, 43, 'S')
    return o


def icon_marauder():
    """Marauder bust: steel armour, shoulder cannon."""
    o = Ops()
    # torso (x 12..42)
    o.rect(12, 30, 42, BOT, 'G')
    o.rect(12, 30, 42, 32, 'T')
    o.rect(12, 44, 42, BOT, 'S')
    o.rect(15, 34, 27, 42, 'C')
    o.rect(15, 34, 27, 35, 'T')
    # big pauldron (x 32..46)
    o.rect(32, 24, 46, 33, 'T')
    o.rect(32, 24, 46, 25, 'R')
    o.rect(34, 34, 46, 37, 'G')
    # neck
    o.rect(23, 29, 30, 33, 'S')
    # helm (x 18..37)
    o.rect(20, 15, 37, 30, 'G')
    o.rect(18, 19, 37, 30, 'G')
    o.rect(23, TOP, 34, TOP + 1, 'T')
    o.rect(23, TOP, 34, TOP, 'R')
    o.rect(30, 20, 37, 26, 'V')     # visor (faces right)
    o.rect(34, 20, 37, 22, 'W')
    o.rect(24, 27, 36, 29, 'S')
    # shoulder cannon over the right shoulder (x 35..51)
    o.rect(37, 16, 49, 23, 'G')
    o.rect(37, 16, 49, 16, 'T')
    o.rect(46, 15, 51, 24, 'C')
    o.rect(35, 18, 39, 22, 'D')
    return o


def icon_hellion():
    """Hellion bust: skimmer hull + gunner + chin gun."""
    o = Ops()
    # hull wedge (x 10..53)
    o.rect(10, 32, 45, 47, 'G')
    o.rect(10, 32, 45, 34, 'T')
    o.poly([(45, 32), (54, 38), (54, 47), (45, 47)], 'G')
    o.poly([(45, 32), (54, 38), (54, 40), (45, 34)], 'T')
    o.rect(10, 43, 53, 47, 'S')
    o.rect(13, 35, 36, 37, 'B')
    o.rect(13, 35, 36, 35, 'L')
    # gunner
    o.rect(19, TOP, 33, 32, 'B')
    o.rect(19, TOP, 33, 15, 'L')
    o.rect(23, 17, 33, 26, 'G')
    o.rect(25, 19, 33, 24, 'V')     # visor (faces right)
    o.rect(30, 19, 33, 21, 'W')
    o.rect(21, 28, 31, 31, 'D')
    # chin gun (x 33..51)
    o.rect(33, 29, 49, 32, 'G')
    o.rect(33, 29, 49, 29, 'T')
    o.rect(48, 27, 51, 34, 'C')
    # hover pods
    o.rect(12, 48, 20, 50, 'G')
    o.rect(33, 48, 41, 50, 'G')
    return o


def icon_siege_tank():
    """Siege Tank bust: turret + heavy barrel + hull front."""
    o = Ops()
    # hull (x 7..48)
    o.rect(7, 34, 48, 46, 'G')
    o.rect(7, 34, 48, 36, 'T')
    o.rect(7, 43, 48, 46, 'S')
    o.rect(10, 38, 30, 40, 'B')
    o.rect(10, 38, 30, 38, 'L')
    # turret (x 13..38)
    o.rect(13, 16, 38, 36, 'G')
    o.rect(13, 16, 38, 20, 'T')
    o.rect(13, 32, 38, 36, 'C')
    o.rect(17, 24, 27, 29, 'C')
    o.rect(17, 24, 27, 25, 'T')
    o.rect(18, TOP, 28, 17, 'C')        # cupola
    o.rect(18, TOP, 28, TOP, 'T')
    # barrel (x 34..56)
    o.rect(34, 22, 52, 27, 'G')
    o.rect(34, 22, 52, 22, 'T')
    o.rect(51, 20, 56, 29, 'C')
    # track (x 9..50)
    o.rect(9, 47, 50, 50, 'S')
    for x in range(12, 46, 8):
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
