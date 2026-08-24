"""Swimming fish — traveling wave along spine chain, amplitude grows to tail.

魚類家族：正弦波由頭向尾傳遞，波幅向尾部遞增；尾鰭隨波掃動，
背鰭胸鰭小幅擺動。冇腳冇地影——水中運動。

Outputs: fish.gif / fish_sheet.png / fish_sheet@8x.png / fish_rig.* / fish.json
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

SCALE_C = (86, 168, 208)
SCALE_D = (54, 118, 158)
FIN = (196, 224, 236)

N = 9
CY = 24

DEG = math.radians


def fk(p0, ang, ln):
    return (p0[0] + math.sin(ang) * ln, p0[1] + math.cos(ang) * ln)


def spine(a):
    """頭(x=12)到尾根(x=36)：波幅遞增。"""
    pts = []
    for j in range(N):
        t = j / (N - 1)
        x = 12 + t * 24
        amp = 0.8 + 3.4 * t ** 1.4
        y = CY + amp * math.sin(j * 0.95 - a)
        pts.append((x, y))
    return pts


def frame(i, mode="normal"):
    a = i / FRAMES * 2 * math.pi
    pts = spine(a)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    char = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(char)
    segs = []

    # 尾鰭：跟住最後一點方向掃
    tx, ty = pts[-1]
    dx = tx - pts[-2][0]
    dy = ty - pts[-2][1]
    ln = math.hypot(dx, dy) or 1
    ux, uy = dx / ln, dy / ln
    spread = 7
    t1 = (tx + ux * 9 - uy * spread, ty + uy * 9 + ux * spread)
    t2 = (tx + ux * 11, ty + uy * 11)
    t3 = (tx + ux * 9 + uy * spread, ty + uy * 9 - ux * spread)
    cd.polygon([pts[-1], t1, t2, t3], fill=SCALE_D)
    segs.append(("tailfin", pts[-1], t2))

    # 身軀粗幼漸變
    for p0, p1 in zip(pts, pts[1:]):
        t = pts.index(p0) / (N - 1)
        w = max(2, round(8 * (1 - 0.72 * t)))
        col = SCALE_D if t < 0.18 else SCALE_C
        cd.line([p0, p1], fill=col, width=w)
    segs.append(("spine", pts[0], pts[-1]))
    # 背鰭（小三角，微擺）
    mp = pts[4]
    dh = 2.0 * math.sin(a + 1.2)
    cd.polygon([(mp[0] - 3, mp[1] - 3), (mp[0] + 3, mp[1] - 3),
                (mp[0] + dh, mp[1] - 7)], fill=FIN)
    segs.append(("dorsal", (mp[0], mp[1] - 3), (mp[0] + dh, mp[1] - 7)))
    # 胸鰭（點頭附近，划水）
    pp = pts[1]
    pf = fk(pp, DEG(120) + DEG(18) * math.sin(a), 5)
    cd.line([pp, pf], fill=FIN, width=1)
    segs.append(("pectoral", pp, pf))
    # 腹部亮線＋眼
    cd.line([pts[0], pts[2]], fill=FIN, width=1)
    ex, ey = pts[0]
    cd.point((ex + 1, ey - 1), fill=(16, 20, 26))

    if mode == "rig":
        al = char.getchannel("A").point(lambda v: int(v * 0.30))
        char.putalpha(al)
        img.alpha_composite(char)
        ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.line(pts, fill=RIG_BONE, width=1)
        for q in pts[::2] + [pts[-1]]:
            od.ellipse([q[0] - 1, q[1] - 1, q[0] + 1, q[1] + 1], fill=RIG_JOINT)
        od.line([pts[-1], t2], fill=RIG_BONE, width=1)
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
    gif[0].save("fish.gif", save_all=True, append_images=gif[1:], duration=dur, loop=0)
    rgif = [up(f) for f in rig]
    rgif[0].save("fish_rig.gif", save_all=True, append_images=rgif[1:], duration=dur,
                 loop=0, disposal=2, transparency=0)
    out = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(normal):
        out.paste(f_, (i_ * S, 0))
    out.save("fish_sheet.png")
    out.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("fish_sheet@8x.png")
    outr = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(rig):
        outr.paste(f_, (i_ * S, 0))
    outr.save("fish_rig.png")
    outr.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("fish_rig@8x.png")
    meta = {
        "name": "fish_swim",
        "rig": {"bones": [f"spine.{j}" for j in range(N)] + ["tailfin", "dorsal", "pectoral"],
                "method": "traveling sine wave, amplitude increases caudally"},
        "frameSize": [S, S], "frameCount": FRAMES, "fps": FPS, "loop": True,
        "files": {"previewGif": "fish.gif", "rigPreviewGif": "fish_rig.gif",
                  "spriteSheetLogical": "fish_sheet.png",
                  "spriteSheetScaled": "fish_sheet@8x.png",
                  "rigSheetScaled": "fish_rig@8x.png", "scale": SCALE},
    }
    with open("fish.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done:", FRAMES, "frames (normal + rig)")


if __name__ == "__main__":
    main()
