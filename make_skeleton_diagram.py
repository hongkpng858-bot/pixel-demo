"""Educational diagram: how a skeletal rig drives a pixel-art walk cycle."""
import math
from PIL import Image, ImageDraw

SC = 5            # upscale
W, H = 150, 110   # per-panel logical size


def fk(p0, ang, ln):
    return (p0[0] + math.sin(ang) * ln, p0[1] + math.cos(ang) * ln)


def draw_rig(d, ox, oy, ph, label_pose):
    """Draw one rig. ph=phase radians; label_pose adds annotations."""
    GY = oy + 88
    DEG = math.radians
    s, c = math.sin(ph), math.cos(ph)
    swing = lambda x: max(0.0, math.sin(x - 0.35)) ** 1.2
    P = {
        "hip_y": GY - 16 - 1.2 * abs(c),
        "thigh_n": DEG(24) * s, "knee_n": DEG(52) * swing(ph),
        "thigh_f": -DEG(24) * s, "knee_f": DEG(52) * swing(ph + math.pi),
        "arm_n": DEG(20) * -s, "elb_n": DEG(14),
        "arm_f": DEG(20) * s,
    }
    L_T, L_S, L_UA, L_FA = 13, 13, 10, 10
    hip = (ox + 75, P["hip_y"])
    chest = (hip[0] + 2, hip[1] - 15)
    shoulder = (chest[0], chest[1] + 3)

    def limb(p0, a1, l1, bend, l2):
        j = fk(p0, a1, l1)
        e = fk(j, a1 - bend, l2)
        d.line([p0, j], fill=(70, 120, 208), width=2)
        d.line([j, e], fill=(70, 120, 208), width=2)
        return p0, j, e

    # far limbs (dim)
    limb(shoulder, P["arm_f"], L_UA, DEG(12), L_FA)
    limb(hip, P["thigh_f"], L_T, P["knee_f"], L_S)
    # torso
    d.line([hip, chest], fill=(230, 90, 90), width=3)
    # near limbs
    near_leg = limb(hip, P["thigh_n"], L_T, P["knee_n"], L_S)
    near_arm = limb(shoulder, P["arm_n"], L_UA, P["elb_n"], L_FA)
    # head
    hc = (chest[0] + 3, chest[1] - 11)
    d.ellipse([hc[0] - 7, hc[1] - 7, hc[0] + 7, hc[1] + 7], outline=(240, 196, 152), width=2)

    # joint dots
    for q in (hip, chest, shoulder, near_leg[1], near_leg[2], near_arm[1]):
        r = 2
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r],
                  fill=(255, 210, 60), outline=(120, 90, 10))

    if label_pose:
        f = ImageFont.load_default()
        def txt(xy, s_, col=(200, 205, 235)):
            d.text(xy, s_, fill=col, font=f)
        txt((hip[0] + 8, hip[1] - 4), "HIP")
        txt((near_leg[1][0] + 8, near_leg[1][1]), "KNEE")
        txt((near_leg[2][0] - 20, near_leg[2][1] + 4), "ANKLE")
        txt((shoulder[0] - 34, shoulder[1] - 4), "SHOULDER")
        txt((near_arm[1][0] - 30, near_arm[1][1] + 2), "ELBOW")
        txt((hc[0] + 9, hc[1] - 4), "HEAD")
        txt((hip[0] - 22, GY - 26), "SPINE", (230, 120, 120))
        # angle arc at hip for near thigh
        ar = [hip[0] - 18, hip[1] - 18, hip[0] + 18, hip[1] + 18]
        start = -math.degrees(P["thigh_n"])
        d.arc(ar, 90 - 24 if s >= 0 else 90, 90 + start if s >= 0 else 90 - 24, fill=(255, 170, 40), width=1)
        txt((hip[0] - 30, hip[1] + 20), "theta", (255, 170, 40))
    # ground
    d.line([(ox + 15, GY), (ox + W - 15, GY)], fill=(90, 95, 130), width=1)


from PIL import ImageFont

def panel(title, ph, annotate=False):
    img = Image.new("RGB", (W * SC, H * SC), (24, 24, 38))
    d = ImageDraw.Draw(img)
    draw_rig(d, 0, 0, ph, annotate)
    try:
        tfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except Exception:
        tfont = ImageFont.load_default()
    d.text((12, 10), title, fill=(232, 236, 255), font=tfont)
    return img

p1 = panel("1. RIG  (all angles = rest)", 0.0001, annotate=True)
p2 = panel("2. POSE A  (phase = 25%)", math.pi / 2)
p3 = panel("3. POSE B  (phase = 75%)", 3 * math.pi / 2)

gap = 24
out = Image.new("RGB", (W * SC * 3 + gap * 2, H * SC), (18, 18, 28))
out.paste(p1, (0, 0)); out.paste(p2, (W * SC + gap, 0)); out.paste(p3, (W * SC * 2 + gap * 2, 0))
out.save("skeleton_explained.png")
print("ok", out.size)
