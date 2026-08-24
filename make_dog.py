"""Quadruped pixel dog — skeletal walk cycle (side view, trot gait).

骨架層級：脊柱（肩→髖，水平）＋ 前腿×2 ＋ 後腿×2（各兩節）
         ＋ 頭頸 ＋ 尾。步態 = trot 對角步：對角兩腳同步，相位差 π。

Outputs: dog.gif / dog_sheet.png / dog_sheet@8x.png / dog_rig.* / dog.json
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


def shade(c, f):
    return tuple(int(v * f) for v in c)


NEAR = {
    "fur":   (168, 116, 74),
    "fur_d": (120, 82, 52),
    "paw":   (60, 44, 34),
    "ear":   (96, 64, 40),
    "nose":  (30, 26, 28),
    "tongue": (222, 108, 118),
}
FAR = {k: shade(v, 0.62) for k, v in NEAR.items()}

SPINE_Y = GROUND_Y - 16
SH_X = 17
HIP_XD = 31
L_UP, L_LO = 7, 7
HEAD_R = 4

DEG = math.radians


def pose(ph):
    s = math.sin(ph)
    wag = math.sin(ph * 2)
    return {
        "bob": 0.8 * abs(math.cos(ph)),
        "up_n": DEG(22) * s,  "lo_n": DEG(38) * max(0.0, math.sin(ph - 0.5)),
        "up_f": DEG(22) * -s, "lo_f": DEG(38) * max(0.0, math.sin(ph - 0.5 + math.pi)),
        "tail1": DEG(18) * wag, "tail2": DEG(24) * wag,
        "head_nod": DEG(6) * s,
    }


def fk(p0, ang, ln):
    return (p0[0] + math.sin(ang) * ln, p0[1] + math.cos(ang) * ln)


def render(d, P, pal, segs, sy):
    sh = (SH_X, sy)
    hp = (HIP_XD, sy)

    def cap(q, col, r=1):
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)

    def leg(tag, base, lp):
        ua = P["up_" + tag]
        j = fk(base, ua, L_UP)
        e = fk(j, ua - P["lo_" + tag], L_LO)
        d.line([base, j], fill=lp["fur"], width=3)
        d.line([j, e], fill=lp["fur_d"], width=3)
        cap(j, lp["fur"])
        d.line([e, (e[0] + 3, e[1])], fill=lp["paw"], width=2)
        segs.extend([("leg_up." + tag, base, j), ("leg_lo." + tag, j, e)])

    # 畫序：遠側腿組 → 尾 → 身軀 → 近側腿組
    leg("f", sh, FAR)               # 遠前（相位由 up_f 控）
    leg("n", hp, NEAR)              # 近後（與遠前同組＝對角步態）
    t0 = (HIP_XD - 1, sy - 1)
    t1 = fk(t0, DEG(140) + P["tail1"], 5)
    t2 = fk(t1, DEG(150) + P["tail1"] + P["tail2"], 4)
    d.line([t0, t1], fill=pal["fur"], width=2)
    d.line([t1, t2], fill=pal["fur_d"], width=2)
    cap(t2, pal["fur"])
    segs.append(("tail", t0, t2))

    d.line([sh, hp], fill=pal["fur"], width=5)
    segs.append(("spine", sh, hp))
    leg("n", sh, NEAR)              # 近前
    leg("f", hp, FAR)               # 遠後

    hx = SH_X + 9
    hy = SPINE_Y - 5 + (sy - SPINE_Y) + P["head_nod"] * 4
    neck_end = (hx - 3, hy + 3)
    d.line([(SH_X, sy - 2), neck_end], fill=pal["fur"], width=3)
    segs.append(("neck", (SH_X, sy - 2), neck_end))
    d.ellipse([hx - HEAD_R, hy - HEAD_R, hx + HEAD_R, hy + HEAD_R], fill=pal["fur"])
    d.line([(hx + 3, hy - 1), (hx + 6, hy)], fill=pal["fur_d"], width=2)
    d.point((hx + 6, hy), fill=pal["nose"])
    d.polygon([(hx - 1, hy - HEAD_R), (hx + 2, hy - HEAD_R - 1), (hx, hy - HEAD_R + 2)],
              fill=pal["ear"])
    if int(P["head_nod"] * 10) % 2 == 0:
        d.point((hx + 5, hy + 2), fill=pal["tongue"])
    segs.append(("head", (hx, hy), (hx, hy)))


def frame(i, mode="normal"):
    P = pose(i / FRAMES * 2 * math.pi)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, GROUND_Y + 1, S, GROUND_Y + 2], fill=(58, 58, 84))
    sy = SPINE_Y - P["bob"]
    srx = 12
    d.ellipse([24 - srx, GROUND_Y - 1, 24 + srx, GROUND_Y + 1],
              fill=((17, 17, 28) if mode == "normal" else (60, 60, 90)))

    char = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(char)
    segs = []
    render(cd, P, NEAR, segs, sy)

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
    gif[0].save("dog.gif", save_all=True, append_images=gif[1:], duration=dur, loop=0)
    rgif = [up(f) for f in rig]
    rgif[0].save("dog_rig.gif", save_all=True, append_images=rgif[1:], duration=dur, loop=0,
                 disposal=2, transparency=0)

    out = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(normal):
        out.paste(f_, (i_ * S, 0))
    out.save("dog_sheet.png")
    out.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("dog_sheet@8x.png")

    outr = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(rig):
        outr.paste(f_, (i_ * S, 0))
    outr.save("dog_rig.png")
    outr.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("dog_rig@8x.png")

    meta = {
        "name": "dog_walk",
        "rig": {"bones": ["spine", "neck", "head", "tail",
                          "leg_front.L/R (upper+lower)", "leg_back.L/R (upper+lower)"],
                "method": "forward-kinematics, trot gait (diagonal pairs)"},
        "frameSize": [S, S], "frameCount": FRAMES, "fps": FPS, "loop": True,
        "files": {"previewGif": "dog.gif", "rigPreviewGif": "dog_rig.gif",
                  "spriteSheetLogical": "dog_sheet.png",
                  "spriteSheetScaled": "dog_sheet@8x.png",
                  "rigSheetScaled": "dog_rig@8x.png", "scale": SCALE},
    }
    with open("dog.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done:", FRAMES, "frames (normal + rig)")


if __name__ == "__main__":
    main()
