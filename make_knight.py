"""Armored knight — second humanoid skeletal walk cycle.

同人類 walker 完全同一套 FK 骨架幾何（S=48、大腿/小腿=8、上臂/前臂=6），
換上裝甲配色＋頭盔紅羽；近手拎劍（劍身沿前臂方向延伸）、遠手掛圓盾。

Outputs: knight.gif / knight_sheet.png / knight_sheet@8x.png / knight_rig.* / knight.json
"""
import json
import math

from PIL import Image, ImageDraw

S = 48
FRAMES = 16
SCALE = 8
FPS = 12.5
GROUND_Y = 44

RIG_BONE = (255, 170, 40)
RIG_JOINT = (120, 255, 160)

STEEL = (196, 204, 218)
STEEL_DK = (110, 118, 134)
TRIM = (168, 58, 54)
PLUME = (206, 64, 64)
BLADE = (222, 230, 245)
SHIELD = (172, 52, 48)


def shade(c, f):
    return tuple(int(v * f) for v in c)


NEAR = {"armor": STEEL, "pants": (70, 76, 98), "boot": (44, 44, 58)}
FAR = {k: shade(v, 0.62) for k, v in NEAR.items()}

HIP_X = 24.0
L_THIGH, L_SHIN = 8, 8
L_UARM, L_FARM = 6, 6
TORSO_DX, TORSO_DY = 1.2, -9.0
HEAD_DX, HEAD_DY, HEAD_R = 2.0, -6.5, 4

DEG = math.radians


def pose(ph):
    s, c = math.sin(ph), math.cos(ph)
    swing = lambda x: max(0.0, math.sin(x - 0.35)) ** 1.2
    return {
        "hip_y": HIP_BASE_Y - 1.2 * abs(c),
        "thigh_n": DEG(24) * s,          "knee_n": DEG(52) * swing(ph),
        "thigh_f": -DEG(24) * s,         "knee_f": DEG(52) * swing(ph + math.pi),
        "arm_n": DEG(20) * -s,           "elb_n": DEG(14) + DEG(12) * max(0.0, s),
        "arm_f": DEG(20) * s,            "elb_f": DEG(14),
    }


HIP_BASE_Y = GROUND_Y - (L_THIGH + L_SHIN)


def fk(p0, ang, ln):
    return (p0[0] + math.sin(ang) * ln, p0[1] + math.cos(ang) * ln)


def render_character(d, P, segs):
    hip = (HIP_X, P["hip_y"])
    chest = (hip[0] + TORSO_DX, hip[1] + TORSO_DY)
    shoulder = (chest[0], chest[1] + 1.5)

    def cap(q, col):
        d.ellipse([q[0] - 1, q[1] - 1, q[0] + 1, q[1] + 1], fill=col)

    def leg(pal, tag):
        th, kn = P["thigh_" + tag], P["knee_" + tag]
        j = fk(hip, th, L_THIGH)
        e = fk(j, th - kn, L_SHIN)
        d.line([hip, j], fill=pal["pants"], width=3)
        d.line([j, e], fill=pal["pants"], width=3)
        cap(j, pal["pants"])
        d.line([e, (e[0] + 3, e[1] + 0.6)], fill=pal["boot"], width=2)
        segs.extend([("thigh." + tag, hip, j), ("shin." + tag, j, e)])

    def arm(pal, tag):
        a, el = P["arm_" + tag], P["elb_" + tag]
        j = fk(shoulder, a, L_UARM)
        e = fk(j, a - el, L_FARM)
        d.line([shoulder, j], fill=pal["armor"], width=2)
        d.line([j, e], fill=pal["armor"], width=2)
        cap(shoulder, STEEL_DK)
        cap(j, pal["armor"])
        cap(e, STEEL_DK)
        segs.extend([("upperarm." + tag, shoulder, j), ("forearm." + tag, j, e)])

    arm(FAR, "f")
    ef = segs[-1][2]                                    # 遠手位置
    d.ellipse([ef[0] - 4, ef[1] - 4, ef[0] + 4, ef[1] + 4],
              fill=SHIELD, outline=STEEL_DK)            # 圓盾（遠側）
    d.point(ef, fill=(240, 200, 90))
    leg(FAR, "f")
    d.line([hip, chest], fill=STEEL, width=4)           # 胸甲
    d.point((hip[0], hip[1] - 1), fill=(60, 56, 70))    # 腰帶
    segs.append(("spine", hip, chest))
    leg(NEAR, "n")
    arm(NEAR, "n")
    en = segs[-1][2]                                    # 近手位置

    # 劍：沿前臂方向延伸
    bl = fk(en, P["arm_n"] - P["elb_n"], 11)
    d.line([en, bl], fill=BLADE, width=1)
    d.point(bl, fill=(255, 255, 255))
    perp = P["arm_n"] - P["elb_n"] + DEG(90)
    g1 = fk(en, perp, 2)
    g2 = fk(en, perp - DEG(180), 2)
    d.line([g1, g2], fill=STEEL_DK, width=1)            # 護手
    segs.append(("sword", en, bl))

    hc = (chest[0] + HEAD_DX, chest[1] + HEAD_DY)
    hr = HEAD_R
    d.ellipse([hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr], fill=STEEL)
    d.pieslice([hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr], 180, 340, fill=STEEL_DK)
    d.point((hc[0] + 2, hc[1]), fill=(20, 20, 28))      # 眼縫
    d.line([(hc[0] + 1, hc[1] - hr + 1), (hc[0] + 1, hc[1] + hr - 1)], fill=STEEL_DK, width=1)
    for k in (-1, 0, 1):                                # 紅羽
        q = fk(hc, DEG(262 + k * 13), hr + 1.5)
        d.point(q, fill=PLUME)
    d.line([(chest[0], chest[1] + 1), (hc[0], hc[1] + hr - 1)], fill=STEEL_DK, width=2)
    return hc


