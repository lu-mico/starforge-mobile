#!/usr/bin/env bash
# check_web_render.sh — prove the WEB build actually renders, not just serves 200s.
#
# Why this exists (2026-11-05): every asset returned 200 and the engine started, but
# the board never drew — the headless Chrome we used had no WebGL2. The fix is ANGLE's
# software rasteriser, and with it the web build renders the same board as the device.
# "The sandbox lacks WebGL2" was never a real limit; it was a missing flag.
#
# What it checks:
#   1. the server is up and every asset returns 200
#   2. the html's <script src=> placeholder was actually substituted (a $GODOT_URL
#      left in place = white screen)
#   3. the engine boots in a real browser AND the canvas draws (colour histogram +
#      per-row structure), captured over CDP after real wall-clock time
#
# Usage: tools/check_web_render.sh [http://127.0.0.1:8123/play/index.html]
set -uo pipefail

URL="${1:-http://127.0.0.1:8123/play/index.html}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT=9223
PROFILE="$(mktemp -d)"
OUT="$(mktemp -d)/web_render.png"
fail=0

echo "== 1. server + assets =="
base="${URL%/*}"
for f in index.html webplay.js webplay.wasm webplay.pck; do
  code=$(curl -s -m 30 -o /dev/null -w '%{http_code}' "$base/$f")
  echo "   $f -> $code"
  [ "$code" = "200" ] || fail=1
done

echo "== 2. placeholder substituted? =="
if curl -s -m 10 "$URL" | grep -q 'src="\$GODOT_URL"'; then
  echo "   FAIL: \$GODOT_URL still in the html -> white screen"
  fail=1
else
  echo "   ok: $(curl -s -m 10 "$URL" | grep -o '<script src="[^"]*"')"
fi

echo "== 3. real browser render =="
if [ ! -x "$CHROME" ]; then
  echo "   SKIP: no Chrome at $CHROME"
  exit $fail
fi
pkill -f "remote-debugging-port=$PORT" 2>/dev/null
"$CHROME" --headless=new --no-sandbox --disable-gpu-sandbox \
  --enable-unsafe-swiftshader --use-angle=swiftshader \
  --remote-debugging-port=$PORT --user-data-dir="$PROFILE" \
  --window-size=720,1280 about:blank >/dev/null 2>&1 &
CHROME_PID=$!
sleep 6
OUT_FILE="$OUT" WEB_URL="$URL" CDP_PORT="$PORT" node "$DIR/web_render_check.js" || fail=1
kill $CHROME_PID 2>/dev/null
rm -rf "$PROFILE"

echo "== 4. did the canvas actually DRAW? =="
# The Godot loading screen is a flat #242424 (36,36,36) field with a progress bar.
# A drawn board has the game's palette and structure: a HUD band at the top, the
# board in the middle and the 4-card bar near the bottom.
SHOT="$OUT" python3 - <<'PY' || fail=1
import os, sys
from collections import Counter
from PIL import Image

im = Image.open(os.environ["SHOT"]).convert("RGB")
px = im.load()
W, H = im.size

def band(y0, y1):
    return set(px[x, y] for y in range(y0, min(y1, H), 3) for x in range(0, W, 3))

c = Counter(px[x, y] for y in range(0, H, 3) for x in range(0, W, 3))
top = c.most_common(1)[0]
print(f"   dominant colour {top[0]} at {top[1]*100/sum(c.values()):.1f}%")

if top[0] == (36, 36, 36) and top[1] / sum(c.values()) > 0.85:
    print("   FAIL: canvas is the Godot loading screen, nothing was drawn")
    sys.exit(1)

hud = len(band(0, 64))
cards = len(band(1088, 1152))
print(f"   HUD band y0-64: {hud} distinct colours | card bar y1088-1152: {cards}")
if hud < 20 or cards < 20:
    print("   FAIL: no board structure found (expected HUD + card bar)")
    sys.exit(1)
print("   ok: board, HUD and card bar are drawn")
PY

echo "== result =="
[ $fail -eq 0 ] && echo "   PASS: web build serves, substitutes the placeholder and renders" \
                 || echo "   FAIL: see above"
exit $fail
