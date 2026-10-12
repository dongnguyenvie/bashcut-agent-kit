#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""Find, download and import music beds and sound effects for a BashCut edit in one command.

    uv run fetch_audio.py --dest /abs/project/media/audio --music "acoustic folk" --sfx whoosh,pop [--import]

Music: Openverse search (Jamendo, ccMixter, Freesound…), the first --music-count results of at least
--min-seconds, in search order. SFX: the first Mixkit preview for each word, else the first short Openverse hit.
Downloads whatever the licence (the user handles rights). With --import, `bashcut media import DEST --base-rev
last` adds them and each line gets its media ID. Prints one compact JSON line per file: you choose from these.
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

AGENT = "Mozilla/5.0 (Macintosh) bashcut-agent-kit"


def get(url, timeout=30):
    # curl, not urllib: it uses the system's certificates, which some Python installs lack.
    out = subprocess.run(["curl", "-sfL", "-A", AGENT, "--max-time", str(timeout), url], capture_output=True)
    if out.returncode != 0:
        raise OSError(f"curl exit {out.returncode} for {url}")
    return out.stdout


def openverse(query, music, size=20):
    params = {"q": query, "page_size": size}
    if music:
        params["category"] = "music"
    data = json.loads(get("https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode(params)))
    return [r for r in data.get("results", []) if r.get("url")]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "audio"


def save(url, path):
    path.write_bytes(get(url, timeout=120))
    return path


def music(query, count, min_seconds, dest):
    rows = []
    for hit in openverse(query, music=True):
        seconds = (hit.get("duration") or 0) / 1000
        if seconds and seconds < min_seconds:
            continue
        name = f"music-{slug(hit.get('title') or query)}.{hit.get('filetype') or 'mp3'}".replace("mp32", "mp3")
        try:
            save(hit["url"], dest / name)
        except Exception as error:  # a dead link: take the next hit
            print(json.dumps({"skipped": hit["url"], "error": str(error)[:80]}), file=sys.stderr)
            continue
        rows.append({"file": name, "kind": "music", "title": hit.get("title"), "seconds": round(seconds) or None,
                     "tags": [t.get("name") for t in hit.get("tags", [])][:5]})
        if len(rows) == count:
            break
    return rows


def sfx(word, dest):
    try:
        page = get(f"https://mixkit.co/free-sound-effects/{urllib.parse.quote(word)}/").decode("utf-8", "ignore")
        found = re.findall(r"https://assets\.mixkit\.co/[^\"']+?\.(?:mp3|wav)", page)
    except Exception:
        found = []
    if found:
        name = f"sfx-{slug(word)}{Path(found[0]).suffix}"
        save(found[0], dest / name)
        return {"file": name, "kind": "sfx", "title": word, "from": "mixkit"}
    for hit in openverse(word, music=False):
        if (hit.get("duration") or 10_000) <= 5_000:
            name = f"sfx-{slug(word)}.{hit.get('filetype') or 'mp3'}"
            save(hit["url"], dest / name)
            return {"file": name, "kind": "sfx", "title": hit.get("title"), "from": "openverse"}
    return {"kind": "sfx", "title": word, "error": "nothing found"}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dest", required=True, help="absolute folder for the files (created)")
    parser.add_argument("--music", help="search words for the bed, e.g. 'acoustic folk upbeat'")
    parser.add_argument("--music-count", type=int, default=3)
    parser.add_argument("--min-seconds", type=float, default=30, help="shortest bed to take")
    parser.add_argument("--sfx", default="", help="comma-separated words, e.g. whoosh,pop,ding")
    parser.add_argument("--import", dest="import_", action="store_true", help="media import the folder")
    args = parser.parse_args()
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    rows = music(args.music, args.music_count, args.min_seconds, dest) if args.music else []
    rows += [sfx(word.strip(), dest) for word in args.sfx.split(",") if word.strip()]
    if args.import_ and any("file" in r for r in rows):
        out = subprocess.run(["bashcut", "media", "import", str(dest), "--base-rev", "last"],
                             capture_output=True, text=True)
        try:
            ids = {f["path"]: f.get("media") for f in json.loads(out.stdout).get("files", [])}
        except ValueError:
            ids = {}
            print(out.stderr.strip()[:300], file=sys.stderr)
        for row in rows:
            row["media"] = ids.get(row.get("file"))
    for row in rows:
        print(json.dumps({k: v for k, v in row.items() if v is not None}, ensure_ascii=False))


if __name__ == "__main__":
    main()