def frame(i, mode="normal"):
    P = pose(i / FRAMES * 2 * math.pi)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, GROUND_Y + 1, S, GROUND_Y + 2], fill=(58, 58, 84))
    hop = max(0.0, math.sin((i / FRAMES) * 2 * math.pi))
    h = hop * 6
    sx = 1 + 0.18 * (1 - hop) * math.cos((i / FRAMES) * 2 * math.pi) - 0.12 * hop
    srx = 9 * sx * (1 - h / 14) + 2
    d.ellipse([HIP_X - srx, GROUND_Y - 1, HIP_X + srx, GROUND_Y + 1],
              fill=((17, 17, 28) if mode == "normal" else (60, 60, 90)))

    char = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(char)
    segs = []
    render_character(cd, P, segs)

    if mode == "rig":
        a = char.getchannel("A").point(lambda v: int(v * 0.30))
        char.putalpha(a)
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
    gif = [up(f).convert("RGB") for f in normal]
    gif[0].save("knight.gif", save_all=True, append_images=gif[1:], duration=dur, loop=0)
    rgif = [up(f) for f in rig]
    rgif[0].save("knight_rig.gif", save_all=True, append_images=rgif[1:], duration=dur,
                 loop=0, disposal=2, transparency=0)

    out = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(normal):
        out.paste(f_, (i_ * S, 0))
    out.save("knight_sheet.png")
    out.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("knight_sheet@8x.png")

    outr = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(rig):
        outr.paste(f_, (i_ * S, 0))
    outr.save("knight_rig.png")
    outr.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("knight_rig@8x.png")

    meta = {
        "name": "knight_walk",
        "rig": {"bones": ["pelvis", "thigh.L/R", "shin.L/R", "spine",
                          "upperarm.L/R", "forearm.L/R", "head", "sword"],
                "method": "forward-kinematics, same skeleton as walker"},
        "frameSize": [S, S], "frameCount": FRAMES, "fps": FPS, "loop": True,
        "files": {"previewGif": "knight.gif", "rigPreviewGif": "knight_rig.gif",
                  "spriteSheetLogical": "knight_sheet.png",
                  "spriteSheetScaled": "knight_sheet@8x.png",
                  "rigSheetScaled": "knight_rig@8x.png", "scale": SCALE},
    }
    with open("knight.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done:", FRAMES, "frames (normal + rig)")


if __name__ == "__main__":
    main()
