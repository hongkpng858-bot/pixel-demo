"""Mechanical pixel robot — skeletal walk cycle.

機械骨架：髖→大腿→小腿（圓形螺絲關節）、脊柱→方形頭＋天線、肩→臂。
金屬灰＋熒光青色板；眼帶同胸口核心會閃；天線隨步伐擺動。

Outputs: robot.gif / robot_sheet.png / robot_sheet@8x.png / robot_rig.* / robot.json
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

METAL = (152, 160, 174)
DARK = (38, 42, 56)
JOINT_C = (52, 58, 74)
GLOW = (96, 224, 236)


def shade(c, f):
    return tuple(int(v * f) for v in c)


FAR_METAL = shade(METAL, 0.62)

HIP_X = 24.0
HIP_BASE_Y = GROUND_Y - 15
L_THIGH, L_SHIN = 7, 8
TORSO_DX, TORSO_DY = 1.2, -9.0
L_UARM, L_FARM = 6, 6

DEG = math.radians


def pose(ph):
    s, c = math.sin(ph), math.cos(ph)
    return {
        "hip_y": HIP_BASE_Y - 0.8 * abs(c),
        "thigh_n": DEG(20) * s,  "knee_n": DEG(32) * max(0.0, math.sin(ph - 0.4)),
        "thigh_f": DEG(20) * -s, "knee_f": DEG(32) * max(0.0, math.sin(ph - 0.4 + math.pi)),
        "arm_n": DEG(17) * -s,   "arm_f": DEG(17) * s,
        "ant": DEG(9) * math.sin(ph * 2),
        "blink": 1 if math.sin(ph * 2) > 0.2 else 0,
    }


def fk(p0, ang, ln):
    return (p0[0] + math.sin(ang) * ln, p0[1] + math.cos(ang) * ln)


def render(d, P, segs):
    hip = (HIP_X, P["hip_y"])
    chest = (hip[0] + TORSO_DX, hip[1] + TORSO_DY)
    shoulder = (chest[0], chest[1] + 2)

    def cap(q, col, r=1):
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)

    def leg(tag, mcol):
        th = P["thigh_" + tag]
        j = fk(hip, th, L_THIGH)
        e = fk(j, th - P["knee_" + tag], L_SHIN)
        d.line([hip, j], fill=mcol, width=3)
        d.line([j, e], fill=mcol, width=3)
        cap(j, JOINT_C)
        cap(e, JOINT_C)
        d.rectangle([e[0] - 1, e[1], e[0] + 4, e[1] + 1], fill=DARK)   # 平腳板
        segs.extend([("thigh." + tag, hip, j), ("shin." + tag, j, e)])

    def arm(tag, mcol):
        a = P["arm_" + tag]
        j = fk(shoulder, a, L_UARM)
        e = fk(j, a - DEG(10), L_FARM)
        d.line([shoulder, j], fill=mcol, width=2)
        d.line([j, e], fill=mcol, width=2)
        cap(j, JOINT_C)
        d.rectangle([e[0] - 1, e[1] - 1, e[0] + 1, e[1] + 1], fill=mcol)
        segs.extend([("upperarm." + tag, shoulder, j), ("forearm." + tag, j, e)])

    arm("f", FAR_METAL)
    leg("f", FAR_METAL)
    d.line([hip, chest], fill=METAL, width=5)                          # 軀幹
    segs.append(("spine", hip, chest))
    core = (int(chest[0]), int(chest[1]) + 3)
    d.point(core, fill=GLOW if P["blink"] else shade(GLOW, 0.45))      # 胸口核心
    leg("n", METAL)
    arm("n", METAL)

    hx, hy = chest[0] + 2.0, chest[1] - 5.5                            # 方形頭
    d.rectangle([hx - 4, hy - 3, hx + 4, hy + 3], fill=METAL)
    d.line([(hx - 2, hy), (hx + 3, hy)],
           fill=GLOW if P["blink"] else shade(GLOW, 0.45))             # 眼帶
    d.line([(chest[0], chest[1] + 1), (hx, hy + 3)], fill=METAL, width=2)
    base = (hx, hy - 3)
    tip = fk(base, DEG(180) + P["ant"], 5)
    d.line([base, tip], fill=METAL, width=1)                           # 天線
    d.point(tip, fill=(255, 120, 120) if P["blink"] else (90, 60, 66))
    segs.extend([("neck", (chest[0], chest[1] + 1), (hx, hy + 3)),
                 ("head", (hx, hy), (hx, hy)),
                 ("antenna", base, tip)])


def frame(i, mode="normal"):
    P = pose(i / FRAMES * 2 * math.pi)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, GROUND_Y + 1, S, GROUND_Y + 2], fill=(58, 58, 84))
    hop = max(0.0, math.sin((i / FRAMES) * 2 * math.pi))
    sx = 1 + 0.15 * (1 - hop) * math.cos((i / FRAMES) * 2 * math.pi)
    srx = 9 * sx + 2
    d.ellipse([HIP_X - srx, GROUND_Y - 1, HIP_X + srx, GROUND_Y + 1],
              fill=((17, 17, 28) if mode == "normal" else (60, 60, 90)))

    char = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(char)
    segs = []
    render(cd, P, segs)

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
    gif[0].save("robot.gif", save_all=True, append_images=gif[1:], duration=dur, loop=0)
    rgif = [up(f) for f in rig]
    rgif[0].save("robot_rig.gif", save_all=True, append_images=rgif[1:], duration=dur,
                 loop=0, disposal=2, transparency=0)

    out = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(normal):
        out.paste(f_, (i_ * S, 0))
    out.save("robot_sheet.png")
    out.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("robot_sheet@8x.png")

    outr = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(rig):
        outr.paste(f_, (i_ * S, 0))
    outr.save("robot_rig.png")
    outr.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("robot_rig@8x.png")

    meta = {
        "name": "robot_walk",
        "rig": {"bones": ["pelvis", "thigh.L/R", "shin.L/R", "spine",
                          "upperarm.L/R", "forearm.L/R", "head", "antenna"],
                "method": "forward-kinematics from joint angles"},
        "frameSize": [S, S], "frameCount": FRAMES, "fps": FPS, "loop": True,
        "files": {"previewGif": "robot.gif", "rigPreviewGif": "robot_rig.gif",
                  "spriteSheetLogical": "robot_sheet.png",
                  "spriteSheetScaled": "robot_sheet@8x.png",
                  "rigSheetScaled": "robot_rig@8x.png", "scale": SCALE},
    }
    with open("robot.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done:", FRAMES, "frames (normal + rig)")


if __name__ == "__main__":
    main()
