#!/usr/bin/env python3
"""Survey a footage folder before editing: specs per clip and contact sheets to look at.

    python3 survey.py <footage_dir> [--out DIR] [--frames N] [--recursive]

Writes to <footage_dir>/_survey (or --out):
  SHEET_<n>.jpg   one row per clip, N frames spread across it (more for long clips)
  survey.json     duration, size, fps, rotation, orientation, audio level per clip
  frames/         the single frames and strips the sheets are made of

Needs ffmpeg and ffprobe on PATH; Python standard library only.
"""
import argparse, json, os, subprocess, sys

EXTS = (".mp4", ".mov", ".mxf", ".m4v", ".mts")
CELL = {"landscape": (320, 180), "portrait": (180, 320)}
ROWS_PER_SHEET = 8


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "stream=codec_type,width,height,r_frame_rate,pix_fmt:stream_side_data=rotation:stream_tags=rotate",
             "-show_entries", "format=duration,size", "-of", "json", path])
    j = json.loads(r.stdout or "{}")
    streams = j.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    rot = 0
    for sd in v.get("side_data_list") or []:
        rot = int(sd.get("rotation", rot) or 0)
    rot = int((v.get("tags") or {}).get("rotate", rot) or rot)
    w, h = v.get("width") or 0, v.get("height") or 0
    if abs(rot) in (90, 270):
        w, h = h, w
    fmt = j.get("format", {})
    return {"duration": round(float(fmt.get("duration", 0) or 0), 2), "bytes": int(fmt.get("size", 0) or 0),
            "width": w, "height": h, "rotation": rot, "fps": v.get("r_frame_rate"), "pix_fmt": v.get("pix_fmt"),
            "orientation": "portrait" if h > w else "landscape",
            "has_audio": any(s.get("codec_type") == "audio" for s in streams)}


def audio_level(path, seconds=60):
    """Mean volume (dB) of the first minute; about -90 means a silent track."""
    r = run(["ffmpeg", "-v", "info", "-t", str(seconds), "-i", path, "-vn", "-af", "volumedetect", "-f", "null", "-"])
    for line in r.stderr.splitlines():
        if "mean_volume:" in line:
            return float(line.split("mean_volume:")[1].split()[0])
    return None


def grab(path, dur, n, out_dir, tag, size):
    w, h = size
    # format=yuvj420p is required: 10-bit HEVC sources fail with error -22 without it
    vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,format=yuvj420p"
    got = []
    for i in range(n):
        o = os.path.join(out_dir, f"{tag}_{i}.jpg")
        run(["ffmpeg", "-v", "error", "-ss", f"{dur * (i + 0.5) / n:.2f}", "-i", path,
             "-frames:v", "1", "-vf", vf, "-y", o])
        if os.path.exists(o):
            got.append(o)
    return got


def stack(files, out, direction, widths=None):
    if not files:
        return None
    a = ["ffmpeg", "-v", "error"]
    for f in files:
        a += ["-i", f]
    if len(files) == 1:
        subprocess.run(a + ["-y", out], check=True)
        return out
    if direction == "h":
        fc = "".join(f"[{i}]" for i in range(len(files))) + f"hstack={len(files)}"
    else:
        # strips differ in width (fewer frames, portrait cells): pad them to the widest
        mw = max(widths)
        fc = ";".join(f"[{i}]pad={mw}:ih:0:0:black[p{i}]" for i in range(len(files)))
        fc += ";" + "".join(f"[p{i}]" for i in range(len(files))) + f"vstack={len(files)}"
    subprocess.run(a + ["-filter_complex", fc, "-y", out], check=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("footage_dir")
    ap.add_argument("--out")
    ap.add_argument("--frames", type=int, default=4, help="frames per clip under one minute (default 4)")
    ap.add_argument("--recursive", action="store_true")
    o = ap.parse_args()

    src = os.path.abspath(o.footage_dir)
    out_dir = os.path.abspath(o.out or os.path.join(src, "_survey"))
    frame_dir = os.path.join(out_dir, "frames")
    os.makedirs(frame_dir, exist_ok=True)

    vids = []
    for root, dirs, files in os.walk(src):
        if os.path.abspath(root).startswith(out_dir):
            continue
        vids += [os.path.join(root, f) for f in files if f.lower().endswith(EXTS) and not f.startswith("._")]
        if not o.recursive:
            break
    vids.sort()
    print(f"{len(vids)} clips\n")
    print(f"{'CLIP':40s} {'SECONDS':>8s} {'SIZE':>10s} {'FPS':>11s} {'AUDIO dB':>9s}")

    rows, meta, seen = [], [], {}
    for p in vids:
        info = probe(p)
        rel = os.path.relpath(p, src)
        tag = os.path.splitext(rel)[0].replace(os.sep, "__")
        seen[tag] = seen.get(tag, 0) + 1
        if seen[tag] > 1:  # the same clip name in two subfolders
            tag = f"{tag}~{seen[tag]}"
        stub = info["bytes"] < 4096 or info["duration"] == 0
        level = audio_level(p) if info["has_audio"] and not stub else None
        info.update(clip=rel, audio_mean_db=level, stub=stub)
        meta.append(info)
        print(f"{rel[:40]:40s} {info['duration']:8.1f} {str(info['width']) + 'x' + str(info['height']):>10s} "
              f"{str(info['fps']):>11s} {'-' if level is None else f'{level:.0f}':>9s}{'  STUB' if stub else ''}")
        if stub:
            continue
        # longer clips get more frames so a clip that changes inside still shows it
        n = o.frames if info["duration"] < 60 else min(o.frames * 4, max(o.frames, int(info["duration"] // 20)))
        size = CELL[info["orientation"]]
        fs = grab(p, info["duration"], max(1, n), frame_dir, tag, size)
        strip = stack(fs, os.path.join(frame_dir, f"strip_{tag}.jpg"), "h")
        if strip:
            rows.append((strip, size[0] * len(fs)))

    for i in range(0, len(rows), ROWS_PER_SHEET):
        part = rows[i:i + ROWS_PER_SHEET]
        stack([r[0] for r in part], os.path.join(out_dir, f"SHEET_{i // ROWS_PER_SHEET + 1}.jpg"), "v",
              [r[1] for r in part])

    json.dump(meta, open(os.path.join(out_dir, "survey.json"), "w"), indent=1, ensure_ascii=False)
    print(f"\nContact sheets: {out_dir}/SHEET_*.jpg (rows in the table's order)")
    print("Look at them before deciding the structure of the edit.")
    if any(m["stub"] for m in meta):
        print("STUB = empty or broken file; leave it out of the edit.")
    silent = [m["clip"] for m in meta if m["audio_mean_db"] is not None and m["audio_mean_db"] < -70]
    if silent:
        print(f"Silent audio tracks: {', '.join(silent)}")


if __name__ == "__main__":
    sys.exit(main())
