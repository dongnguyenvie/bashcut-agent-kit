#!/usr/bin/env python3
"""Measure the time offset between two recordings of the same session from their sound.

    python3 sync.py CAMERA SCREEN            # prints: SCREEN time = CAMERA time + OFFSET
    python3 sync.py SCREEN OUTPUT.mp4        # where a short file (a render played on screen) starts in SCREEN

Both files' loudness envelopes (100 per second, log RMS) are cross-correlated: a coarse search at 10 per second
over every overlap, then a fine one at 100 per second around the best lag. The result is checked on the first
and last half of the overlap; two agreeing offsets mean a constant offset (no drift). Analysis only: it reads the
files with ffmpeg and writes nothing. Needs ffmpeg; Python standard library only.
"""
import array, math, subprocess, sys

RATE = 8000          # audio sample rate read from ffmpeg
HOP = RATE // 100    # 100 envelope values per second


def envelope(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-ac", "1", "-ar", str(RATE),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    x = array.array("h", raw[:len(raw) // 2 * 2])
    if sys.byteorder == "big":
        x.byteswap()
    env = []
    for i in range(0, len(x) - HOP + 1, HOP):
        s = sum(v * v for v in x[i:i + HOP])
        env.append(math.log(math.sqrt(s / HOP) + 1.0))
    return env


def decimate(e, k):
    return [sum(e[i:i + k]) / k for i in range(0, len(e) - k + 1, k)]


def corr(a, b, lag, lo=0, hi=None):
    """Normalized correlation of a[t] with b[t + lag] over the overlap (restricted to a[lo:hi])."""
    hi = len(a) if hi is None else hi
    s, e = max(lo, -lag), min(hi, len(b) - lag)
    n = e - s
    if n < 20:
        return -1.0, n
    xa, xb = a[s:e], b[s + lag:e + lag]
    ma, mb = sum(xa) / n, sum(xb) / n
    sab = saa = sbb = 0.0
    for p, q in zip(xa, xb):
        p -= ma; q -= mb
        sab += p * q; saa += p * p; sbb += q * q
    return (sab / math.sqrt(saa * sbb) if saa and sbb else -1.0), n


def best(a, b, lags, min_n, lo=0, hi=None):
    top = (-2.0, 0)
    for lag in lags:
        c, n = corr(a, b, lag, lo, hi)
        if n >= min_n and c > top[0]:
            top = (c, lag)
    return top


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pa, pb = sys.argv[1:]
    a, b = envelope(pa), envelope(pb)
    if min(len(a), len(b)) < 300:
        sys.exit("need at least 3 s of sound in both files")
    min_n = min(len(a), len(b)) // 2          # at least half of the shorter file must overlap
    ca, cb = decimate(a, 10), decimate(b, 10)
    c0, lag0 = best(ca, cb, range(-(len(ca) - 1), len(cb)), min_n // 10)
    c1, lag1 = best(a, b, range(lag0 * 10 - 30, lag0 * 10 + 31), min_n)
    # b[t + lag] matches a[t]  ->  time in B = time in A + lag
    off = lag1 / 100
    s, e = max(0, -lag1), min(len(a), len(b) - lag1)
    mid = (s + e) // 2
    halves = [best(a, b, range(lag1 - 30, lag1 + 31), (mid - s) // 2, lo, hi) for lo, hi in ((s, mid), (mid, e))]
    print(f"{pb} time = {pa} time {'+' if off >= 0 else '-'} {abs(off):.2f} s   (correlation {c1:.2f})")
    print(f"overlap: {pa} {s / 100:.1f}-{e / 100:.1f} s")
    if off < 0:
        print(f"{pb} starts at {pa} {-off:.2f} s")
    else:
        print(f"{pa} starts at {pb} {off:.2f} s")
    print("halves: " + ", ".join(f"{l / 100:+.2f} s (corr {c:.2f})" for c, l in halves))
    if c1 < 0.4:
        print("WARNING: weak correlation; the files may not share sound. Check a frame or a clap by eye.")
    if abs(halves[0][1] - halves[1][1]) > 2:
        print("WARNING: the halves disagree by more than 0.02 s: the clocks drift or the match is wrong.")


if __name__ == "__main__":
    main()
