"""QA check: sprite sheets must be alive AND seamlessly looping.

Rules per *_sheet.png (+ its .json metadata):
- ALIVE:    peak inter-frame motion must exceed MIN_PEAK (animation isn't stuck)
- AVERAGE:  mean inter-frame motion above MIN_AVG (there IS visible motion)
- SEAMLESS: wrap-around diff (last->first frame) within LOOP_TOLERANCE of
            normal frame-to-frame motion (no visual pop when looping)

Exit 0 = all pass. Run from this folder: python3 verify.py
"""
import json
import sys
import warnings
from pathlib import Path

from PIL import Image, ImageChops

MIN_PEAK = 20    # px that must change at busiest frame transition
MIN_AVG = 5      # px average motion per transition


def changed_px(a: Image.Image, b: Image.Image) -> int:
    d = ImageChops.difference(a, b)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return sum(1 for p in d.getdata() if p[3] > 0 or sum(p[:3]) > 0)


def check(sheet_path: Path):
    meta = json.loads(sheet_path.with_name(sheet_path.name.replace("_sheet.png", ".json")).read_text())
    n, (w, h) = meta["frameCount"], meta["frameSize"]
    im = Image.open(sheet_path).convert("RGBA")
    assert im.width == w * n and im.height == h, \
        f"{sheet_path}: size {im.size} != strip {w * n}x{h}"
    frames = [im.crop((i * w, 0, (i + 1) * w, h)) for i in range(n)]

    adj = [changed_px(frames[i], frames[(i + 1) % n]) for i in range(n)]
    wrap = adj[-1]                      # last -> first IS part of the cycle
    inner = adj[:-1]
    peak, avg = max(inner), sum(inner) / len(inner)
    tol = max(2 * peak, 12)             # wrap may continue motion, not restart it

    ok = peak >= MIN_PEAK and avg >= MIN_AVG and wrap <= tol
    verdict = "PASS" if ok else (
        "FAIL(static)" if peak < MIN_PEAK or avg < MIN_AVG else "FAIL(loop-pop)")
    print(f"{verdict} {sheet_path.name}: {n}f {w}x{h} "
          f"motion avg={avg:.0f} peak={peak} wrap={wrap} (tol={tol})")
    return ok


if __name__ == "__main__":
    sheets = sorted(Path(".").glob("*_sheet.png"))
    if not sheets:
        sys.exit("no *_sheet.png found")
    results = [check(p) for p in sheets]
    print(f"== {'ALL PASS' if all(results) else 'FAILURES PRESENT'} ==")
    sys.exit(0 if all(results) else 1)
