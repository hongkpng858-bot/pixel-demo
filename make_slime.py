"""Slime hop animation -> game/web-ready assets.

Outputs (same folder):
  slime.gif         looping GIF preview (night backdrop baked in)
  slime_sheet.png   transparent sprite strip, 16 x 32x32 frames (game engines)
  slime_sheet@8x.png  same strip pre-scaled 8x nearest-neighbour (direct web use)
  slime.json        frame metadata (fps / count / size)
"""
import json
import math

from PIL import Image, ImageDraw

S = 32          # logical frame size
FRAMES = 16
SCALE = 8
FPS = 12.5
GROUND = 26

BG = (27, 27, 41)
GROUND_C = (58, 58, 84)
BODY = (86, 196, 102)
BODY_D = (52, 140, 74)
DARK = (24, 60, 36)
EYE = (20, 25, 30)
GLINT = (255, 255, 255)
SHADOW = (15, 15, 24)
HIGHLIGHT = (190, 240, 200)
CLEAR = (0, 0, 0, 0)

STARS = [(4, 5), (25, 3), (28, 9), (8, 12), (20, 7), (13, 3)]


def draw_slime(d, p):
    """Squash-and-stretch hopping blob."""
    hop = max(0.0, math.sin(p * 2 * math.pi))
    h = hop * 6
    sx = 1 + 0.18 * (1 - hop) * math.cos(p * 2 * math.pi) - 0.12 * hop
    sy = 2 - sx
    cx = 16
    bottom = GROUND + 1 - h
    rx = 9 * sx
    ry = 7 * sy

    x0, x1 = int(cx - rx), int(cx + rx)
    top = max(0, int(bottom - ry * 2))
    for y in range(top, min(S, int(bottom) + 1)):
        for x in range(max(0, x0), min(S, x1 + 1)):
            nx = (x - cx) / rx
            ny = (bottom - y) / ry
            v = nx * nx + ny * ny
            if v <= 1.0:
                edge = v > 0.72
                lowband = ny < -0.35
                col = DARK if edge else (BODY_D if lowband else BODY)
                d.point((x, y), fill=col)

    hx, hy = int(cx - rx * 0.45), int(bottom - ry * 1.35)
    d.point((hx, hy), fill=HIGHLIGHT)
    d.point((hx + 1, hy), fill=HIGHLIGHT)

    ey = int(bottom - ry * 0.9)
    exl, exr = int(cx - rx * 0.30), int(cx + rx * 0.34)
    for ex in (exl, exr):
        d.rectangle([ex, ey, ex, ey + 2], fill=EYE)
    d.point((exl, ey), fill=GLINT)
    d.point((exr, ey), fill=GLINT)


def frame(p, transparent=False):
    if transparent:
        img = Image.new("RGBA", (S, S), CLEAR)
        draw_slime(ImageDraw.Draw(img), p)
        return img
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)
    for (x, y) in STARS:
        d.point((x, y), fill=(70, 70, 110))
    d.rectangle([0, GROUND + 1, S, GROUND + 2], fill=GROUND_C)
    for x in range(0, S, 4):
        d.point((x, GROUND + 3), fill=(40, 40, 60))
    hop = max(0.0, math.sin(p * 2 * math.pi))
    h = hop * 6
    srx = 9 * (1 + 0.18 * (1 - hop) * math.cos(p * 2 * math.pi)) * (1 - h / 14) + 2
    d.ellipse([16 - srx, GROUND - 1, 16 + srx, GROUND + 1], fill=SHADOW)
    draw_slime(d, p)
    return img


def main():
    dur = int(1000 / FPS)
    gif_frames = [frame(i / FRAMES).resize((S * SCALE, S * SCALE), Image.NEAREST)
                  for i in range(FRAMES)]
    gif_frames[0].save("slime.gif", save_all=True,
                       append_images=gif_frames[1:], duration=dur, loop=0)

    strip = Image.new("RGBA", (S * FRAMES, S), CLEAR)
    for i in range(FRAMES):
        strip.paste(frame(i / FRAMES, transparent=True), (i * S, 0))
    strip.save("slime_sheet.png")
    strip.resize((strip.width * SCALE, strip.height * SCALE),
                 Image.NEAREST).save("slime_sheet@8x.png")

    meta = {
        "name": "slime_hop",
        "frameSize": [S, S],
        "frameCount": FRAMES,
        "fps": FPS,
        "loop": True,
        "layout": "horizontal-strip",
        "files": {
            "previewGif": "slime.gif",
            "spriteSheetLogical": "slime_sheet.png",
            "spriteSheetScaled": "slime_sheet@8x.png",
            "scale": SCALE,
        },
    }
    with open("slime.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done:", FRAMES, "frames |", f"{dur}ms/frame")


if __name__ == "__main__":
    main()
