#!/usr/bin/env python3
"""
Build Godot 4 SpriteFrames (.tres) resources from a unit's frames JSON.

Reads  <unit>_frames.json  (canvas, strip filename, per-frame regions) and emits
<unit>_spriteframes.tres with one AtlasTexture per frame, grouped into the
4 animations the frame table declares (idle / walk / attack / death).

Why AtlasTexture: Godot 4's SpriteFrames.add_frame() does NOT accept a Rect2
region — a sheet cell must be wrapped in an AtlasTexture (atlas + region +
filter_clip). This is baked into the .tres so scenes just assign the resource.

Usage (from the repo root):
    python3 tools/build_spriteframes.py                       # all units
    python3 tools/build_spriteframes.py assets/sprites/marine/marine_frames.json
"""
import json
import os
import sys

FPS_FALLBACK = {"idle": 2.0, "walk": 6.0, "attack": 8.0, "death": 4.0}
LOOP_FALLBACK = {"idle": True, "walk": True, "attack": False, "death": False}


def build(manifest_path: str) -> str:
    with open(manifest_path) as fh:
        meta = json.load(fh)
    out_dir = os.path.dirname(manifest_path)
    unit = meta.get("unit", os.path.basename(out_dir))
    strip = meta["strip"]
    strip_res = "res://" + os.path.join(out_dir, strip).replace(os.sep, "/")

    frames = meta["frames"]
    subs, order, by_state = [], [], {}
    for fr in frames:
        state = fr.get("state")
        if state in ("idle", "walk", "attack", "death"):
            by_state.setdefault(state, []).append(fr)
        else:
            # static art (towers) — one animation per sprite
            by_state.setdefault(state, []).append(fr)

    for state in by_state:
        order.append(state)

    for i, fr in enumerate(frames):
        sid = "AtlasTexture_%d_%s" % (i, fr["name"])
        subs.append(
            '[sub_resource type="AtlasTexture" id="%s"]\n'
            'atlas = ExtResource("1_sheet")\n'
            'region = Rect2(%d, %d, %d, %d)\n'
            % (sid, fr["x"], fr["y"], fr["w"], fr["h"])
        )

    anims = []
    for state in order:
        fl = ", ".join(
            '{"duration": 1.0, "texture": SubResource("AtlasTexture_%d_%s")}'
            % (frames.index(fr), fr["name"])
            for fr in by_state[state]
        )
        fps = by_state[state][0].get("fps") or FPS_FALLBACK.get(state, 8.0)
        loop = by_state[state][0].get("loop")
        if loop is None:
            loop = LOOP_FALLBACK.get(state, False)
        anims.append(
            '{\n"frames": [%s],\n"loop": %s,\n"name": &"%s",\n"speed": %s\n}'
            % (fl, "true" if loop else "false", state, float(fps))
        )

    out_path = os.path.join(out_dir, unit + "_spriteframes.tres")
    body = (
        '[gd_resource type="SpriteFrames" load_steps=%d format=3]\n\n'
        '[ext_resource type="Texture2D" path="%s" id="1_sheet"]\n\n' % (len(subs) + 2, strip_res)
        + "\n".join(subs)
        + "\n[resource]\nanimations = [\n"
        + ",\n".join(anims)
        + "\n]\n"
    )
    with open(out_path, "w") as fh:
        fh.write(body)
    return out_path


def main() -> int:
    roots = ["assets/sprites"]
    if len(sys.argv) > 1:
        roots = [sys.argv[1]]
    made = []
    for root in roots:
        for dirpath, _dirs, files in os.walk(root):
            for f in sorted(files):
                if f.endswith("_frames.json"):
                    made.append(build(os.path.join(dirpath, f)))
    for p in made:
        print("wrote", p)
    if not made:
        print("no *_frames.json found")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
