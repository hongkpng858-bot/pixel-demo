#!/usr/bin/env python3
"""Deterministic pixel-creature animation engine (Phase 1 of B4).

Any text AI can drive this: emit a JSON spec, run the script, get web-ready assets.

Spec (all keys optional except defaults are sensible):
  {"creature": "cat",        # keyword: see VOCAB below (or explicit family+species)
   "action":   "walk",       # family-appropriate action; default per family
   "seed":     "auto",       # "auto" = new creature every run | fixed value = reproducible
   "speed":    "normal",     # slow | normal | fast
   "palette":  {"body": "#56c466"},   # optional hex overrides
   "bg":       "night"}      # night | none (transparent gif)

Outputs to out/<name>/: <name>.gif, <name>_sheet.png, <name>_sheet@8x.png, <name>.json
Same contract as the hand-made generators: 16 frames x 32x32, 12.5fps, horizontal strip.

Usage:
  python3 generate.py '{"creature":"cat","seed":"mochi"}'
  python3 generate.py --spec spec.json --out mypet
"""
import argparse, colorsys, hashlib, json, math, os, random, sys, warnings
from PIL import Image, ImageDraw, ImageChops

S, FRAMES, SCALE, FPS = 32, 16, 8, 12.5
TAU = math.pi * 2
CLEAR = (0, 0, 0, 0)

def shade(c, f): return tuple(max(0, min(255, int(v * f))) for v in c)
def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0, min(1, s)), max(0, min(1, v)))
    return (int(r * 255), int(g * 255), int(b * 255))
def hx(c):
    c = c.lstrip("#"); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

# ---------------- seeding ----------------
def resolve_seed(v):
    if v in (None, "auto"):
        return random.SystemRandom().randrange(2**31)
    if isinstance(v, int): return v
    return int(hashlib.sha256(str(v).encode()).hexdigest()[:8], 16)

class R:
    """Seeded RNG: every appearance parameter comes from here."""
    def __init__(self, seed): self.g = random.Random(seed)
    def f(self, a, b): return self.g.uniform(a, b)
    def i(self, a, b): return self.g.randint(a, b)
    def pick(self, xs): return self.g.choice(xs)
    def chance(self, p): return self.g.random() < p
    def random(self): return self.g.random()

# ---------------- vocabulary: keyword -> rig/species ----------------
VOCAB = {
    "slime": ("blob", "slime"), "jelly": ("blob", "slime"), "ooze": ("blob", "slime"),
    "blob": ("blob", "slime"), "goo": ("blob", "slime"),
    "ghost": ("ghost", "ghost"), "spirit": ("ghost", "ghost"), "wraith": ("ghost", "ghost"),
    "cat": ("quad", "cat"), "kitten": ("quad", "cat"), "neko": ("quad", "cat"),
    "dog": ("quad", "dog"), "puppy": ("quad", "dog"), "shiba": ("quad", "dog"),
    "wolf": ("quad", "wolf"),
    "fox": ("quad", "fox"),
    "bird": ("bird", "bird"), "parrot": ("bird", "bird"), "chick": ("bird", "bird"),
    "fish": ("fish", "fish"), "goldfish": ("fish", "fish"),
    "bug": ("bug", "bug"), "beetle": ("bug", "bug"), "spider": ("bug", "bug"),
    "snake": ("serpent", "serpent"), "serpent": ("serpent", "serpent"),
    "dragon": ("serpent", "dragon"),
    "knight": ("biped", "knight"), "soldier": ("biped", "knight"), "hero": ("biped", "knight"),
    "human": ("biped", "walker"), "person": ("biped", "walker"), "walker": ("biped", "walker"),
    "robot": ("biped", "robot"), "mech": ("biped", "robot"), "bot": ("biped", "robot"),
}
DEFAULT_ACTION = {"blob": "hop", "ghost": "float", "quad": "walk", "bird": "fly",
                  "fish": "swim", "bug": "walk", "serpent": "slither", "biped": "walk"}

