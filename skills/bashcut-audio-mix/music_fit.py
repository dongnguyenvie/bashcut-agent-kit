#!/usr/bin/env python3
"""Measure how much a music track will compete with speech, to choose a bed for a talking video.

    python3 music_fit.py TRACK [TRACK ...] [--voice SPEECH_CLIP]

Per file: duration, loudness range (LRA, EBU R128), and the share of its energy in the speech band (300-3000 Hz)
and in the presence band (1-4 kHz, where consonants make words intelligible). A lower presence share masks the
voice less. Bands are measured with ffmpeg band-pass filters + volumedetect, so the shares are approximate.
Analysis only; needs ffmpeg. Python standard library only.
"""
import re, subprocess, sys


def mean_db(path, filt=None):
    af = (filt + ",") if filt else ""
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-map", "0:a:0", "-ac", "1",
                          "-af", af + "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"mean_volume: (-?[\d.]+) dB", out)
    return float(m.group(1)) if m else None


def lra(path):
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-map", "0:a:0", "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.findall(r"LRA:\s+(-?[\d.]+) LU", out)
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    dur = int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)) if d else 0.0
    return (float(m[-1]) if m else None), dur


def share(path, full, lo, hi):
    band = mean_db(path, f"highpass=f={lo}:poles=2,highpass=f={lo}:poles=2,lowpass=f={hi}:poles=2,lowpass=f={hi}:poles=2")
    return 10 ** ((band - full) / 10) if band is not None and full is not None else None


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    voice = None
    if "--voice" in args:
        i = args.index("--voice"); voice = args[i + 1]; del args[i:i + 2]
    rows = ([("VOICE", voice)] if voice else []) + [("", p) for p in args]
    print(f"{'file':48s} {'dur s':>6s} {'LRA LU':>6s} {'speech':>6s} {'presence':>8s}")
    for tag, p in rows:
        full = mean_db(p)
        r, dur = lra(p)
        sp, pr = share(p, full, 300, 3000), share(p, full, 1000, 4000)
        name = (tag + " " if tag else "") + p.split("/")[-1]
        print(f"{name[:48]:48s} {dur:6.1f} {r if r is not None else float('nan'):6.1f} "
              f"{sp if sp is not None else float('nan'):6.2f} {pr if pr is not None else float('nan'):8.3f}")


if __name__ == "__main__":
    main()
