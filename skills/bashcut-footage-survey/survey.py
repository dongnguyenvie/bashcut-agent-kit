#!/usr/bin/env python3
"""Survey footage before editing, or review a rendered cut: specs per clip and labelled contact sheets.

    python3 survey.py <footage_dir | video ...> [--out DIR] [--frames N | --every SECONDS] [--recursive]

Each sheet is a grid of frames (8 x 3 portrait, 6 x 6 landscape). Every cell is labelled
"<cell> <clip> <time>", e.g. "14 c06 0:33": cell 14 is clip c06 (the ID column of the printed table) at
0:33 into that clip. Clips follow each other in table order; the label colour changes with each clip.

Writes to <first input's folder>/_survey (or --out):
  SHEET_<n>.jpg   the contact sheets
  survey.json     {"clips": duration, size, fps, rotation, orientation, audio level per clip,
                   "cells": sheet, cell, clip and time of every frame on the sheets}

Needs ffmpeg and ffprobe on PATH; Python standard library only.
"""
import argparse, json, os, subprocess, sys

EXTS = (".mp4", ".mov", ".mxf", ".m4v", ".mts")
# cell size and grid per sheet orientation; sheets are 1728 px wide
LAYOUT = {"portrait": ((216, 384), 8, 3), "landscape": ((288, 162), 6, 6)}
BAR = 26  # label bar height
SCALE = 3  # label glyphs are 5 x 7 pixels scaled by this
COLORS = [(255, 230, 0), (0, 230, 255)]  # label colour alternates per clip

# 5 x 7 bitmap glyphs: each row is 5 bits, most significant bit on the left
FONT = {
    "0": [14, 17, 19, 21, 25, 17, 14], "1": [4, 12, 4, 4, 4, 4, 14], "2": [14, 17, 1, 2, 4, 8, 31],
    "3": [31, 2, 4, 2, 1, 17, 14], "4": [2, 6, 10, 18, 31, 2, 2], "5": [31, 16, 30, 1, 1, 17, 14],
    "6": [6, 8, 16, 30, 17, 17, 14], "7": [31, 1, 2, 4, 8, 8, 8], "8": [14, 17, 17, 14, 17, 17, 14],
    "9": [14, 17, 17, 15, 1, 2, 12], "c": [0, 0, 14, 16, 16, 17, 14], "s": [0, 0, 15, 16, 14, 1, 30],
    ":": [0, 12, 12, 0, 12, 12, 0], ".": [0, 0, 0, 0, 0, 12, 12], " ": [0] * 7,
}


def run(args, **kw):
    return subprocess.run(args, capture_output=True, **kw)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "stream=codec_type,width,height,r_frame_rate,pix_fmt:stream_side_data=rotation:stream_tags=rotate",
             "-show_entries", "format=duration,size", "-of", "json", path], text=True)
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
    r = run(["ffmpeg", "-v", "info", "-t", str(seconds), "-i", path, "-vn", "-af", "volumedetect", "-f", "null", "-"],
            text=True)
    for line in r.stderr.splitlines():
        if "mean_volume:" in line:
            return float(line.split("mean_volume:")[1].split()[0])
    return None


