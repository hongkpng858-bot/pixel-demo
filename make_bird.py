"""Flapping bird — FK wing chain (shoulder→elbow→wingtip), figure-eight-ish flap.

骨架：脊柱短鏈＋頭喙尾、雙腿懸垂、翼＝兩節骨鏈拍動（相位驅動）。
身軀隨下撲輕微上升；遠翼自動調暗。

Outputs: bird.gif / bird_sheet.png / bird_sheet@8x.png / bird_rig.* / bird.json
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

BODY = (92, 148, 220)
BELLY = (222, 232, 248)
WING = (58, 96, 170)
BEAK = (240, 178, 60)


def shade(c, f):
    return tuple(int(v * f) for v in c)


FAR_WING = shade(WING, 0.62)

CX, CY = 21, 22
HEAD = (29, 14)
W_SH = (17, 18)
L1, L2 = 7, 7

DEG = math.radians


def fk(p0, ang, ln):
    return (p0[0] + math.sin(ang) * ln, p0[1] + math.cos(ang) * ln)


def frame(i, mode="normal"):
    a = i / FRAMES * 2 * math.pi
    s = math.sin(a)
    bob = -1.4 * abs(s)
    flap = DEG(46) * s
    eb = DEG(28) + DEG(12) * max(0.0, s)

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    char = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(char)
    segs = []

    def wing(col, sh, tag):
        e = fk(sh, -DEG(90) + flap, L1)
        t = fk(e, -DEG(90) + flap + eb, L2)
        cd.line([sh, e], fill=col, width=3)
        cd.line([e, t], fill=col, width=2)
        segs.extend([(f"wing1.{tag}", sh, e), (f"wing2.{tag}", e, t)])

    def leg(dx, col):
        h0 = (CX + dx, CY + 6 + bob)
        k = (h0[0] - 1 + 1.2 * s, h0[1] + 5)
        f_ = (k[0] + 1.5, k[1] + 4)
        cd.line([h0, k], fill=col, width=1)
        cd.line([k, f_], fill=col, width=1)
        segs.append((f"leg.{dx}", h0, f_))

    wing(FAR_WING, W_SH, "f")                       # 遠翼
    # 身軀
    cd.ellipse([CX - 9, CY - 6 + bob, CX + 9, CY + 7 + bob], fill=BODY)
    cd.chord([CX - 8, CY + 1 + bob, CX + 7, CY + 7 + bob], 0, 180, fill=BELLY)
    segs.append(("spine", (CX - 7, CY + bob), (CX + 7, CY + bob)))
    # 尾羽
    t0 = (CX - 8, CY - 1 + bob)
    for k in (-2, 0, 2):
        q = fk(t0, DEG(180 + k * 8) + DEG(6) * s, 7)
        cd.line([t0, q], fill=WING, width=1)
        if k == 0:
            segs.append(("tail", t0, q))
    # 頭頸＋喙眼
    neck = (HEAD[0], HEAD[1] + 3)
    hc = (HEAD[0], HEAD[1] + bob)
    cd.line([(CX + 4, CY - 4 + bob), neck], fill=BODY, width=3)
    cd.ellipse([hc[0] - 4, hc[1] - 4, hc[0] + 4, hc[1] + 4], fill=BODY)
    cd.polygon([(hc[0] + 3, hc[1] - 1), (hc[0] + 8, hc[1]), (hc[0] + 3, hc[1] + 2)], fill=BEAK)
    cd.point((hc[0] + 1, hc[1] - 1), fill=(20, 22, 30))
    segs.append(("head", hc, hc))
    wing(WING, (W_SH[0], W_SH[1] + bob), "n")       # 近翼
    leg(-2, shade(BODY, 0.75)); leg(3, BODY)

    if mode == "rig":
        al = char.getchannel("A").point(lambda v: int(v * 0.30))
        char.putalpha(al)
        img.alpha_composite(char)
        ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        joints = []
        for _, p0, p1 in segs:
            od.line([p0, p1], fill=RIG_BONE, width=1)
            joints += [p0, p1]
        seen = set()
        for q in joints:
            key = (int(q[0]), int(q[1]))
            if key not in seen:
                seen.add(key)
                od.ellipse([q[0] - 1, q[1] - 1, q[0] + 1, q[1] + 1], fill=RIG_JOINT)
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
    gif[0].save("bird.gif", save_all=True, append_images=gif[1:], duration=dur, loop=0)
    rgif = [up(f) for f in rig]
    rgif[0].save("bird_rig.gif", save_all=True, append_images=rgif[1:], duration=dur,
                 loop=0, disposal=2, transparency=0)
    out = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(normal):
        out.paste(f_, (i_ * S, 0))
    out.save("bird_sheet.png")
    out.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("bird_sheet@8x.png")
    outr = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(rig):
        outr.paste(f_, (i_ * S, 0))
    outr.save("bird_rig.png")
    outr.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("bird_rig@8x.png")
    meta = {
        "name": "bird_flap",
        "rig": {"bones": ["spine", "tail", "head", "leg.x2", "wing.L/R (2-segment FK)"],
                "method": "forward-kinematics wing flap + body counter-bob"},
        "frameSize": [S, S], "frameCount": FRAMES, "fps": FPS, "loop": True,
        "files": {"previewGif": "bird.gif", "rigPreviewGif": "bird_rig.gif",
                  "spriteSheetLogical": "bird_sheet.png",
                  "spriteSheetScaled": "bird_sheet@8x.png",
                  "rigSheetScaled": "bird_rig@8x.png", "scale": SCALE},
    }
    with open("bird.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done:", FRAMES, "frames (normal + rig)")


if __name__ == "__main__":
    main()
