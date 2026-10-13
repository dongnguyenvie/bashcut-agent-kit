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
  grade.py candidates --target TAGS|LOOK|profile.json [CLIP|MEDIA ...] [--n 8]   # rank library LUTs, one sheet
  grade.py candidates --pick N[@frame[:duration]] [--strength 0.8]   # apply it, remember the pick for the recipe

Nothing here picks a correction. `match` measures the footage, the footage with the look (plus only the exposure
and white balance you pass) and reports both against the look's reference ranges; it writes no file. You choose
exposure/wb from that report and pass them to `lut`. `--exposure` is added to the look's exposure (stops);
`--wb` multiplies the look's white balance. Scale 0-100, the same as `bashcut color measure`.

Apply the result in BashCut with `bashcut luts import OUT.cube`, then an adjustment item; save it as a library look with `library save-selection --kind look`.
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


# --- candidates: rank the library's LUTs, check the best on real frames, draw one numbered sheet -------------
# Ranking memory per recipe or channel (params.lut.picks / .shown): a pick halves a LUT's distance, every skip
# beyond the first two makes it 15 % farther.
PICK_BOOST, SKIP_COST, SKIP_FREE = 0.5, 1.15, 2


def luts():
    sys.path.insert(0, HERE)
    import fetch_luts
    return fetch_luts


def skin_mask(f):
    """Skin-like pixels of a float frame: warm hues, moderate saturation, not dark."""
    h, s, v = rgb2hsv(f)
    return ((h < 50) | (h > 345)) & (s > 0.15) & (s < 0.65) & (v > 0.2)


def pick_frames(arrays, count=3):
    """The brightest, the darkest and the most skin of the sampled frames (each once), then the rest in order;
    black or nearly flat frames (fades, title cards) only when nothing else is left."""
    if len(arrays) <= count:
        return list(range(len(arrays)))
    mids = [float(luma(a).mean()) for a in arrays]
    blank = [m < 0.03 or float(luma(a).std()) < 0.02 for m, a in zip(mids, arrays)]
    if sum(not b for b in blank) >= count:
        mids_hi = [m if not b else -1 for m, b in zip(mids, blank)]
        mids_lo = [m if not b else 2 for m, b in zip(mids, blank)]
    else:
        mids_hi = mids_lo = mids
    skin = [float(skin_mask(a).mean()) for a in arrays]
    chosen = []
    skin = [s if mids_hi[i] >= 0 else -1 for i, s in enumerate(skin)]
    for i in (int(np.argmax(mids_hi)), int(np.argmin(mids_lo)), *np.argsort(skin)[::-1].tolist(), *range(len(arrays))):
        if i not in chosen:
            chosen.append(int(i))
    return sorted(chosen[:count])


def clip_frames(sources, count=3, size=320):
    """Frames read by BashCut (AVFoundation, `media frames`), never ffmpeg: from files, media IDs, or every media of
    the open project when none is given. Returns float 0-1 arrays."""
    from PIL import Image
    B = luts().bashcut
    calls = [["--file", s] if os.path.isfile(s) else ["--media", s] for s in sources] or [[]]
    paths = []
    for c in calls:
        got = B("media", "frames", *c, "--count", "4" if c else "2", "--size", str(size))
        if got.get("error"):
            sys.exit(f"media frames: {got['error']}")
        paths += [f["path"] for f in got.get("frames") or [] if f.get("path")]
    arrays = [np.asarray(Image.open(p).convert("RGB"), np.float32) / 255 for p in paths[:24]]
    if not arrays:
        sys.exit("no frames: pass a clip file or media ID")
    return [arrays[i] for i in pick_frames(arrays, count)]


def find(d, *names):
    """The first value under any of names, searched through nested dicts (a style-study profile)."""
    if isinstance(d, dict):
        for n in names:
            if n in d and not isinstance(d[n], dict):
                return d[n]
        for v in d.values():
            got = find(v, *names)
            if got is not None:
                return got
    return None


