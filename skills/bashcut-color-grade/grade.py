#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=1.26", "pillow>=10"]
# ///
"""Make .cube LUTs for colour looks, preview them on real frames and measure footage colour.

  grade.py looks                                     # list looks in looks.json
  grade.py lut <look|params.json> -o OUT.cube [--size 33]
  grade.py match IN.mp4 <look> -o OUT.cube           # look + automatic exposure/white balance for this footage
  grade.py preview IN.mp4 OUT.cube -o sheet.jpg [--n 6]   # before | after on n frames (for looking only)
  grade.py measure IN.mp4 [--n 12]                   # black/white point, saturation, tint per luma band

Apply the result in BashCut with `bashcut luts import OUT.cube`, then an adjustment item or `looks save`.
Needs ffmpeg/ffprobe on PATH. Run with `uv run grade.py ...` (uv installs numpy and Pillow on first run).

Parameters (all optional; 0 / 1 = unchanged):
  exposure (stops), wb [R,G,B] multipliers, lift/gamma/gain [R,G,B] (ASC-CDL style),
  black 0-0.1 (lift the black point = matte), white 0.85-1 (roll off highlights),
  contrast (S-curve around pivot, 0.3 = medium), pivot (0.4), sat, sat_shadow, sat_high,
  split {"shadow": [R,G,B], "high": [R,G,B]} offsets, hue_shifts [{"hue","width","shift","sat"}],
  skin_protect 0-1 (default 0.6), fade 0-0.2 (mix with grey for an old-film look).
"""
import argparse, json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LOOKS = os.path.join(HERE, "looks.json")


def load_look(name):
    if os.path.exists(name):
        return json.load(open(name))
    looks = json.load(open(LOOKS, encoding="utf-8"))
    if name not in looks or name.startswith("_"):
        sys.exit(f"no look '{name}'. Looks: {', '.join(k for k in looks if not k.startswith('_'))}")
    return looks[name]["params"]


def luma(c):
    return c[..., 0] * 0.2126 + c[..., 1] * 0.7152 + c[..., 2] * 0.0722


def rgb2hsv(c):
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    mx, mn = c.max(-1), c.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rm = m & (mx == r)
    gm = m & (mx == g) & ~rm
    bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = (b - r)[gm] / d[gm] + 2
    h[bm] = (r - g)[bm] / d[bm] + 4
    return h * 60, np.where(mx > 0, d / np.maximum(mx, 1e-6), 0), mx


def hsv2rgb(h, s, v):
    h = (h % 360) / 60
    i = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    out = np.stack([np.choose(i, [v, q, p, p, t, v]), np.choose(i, [t, v, v, q, p, p]),
                    np.choose(i, [p, p, t, v, v, q])], -1)
    return out


def apply(c, P):
    """c: (...,3) float 0-1 (Rec709 display). Returns the same shape."""
    c = c.copy()
    c *= 2 ** P.get("exposure", 0)
    c *= np.array(P.get("wb", [1, 1, 1]), np.float32)
    lift = np.array(P.get("lift", [0, 0, 0]), np.float32)
    gain = np.array(P.get("gain", [1, 1, 1]), np.float32)
    gamma = np.array(P.get("gamma", [1, 1, 1]), np.float32)
    c = np.clip(c * gain + lift * (1 - c), 0, None)
    c = np.power(np.clip(c, 0, 4), 1 / gamma)
    k = P.get("contrast", 0)
    if k:
        piv = P.get("pivot", 0.4)
        x = np.clip(c, 0, 1)
        # logistic S-curve, normalised so 0->0 and 1->1
        s = 1 + 8 * k
        f = lambda v: 1 / (1 + np.exp(-s * (v - piv)))
        c = (f(x) - f(0)) / (f(1) - f(0))
    # shadow/highlight weights from luma (for split toning and per-band saturation)
    y = np.clip(luma(c), 0, 1)[..., None]
    w_sh = np.clip(1 - y / 0.45, 0, 1) ** 1.5
    w_hi = np.clip((y - 0.5) / 0.5, 0, 1) ** 1.2
    h, s, v = rgb2hsv(np.clip(c, 0, 1))
    skin = np.exp(-((((h - 25 + 180) % 360) - 180) / 22) ** 2) * np.clip(s * 3, 0, 1)
    protect = 1 - P.get("skin_protect", 0.6) * skin[..., None]
    # saturation
    sat = P.get("sat", 1) * (1 + (P.get("sat_shadow", 1) - 1) * w_sh[..., 0]) * (1 + (P.get("sat_high", 1) - 1) * w_hi[..., 0])
    for hs in P.get("hue_shifts", []):
        d = (((h - hs["hue"] + 180) % 360) - 180)
        wgt = np.exp(-(d / hs.get("width", 30)) ** 2) * (1 - P.get("skin_protect", 0.6) * skin)
        h = h + hs.get("shift", 0) * wgt
        sat = sat * (1 + (hs.get("sat", 1) - 1) * wgt)
    c = hsv2rgb(h, np.clip(s * sat, 0, 1), v)
    sp = P.get("split")
    if sp:
        c = c + protect * (w_sh * np.array(sp.get("shadow", [0, 0, 0])) + w_hi * np.array(sp.get("high", [0, 0, 0])))
    blk, wht = P.get("black", 0), P.get("white", 1)
    c = blk + np.clip(c, 0, 1) * (wht - blk)
    fd = P.get("fade", 0)
    if fd:
        c = c * (1 - fd) + 0.5 * fd
    return np.clip(c, 0, 1)


