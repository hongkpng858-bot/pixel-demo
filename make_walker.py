"""Skeleton-based pixel character — walk cycle + X-ray rig view.

真・骨架動畫：定義骨骼層級（髖→大腿→小腿、脊柱→頭、肩→上臂→前臂），
每帧只係計關節角度，再用正向運動學（FK）算出每個關節位置畫像素。
改 pose() 入面嘅角度參數就可以重新生成成個動作。

Outputs:
  walker.gif / walker_sheet.png / walker_sheet@8x.png   — 正常版
  walker_rig.gif / walker_rig.png / walker_rig@8x.png   — X光骨架版（身體半透明＋骨頭高亮）
  walker.json
"""
import json
import math

from PIL import Image, ImageDraw

S = 48            # logical frame size
FRAMES = 16
SCALE = 8
FPS = 12.5
GROUND_Y = 44

BG = (27, 27, 41)
GROUND_C = (58, 58, 84)
SHADOW = (17, 17, 28)

RIG_BONE = (255, 170, 40)     # 骨頭：亮橙
RIG_JOINT = (120, 255, 160)   # 關節：熒光綠


def shade(c, f):
    return tuple(int(v * f) for v in c)


NEAR = {
    "skin": (240, 196, 152), "arm": (86, 140, 224),
    "pants": (64, 70, 96), "shoe": (36, 33, 46),
    "hair": (84, 54, 34), "torso": (70, 120, 208),
}
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
    """畫成個角色；同時將每段骨記錄入 segs（name, p0, p1）。"""
    hip = (HIP_X, P["hip_y"])
    chest = (hip[0] + TORSO_DX, hip[1] + TORSO_DY)
    shoulder = (chest[0], chest[1] + 1.5)

    def cap(q, col):
        r = 1
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)

    def leg(pal, tag):
        th, kn = P["thigh_" + tag], P["knee_" + tag]
        j = fk(hip, th, L_THIGH)
        e = fk(j, th - kn, L_SHIN)
        d.line([hip, j], fill=pal["pants"], width=3)
        d.line([j, e], fill=pal["pants"], width=3)
        cap(hip, pal["pants"]); cap(j, pal["pants"])
        d.line([e, (e[0] + 3, e[1] + 0.6)], fill=pal["shoe"], width=2)
        segs.extend([("thigh." + tag, hip, j), ("shin." + tag, j, e)])

    def arm(pal, tag):
        a, el = P["arm_" + tag], P["elb_" + tag]
        j = fk(shoulder, a, L_UARM)
        e = fk(j, a - el, L_FARM)
        d.line([shoulder, j], fill=pal["arm"], width=2)
        d.line([j, e], fill=pal["arm"], width=2)
        cap(shoulder, pal["arm"]); cap(j, pal["arm"])
        cap(e, pal["skin"])
        segs.extend([("upperarm." + tag, shoulder, j), ("forearm." + tag, j, e)])

    arm(FAR, "f")
    leg(FAR, "f")
    d.line([hip, chest], fill=NEAR["torso"], width=4)
    segs.append(("spine", hip, chest))
    leg(NEAR, "n")
    arm(NEAR, "n")

    hc = (chest[0] + HEAD_DX, chest[1] + HEAD_DY)
    hr = HEAD_R
    d.ellipse([hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr], fill=NEAR["skin"])
    d.pieslice([hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr], 180, 340, fill=NEAR["hair"])
    d.point((hc[0] + 2, hc[1]), fill=(25, 22, 30))
    d.line([(chest[0], chest[1] + 1), (hc[0], hc[1] + hr - 1)], fill=NEAR["skin"], width=2)
    return hc


def frame(i, mode="normal"):
    """mode: 'normal' 或 'rig'（X光）。回傳 RGBA。"""
    P = pose(i / FRAMES * 2 * math.pi)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, GROUND_Y + 1, S, GROUND_Y + 2], fill=GROUND_C)
    hop = max(0.0, math.sin((i / FRAMES) * 2 * math.pi))
    h = hop * 6
    sx = 1 + 0.18 * (1 - hop) * math.cos((i / FRAMES) * 2 * math.pi) - 0.12 * hop
    srx = 9 * sx * (1 - h / 14) + 2
    d.ellipse([HIP_X - srx, GROUND_Y - 1, HIP_X + srx, GROUND_Y + 1],
              fill=(SHADOW if mode == "normal" else (60, 60, 90)))

    char = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(char)
    segs = []
    hc = render_character(cd, P, segs)

    if mode == "rig":
        # 身體變半透明 X 光底
        a = char.getchannel("A").point(lambda v: int(v * 0.30))
        char.putalpha(a)
        img.alpha_composite(char)
        # 畫骨＋關節
        ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        joints = []
        for _, p0, p1 in segs:
            od.line([p0, p1], fill=RIG_BONE, width=1)
            joints += [p0, p1]
        seen = set()
        for q in joints:
            key = (int(q[0]), int(q[1]))
            if key in seen:
                continue
            seen.add(key)
            od.ellipse([q[0] - 1, q[1] - 1, q[0] + 1, q[1] + 1], fill=RIG_JOINT)
        od.ellipse([hc[0] - HEAD_R, hc[1] - HEAD_R, hc[0] + HEAD_R, hc[1] + HEAD_R],
                   outline=RIG_BONE, width=1)
        img.alpha_composite(ov)
    else:
        img.alpha_composite(char)
    return img


def strip(frames):
    out = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.paste(f, (i * S, 0))
    return out


def main():
    dur = int(1000 / FPS)

    normal = [frame(i, "normal") for i in range(FRAMES)]
    rig = [frame(i, "rig") for i in range(FRAMES)]

    up = lambda f: f.resize((S * SCALE, S * SCALE), Image.NEAREST)
    gif = [up(f).convert("RGB") for f in normal]
    gif[0].save("walker.gif", save_all=True, append_images=gif[1:], duration=dur, loop=0)
    rgif = [up(f) for f in rig]
    rgif[0].save("walker_rig.gif", save_all=True, append_images=rgif[1:], duration=dur, loop=0,
                 disposal=2, transparency=0)

    strip(normal).save("walker_sheet.png")
    strip(normal).resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("walker_sheet@8x.png")
    strip(rig).save("walker_rig.png")
    strip(rig).resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("walker_rig@8x.png")

    meta = {
        "name": "walker_walk",
        "rig": {"bones": ["pelvis", "thigh.L/R", "shin.L/R", "spine",
                          "upperarm.L/R", "forearm.L/R", "head"],
                "method": "forward-kinematics from joint angles"},
        "frameSize": [S, S], "frameCount": FRAMES, "fps": FPS, "loop": True,
        "files": {"previewGif": "walker.gif", "rigPreviewGif": "walker_rig.gif",
                  "spriteSheetLogical": "walker_sheet.png",
                  "spriteSheetScaled": "walker_sheet@8x.png",
                  "rigSheetScaled": "walker_rig@8x.png", "scale": SCALE},
    }
    with open("walker.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done:", FRAMES, "frames (normal + rig)")


if __name__ == "__main__":
    main()
