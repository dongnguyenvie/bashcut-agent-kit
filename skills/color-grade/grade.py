#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=1.26", "pillow>=10"]
# ///
"""Make .cube LUTs for colour looks, preview them on real frames and measure footage colour.

  grade.py looks                                     # list looks in looks.json
  grade.py lut <look|params.json> -o OUT.cube [--size 33] [--exposure S] [--wb R,G,B]
  grade.py match IN.mp4 <look> [--n 12] [--exposure S] [--wb R,G,B]   # JSON: footage vs the look's ranges
  grade.py preview IN.mp4 OUT.cube -o sheet.jpg [--n 6]   # before | after on n frames (for looking only)
  grade.py measure IN.mp4 [--n 12] [--json]          # black/white point, saturation, tint per luma band

Nothing here picks a correction. `match` measures the footage, the footage with the look (plus only the exposure
and white balance you pass) and reports both against the look's reference ranges; it writes no file. You choose
exposure/wb from that report and pass them to `lut`. `--exposure` is added to the look's exposure (stops);
`--wb` multiplies the look's white balance. Scale 0-100, the same as `bashcut color measure`.

Apply the result in BashCut with `bashcut luts import OUT.cube`, then an adjustment item or `looks save`.
Needs ffmpeg/ffprobe on PATH. Run with `uv run grade.py ...` (uv installs numpy and Pillow on first run).

Parameters (all optional; 0 / 1 = unchanged):
  exposure (stops), wb [R,G,B] multipliers, lift/gamma/gain [R,G,B] (ASC-CDL style),
  black 0-0.1 (lift the black point = matte), white 0.85-1 (roll off highlights),
  contrast (S-curve around pivot, 0.3 = medium), pivot (0.4), sat, sat_shadow, sat_high,
  split {"shadow": [R,G,B], "high": [R,G,B]} offsets, hue_shifts [{"hue","width","shift","sat"}],
  skin_protect 0-1 (default 0.6), fade 0-0.2 (mix with grey for an old-film look).
"""
import argparse, json, os, re, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LOOKS = os.path.join(HERE, "looks.json")


def read_looks():
    with open(LOOKS, encoding="utf-8") as fh:
        return json.load(fh)


def load_look(name):
    if os.path.exists(name):
        with open(name, encoding="utf-8") as fh:
            return json.load(fh)
    looks = read_looks()
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
    with open(path) as fh:
        lines = fh.read().splitlines()
    for ln in lines:
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
    """a: uint8 RGB frame, or float 0-1."""
    f = a.astype(np.float32) / 255 if a.dtype == np.uint8 else a.astype(np.float32)
    y = luma(f)
    q = np.percentile(y, [1, 5, 50, 95, 99]) * 100
    mx, mn = f.max(-1), f.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0).mean() * 100
    def tint(m):
        if m.sum() < 20:
            return None
        return [round(float((f[..., 0] - f[..., 2])[m].mean()) * 100, 1),
                round(float((f[..., 1] - (f[..., 0] + f[..., 2]) / 2)[m].mean()) * 100, 1)]
    return dict(black=float(q[0]), p5=float(q[1]), mid=float(q[2]), p95=float(q[3]), white=float(q[4]), sat=float(sat),
                tint_shadow=tint(y < .25), tint_mid=tint((y >= .25) & (y < .7)), tint_high=tint(y >= .7))


def med(ss, k):
    v = [s[k] for s in ss if s[k] is not None]
    if not v:
        return None
    m = np.median(np.array(v, np.float64), 0)
    return [round(float(x), 1) for x in m] if m.ndim else round(float(m), 1)


def summarise(ss):
    return {k: med(ss, k) for k in ss[0]}


def measure(p, n):
    fs = frames(p, n, 320)
    if not fs:
        sys.exit(f"could not read frames from {p}")
    return summarise([stats(a) for _, a in fs])


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


def with_overrides(P, exposure=None, wb=None):
    """The look's params plus only what the caller passed: exposure adds stops, wb multiplies."""
    P = dict(P)
    if exposure is not None:
        P["exposure"] = round(P.get("exposure", 0) + exposure, 4)
    if wb is not None:
        P["wb"] = [round(a * b, 4) for a, b in zip(P.get("wb", [1, 1, 1]), wb)]
    return P