def resolve_creature(spec):
    fam = spec.get("family")
    if fam: return fam, spec.get("species") or ""
    word = str(spec.get("creature", "slime")).strip().lower()
    return VOCAB.get(word, ("blob", "slime"))

# ---------------- palettes ----------------
STYLES = {
    "cat":   [("cream", .09, .30, .88), ("brown", .06, .38, .52), ("orange", .05, .70, .85),
              ("grey", .60, .06, .68), ("black", .62, .04, .26)],
    "dog":   [("golden", .09, .55, .82), ("brown", .05, .45, .55), ("grey", .58, .05, .72)],
    "wolf":  [("grey", .58, .07, .55), ("dark", .60, .10, .35)],
    "fox":   [("orange", .04, .78, .88)],
    "bird":  [("blue", .58, .55, .80), ("red", .00, .65, .85), ("yellow", .12, .75, .92)],
    "fish":  [("orange", .07, .80, .92), ("tropical", .52, .65, .88)],
    "bug":   [("green", .30, .45, .62), ("red", .98, .55, .70), ("dark", .28, .30, .40)],
    "serpent":[("green", .33, .50, .70), ("purple", .75, .45, .68)],
    "dragon":[("green", .33, .55, .72), ("red", .99, .60, .75)],
}
def build_colors(species, rig, r, user):
    key = None
    if user and "body" in user: body = hx(user["body"]); key = "custom"
    elif species in STYLES:
        key, hs, ss, vs = None, None, None, None
        key, h, s, v = r.pick([(n, h, s, v) for n, h, s, v in STYLES[species]])
        body = hsv(h + r.f(-.02, .02), s + r.f(-.06, .06), v + r.f(-.06, .06))
    else:
        key = "wild"; body = hsv(r.random(), r.f(.45, .7), r.f(.6, .85))
    cols = {"body": body, "dark": shade(body, .42), "mid": shade(body, .72)}
    if rig == "quad":
        cols["belly"] = (238, 236, 228) if r.chance(.45) else shade(body, 1.25)
        cols["eye"] = r.pick([(255, 200, 60), (150, 225, 130), (130, 185, 255), (225, 225, 235)])
    if rig == "biped":
        cols["metal"] = (176, 182, 198); cols["tabard"] = hsv(r.random(), .55, .6)
    if user:
        for k, v in user.items():
            if k in cols: cols[k] = hx(v) if isinstance(v, str) else v
    return key, cols

# ---------------- per-rig parameters ----------------
def make_params(rig, species, r, cols):
    P = {"cols": cols, "style_key": cols.get("_key")}
    if rig == "blob":
        P.update(rx=r.f(8, 10.5), ry=r.f(6, 8.5), hop=r.f(2.5, 7),
                 big_eyes=r.chance(.5), spots=[(r.f(0, TAU), r.f(.1, .55)) for _ in range(r.i(0, 5))])
    elif rig == "ghost":
        P.update(rx=r.f(8, 10), h=r.f(11, 14), scallop=r.i(3, 5),
                 eye=r.pick(["dot", "oval"]), alpha=r.i(200, 240),
                 aura=r.chance(.35), tint=hsv(r.random(), .3, .95))
    elif rig == "quad":
        P.update(ear_h=r.f(4, 7) if species != "dog" else r.f(3, 5),
                 ear_floppy=species == "dog" and r.chance(.5),
                 tail_curl=r.f(.6, 1.5), tail_len=r.f(.8, 1.4),
                 stripes=r.chance(.55) and species in ("cat", "wolf"), stripe_n=r.i(3, 5),
                 spots=r.chance(.4) and species == "dog",
                 leg=r.f(9, 11.5), blen=r.f(13, 16), snout=species in ("dog", "wolf", "fox"))
    elif rig == "bird":
        P.update(wing=r.f(9, 12), beak=hsv(.10, .85, .95), crest=r.chance(.5),
                 roundness=r.f(.8, 1.1), leglet=r.chance(.4))
    elif rig == "fish":
        P.update(seg=7, amp=r.f(2.2, 3.6), fin=r.f(4, 6.5), dorsal=r.chance(.5),
                 stripe=r.chance(.5), eye_big=r.f(1.4, 2.2))
    elif rig == "bug":
        P.update(rad=r.f(5, 6.5), seg2=r.f(3.4, 4.4), legs=6,
                 antennae=r.chance(.8), shell_split=True, dots=r.i(0, 4))
    elif rig == "serpent":
        P.update(seg=7, amp=r.f(2.5, 4.2), thick=r.f(2.2, 3.2),
                 hood="dragon" in (species or "") or r.chance(.2), fangs=r.chance(.4))
    elif rig == "biped":
        P.update(leg=r.f(7, 9), arm=r.f(6, 8.5), head_r=r.f(4, 5.5),
                 shoulder=r.f(4.5, 6.5), helm=species == "knight",
                 antenna=species == "robot" and r.chance(.8), visor=species == "robot")
    return P

