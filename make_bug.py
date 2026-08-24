"""Six-legged arthropod — tripod gait, segmented shell, waving antennae.

節肢家族：三對腿以「三腳架步態」行進（每邊前後腳＋另一邊中腳同步），
分節背殼＋擺動觸鬚。腿＝髖→股→脛兩節 FK。

Outputs: bug.gif / bug_sheet.png / bug_sheet@8x.png / bug_rig.* / bug.json
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

CARAPACE = (150, 92, 52)
CARAPACE_D = (108, 66, 38)
LEG_C = (84, 52, 32)
EYE_C = (24, 22, 26)

GY = 42
CY = 30

DEG = math.radians


def fk(p0, ang, ln):
    return (p0[0] + math.sin(ang) * ln, p0[1] + math.cos(ang) * ln)


def leg(cd, hx, phase_a, off, segs, tag):
    """兩節腿；off 決定屬邊組（0 或 π）。"""
    sw = DEG(16) * math.sin(phase_a + off)
    lift = max(0.0, math.sin(phase_a + off)) * 2.0
    hip = (hx, CY + 8)
    kn = fk(hip, DEG(90) + sw, 4)
    ft = (kn[0] + (2 if hx < 26 else -2) + sw * 4, GY - lift)
    cd.line([hip, kn], fill=LEG_C, width=2)
    cd.line([kn, ft], fill=LEG_C, width=1)
    segs.append((f"leg.{tag}", hip, ft))


def frame(i, mode="normal"):
    a = i / FRAMES * 2 * math.pi
    bob = 0.6 * abs(math.cos(a))
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    char = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(char)
    segs = []

    # 地面＋影子
    d = ImageDraw.Draw(img)
    d.rectangle([0, GY + 1, S, GY + 2], fill=(58, 58, 84))

    # 腿（畫先，喺身體底）——三對：x=15,23,31；tripod 分組
    for k, hx in enumerate((15, 23, 31)):
        off = 0 if k % 2 == 0 else math.pi      # 近側交替
        leg(cd, hx, a, off, segs, f"n{k}")
    for k, hx in enumerate((15, 23, 31)):
        off = math.pi if k % 2 == 0 else 0      # 遠側同近側相反
        col = None
        # 遠側腿調暗：直接畫深色
        sw = DEG(16) * math.sin(a + off)
        lift = max(0.0, math.sin(a + off)) * 2.0
        hip = (hx + 1, CY + 7)
        kn = fk(hip, DEG(90) + sw, 4)
        ft = (kn[0] + (2 if hx < 26 else -2) + sw * 4, GY - 1 - lift)
        cd.line([hip, kn], fill=CARAPACE_D, width=2)
        cd.line([kn, ft], fill=CARAPACE_D, width=1)
        segs.append((f"leg.f{k}", hip, ft))

    # 頭（先畫，俾殼蓋住少少）
    hd = (37, CY - 1 + bob)
    cd.ellipse([hd[0] - 4, hd[1] - 4, hd[0] + 5, hd[1] + 4], fill=CARAPACE)
    # 觸鬚兩條（擺動）
    for k, ang0 in ((0, -62), (1, -48)):
        tip = fk(hd, DEG(ang0 + 6 * math.sin(a * 2 + k)), 8)
        cd.line([(hd[0] + 2, hd[1] - 2), tip], fill=LEG_C, width=1)
        cd.point(tip, fill=EYE_C)
        segs.append((f"antenna.{k}", (hd[0] + 2, hd[1] - 2), tip))
    cd.point((hd[0] + 3, hd[1] - 1), fill=EYE_C)

    # 背殼（分節橢圓）
    sh_y = CY - 2 + bob
    cd.ellipse([11, sh_y - 8, 39, sh_y + 8], fill=CARAPACE, outline=CARAPACE_D)
    for k, xx in enumerate((19, 27)):
        cd.line([(xx, sh_y - 7), (xx, sh_y + 7)], fill=CARAPACE_D, width=1)
    cd.arc([13, sh_y - 9, 25, sh_y - 1], 180, 360, fill=CARAPACE_D, width=1)
    segs.append(("shell", (12, sh_y), (38, sh_y)))

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
        od.ellipse([11, sh_y - 8, 39, sh_y + 8], outline=RIG_BONE, width=1)
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
    gif[0].save("bug.gif", save_all=True, append_images=gif[1:], duration=dur, loop=0)
    rgif = [up(f) for f in rig]
    rgif[0].save("bug_rig.gif", save_all=True, append_images=rgif[1:], duration=dur,
                 loop=0, disposal=2, transparency=0)
    out = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(normal):
        out.paste(f_, (i_ * S, 0))
    out.save("bug_sheet.png")
    out.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("bug_sheet@8x.png")
    outr = Image.new("RGBA", (S * FRAMES, S), (0, 0, 0, 0))
    for i_, f_ in enumerate(rig):
        outr.paste(f_, (i_ * S, 0))
    outr.save("bug_rig.png")
    outr.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save("bug_rig@8x.png")
    meta = {
        "name": "bug_walk",
        "rig": {"bones": ["shell", "head", "antenna.x2", "legs.x6 (coxa+femur+tibia)"],
                "method": "tripod gait (alternating leg triangles)"},
        "frameSize": [S, S], "frameCount": FRAMES, "fps": FPS, "loop": True,
        "files": {"previewGif": "bug.gif", "rigPreviewGif": "bug_rig.gif",
                  "spriteSheetLogical": "bug_sheet.png",
                  "spriteSheetScaled": "bug_sheet@8x.png",
                  "rigSheetScaled": "bug_rig@8x.png", "scale": SCALE},
    }
    with open("bug.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done:", FRAMES, "frames (normal + rig)")


if __name__ == "__main__":
    main()