def outside(v, rng):
    """0 inside the range, v - low below it (negative), v - high above it (positive); None without a range."""
    if v is None or rng is None:
        return None
    lo, hi = rng
    if lo is not None and v < lo:
        return round(v - lo, 1)
    if hi is not None and v > hi:
        return round(v - hi, 1)
    return 0


def compare(m, target):
    """Footage stats m against a look's target {field: {ref, range, why}}: differences only, no verdict."""
    out = {}
    for k, t in target.items():
        v, ref, rng = m.get(k), t.get("ref"), t.get("range")
        if isinstance(v, list):
            refs = ref if isinstance(ref, list) else [None] * len(v)
            rngs = rng if isinstance(rng, list) else [None] * len(v)
            out[k] = dict(value=v,
                          minusRef=[None if r is None else round(a - r, 1) for a, r in zip(v, refs)],
                          outside=[outside(a, r) for a, r in zip(v, rngs)])
        else:
            out[k] = dict(value=v, minusRef=None if v is None or ref is None else round(v - ref, 1),
                          outside=outside(v, rng))
    return out


def cmd_match(src, look, n, exposure=None, wb=None):
    """Measure only: the footage, and the footage through the look (+ passed exposure/wb), against its ranges."""
    looks = read_looks()
    if look not in looks or look.startswith("_"):
        sys.exit(f"no look '{look}'. Looks: {', '.join(k for k in looks if not k.startswith('_'))}")
    L = looks[look]
    fs = frames(src, n, 320)
    if not fs:
        sys.exit(f"could not read frames from {src}")
    P = with_overrides(L["params"], exposure, wb)
    raw = summarise([stats(a) for _, a in fs])
    graded = summarise([stats(apply(a.astype(np.float32) / 255, P)) for _, a in fs])
    target = L.get("target", {})
    a, b = compare(raw, target), compare(graded, target)
    fields = {k: dict(t, footage=a[k], withLook=b[k]) for k, t in target.items()}
    return dict(look=look, fitted=L.get("fitted"), frames=len(fs), passed=dict(exposure=exposure, wb=wb),
                footage=raw, withLook=graded, fields=fields)


def dumps(obj):
    """JSON with short lists kept on one line."""
    s = json.dumps(obj, indent=1, ensure_ascii=False)
    flat = lambda m: "[" + ", ".join(x.strip() for x in m.group(1).split(",")) + "]"
    for _ in range(2):
        s = re.sub(r"\[\s*([^\[\]{}]*?)\s*\]", flat, s)
    return s


def wb_arg(v):
    w = [float(x) for x in v.split(",")]
    if len(w) != 3:
        raise argparse.ArgumentTypeError("--wb takes three multipliers R,G,B")
    return w


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["looks", "lut", "match", "preview", "measure"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("-o")
    ap.add_argument("--size", type=int, default=33)
    ap.add_argument("--n", type=int, help="frames to sample (preview 6, measure and match 12)")
    ap.add_argument("--exposure", type=float, help="lut/match: stops added to the look's exposure")
    ap.add_argument("--wb", type=wb_arg, help="lut/match: R,G,B multipliers on the look's white balance")
    ap.add_argument("--json", action="store_true", help="measure: print JSON")
    o = ap.parse_args()
    if o.cmd == "looks":
        for k, v in read_looks().items():
            if not k.startswith("_"):
                print(f"{k:18s} {v.get('description', '')}")
    elif o.cmd == "lut":
        if not o.o:
            sys.exit("lut needs -o OUT.cube")
        P = with_overrides(load_look(o.args[0]), o.exposure, o.wb)
        print(write_cube(P, o.o, o.size, os.path.splitext(os.path.basename(o.args[0]))[0]))
    elif o.cmd == "match":
        if o.o:
            sys.exit("match writes nothing: read its report, then make the LUT with lut --exposure S --wb R,G,B -o OUT.cube")
        print(dumps(cmd_match(o.args[0], o.args[1], o.n or 12, o.exposure, o.wb)))
    elif o.cmd == "preview":
        cmd_preview(o.args[0], o.args[1], o.o, o.n or 6)
    elif o.cmd == "measure":
        m = measure(o.args[0], o.n or 12)
        print(dumps(dict(file=o.args[0], **m)) if o.json else fmt(m))