# ---------------- renderers (one frame each) ----------------
def render_blob(d, P, ph, amp):
    C = P["cols"]; cx = 16
    hop = max(0.0, math.sin(ph * TAU)) * P["hop"] * amp
    sx = 1 + .18 * (1 - hop / max(P["hop"], .1)) * math.cos(ph * TAU) - .12 * (hop > .1)
    sy = 2 - min(sx, 1.6)
    bottom = 27 - hop; RX, RY = P["rx"] * sx, P["ry"] * (sy if sy < 1 else 1 / sy)
    x0, x1 = int(cx - RX), int(cx + RX); top = max(0, int(bottom - RY * 2))
    for y in range(top, min(S, int(bottom) + 1)):
        for x in range(max(0, x0), min(S, x1 + 1)):
            nx = (x - cx) / RX; ny = (bottom - y) / RY; v = nx * nx + ny * ny
            if v <= 1:
                col = C["dark"] if v > .72 else (C["mid"] if ny < -.35 else C["body"])
                d.point((x, y), fill=col)
    ey = int(bottom - RY * 1.05); ew = 2 if P["big_eyes"] else 1
    for sg in (-1, 1):
        ex = cx + sg * max(2, int(RX * .35))
        if ew == 2: d.rectangle([ex - 1, ey - 1, ex, ey], fill=(20, 25, 30))
        else: d.point((ex, ey), fill=(20, 25, 30))
    for ang, rr in P["spots"]:
        px = int(cx + math.cos(ang) * RX * rr); py = int(bottom - abs(math.sin(ang)) * RY * (rr + .4))
        d.point((px, py), fill=shade(C["body"], 1.3))

def render_ghost(d, P, ph, amp):
    C = P["cols"]; bob = math.sin(ph * TAU) * 1.5 * amp
    cx = 16; rx = P["rx"]; top = 6 + bob; bot = top + P["h"]
    col = (*C["body"], P["alpha"]); dk = (*C["dark"], P["alpha"])
    for y in range(int(top), int(bot)):
        t = (y - top) / P["h"]
        wob = math.sin(t * math.pi * P["scallop"]) * 1.5 if t > .6 else 0
        half = rx * (1 - .15 * t ** 2) + wob
        x0, x1 = int(cx - half), int(cx + half)
        for x in range(max(0, x0), min(S, x1 + 1)):
            edge = x <= x0 + 1 or x >= x1 - 1
            d.point((x, y), fill=dk if edge else col)
    n = P["scallop"]
    for k in range(n):  # wavy bottom
        wx = cx - rx + (2 * rx) * (k + .5) / n
        wy = bot + math.sin(ph * TAU * 2 + k) * 1.2
        d.line([(wx - 1, bot - 1), (wx, wy)], fill=col)
    ey = int(top + 4)
    for sg in (-1, 1):
        ex = cx + sg * 3
        if P["eye"] == "dot": d.point((ex, ey), fill=(25, 22, 34))
        else: d.rectangle([ex - 1, ey - 1, ex, ey], fill=(25, 22, 34))
    if P["aura"]:
        for ang in range(0, 360, 30):
            ax = cx + math.cos(math.radians(ang)) * (rx + 2.5); ay = top + 3 + math.sin(math.radians(ang)) * 2
            d.point((int(ax), int(ay)), fill=(*P["tint"], 90))

