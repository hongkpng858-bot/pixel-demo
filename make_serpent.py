"""Slithering serpent — traveling sine wave along the spine chain.

骨架：一條 12 點鏈狀脊柱，正弦波由頭傳到尾（相位行進），越近尾越窄。
冇腳：運動完全來自波傳遞；頭有眼＋間歇吐舌。

Outputs: serpent.gif / serpent_sheet.png / serpent_sheet@8x.png / serpent_rig.* / serpent.json
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

SKIN = (94, 168, 106)
SKIN_D = (62, 122, 78)
BELLY = (198, 216, 168)

N = 12                       # 脊柱點數
DX = 3.4                     # 點距
AMP = 5.2                    # 波幅
K = 0.52                     # 空間頻率
CY = 26


def spine_points(ph):
    """第 i 點位置：波由左（尾）向右（頭）行進。"""
    pts = []
    for i in range(N):
        x = 6 + i * DX
        f = i / (N - 1)
        y = CY + AMP * math.sin(i * K - ph * 2 * math.pi) * (0.55 + 0.45 * f)
        pts.append((x, y))
    return pts


def frame(i, mode="normal"):
    ph = i / FRAMES
    pts = spine_points(ph)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    char = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(char)

    # 身軀：粗幼漸變
    for a, b in zip(pts, pts[1:]):
        t = pts.index(a) / (N - 1)
        w = max(1, round(5 * (1 - 0.65 * t)))
        col = SKIN if t > 0.25 else BELLY if False else SKIN_D
        cd.line([a, b], fill=col if t > 0.3 else SKIN, width=w)
    # 背紋
    for j in range(2, N - 2, 2):
        q = pts[j]
        cd.point(q, fill=SKIN_D)
    # 腹側亮線
    cd.line([pts[0], pts[4]], fill=BELLY, width=1)

    # 頭
    hx, hy = pts[-1]
    d2 = (hx + 3, hy)
    cd.line([pts[-2], d2], fill=SKIN, width=4)
    cd.ellipse([d2[0] - 2, d2[1] - 3, d2[0] + 5, d2[1] + 3], fill=SKIN)
    cd.point((d2[0] + 3, d2[1] - 1), fill=(20, 24, 22))
    if i % 8 < 2:                                   # 吐舌（1/4 時間）
        cd.line([(d2[0] + 4, d2[1]), (d2[0] + 8, d2[1] - 1)], fill=(220, 80, 90), width=1)
        cd.point((d2[0] + 8, d2[1] - 1), fill=(220, 80, 90))

    if mode == "rig":
        a = char.getchannel("A").point(lambda v: int(v * 0.30))
        char.putalpha(a)
        img.alpha_composite(char)
        ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.line(pts, fill=RIG_BONE, width=1)
        for q in pts[::2] + [pts[-1]]:
            od.ellipse([q[0] - 1, q[1] - 1, q[0] + 1, q[1] + 1], fill=RIG_JOINT)
        od.ellipse([d2[0] - 2, d2[1] - 3, d2[0] + 5, d2[1] + 3], outline=RIG_BONE, width=1)
        img.alpha_composite(ov)
    else:
        img.alpha_composite(char)
    return img


def main():
    dur = int(1000 / FPS)
    normal = [frame(i, "normal") for i in range(FRAMES)]
    rig = [frame(i, "rig") for i in range(FRAMES)]

    up = lambda f: f.resize((S * SCALE, S * SCALE), Image.NEAREST)
    gif = [up(f).convert("RGB") for f in normal]
    gif[0].save("serpent.gif", save_all=True, append_images=gif[1:], duration=dur, loop=0)
    rgif = [up(f) for f in rig]
    rgif[0].save("serpent_rig.gif", save_all=True, append_images=rgif[1:], duration=dur,
                 loop=0, disposal=2, transparency=0)

    out = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(normal):
        out.paste(f_, (i_ * S, 0))
    out.save("serpent_sheet.png")
    out.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("serpent_sheet@8x.png")

    outr = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(rig):
        outr.paste(f_, (i_ * S, 0))
    outr.save("serpent_rig.png")
    outr.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("serpent_rig@8x.png")

    meta = {
        "name": "serpent_slither",
        "rig": {"bones": [f"spine.{j}" for j in range(N)] + ["head"],
                "method": "traveling sine wave along chain (no limbs)"},
        "frameSize": [S, S], "frameCount": FRAMES, "fps": FPS, "loop": True,
        "files": {"previewGif": "serpent.gif", "rigPreviewGif": "serpent_rig.gif",
                  "spriteSheetLogical": "serpent_sheet.png",
                  "spriteSheetScaled": "serpent_sheet@8x.png",
                  "rigSheetScaled": "serpent_rig@8x.png", "scale": SCALE},
    }
    with open("serpent.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done:", FRAMES, "frames (normal + rig)")


if __name__ == "__main__":
    main()