def write_cube(P, out, size=33, title="look"):
    g = np.linspace(0, 1, size, dtype=np.float32)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")  # .cube: R varies fastest
    c = np.stack([r, gg, b], -1).reshape(-1, 3)
    o = apply(c, P)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w") as f:
        f.write(f'TITLE "{title}"\nLUT_3D_SIZE {size}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        for row in o:
            f.write(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}\n")
    return out


def frames(p, n, w=480):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                             capture_output=True, text=True).stdout or 0)
    out = []
    for i in range(n):
        t = d * (i + 0.5) / n
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1", "-vf",
                            f"scale={w}:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if r.stdout:
            from PIL import Image
            import io
            out.append((t, np.asarray(Image.open(io.BytesIO(r.stdout)).convert("RGB"))))
    return out


def read_cube(path):
    rows, size = [], None
    for ln in open(path):
        ln = ln.strip()
        if ln.startswith("LUT_3D_SIZE"):
            size = int(ln.split()[1])
        elif ln and (ln[0].isdigit() or ln[0] in "-."):
            rows.append([float(x) for x in ln.split()])
    return size, np.array(rows, np.float32).reshape(size, size, size, 3)  # [b][g][r]


def apply_cube(img, path):
    size, L = read_cube(path)
    x = img.astype(np.float32) / 255 * (size - 1)
    i = np.clip(np.round(x).astype(int), 0, size - 1)  # nearest neighbour: good enough for looking
    return (L[i[..., 2], i[..., 1], i[..., 0]] * 255).astype(np.uint8)


def stats(a):
    f = a.astype(np.float32) / 255
    y = luma(f)
    q = np.percentile(y, [1, 5, 50, 95, 99]) * 100
    mx, mn = f.max(-1), f.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0).mean() * 100
    def tint(m):
        if m.sum() < 20:
            return None
        return [round(float((f[..., 0] - f[..., 2])[m].mean()) * 100, 1),
                round(float((f[..., 1] - (f[..., 0] + f[..., 2]) / 2)[m].mean()) * 100, 1)]
    return dict(black=q[0], p5=q[1], mid=q[2], p95=q[3], white=q[4], sat=sat,
                tint_shadow=tint(y < .25), tint_mid=tint((y >= .25) & (y < .7)), tint_high=tint(y >= .7))


def med(ss, k):
    v = [s[k] for s in ss if s[k] is not None]
    if not v:
        return None
    return np.round(np.median(np.array(v, np.float32), 0), 1).tolist()


def measure(p, n):
    ss = [stats(a) for _, a in frames(p, n, 320)]
    return {k: med(ss, k) for k in ss[0]}


def fmt(m):
    return (f"black {m['black']:.1f} | p5 {m['p5']:.1f} | mid {m['mid']:.1f} | p95 {m['p95']:.1f} | white {m['white']:.1f}"
            f" | sat {m['sat']:.1f} | tint shadow {m['tint_shadow']} mid {m['tint_mid']} high {m['tint_high']}")


def cmd_preview(src, cube, out, n):
    from PIL import Image, ImageDraw
    fs = frames(src, n)
    if not fs:
        sys.exit("could not read frames")
    h, w = fs[0][1].shape[:2]
    sheet = Image.new("RGB", (w * 2, h * len(fs)), "black")
    for i, (t, a) in enumerate(fs):
        sheet.paste(Image.fromarray(a), (0, i * h))
        sheet.paste(Image.fromarray(apply_cube(a, cube)), (w, i * h))
        d = ImageDraw.Draw(sheet)
        d.text((4, i * h + 4), f"original {t:.1f}s", fill="yellow")
        d.text((w + 4, i * h + 4), os.path.basename(cube), fill="yellow")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out, quality=85)
    print(out)


def cmd_match(src, look, out):
    """Bring this footage to the look's starting point (mid exposure, neutral mid tint), then apply the look."""
    L = json.load(open(LOOKS, encoding="utf-8"))[look]
    P = dict(L["params"])
    m = measure(src, 12)
    tgt_mid = L.get("target", {}).get("mid_before_look", 38)
    exp = float(np.clip(np.log2(max(tgt_mid, 1) / max(m["mid"], 1)), -1.5, 1.5)) * 0.8
    wb = [1, 1, 1]
    if m["tint_mid"]:
        rb, gm = m["tint_mid"]
        wb = [round(1 - rb / 200, 3), round(1 - gm / 150, 3), round(1 + rb / 200, 3)]
    P["exposure"] = round(P.get("exposure", 0) + exp, 2)
    P["wb"] = [round(a * b, 3) for a, b in zip(P.get("wb", [1, 1, 1]), wb)]
    write_cube(P, out, title=f"{look}-match")
    print(json.dumps(dict(footage=fmt(m), exposure=P["exposure"], wb=P["wb"], cube=out), indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["looks", "lut", "match", "preview", "measure"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("-o")
    ap.add_argument("--size", type=int, default=33)
    ap.add_argument("--n", type=int, default=6)
    o = ap.parse_args()
    if o.cmd == "looks":
        for k, v in json.load(open(LOOKS, encoding="utf-8")).items():
            if not k.startswith("_"):
                print(f"{k:18s} {v.get('description', '')}")
    elif o.cmd == "lut":
        print(write_cube(load_look(o.args[0]), o.o, o.size, os.path.splitext(os.path.basename(o.args[0]))[0]))
    elif o.cmd == "match":
        cmd_match(o.args[0], o.args[1], o.o)
    elif o.cmd == "preview":
        cmd_preview(o.args[0], o.args[1], o.o, o.n)
    elif o.cmd == "measure":
        print(fmt(measure(o.args[0], o.n)))
