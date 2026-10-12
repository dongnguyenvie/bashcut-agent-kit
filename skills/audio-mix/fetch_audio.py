#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""Find, download and import music beds and sound effects for a BashCut edit in one command.

    uv run fetch_audio.py --dest /abs/project/media/audio --music "acoustic folk" --sfx whoosh,pop [--import]

Music: Openverse search (Jamendo, ccMixter, Freesound…), the first --music-count results of at least
--min-seconds, in search order. SFX: with FREESOUND_API_KEY set (free key: freesound.org/apiv2/apply), the best
Freesound match up to --sfx-seconds, CC0 first, then CC BY (its line carries license, author and page for the
credit), never NonCommercial; else the first Mixkit preview for each word, else the first short Openverse hit.
--sfx-source picks one source. Downloads whatever the licence (the user handles rights). With --import, `bashcut media import DEST --base-rev
last` adds them and each line gets its media ID. Prints one compact JSON line per file: you choose from these.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

AGENT = "Mozilla/5.0 (Macintosh) bashcut-agent-kit"


def get(url, timeout=30, headers=None):
    # curl, not urllib: it uses the system's certificates, which some Python installs lack.
    command = ["curl", "-sfL", "-A", AGENT, "--max-time", str(timeout)]
    for name, value in (headers or {}).items():
        command += ["-H", f"{name}: {value}"]
    out = subprocess.run(command + [url], capture_output=True)
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


FREESOUND_LICENCES = ['"Creative Commons 0"', '"Attribution"']  # CC0 first; NonCommercial never


def freesound(word, dest, max_seconds):
    key = os.environ.get("FREESOUND_API_KEY")
    if not key:
        return None
    for licence in FREESOUND_LICENCES:
        params = {"query": word, "filter": f"license:{licence} duration:[0 TO {max_seconds:g}]",
                  "fields": "id,name,username,license,duration,url,previews", "page_size": 5, "sort": "score"}
        data = json.loads(get("https://freesound.org/apiv2/search/?" + urllib.parse.urlencode(params),
                              headers={"Authorization": f"Token {key}"}))
        for hit in data.get("results", []):
            preview = (hit.get("previews") or {}).get("preview-hq-mp3")
            if not preview:
                continue
            name = f"sfx-{slug(word)}.mp3"
            save(preview, dest / name)  # previews are public files: the key stays off the CDN
            return {"file": name, "kind": "sfx", "title": hit.get("name"), "from": "freesound",
                    "seconds": round(hit.get("duration") or 0, 1) or None, "license": hit.get("license"),
                    "author": hit.get("username"), "source": hit.get("url")}
    return None


def mixkit(word, dest):
    try:
        page = get(f"https://mixkit.co/free-sound-effects/{urllib.parse.quote(word)}/").decode("utf-8", "ignore")
        found = re.findall(r"https://assets\.mixkit\.co/[^\"']+?\.(?:mp3|wav)", page)
    except Exception:
        found = []
    if not found:
        return None
    name = f"sfx-{slug(word)}{Path(found[0]).suffix}"
    save(found[0], dest / name)
    return {"file": name, "kind": "sfx", "title": word, "from": "mixkit"}


def openverse_sfx(word, dest, max_seconds):
    for hit in openverse(word, music=False):
        if (hit.get("duration") or 10_000_000) <= max_seconds * 1000:
            name = f"sfx-{slug(word)}.{hit.get('filetype') or 'mp3'}"
            save(hit["url"], dest / name)
            return {"file": name, "kind": "sfx", "title": hit.get("title"), "from": "openverse",
                    "license": hit.get("license"), "author": hit.get("creator"), "source": hit.get("foreign_landing_url")}
    return None


def sfx(word, dest, source="auto", max_seconds=5):
    finders = {"freesound": lambda: freesound(word, dest, max_seconds), "mixkit": lambda: mixkit(word, dest),
               "openverse": lambda: openverse_sfx(word, dest, max_seconds)}
    order = list(finders) if source == "auto" else [source]
    if source == "freesound" and not os.environ.get("FREESOUND_API_KEY"):
        return {"kind": "sfx", "title": word, "error": "FREESOUND_API_KEY is not set"}
    for name in order:
        try:
            row = finders[name]()
        except Exception as error:  # a source down or a dead link: try the next one
            print(json.dumps({"skipped": name, "word": word, "error": str(error)[:80]}), file=sys.stderr)
            row = None
        if row:
            return row
    return {"kind": "sfx", "title": word, "error": "nothing found"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dest", required=True, help="absolute folder for the files (created)")
    parser.add_argument("--music", help="search words for the bed, e.g. 'acoustic folk upbeat'")
    parser.add_argument("--music-count", type=int, default=3)
    parser.add_argument("--min-seconds", type=float, default=30, help="shortest bed to take")
    parser.add_argument("--sfx", default="", help="comma-separated words, e.g. whoosh,pop,ding")
    parser.add_argument("--sfx-source", choices=["auto", "freesound", "mixkit", "openverse"], default="auto")
    parser.add_argument("--sfx-seconds", type=float, default=5, help="longest effect to take")
    parser.add_argument("--import", dest="import_", action="store_true", help="media import the folder")
    args = parser.parse_args(argv)
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    rows = music(args.music, args.music_count, args.min_seconds, dest) if args.music else []
    rows += [sfx(word.strip(), dest, args.sfx_source, args.sfx_seconds) for word in args.sfx.split(",") if word.strip()]
    if args.import_ and any("file" in r for r in rows):
        out = subprocess.run(["bashcut", "media", "import", str(dest), "--base-rev", "last"],
                             capture_output=True, text=True)
        try:
            ids = {Path(f["path"]).name: f.get("media") for f in json.loads(out.stdout).get("files", [])}
        except (ValueError, AttributeError):
            ids = {}
            print(out.stderr.strip()[:300], file=sys.stderr)
        for row in rows:
            row["media"] = ids.get(row.get("file"))
    for row in rows:
        print(json.dumps({k: v for k, v in row.items() if v is not None}, ensure_ascii=False))


if __name__ == "__main__":
    main()
