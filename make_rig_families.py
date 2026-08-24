"""Educational chart: the ~8 skeletal body-plan families in 2D character animation."""
import math

from PIL import Image, ImageDraw, ImageFont

SC = 4
W, H = 130, 130
BONE = (255, 170, 40)
JOINT = (120, 255, 160)
BODY = (110, 160, 235)
DIM = (150, 155, 185)


def panel(draw_tag):
    img = Image.new("RGB", (W * SC, H * SC), (24, 24, 38))
    d = ImageDraw.Draw(img)
    cx = W // 2
    draw_tag(d, cx)
    return img


def stick(d, pts, w=2, col=BONE):
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=col, width=w)


def dot(d, q, r=2, col=JOINT):
    d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)


def p_humanoid(d, cx):
    gy = 108
    hip = (cx, gy - 34)
    chest = (cx, gy - 52)
    head = (cx + 3, gy - 64)
    stick(d, [hip, chest], 3, BODY)                       # spine
    for sgn in (-1, 1):                                    # legs
        k = (hip[0] + sgn * 7, gy - 18); a = (k[0] + sgn * 3, gy)
        stick(d, [hip, k, a]); dot(d, k)
    for sgn in (-1, 1):                                    # arms
        e = (chest[0] + sgn * 9, chest[1] + 12); h = (e[0] + sgn * 5, e[1] + 10)
        stick(d, [(chest[0], chest[1] + 3), e, h]); dot(d, e)
    d.ellipse([head[0] - 8, head[1] - 8, head[0] + 8, head[1] + 8], outline=BONE, width=2)
    dot(d, hip)


def p_quadruped(d, cx):
    gy = 104
    sy = gy - 26
    sh, hp = (cx - 16, sy), (cx + 14, sy)
    stick(d, [sh, hp], 3, BODY); dot(d, sh); dot(d, hp)
    for bx in (sh[0], hp[0]):
        for sgn in (-1, 1):
            j = (bx + sgn * 4, sy + 13); f_ = (j[0] + sgn * 1, gy)
            stick(d, [(bx, sy), j, f_]); dot(d, j)
    hd = (sh[0] - 10, sy - 12)
    stick(d, [sh, (sh[0] - 5, sy - 6), hd])
    d.ellipse([hd[0] - 6, hd[1] - 6, hd[0] + 6, hd[1] + 6], outline=BONE, width=2)
    t1 = (hp[0] + 9, sy - 9); t2 = (t1[0] + 8, sy - 14)
    stick(d, [hp, t1, t2])


def p_bird(d, cx):
    gy = 100
    hip = (cx, gy - 20)
    chest = (cx + 4, gy - 38)
    stick(d, [hip, chest], 3, BODY)
    for sgn in (-1, 1):                                    # thin legs
        a = (hip[0] + sgn * 3, gy - 8); f_ = (a[0], gy)
        stick(d, [hip, a, f_])
    wk = (chest[0] - 12, chest[1] + 2)                     # wing fold
    wt = (wk[0] - 6, chest[1] + 14)
    stick(d, [chest, wk, wt])
    hd = (chest[0] + 8, chest[1] - 10)
    stick(d, [chest, hd])
    d.ellipse([hd[0] - 5, hd[1] - 5, hd[0] + 5, hd[1] + 5], outline=BONE, width=2)
    d.line([(hd[0] + 4, hd[1]), (hd[0] + 10, hd[1] + 2)], fill=BONE, width=1)  # beak
    tail = (hip[0] - 10, gy - 26)
    stick(d, [hip, tail])


def p_serpent(d, cx):
    gy = 96
    pts = []
    for i in range(11):
        x = cx - 40 + i * 8
        y = gy - 14 + int(math.sin(i * 0.85) * 9)
        pts.append((x, y))
    stick(d, pts, 2)
    for q in pts[::2]:
        dot(d, q, 1)
    hd = pts[-1]
    d.ellipse([hd[0] - 2, hd[1] - 5, hd[0] + 7, hd[1] + 5], outline=BONE, width=2)


