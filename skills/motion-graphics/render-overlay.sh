#!/bin/bash
# Render a HyperFrames composition (HTML/CSS + GSAP, Apache-2.0) to a .mov with alpha for BashCut's Overlay layer.
# Usage: render-overlay.sh <composition-dir> <out.mov> [--fps 30] [--codec hevc|prores] [--variables JSON]
# HyperFrames renders RGBA PNGs in headless Chrome; encode-alpha (AVAssetWriter) writes HEVC with alpha (default,
# small) or ProRes 4444. Without swiftc it falls back to HyperFrames' own ProRes 4444 .mov (needs FFmpeg).
# Prints one JSON line: output, codec, frames, fps, width, height, bytes, renderSeconds, encodeSeconds, peakRSSMB.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
[ $# -ge 2 ] || { sed -n 2,6p "$0" >&2; exit 2; }
dir="$1"; out="$2"; shift 2
fps=30; codec=hevc; variables="{}"
while [ $# -gt 0 ]; do
    case "$1" in
        --fps) fps="$2"; shift 2 ;;
        --codec) codec="$2"; shift 2 ;;
        --variables) variables="$2"; shift 2 ;;
        *) echo "unknown option $1" >&2; exit 2 ;;
    esac
done
command -v npx >/dev/null || { echo "Node.js (npx) is not installed: use native text items instead" >&2; exit 3; }
# No telemetry, no skills check against GitHub.
export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 HF_CLI_TELEMETRY_DISABLED=1 HYPERFRAMES_SKIP_SKILLS=1
hf=(npx --yes hyperframes@0.8.140)
mkdir -p "$(dirname "$out")"
# GSAP (its own free licence, not bundled): fetched once with npm and copied next to index.html when it is missing.
if grep -q 'src="gsap.min.js"' "$dir/index.html" && [ ! -f "$dir/gsap.min.js" ]; then
    gsap="${XDG_CACHE_HOME:-$HOME/Library/Caches}/bashcut-motion-graphics/gsap"
    [ -f "$gsap/node_modules/gsap/dist/gsap.min.js" ] || npm install --silent --ignore-scripts --prefix "$gsap" gsap@3.14.2 >&2
    cp "$gsap/node_modules/gsap/dist/gsap.min.js" "$dir/gsap.min.js"
fi
start=$(date +%s)
cache="${XDG_CACHE_HOME:-$HOME/Library/Caches}/bashcut-motion-graphics"
if command -v swiftc >/dev/null; then
    encoder="$cache/encode-alpha"
    if [ ! -x "$encoder" ] || [ "$here/encode-alpha.swift" -nt "$encoder" ]; then
        mkdir -p "$cache"
        swiftc -O "$here/encode-alpha.swift" -o "$encoder" 2>/dev/null
    fi
    frames="$(mktemp -d)"
    trap 'rm -rf "$frames"' EXIT
    "${hf[@]}" render "$dir" --format png-sequence -o "$frames/png" --fps "$fps" --variables "$variables" --quiet >&2
    render=$(( $(date +%s) - start ))
    "$encoder" "$frames/png" "$out" --fps "$fps" --codec "$codec" \
        | python3 -c "import json,sys; d=json.load(sys.stdin); d['renderSeconds']=$render; print(json.dumps(d, sort_keys=True))"
else
    "${hf[@]}" render "$dir" --format mov -o "$out" --fps "$fps" --variables "$variables" --quiet >&2
    echo "{\"output\": \"$out\", \"codec\": \"prores\", \"renderSeconds\": $(( $(date +%s) - start ))}"
fi