def quad_leg(d, x0, y0, ph, L, col):
    a = math.sin(ph) * .45
    L1 = L * .55; L2 = L - L1
    kx = x0 + math.sin(a) * L1; ky = y0 + math.cos(a) * L1
    a2 = a * .35
    fx = kx + math.sin(a2) * L2; fy = ky + math.cos(a2) * L2
    d.line([(x0, y0), (kx, ky), (fx, fy)], fill=col, width=2)

def render_quad(d, P, ph, amp):
    C = P["cols"]; cyc = TAU * amp
    bob = int(round(math.sin(ph * cyc)))
    blen = P["blen"]; half = blen / 2; cx = 16
    shx, hpx = cx - half, cx + half
    ecy, erx, ery = 16.5 + bob, half + 3, 4.5
    bx, by = hpx + 2, 14 + bob
    pts = []
    tl = P["tail_len"]; tc = P["tail_curl"]
    for i in range(9):
        t = i / 8
        tx = bx + t * (4 + 2 * tl) + math.sin(ph * cyc) * 2 * t
        ty = by - t * 8 * tc * (1 - t * .12) - math.sin(t * math.pi) * 1.5 * tc
        pts.append((tx, ty))
    for a_, b_ in zip(pts, pts[1:]): d.line([a_, b_], fill=C["mid"], width=2)
    d.point(pts[-1], fill=C["dark"])
    gy = 19 + bob
    quad_leg(d, shx - 1, gy, ph * cyc + math.pi, P["leg"], C["dark"])
    quad_leg(d, hpx - 1, gy, ph * cyc, P["leg"], C["dark"])
    d.ellipse([shx - erx, ecy - ery, hpx + erx, ecy + ery], fill=C["body"])
    ecx = (shx + hpx) / 2
    if P["stripes"]:
        for k in range(P["stripe_n"]):
            sx = shx - erx + 2 + (2 * erx - 4) * k / max(1, P["stripe_n"] - 1)
            for y in range(int(ecy - ery), int(ecy) + 1):
                nx = (sx - ecx) / erx; ny = (y - ecy) / ery
                if nx * nx + ny * ny <= 1: d.point((sx, y), fill=C["dark"])
    if P["spots"]:
        for k in range(4):
            px = ecx + (-1) ** k * (2 + k % 2); py = ecy - 2 + (k % 3)
            d.point((int(px), int(py)), fill=C["dark"])
    for x in range(int(ecx) - 2, int(ecx) + 3):
        for y in range(int(ecy), int(ecy + ery) + 1):
            nx = (x - ecx) / erx; ny = (y - ecy) / ery
            if nx * nx + ny * ny <= 1: d.point((x, y), fill=C["belly"])
    quad_leg(d, shx + 1, gy, ph * cyc, P["leg"], C["mid"])
    quad_leg(d, hpx + 1, gy, ph * cyc + math.pi, P["leg"], C["mid"])
    hx_, hy_ = shx - 4, 12 + bob; eh = P["ear_h"]
    if P["ear_floppy"]:
        d.ellipse([hx_ - 6, hy_ - 3, hx_ - 3, hy_ + 2], fill=C["dark"])
        d.ellipse([hx_ + 3, hy_ - 3, hx_ + 6, hy_ + 2], fill=C["dark"])
    else:
        d.polygon([(hx_ - 4, hy_ - 2), (hx_ - 3, hy_ - 2 - eh), (hx_ - 1, hy_ - 3)], fill=C["mid"])
        d.polygon([(hx_ + 1, hy_ - 3), (hx_ + 3, hy_ - 2 - eh), (hx_ + 4, hy_ - 2)], fill=C["mid"])
    d.ellipse([hx_ - 4, hy_ - 4, hx_ + 4, hy_ + 4], fill=C["body"])
    if P["snout"]: d.rectangle([hx_ - 4, hy_ + 1, hx_ - 2, hy_ + 3], fill=C["belly"])
    d.point((hx_ - 2, hy_), fill=C["eye"]); d.point((hx_ + 2, hy_), fill=C["eye"])
    d.point((hx_, hy_ + 2), fill=(225, 145, 155))