def p_fish(d, cx):
    cy = 70
    nose = (cx - 28, cy)
    stick(d, [(nose[0], cy), (cx - 10, cy - 10), (cx + 8, cy), (cx - 10, cy + 10), nose],
          2, BODY)
    tf = (cx + 20, cy)
    stick(d, [(cx + 8, cy), tf, (tf[0] + 6, cy - 9)], 2)
    stick(d, [tf, (tf[0] + 6, cy + 9)])
    stick(d, [(cx - 6, cy - 9), (cx + 2, cy - 17)])        # dorsal
    stick(d, [(cx - 14, cy + 8), (cx - 20, cy + 15)])      # pelvic
    dot(d, (cx - 22, cy - 2), 1)


def p_blob(d, cx):
    gy = 106
    for k, r in ((0, 22), (1, 19), (2, 24)):               # squash cycle hint
        pass
    d.ellipse([cx - 24, gy - 30, cx + 24, gy], fill=(70, 90, 140), outline=BODY, width=2)
    d.ellipse([cx - 10, gy - 22, cx - 2, gy - 14], fill=(240, 240, 250))
    d.ellipse([cx + 4, gy - 22, cx + 12, gy - 14], fill=(240, 240, 250))
    d.text((cx - 20, 12), "NO BONES", fill=DIM)


def p_arthropod(d, cx):
    gy = 100
    sy = gy - 24
    d.ellipse([cx - 22, sy - 10, cx + 18, sy + 10], outline=BODY, width=2)
    hd = (cx + 24, sy - 2)
    d.ellipse([hd[0] - 6, hd[1] - 6, hd[0] + 6, hd[1] + 6], outline=BONE, width=2)
    for i, x in enumerate(range(cx - 18, cx + 16, 7)):
        sgn = -1 if i % 2 == 0 else 1
        k = (x + sgn * 3, sy + 10); f_ = (k[0] + sgn * 2, gy)
        stick(d, [(x, sy), k, f_]); dot(d, k, 1)
    stick(d, [(hd[0], sy - 5), (hd[0] + 6, sy - 13)])      # antenna
    stick(d, [(hd[0], sy - 3), (hd[0] + 8, sy - 9)])


def p_floater(d, cx):
    gy = 92
    c = (cx, gy - 22)
    d.ellipse([c[0] - 20, c[1] - 20, c[0] + 20, c[1] + 20], fill=(70, 90, 140),
              outline=BODY, width=2)
    d.ellipse([c[0] - 9, c[1] - 8, c[0] - 1, c[1]], fill=(240, 240, 250))
    d.ellipse([c[0] + 3, c[1] - 8, c[0] + 11, c[1]], fill=(240, 240, 250))
    for i, x in enumerate(range(c[0] - 16, c[0] + 17, 8)):  # wisp tails
        stick(d, [(x, c[1] + 18), (x + 3, c[1] + 27), (x, c[1] + 36)], 1, DIM)
    d.text((c[0] - 16, 12), "NO LEGS", fill=DIM)


panels = [
    ("HUMANOID", p_humanoid, "human / knight / robot"),
    ("QUADRUPED", p_quadruped, "dog / horse / lion"),
    ("BIRD / WINGED", p_bird, "bird / bat / dragon"),
    ("SERPENT", p_serpent, "snake / worm / eel"),
    ("FISH", p_fish, "fish / whale / shark"),
    ("SOFT-BODY", p_blob, "slime / jelly / octopus"),
    ("ARTHROPOD", p_arthropod, "ant / spider / crab"),
    ("FLOATER", p_floater, "ghost / drone / wisp"),
]

try:
    tf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
    sf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
except Exception:
    tf = sf = ImageFont.load_default()

imgs = []
for title, fn, ex in panels:
    im = panel(fn)
    d = ImageDraw.Draw(im)
    d.text((10 * SC, 8 * SC), title, fill=(232, 236, 255), font=tf)
    d.text((10 * SC, 112 * SC), ex, fill=DIM, font=sf)
    imgs.append(im)

gap = 14 * SC
cols, rows = 4, 2
out = Image.new("RGB", (W * SC * cols + gap * (cols - 1), H * SC * rows + gap), (18, 18, 28))
for i, im in enumerate(imgs):
    out.paste(im, ((i % cols) * (W * SC + gap), (i // cols) * (H * SC + gap)))
out.save("rig_families.png")
print("ok", out.size)