def sample_times(duration, frames, every):
    if every:
        n = max(1, int(duration // every) + (1 if duration % every > every / 2 else 0))
        return [min(i * every, max(0, duration - 0.05)) for i in range(n)]
    # longer clips get more frames so a clip that changes inside still shows it
    n = frames if duration < 60 else min(frames * 4, max(frames, int(duration // 20)))
    return [duration * (i + 0.5) / n for i in range(max(1, n))]


def grab(path, t, size):
    """One frame as raw RGB, fitted into the cell with black bars; None when ffmpeg returns nothing."""
    w, h = size
    # format=yuvj420p first: 10-bit HEVC sources fail with error -22 without it
    vf = (f"format=yuvj420p,scale={w}:{h}:force_original_aspect_ratio=decrease,"
          f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,format=rgb24")
    r = run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-vf", vf,
             "-f", "rawvideo", "-"])
    return r.stdout if len(r.stdout) == w * h * 3 else None


def mmss(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def draw_text(img, width, x0, y0, text, color):
    for ch in text:
        rows = FONT.get(ch, FONT[" "])
        for gy, bits in enumerate(rows):
            for gx in range(5):
                if bits & (16 >> gx):
                    for dy in range(SCALE):
                        y = y0 + gy * SCALE + dy
                        start = (y * width + x0 + gx * SCALE) * 3
                        img[start:start + SCALE * 3] = bytes(color) * SCALE
        x0 += 6 * SCALE


def write_sheet(cells, size, cols, out):
    w, h = size
    rows = (len(cells) + cols - 1) // cols
    width, ch = cols * w, h + BAR
    img = bytearray(width * rows * ch * 3)
    for i, (pixels, label, color) in enumerate(cells):
        x, y = (i % cols) * w, (i // cols) * ch
        draw_text(img, width, x + 4, y + (BAR - 7 * SCALE) // 2, label, color)
        if pixels:
            for row in range(h):
                start = ((y + BAR + row) * width + x) * 3
                img[start:start + w * 3] = pixels[row * w * 3:(row + 1) * w * 3]
    run(["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{rows * ch}", "-i", "-",
         "-q:v", "3", "-y", out], input=bytes(img), check=True)


def collect(inputs, recursive, out_dir):
    vids = []
    for src in inputs:
        if os.path.isfile(src):
            vids.append((src, os.path.basename(src)))
            continue
        found = []
        for root, dirs, files in os.walk(src):
            if os.path.abspath(root).startswith(out_dir):
                continue
            found += [os.path.join(root, f) for f in files if f.lower().endswith(EXTS) and not f.startswith("._")]
            if not recursive:
                break
        vids += [(p, os.path.relpath(p, src)) for p in sorted(found)]
    return vids


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="footage folders or video files (a rendered cut to review)")
    ap.add_argument("--out")
    ap.add_argument("--frames", type=int, default=4, help="frames per clip under one minute (default 4)")
    ap.add_argument("--every", type=float, help="one frame every SECONDS instead (e.g. 2 to review a cut)")
    ap.add_argument("--recursive", action="store_true")
    o = ap.parse_args()

    inputs = [os.path.abspath(p) for p in o.inputs]
    first = inputs[0] if os.path.isdir(inputs[0]) else os.path.dirname(inputs[0])
    out_dir = os.path.abspath(o.out or os.path.join(first, "_survey"))
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):
        if old.startswith("SHEET_") and old.endswith(".jpg"):
            os.remove(os.path.join(out_dir, old))

    vids = collect(inputs, o.recursive, out_dir)
    print(f"{len(vids)} clips\n")
    print(f"{'ID':4s} {'CLIP':40s} {'SECONDS':>8s} {'SIZE':>10s} {'FPS':>11s} {'AUDIO dB':>9s}")
    clips = []
    for n, (p, rel) in enumerate(vids, 1):
        info = probe(p)
        stub = info["bytes"] < 4096 or info["duration"] == 0
        level = audio_level(p) if info["has_audio"] and not stub else None
        info.update(id=f"c{n:02d}", clip=rel, audio_mean_db=level, stub=stub)
        clips.append((p, info))
        print(f"{info['id']:4s} {rel[:40]:40s} {info['duration']:8.1f} "
              f"{str(info['width']) + 'x' + str(info['height']):>10s} {str(info['fps']):>11s} "
              f"{'-' if level is None else f'{level:.0f}':>9s}{'  STUB' if stub else ''}")

    usable = [(p, i) for p, i in clips if not i["stub"]]
    portrait = sum(i["orientation"] == "portrait" for _, i in usable)
    size, cols, rows = LAYOUT["portrait" if portrait * 2 >= len(usable) and usable else "landscape"]
    per_sheet = cols * rows

    cells, index, sheet_cells = [], [], []
    for k, (p, info) in enumerate(usable):
        for t in sample_times(info["duration"], o.frames, o.every):
            n = len(index)
            sheet_cells.append((grab(p, t, size), f"{n} {info['id']} {mmss(t)}", COLORS[k % 2]))
            index.append({"sheet": n // per_sheet + 1, "cell": n, "clip": info["id"], "time": round(t, 2)})
            if len(sheet_cells) == per_sheet:
                cells.append(sheet_cells)
                sheet_cells = []
    if sheet_cells:
        cells.append(sheet_cells)
    for s, part in enumerate(cells, 1):
        write_sheet(part, size, cols, os.path.join(out_dir, f"SHEET_{s}.jpg"))

    meta = {"clips": [i for _, i in clips], "cells": index}
    with open(os.path.join(out_dir, "survey.json"), "w") as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    print(f"\n{len(cells)} contact sheet(s), {len(index)} frames: {out_dir}/SHEET_*.jpg")
    print('Cell labels read "<cell> <clip ID> <time in clip>". Look at every sheet before planning the edit.')
    if any(i["stub"] for _, i in clips):
        print("STUB = empty or broken file; leave it out of the edit.")
    silent = [i["id"] for _, i in clips if i["audio_mean_db"] is not None and i["audio_mean_db"] < -70]
    if silent:
        print(f"Silent audio tracks: {', '.join(silent)}")


if __name__ == "__main__":
    sys.exit(main())