def render_bird(d, P, ph, amp):
    C = P["cols"]; cyc = 1 if amp <= 1 else 2
    flap = math.sin(ph * TAU * cyc)
    cy = 15 - max(0, flap) * 2 * amp; cx = 16
    wy = cy - 3 - abs(flap) * 3
    d.polygon([(cx - 2, wy + 4), (cx - P["wing"], wy), (cx - 2, cy + 2)], fill=C["dark"])
    d.polygon([(cx + 2, wy + 4), (cx + P["wing"], wy), (cx + 2, cy + 2)], fill=C["dark"])
    rx, ry = 6 * P["roundness"], 5 * P["roundness"]
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=C["body"])
    for y in range(int(cy), int(cy + ry)):
        nx = 0; ny = (y - cy) / ry
        for x in range(int(cx) - 3, int(cx) + 4):
            nx = (x - cx) / rx
            if nx * nx + ny * ny <= .55: d.point((x, y), fill=shade(C["body"], 1.2))
    bk = P["beak"]
    d.polygon([(cx - 3, cy), (cx - 8, cy + 1), (cx - 3, cy + 2)], fill=bk)
    d.polygon([(cx + 3, cy), (cx + 8, cy + 1), (cx + 3, cy + 2)], fill=bk)
    d.point((cx - 3, cy - 2), fill=(20, 25, 30)); d.point((cx + 3, cy - 2), fill=(20, 25, 30))
    if P["crest"]:
        d.line([(cx, cy - ry), (cx + 1, cy - ry - 3)], fill=C["dark"], width=2)
    if P["leglet"] and amp >= 1:
        ly = cy + ry
        d.line([(cx - 2, ly), (cx - 3, ly + 3)], fill=P["beak"], width=1)
        d.line([(cx + 2, ly), (cx + 3, ly + 3)], fill=P["beak"], width=1)

def render_fish(d, P, ph, amp):
    C = P["cols"]; n = P["seg"]; ampw = P["amp"] * amp
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = 24 - t * 17
        y = 16 + math.sin(ph * TAU - t * 2.2) * ampw * (.3 + t)
        pts.append((x, y))
    th = P.get("thick", 3.2)
    for i in range(n - 1):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        w1 = th * (1 - .55 * i / (n - 1)); w2 = th * (1 - .55 * (i + 1) / (n - 1))
        steps = max(2, int(abs(xb - xa) + abs(yb - ya)) * 2)
        for s in range(steps + 1):
            t = s / steps
            x = xa + (xb - xa) * t; y = ya + (yb - ya) * t; w = w1 + (w2 - w1) * t
            d.ellipse([x - w, y - w * .8, x + w, y + w * .8],
                      fill=C["body"] if i < n - 3 else C["mid"])
    (tx, ty) = pts[-1]; (px, py) = pts[-2]
    dx, dy = tx - px, ty - py
    L = math.hypot(dx, dy) or 1
    ox, oy = -dy / L, dx / L; F = P["fin"]
    for sg in (1, -1):
        d.polygon([(tx, ty), (tx + dx * .8 + ox * F * sg, ty + dy * .8 + oy * F * sg),
                   (tx + dx * 1.4, ty + dy * 1.4)], fill=C["mid"])
    hx_, hy_ = pts[0]
    if P["dorsal"]:
        mx, my = pts[2]
        d.polygon([(mx - 1, my - th), (mx, my - th - 3), (mx + 1.5, my - th)], fill=C["dark"])
    if P["stripe"]:
        for i in (2, 4):
            x, y = pts[i]
            d.point((int(x), int(y - 2)), fill=C["dark"]); d.point((int(x), int(y)), fill=C["dark"])
    er = P["eye_big"]
    d.ellipse([hx_ - er, hy_ - er - 1, hx_ + er, hy_ + er - 1], fill=(18, 20, 26))