def profile_target(prof, footage):
    """A style-study profile's colour (graded stats) → the change a LUT should make to this footage."""
    t = {}
    black, white, mid = find(prof, "black"), find(prof, "white"), find(prof, "mid")
    sat = find(prof, "sat", "saturation")
    if black is not None:
        t["black"] = max(0.0, black - footage["black"])
    if white is not None:
        t["white"] = 100 - max(0.0, footage["white"] - white)
    if mid is not None:
        t["mid"] = 50 + mid - footage["mid"]
    if sat is not None and footage["sat"]:
        t["sat"] = sat / footage["sat"]
    for key, names in (("warm", ("tint_mid", "tintMid", "tintMids")), ("shadow_rb", ("tint_shadow", "tintShadow", "tintShadows")),
                       ("high_rb", ("tint_high", "tintHigh", "tintHighlights"))):
        v, f = find(prof, *names), footage[names[0]]
        if isinstance(v, list) and f:
            t[key] = v[0] - f[0]
            if key == "warm":
                t["tint"] = v[1] - f[1]
    return t


def target_of(spec, frames):
    """--target: a look in looks.json, a JSON file (fingerprint keys, or a style-study profile), or tags."""
    F, looks = luts(), read_looks()
    if spec in looks and not spec.startswith("_"):
        P = looks[spec]["params"]
        fp = F.fingerprint(lambda c: apply(c, P))
        return {k: v for k, v in fp.items() if k not in ("clip", "crush", "low")}
    if os.path.exists(spec):
        with open(spec, encoding="utf-8") as fh:
            prof = json.load(fh)
        direct = {k: v for k, v in prof.items() if k in F.SCALE and isinstance(v, (int, float))}
        return direct or profile_target(prof, summarise([stats(f) for f in frames]))
    t = {}
    for tag in [x.strip() for x in spec.split(",") if x.strip()]:
        if tag not in F.TAG_TARGETS:
            sys.exit(f"unknown target '{tag}': a look ({', '.join(k for k in looks if not k.startswith('_'))}), "
                     f"a JSON file, or tags ({', '.join(F.TAG_TARGETS)})")
        t.update(F.TAG_TARGETS[tag])
    return t


def rank(items, target, key, log=False):
    """Library LUT looks nearest the target first; picks for this key pull a LUT closer, many skips push it away."""
    F, out = luts(), []
    for it in items:
        lut = (it.get("params") or {}).get("lut") or {}
        if not lut.get("fp") or ("log" in (it.get("tags") or [])) != log:
            continue
        picks, shown = (lut.get("picks") or {}).get(key, 0), (lut.get("shown") or {}).get(key, 0)
        d = F.distance(target, lut["fp"]) * PICK_BOOST ** picks * SKIP_COST ** max(0, shown - picks - SKIP_FREE)
        out.append((d, it))
    out.sort(key=lambda x: x[0])
    return out


def damage(frames, graded, fn):
    """Clipped and crushed (% of pixels that held detail, worst frame) and the mean skin hue shift in degrees (None
    without skin or for a black-and-white result). Clipped and crushed are counted against the transform fn's own
    white and black (a look that rolls white off to 90 flattens highlights at 90, not at 100)."""
    share = lambda m: float(m.mean() * 100)
    top, bottom = float(luma(fn(np.ones(3, np.float32)))), float(luma(fn(np.zeros(3, np.float32))))
    # pixels that held detail in the source (not already near black or white) and end flat at the look's ends
    clip = max(share((luma(g) >= top - 0.01) & (luma(f) < 0.96)) for f, g in zip(frames, graded))
    crush = max(share((luma(g) <= bottom + 0.01) & (luma(f) > 0.04)) for f, g in zip(frames, graded))
    shifts = []
    for f, g in zip(frames, graded):
        m = skin_mask(f)
        if m.mean() < 0.005 or rgb2hsv(g)[1][m].mean() < 0.05:
            continue
        shifts.append(float(np.mean((((rgb2hsv(g)[0] - rgb2hsv(f)[0])[m] + 180) % 360) - 180)))
    return round(clip, 2), round(crush, 2), None if not shifts else round(float(np.mean(shifts)), 1)


