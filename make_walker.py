"""Skeleton-based pixel character — walk cycle.

真・骨架動畫：定義骨骼層級（髖→大腿→小腿、脊柱→頭、肩→上臂→前臂），
每帧只係計關節角度，再用正向運動學（FK）算出每個關節位置畫像素。
改 pose() 入面嘅角度參數就可以重新生成成個動作。

Outputs: walker.gif / walker_sheet.png / walker_sheet@8x.png / walker.json
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


def shade(c, f):
    return tuple(int(v * f) for v in c)


NEAR = {  # 近嗰邊手腳（面向右行）
    "skin": (240, 196, 152), "arm": (86, 140, 224),
    "pants": (64, 70, 96), "shoe": (36, 33, 46),
    "hair": (84, 54, 34), "torso": (70, 120, 208),
}
FAR = {k: shade(v, 0.62) for k, v in NEAR.items()}  # 遠嗰邊自動調暗

# ---- 骨架參數 ----
HIP_X = 24.0
L_THIGH, L_SHIN = 8, 8
L_UARM, L_FARM = 6, 6
TORSO_DX, TORSO_DY = 1.2, -9.0     # 髖 → 胸
HEAD_DX, HEAD_DY, HEAD_R = 2.0, -6.5, 4

DEG = math.radians


def pose(ph):
    """ph ∈ [0, 2π)。一個 walk cycle 嘅關節角度。"""
    s, c = math.sin(ph), math.cos(ph)
    swing = lambda x: max(0.0, math.sin(x - 0.35)) ** 1.2   # 邊隻腳喺盪腿相位
    return {
        "hip_y": HIP_BASE_Y - 1.2 * abs(c),                  # 重心上下（每步兩次）
        # 近腳 / 遠腳：大腿擺幅 ±24°，膝蓋只向後屈
        "thigh_n": DEG(24) * s,          "knee_n": DEG(52) * swing(ph),
        "thigh_f": -DEG(24) * s,         "knee_f": DEG(52) * swing(ph + math.pi),
        # 手反方向擺，手肘微屈
        "arm_n": DEG(20) * -s,           "elb_n": DEG(14) + DEG(12) * max(0.0, s),
        "arm_f": DEG(20) * s,            "elb_f": DEG(14),
    }


HIP_BASE_Y = GROUND_Y - (L_THIGH + L_SHIN)   # 髖基準高度 = 腳剛好掂地


def fk(p0, ang, ln):
    """由 p0 沿角度 ang（0=垂直向下，正=向前）伸長 ln。"""
    return (p0[0] + math.sin(ang) * ln, p0[1] + math.cos(ang) * ln)


def limb(d, p0, a1, l1, bend, l2, w, col):
    """兩節骨：p0→關節→末端，圓頭加粗。回傳末端點。"""
    j = fk(p0, a1, l1)
    e = fk(j, a1 - bend, l2)          # 屈曲令末段向後收
    r = max(1, w // 2)
    d.line([p0, j], fill=col, width=w)
    d.line([j, e], fill=col, width=w)
    for q in (p0, j):
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)
    return e


def frame(i, transparent=False):
    P = pose(i / FRAMES * 2 * math.pi)
    img = Image.new("RGBA" if transparent else "RGB", (S, S), (0, 0, 0, 0) if transparent else BG)
    d = ImageDraw.Draw(img)

    if not transparent:
        d.rectangle([0, GROUND_Y + 1, S, GROUND_Y + 2], fill=GROUND_C)
        d.ellipse([HIP_X - 7, GROUND_Y - 1, HIP_X + 7, GROUND_Y + 1], fill=SHADOW)

    hip = (HIP_X, P["hip_y"])
    chest = (hip[0] + TORSO_DX, hip[1] + TORSO_DY)
    shoulder = (chest[0], chest[1] + 1.5)

    def leg(P, pal):
        ank = limb(d, hip, P["thigh"], L_THIGH, P["knee"], L_SHIN, 3, pal["pants"])
        d.line([ank, (ank[0] + 3, ank[1] + 0.6)], fill=pal["shoe"], width=2)

    def arm(P, pal):
        hnd = limb(d, shoulder, P["arm"], L_UARM, P["elb"], L_FARM, 2, pal["arm"])
        d.ellipse([hnd[0] - 1, hnd[1] - 1, hnd[0] + 1, hnd[1] + 1], fill=pal["skin"])

    # 畫序：遠手 → 遠腳 → 身軀 → 近腳 → 近手 → 頭
    arm({k: P[k + "_f"] for k in ("arm", "elb")}, FAR)
    leg({k: P[k + "_f"] for k in ("thigh", "knee")}, FAR)

    d.line([hip, chest], fill=NEAR["torso"], width=4)

    leg({k: P[k + "_n"] for k in ("thigh", "knee")}, NEAR)
    arm({k: P[k + "_n"] for k in ("arm", "elb")}, NEAR)

    hc = (chest[0] + HEAD_DX, chest[1] + HEAD_DY)
    hr = HEAD_R
    d.ellipse([hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr], fill=NEAR["skin"])
    d.pieslice([hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr],
               180, 340, fill=NEAR["hair"])                     # 頭髮冚住上半
    d.point((hc[0] + 2, hc[1]), fill=(25, 22, 30))              # 眼（望右）
    d.line([(chest[0], chest[1] + 1), (hc[0], hc[1] + hr - 1)], fill=NEAR["skin"], width=2)
    return img


def main():
    dur = int(1000 / FPS)
    gif = [frame(i).resize((S * SCALE, S * SCALE), Image.NEAREST) for i in range(FRAMES)]
    gif[0].save("walker.gif", save_all=True, append_images=gif[1:], duration=dur, loop=0)

    strip = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i in range(FRAMES):
        strip.paste(frame(i, transparent=True), (i * S, 0))
    strip.save("walker_sheet.png")
    strip.resize((strip.width * SCALE, strip.height * SCALE), Image.NEAREST).save("walker_sheet@8x.png")

    meta = {
        "name": "walker_walk",
        "rig": {"bones": ["pelvis", "thigh.L/R", "shin.L/R", "spine", "upperarm.L/R", "forearm.L/R", "head"],
                "method": "forward-kinematics from joint angles"},
        "frameSize": [S, S], "frameCount": FRAMES, "fps": FPS, "loop": True,
        "files": {"previewGif": "walker.gif",
                  "spriteSheetLogical": "walker_sheet.png",
                  "spriteSheetScaled": "walker_sheet@8x.png", "scale": SCALE},
    }
    with open("walker.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done:", FRAMES, "frames")


if __name__ == "__main__":
    main()