def render_bug(d, P, ph, amp):
    C = P["cols"]; cyc = TAU * amp
    cx, cy = 16, 17
    r1, r2 = P["rad"], P["seg2"]
    wig = math.sin(ph * cyc) * 1
    for sg in (-1, 1):
        hx_ = cx + sg * (r1 - 1)
        d.ellipse([hx_ - r2, cy - r2 + wig * sg * .3, hx_ + r2, cy + r2 + wig * sg * .3], fill=C["mid"])
        for k in (-1, 0, 1):
            lx = hx_ + k * 2.2
            sw = math.sin(ph * cyc + (k + 1) * 1.6 + (0 if sg > 0 else math.pi))
            fx = lx + sw * 2.5 * amp; fy = cy + r2 + 4 - abs(sw) * 1.2
            d.line([(lx, cy + r2 - 1), (fx, fy)], fill=C["dark"], width=1)
    d.ellipse([cx - r1, cy - r1 + wig * .2, cx + r1, cy + r1 + wig * .2], fill=C["body"])
    d.line([(cx, cy - r1 + wig * .2), (cx, cy + r1 + wig * .2)], fill=C["dark"])
    for k in range(P["dots"]):
        ang = k * 2.1; rr = r1 * .45
        d.point((int(cx + math.cos(ang) * rr), int(cy + math.sin(ang) * rr + wig * .2)), fill=C["dark"])
    hd = cx - r1 - 3
    d.ellipse([hd - 3, cy - 3, hd + 2, cy + 3], fill=C["mid"])
    d.point((hd - 1, cy - 1), fill=(18, 20, 26))
    if P["antennae"]:
        wa = math.sin(ph * cyc) * .3
        d.line([(hd, cy - 2), (hd - 3, cy - 5 + wa * 2)], fill=C["dark"], width=1)
        d.line([(hd - 1, cy - 2), (hd - 4, cy - 4 - wa * 2)], fill=C["dark"], width=1)

def render_serpent(d, P, ph, amp):
    C = P["cols"]; n = P["seg"]; aw = P["amp"] * amp
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = 27 - t * 21
        y = 16 + math.sin(ph * TAU - t * 2.6) * aw * (.4 + .6 * t)
        pts.append((x, y))
    th = P["thick"]
    for i in range(n - 1):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        steps = max(2, int((abs(xb - xa) + abs(yb - ya)) * 2))
        for s in range(steps + 1):
            t = s / steps
            x = xa + (xb - xa) * t; y = ya + (yb - ya) * t
            w = th * (1 - .5 * (i + t) / (n - 1))
            d.ellipse([x - w, y - w, x + w, y + w], fill=C["body"] if (i + int(t * 2)) % 3 else C["mid"])
    hx_, hy_ = pts[0]
    hr = th + 1.2
    if P["hood"]:
        d.ellipse([hx_ - hr - 1.5, hy_ - hr - 1.5, hx_ + hr + 1.5, hy_ + hr + 1.5], fill=C["mid"])
    d.ellipse([hx_ - hr, hy_ - hr, hx_ + hr, hy_ + hr], fill=C["body"])
    d.point((int(hx_ - 1), int(hy_ - 1)), fill=(220, 60, 60))
    d.point((int(hx_ + 1), int(hy_ - 1)), fill=(220, 60, 60))
    if P["fangs"]:
        d.point((int(hx_), int(hy_ + hr)), fill=(240, 240, 245))