def fit(P, look, frames, wb_fit=0.5):
    """Exposure that brings the graded mid inside the look's mid range, and white balance that takes wb_fit of
    the footage's mid tint out: (exposure or None, wb or None)."""
    graded = summarise([stats(apply(f, P)) for f in frames])
    lo, hi = (look.get("target", {}).get("mid") or {}).get("range") or [30, 50]
    edge = lo if lo is not None and graded["mid"] < lo else hi if hi is not None and graded["mid"] > hi else None
    exposure = None if edge is None else round(float(np.clip(np.log2(edge / max(graded["mid"], 1)), -1, 1)), 2)
    raw = summarise([stats(f) for f in frames])["tint_mid"]
    wb = None
    if wb_fit and raw and max(abs(raw[0]), abs(raw[1])) > 2:
        rb, gm = raw[0] * wb_fit / 200, raw[1] * wb_fit / 100
        wb = [round(1 - rb, 3), round(1 - gm, 3), round(1 + rb, 3)]
    return exposure, wb


def draw_sheet(frames, cells, out):
    """One numbered sheet: a cell per candidate (cell 0 = the source), each a strip of the same frames."""
    from PIL import Image, ImageDraw, ImageFont
    h0, w0 = frames[0].shape[:2]
    fw = 200 if w0 >= h0 else 120
    fh = round(fw * h0 / w0)
    strip_w, label_h, pad = fw * len(frames), 20, 6
    cols = 3 if w0 >= h0 else 4
    rows = -(-len(cells) // cols)
    sheet = Image.new("RGB", (pad + cols * (strip_w + pad), pad + rows * (label_h + fh + pad)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=14)
    for i, (label, graded) in enumerate(cells):
        x, y = pad + (i % cols) * (strip_w + pad), pad + (i // cols) * (label_h + fh + pad)
        draw.text((x, y + 2), label[:48], fill=(255, 210, 0), font=font)
        for j, g in enumerate(graded):
            pic = Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).resize((fw, fh))
            sheet.paste(pic, (x + j * fw, y + label_h))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out, quality=84)
    return out


def library_luts(scope):
    items, offset, B = [], 0, luts().bashcut
    while True:
        page = B("library", "list", "--kind", "look", "--tag", "lut", *(["--scope", scope] if scope else []),
                 "--offset", str(offset), "--limit", "500")
        if not isinstance(page, dict) or page.get("error"):
            return items
        items += page.get("items") or []
        if page.get("next") is None:
            return items
        offset = page["next"]


def recipe_key():
    """The open project's recipe (plan.recipe, or recipe.skill in project get), the key picks are remembered under."""
    B = luts().bashcut
    found = find(B("project", "data", "plan"), "recipe", "skill") or find(B("project", "get").get("recipe") or {}, "skill")
    return str(found or "any")


def cmd_candidates(sources, o):
    F = luts()
    frames = clip_frames(sources, 3)
    target = target_of(o.target, frames)
    key = o.key or recipe_key()
    ranked = rank(library_luts(o.scope), target, key, o.log)
    folder = F.CACHE / "candidates"
    kept, dropped, cells = [], 0, [("0 source", frames)]
    tried = 0
    for d, it in ranked[:max(o.check, 3 * o.n)]:
        if len(kept) >= o.n:
            break
        tried += 1
        lut = it["params"]["lut"]
        try:
            table = F.read_cube(lut.get("file") or it.get("file") or "")
        except (OSError, ValueError):
            dropped += 1
            continue
        graded = [F.apply_lut(f, table) for f in frames]
        clip, crush, skin = damage(frames, graded, lambda c: F.apply_lut(c, table))
        if clip > o.max_clip or crush > o.max_crush or (skin is not None and abs(skin) > o.max_skin):
            dropped += 1
            continue
        n = len(kept) + 1
        ref = it["id"] if ":" in it["id"] else f"{it.get('scope', 'user')}:{it['id']}"
        kept.append(dict(n=n, kind="lut", id=ref, name=it.get("name"), file=lut.get("file"), params=it["params"],
                         tags=[t for t in it.get("tags") or [] if t != "lut"], d=round(d, 2),
                         clip=clip, crush=crush, skin=skin))
        cells.append((f"{n} {it.get('name')}", graded))
    looks = read_looks()
    near = sorted((F.distance(target, F.fingerprint(lambda c, P=v["params"]: apply(c, P))), k)
                  for k, v in looks.items() if not k.startswith("_"))
    for _, name in near[:o.gen]:
        P = looks[name]["params"]
        exposure, wb = (None, None) if o.no_fit else fit(P, looks[name], frames, o.wb_fit)
        while True:  # a fitted exposure that clips is halved until it does not
            Q = with_overrides(P, exposure, wb)
            graded = [apply(f, Q) for f in frames]
            clip, crush, skin = damage(frames, graded, lambda c: apply(c, Q))
            if not exposure or exposure < 0 or clip <= o.max_clip or abs(exposure) < 0.1:
                break
            exposure = round(exposure / 2, 2)
        P = Q
        n = len(kept) + 1
        cube = write_cube(P, str(folder / f"{name}-fit.cube"), 33, name)
        kept.append(dict(n=n, kind="generated", name=name, file=cube, exposure=exposure, wb=wb,
                         clip=clip, crush=crush, skin=skin))
        cells.append((f"{n} {name} (generated)", graded))
    sheet = draw_sheet(frames, cells, str(folder / "sheet.jpg"))
    with open(folder / "last.json", "w", encoding="utf-8") as fh:
        json.dump(dict(key=key, scope=o.scope, sheet=sheet, entries=kept), fh)
    print(f"{sheet}  ({len(ranked)} ranked, {tried} checked, {dropped} dropped; picks for '{key}')")
    for e in kept:
        extra = (" ".join(e["tags"][1:4]) + f" d{e['d']}") if e["kind"] == "lut" else \
            f"generated exp {e['exposure'] or 0:+} wb {','.join(map(str, e['wb'])) if e['wb'] else '-'}"
        skin = "" if e["skin"] is None else f" skin {e['skin']:+}°"
        print(f"{e['n']} {e['name']}  {extra}  clip {e['clip']:+} crush {e['crush']:+}{skin}")


def total_frames():
    tl = luts().bashcut("timeline", "get")
    ends = [i.get("at", 0) + i.get("dur", 0) for t in tl.get("tracks") or [] for i in t.get("items") or []]
    return max(ends, default=0)


def first_id(result, *keys):
    for k in keys:
        v = result.get(k)
        if isinstance(v, dict):
            v = v.get("id")
        if v:
            return str(v)
    return None


def cmd_pick(spec, strength, o):
    """--pick N[@frame[:duration]]: import that candidate's LUT, add it as an adjustment over the range (the whole
    edit by default), and remember the pick and the skipped ones for this recipe."""
    F = luts()
    with open(F.CACHE / "candidates" / "last.json", encoding="utf-8") as fh:
        last = json.load(fh)
    m = re.fullmatch(r"(\d+)(?:@(\d+)(?::(\d+))?)?", spec.strip())
    if not m:
        sys.exit('--pick takes N, N@frame or N@frame:duration')
    n, at, dur = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    entry = next((e for e in last["entries"] if e["n"] == n), None)
    if not entry:
        sys.exit(f"no candidate {n} on the last sheet")
    dur = int(dur) if dur else total_frames() - at
    if dur < 1:
        sys.exit("nothing on the timeline: pass N@frame:duration")
    imported = F.bashcut("luts", "import", entry["file"], "--name", entry["name"][:60], "--base-rev", "last")
    lut = first_id(imported, "lut", "id", "lutId")
    if imported.get("error") or not lut:
        sys.exit(f"luts import: {imported.get('error') or 'no LUT ID in ' + json.dumps(imported)[:160]}")
    added = F.bashcut("adjustment", "add", "--lut", lut, "--lut-strength", str(strength), "--at-frame", str(at),
                      "--duration", str(dur), "--base-rev", "last")
    if added.get("error"):
        sys.exit(f"adjustment add: {added['error']}")
    learned = 0
    for e in last["entries"]:
        if e["kind"] != "lut":
            continue
        params = json.loads(json.dumps(e["params"]))
        rec = params.setdefault("lut", {})
        for field, hit in (("shown", True), ("picks", e["n"] == n)):
            if hit:
                rec.setdefault(field, {})[last["key"]] = rec.get(field, {}).get(last["key"], 0) + 1
        if not F.bashcut("library", "update", e["id"], "--params", json.dumps(params)).get("error"):
            learned += 1
    item = first_id(added, "item", "id", "itemId")
    print(f"applied {n} {entry['name']}: adjustment {item}, lut {lut}, strength {strength}, frames {at}+{dur}; "
          f"{learned} looks remembered for '{last['key']}'")


def wb_arg(v):
    w = [float(x) for x in v.split(",")]
    if len(w) != 3:
        raise argparse.ArgumentTypeError("--wb takes three multipliers R,G,B")
    return w


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["looks", "lut", "match", "preview", "measure", "candidates"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("-o")
    ap.add_argument("--size", type=int, default=33)
    ap.add_argument("--n", type=int, help="frames to sample (preview 6, measure and match 12); candidates: LUTs kept (8)")
    ap.add_argument("--exposure", type=float, help="lut/match: stops added to the look's exposure")
    ap.add_argument("--wb", type=wb_arg, help="lut/match: R,G,B multipliers on the look's white balance")
    ap.add_argument("--json", action="store_true", help="measure: print JSON")
    c = ap.add_argument_group("candidates [CLIP|MEDIA ...] --target T: rank library LUTs, check them on 3 frames, one sheet")
    c.add_argument("--target", help="a look in looks.json, tags (warm,matte,...), or a JSON file (style-study profile)")
    c.add_argument("--check", type=int, default=20, help="the best ranked tried on the frames (more, up to 3×n, until n pass)")
    c.add_argument("--gen", type=int, default=3, help="generated looks (looks.json, fitted to the footage) added")
    c.add_argument("--max-clip", type=float, default=1.0, help="drop: clipped highlights grow by more (%% of pixels)")
    c.add_argument("--max-crush", type=float, default=2.0, help="drop: crushed blacks grow by more (%% of pixels)")
    c.add_argument("--max-skin", type=float, default=8.0, help="drop: skin hue moves by more (degrees)")
    c.add_argument("--wb-fit", type=float, default=0.5, help="share of the footage's mid tint a generated look takes out")
    c.add_argument("--no-fit", action="store_true", help="generated looks as they are, no exposure/wb fitted")
    c.add_argument("--log", action="store_true", help="rank log-to-Rec.709 LUTs only (log footage)")
    c.add_argument("--for", dest="key", help="remember picks under this key (default: the project's recipe)")
    c.add_argument("--scope", help="library scope to rank (default every scope)")
    c.add_argument("--pick", help="N[@frame[:duration]]: apply candidate N of the last sheet (whole edit by default)")
    c.add_argument("--strength", type=float, default=0.8, help="--pick: LUT strength 0-1")
    o = ap.parse_args()
    if o.pick:
        cmd_pick(o.pick, o.strength, o)
    elif o.cmd == "candidates":
        if not o.target:
            sys.exit("candidates needs --target (a look, tags or a profile JSON)")
        o.n = o.n or 8
        cmd_candidates(o.args, o)
    elif o.cmd == "looks":
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
