"""Ghostly floater — no legs, hovering bob + traveling skirt wave.

冇骨家族：身體本身係「骨架」。半透明浮空體上下漂浮，
底邊裙擺行進波經典鬼魂做法；拖尾飄帶三縷。
Rig 模式顯示輪廓＋裙擺波形控制點。

Outputs: ghost.gif / ghost_sheet.png / ghost_sheet@8x.png / ghost_rig.* / ghost.json
"""
import json
import math

from PIL import Image, ImageDraw

S = 48
FRAMES = 16
SCALE = 8
FPS = 12.5

RIG_BONE = (255, 170, 40)
RIG_JOINT = (120, 255, 160)

GHOST = (226, 230, 248, 205)
GHOST_EDGE = (168, 176, 214, 235)
EYE = (30, 32, 52)
MOUTH = (30, 32, 52)
WISP = (196, 204, 236, 150)

CX = 24


def frame(i, mode="normal"):
    ph = i / FRAMES * 2 * math.pi
    bob = 2.2 * math.sin(ph)
    cy = 20 + bob
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    char = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(char)

    # 裙擺底邊：行進波
    skirt_y = cy + 13
    xs = list(range(CX - 11, CX + 12))
    wave = [skirt_y + 3.0 * math.sin(x * 0.72 - ph * 2 * math.pi) for x in xs]

    # 身形多邊形：圓頂＋波浪底
    poly = []
    for k in range(-90, 91, 15):                     # 半圓頂
        a = math.radians(k)
        poly.append((CX + 11 * math.sin(a) * -1, cy + 11 * math.cos(a)))
    for x, y in zip(xs, wave):                        # 波浪裙
        poly.append((x, y))
    cd.polygon(poly, fill=GHOST, outline=GHOST_EDGE)

    # 面孔
    blink = 1 if math.sin(ph * 2) > 0.92 else 0       # 偶爾眨眼
    eh = 1 if blink else 2
    cd.ellipse([CX - 7, cy - 4 - eh // 2, CX - 3, cy - 4 + eh], fill=EYE)
    cd.ellipse([CX + 3, cy - 4 - eh // 2, CX + 7, cy - 4 + eh], fill=EYE)
    if math.sin(ph) > 0.3:                            # 張口／閉口
        cd.ellipse([CX - 1, cy + 2, CX + 3, cy + 5], fill=MOUTH)
    else:
        cd.line([(CX, cy + 3), (CX + 3, cy + 3)], fill=MOUTH, width=1)

    # 拖尾飄帶三縷
    for k, (dx, ln, spd) in enumerate(((-6, 7, 1.0), (0, 9, 1.3), (6, 7, 0.8))):
        base = (CX + dx, skirt_y - 1)
        for t in range(ln):
            wob = math.sin(ph * 2 * math.pi * spd + t * 0.9 + k)
            q = (base[0] + wob * 1.6, base[1] + 1 + t)
            cd.point(q, fill=WISP)

    if mode == "rig":
        a = char.getchannel("A").point(lambda v: int(v * 0.30))
        char.putalpha(a)
        img.alpha_composite(char)
        ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        # 圓頂輪廓
        od.arc([CX - 11, cy - 11, CX + 11, cy + 11], 180, 360, fill=RIG_BONE, width=1)
        # 裙擺控制點鏈
        pts = [(x, y) for x, y in zip(xs, wave)][::3]
        od.line(pts, fill=RIG_BONE, width=1)
        for q in pts:
            od.ellipse([q[0] - 1, q[1] - 1, q[0] + 1, q[1] + 1], fill=RIG_JOINT)
        od.point((CX, cy), fill=RIG_JOINT)
        img.alpha_composite(ov)
    else:
        img.alpha_composite(char)
    return img


def main():
    dur = int(1000 / FPS)
    normal = [frame(i, "normal") for i in range(FRAMES)]
    rig = [frame(i, "rig") for i in range(FRAMES)]

    up = lambda f: f.resize((S * SCALE, S * SCALE), Image.NEAREST)
    gif = [up(f) for f in normal]
    gif[0].save("ghost.gif", save_all=True, append_images=gif[1:], duration=dur, loop=0)
    rgif = [up(f) for f in rig]
    rgif[0].save("ghost_rig.gif", save_all=True, append_images=rgif[1:], duration=dur,
                 loop=0, disposal=2, transparency=0)

    out = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(normal):
        out.paste(f_, (i_ * S, 0))
    out.save("ghost_sheet.png")
    out.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("ghost_sheet@8x.png")

    outr = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(rig):
        outr.paste(f_, (i_ * S, 0))
    outr.save("ghost_rig.png")
    outr.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("ghost_rig@8x.png")

    meta = {
        "name": "ghost_float",
        "rig": {"bones": ["dome-outline", "skirt-wave-control-points", "wisps.x3"],
                "method": "boneless: volume itself deforms (soft-body family)"},
        "frameSize": [S, S], "frameCount": FRAMES, "fps": FPS, "loop": True,
        "files": {"previewGif": "ghost.gif", "rigPreviewGif": "ghost_rig.gif",
                  "spriteSheetLogical": "ghost_sheet.png",
                  "spriteSheetScaled": "ghost_sheet@8x.png",
                  "rigSheetScaled": "ghost_rig@8x.png", "scale": SCALE},
    }
    with open("ghost.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done:", FRAMES, "frames (normal + rig)")


if __name__ == "__main__":
    main()