def render_biped(d, P, ph, amp):
    C = P["cols"]; cyc = TAU * amp
    sp = P["shoulder"]; hipY = 19; chestY = hipY - sp - 2
    bob = int(round(math.sin(ph * cyc))) * .8
    hipY += bob; chestY += bob
    cx = 16
    def limb(x0, y0, ang, L, col, w=1):
        ex = x0 + math.sin(ang) * L; ey = y0 + math.cos(ang) * L
        d.line([(x0, y0), (ex, ey)], fill=col, width=w)
        return ex, ey
    for sg in (-1, 1):  # far arm+leg behind
        limb(cx + sg * 2, hipY, math.pi + sg * math.sin(ph * cyc) * .5, P["leg"], C["dark"], 2)
        limb(cx + sg * 2, chestY + 1, math.pi + sg * math.sin(ph * cyc + math.pi) * .55, P["arm"], C["dark"], 1)
    d.line([(cx, hipY), (cx, chestY)], fill=C["body"], width=3)
    if "tabard" in C:
        d.rectangle([cx - 1, chestY, cx + 1, hipY], fill=C["tabard"])
    for sg in (-1, 1):  # near limbs
        limb(cx + sg * 2, hipY, sg * math.sin(ph * cyc) * .5, P["leg"], C["mid"], 2)
        limb(cx + sg * 2, chestY + 1, sg * math.sin(ph * cyc + math.pi) * .55, P["arm"], C["mid"], 1)
    hr = P["head_r"]; hy_ = chestY - hr - 1
    if P["helm"]:
        d.rectangle([cx - hr, hy_ - hr - 1, cx + hr, hy_ - hr + 1], fill=C.get("metal", (176, 182, 198)))
        d.line([(cx, hy_ - hr - 1), (cx, hy_ - hr - 4)], fill=(220, 70, 80), width=2)
        d.rectangle([cx - hr, hy_ - 1, cx - hr + 1, hy_ + 1], fill=(25, 28, 36))
    elif P["visor"]:
        d.rectangle([cx - hr, hy_ - hr, cx + hr, hy_ + hr], fill=C.get("metal", (176, 182, 198)))
        d.rectangle([cx - hr + 1, hy_ - 1, cx + hr - 1, hy_], fill=(60, 220, 220))
        if P["antenna"]: d.line([(cx, hy_ - hr), (cx + 2, hy_ - hr - 3)], fill=C["dark"], width=1)
    else:
        d.ellipse([cx - hr, hy_ - hr, cx + hr, hy_ + hr], fill=shade(C["body"], 1.15))
        d.point((cx - 1, hy_), fill=(25, 28, 36)); d.point((cx + 1, hy_), fill=(25, 28, 36))

RENDER = {"blob": render_blob, "ghost": render_ghost, "quad": render_quad, "bird": render_bird,
          "fish": render_fish, "bug": render_bug, "serpent": render_serpent, "biped": render_biped}

NIGHT_BG = (27, 27, 41); NIGHT_GROUND = (58, 58, 84)
STARS = [(4, 5), (25, 3), (28, 9), (8, 12), (20, 7), (13, 3)]

def make_frame(rig, P, action, ph, bg):
    img = Image.new("RGBA", (S, S), CLEAR)
    d = ImageDraw.Draw(img)
    amp = {"slow": .6, "fast": 1.9}.get(_speed_ctx, 1.0)
    if bg:
        d.rectangle([0, 0, S, S], fill=NIGHT_BG)
        for sx, sy in STARS: d.point((sx, sy), fill=(200, 205, 235))
        d.rectangle([0, 26, S, S], fill=NIGHT_GROUND)
    RENDER[rig](d, P, ph, amp)
    return img

ACTIONS = {
    "blob": {"hop": {}, "bounce": {"amp_mode": "fast"}, "idle": {"amp_mode": "slow"}},
    "ghost": {"float": {}, "drift": {"amp_mode": "slow"}, "haunt": {"amp_mode": "fast"}},
    "quad": {"walk": {}, "run": {"amp_mode": "fast"}, "stroll": {"amp_mode": "slow"}},
    "bird": {"fly": {}, "soar": {"amp_mode": "slow"}, "flutter": {"amp_mode": "fast"}},
    "fish": {"swim": {}, "dart": {"amp_mode": "fast"}, "drift": {"amp_mode": "slow"}},
    "bug": {"walk": {}, "scuttle": {"amp_mode": "fast"}},
    "serpent": {"slither": {}, "hunt": {"amp_mode": "fast"}, "laze": {"amp_mode": "slow"}},
    "biped": {"walk": {}, "march": {"amp_mode": "slow"}, "run": {"amp_mode": "fast"}},
}
_speed_ctx = "normal"

def diff_px(a, b):
    dd = ImageChops.difference(a, b)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return sum(1 for q in dd.getdata() if q[3] > 0 or sum(q[:3]) > 0)

def generate(spec, outdir=None):
    global _speed_ctx
    seed = resolve_seed(spec.get("seed", "auto"))
    rig, species = resolve_creature(spec)
    action = spec.get("action") or DEFAULT_ACTION[rig]
    if action not in ACTIONS[rig]:
        action = DEFAULT_ACTION[rig]
    _speed_ctx = spec.get("speed", "normal")
    bgmode = spec.get("bg", "night")
    r = R(seed)
    _, cols = build_colors(species, rig, r, spec.get("palette"))
    cols["_key"] = _
    P = make_params(rig, species, r, cols)
    frames = [make_frame(rig, P, action, i / FRAMES, bgmode) for i in range(FRAMES)]

    tag = "auto%08x" % (seed & 0xffffffff) if spec.get("seed", "auto") in (None, "auto") \
        else hashlib.sha256(str(spec.get("seed")).encode()).hexdigest()[:6]
    label = species or rig
    name = "%s-%s-%s" % (label, action, tag)
    outdir = outdir or os.path.join("out", name)
    os.makedirs(outdir, exist_ok=True)

    sheet = Image.new("RGBA", (S * FRAMES, S), CLEAR)
    for i, f in enumerate(frames): sheet.paste(f, (i * S, 0))
    sheet.save(os.path.join(outdir, "%s_sheet.png" % name))
    sheet.resize((S * FRAMES * SCALE, S * SCALE), Image.NEAREST).save(
        os.path.join(outdir, "%s_sheet@8x.png" % name))
    frames[0].save(os.path.join(outdir, "%s.gif" % name), save_all=True,
                   append_images=frames[1:], duration=int(1000 / FPS), loop=0,
                   transparency=0, disposal=2)
    meta = {"name": name, "frameSize": [S, S], "frameCount": FRAMES, "fps": FPS,
            "loop": True, "layout": "horizontal-strip",
            "engine": "generate.py v1 (B4 phase 1)",
            "spec": {**spec, "resolvedSeed": seed},
            "files": {"previewGif": "%s.gif" % name,
                      "spriteSheetLogical": "%s_sheet.png" % name,
                      "spriteSheetScaled": "%s_sheet@8x.png" % name, "scale": SCALE}}
    with open(os.path.join(outdir, "%s.json" % name), "w") as fp:
        json.dump(meta, fp, indent=2)

    motion = [diff_px(frames[i], frames[(i + 1) % FRAMES]) for i in range(FRAMES)]
    ok = max(motion) >= 20 and sum(motion) / len(motion) >= 5 and \
        motion[-1] <= max(motion) * .9 + 20
    print("%s  seed=%s  motion peak=%d avg=%.1f  QA=%s" %
          (outdir, meta["spec"]["resolvedSeed"] if spec.get("seed") == "auto" else spec.get("seed"),
           max(motion), sum(motion) / len(motion), "PASS" if ok else "FAIL"))
    return outdir, name, ok

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?", help="JSON spec string")
    ap.add_argument("--spec", dest="specfile", help="path to spec json")
    ap.add_argument("--out", help="output directory override")
    a = ap.parse_args()
    if a.specfile:
        spec = json.load(open(a.specfile))
    elif a.spec:
        spec = json.loads(a.spec)
    else:
        spec = {}
    generate(spec, a.out)
