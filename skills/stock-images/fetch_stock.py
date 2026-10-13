#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# ///
"""Search Pixabay or Pexels for stock photos and video, then download the ones you pick.

    uv run fetch_stock.py --query "clay pot" [--kind photo|video] [--orientation portrait] [--source pixabay|pexels]
    uv run fetch_stock.py --source pixabay --kind video --ids 12345,67890 --dest /abs/project/media/stock [--import]

Keys come from the environment only: PIXABAY_API_KEY (pixabay.com/api/docs), PEXELS_API_KEY (pexels.com/api).
Without --source, the first source with a key is used. A search prints one compact JSON line per candidate
(id, size, seconds, tags, preview, page): look at the previews and choose. --ids downloads those (photos about
1080 px on the short side, video the smallest rendition at least --min-short pixels) and prints file, licence,
author and page per file. With --import, `bashcut media import DEST --base-rev last` adds them and each line gets
its media ID. Pixabay asks that results are cached, not hotlinked: download, never place a URL.
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
KEYS = {"pixabay": "PIXABAY_API_KEY", "pexels": "PEXELS_API_KEY"}
LICENCE = {"pixabay": "Pixabay Content License", "pexels": "Pexels License"}


def get(url, headers=None, timeout=30):
    # curl, not urllib: it uses the system's certificates, which some Python installs lack.
    command = ["curl", "-sfL", "-A", AGENT, "--max-time", str(timeout)]
    for name, value in (headers or {}).items():
        command += ["-H", f"{name}: {value}"]
    out = subprocess.run(command + [url], capture_output=True)
    if out.returncode != 0:
        raise OSError(f"curl exit {out.returncode} for {url.split('?')[0]}")
    return out.stdout


def get_json(url, headers=None):
    return json.loads(get(url, headers))


def pick_source(name):
    if name:
        if not os.environ.get(KEYS[name]):
            sys.exit(f"{KEYS[name]} is not set: get a free key ({name}) and export it")
        return name
    for source, env in KEYS.items():
        if os.environ.get(env):
            return source
    sys.exit("no stock key: export PIXABAY_API_KEY or PEXELS_API_KEY (free), or search pexels.com in a browser")


def smallest_at_least(renditions, min_short):
    """renditions: [(width, height, url)] → the smallest whose short side is >= min_short, else the largest."""
    usable = [r for r in renditions if r[2] and r[0] and r[1]]
    if not usable:
        return None
    big = [r for r in usable if min(r[0], r[1]) >= min_short]
    return min(big, key=lambda r: r[0] * r[1]) if big else max(usable, key=lambda r: r[0] * r[1])


# Pixabay: key as a query parameter; orientation is horizontal/vertical.
def pixabay_url(kind, params):
    params = {"key": os.environ[KEYS["pixabay"]], **params}
    base = "https://pixabay.com/api/videos/" if kind == "video" else "https://pixabay.com/api/"
    return base + "?" + urllib.parse.urlencode(params)


def pixabay_row(hit, kind, min_short):
    row = {"id": str(hit["id"]), "source": "pixabay", "kind": kind, "page": hit.get("pageURL"),
           "author": hit.get("user"), "tags": (hit.get("tags") or "")[:80], "license": LICENCE["pixabay"]}
    if kind == "video":
        videos = hit.get("videos") or {}
        best = smallest_at_least([(v.get("width"), v.get("height"), v.get("url")) for v in videos.values()], min_short)
        row.update(seconds=hit.get("duration"), preview=(videos.get("tiny") or {}).get("thumbnail"))
        if best:
            row.update(size=f"{best[0]}x{best[1]}", url=best[2])
    else:
        row.update(size=f"{hit.get('imageWidth')}x{hit.get('imageHeight')}", preview=hit.get("previewURL"),
                   url=hit.get("largeImageURL") or hit.get("webformatURL"))
    return row


def pixabay_search(query, kind, orientation, count, min_short):
    params = {"q": query[:100], "per_page": max(3, min(count, 200)), "safesearch": "true"}
    if kind == "photo":
        params["image_type"] = "photo"
        if orientation in ("portrait", "landscape"):
            params["orientation"] = "vertical" if orientation == "portrait" else "horizontal"
    data = get_json(pixabay_url(kind, params))
    return [pixabay_row(hit, kind, min_short) for hit in data.get("hits", [])][:count]


def pixabay_by_id(item_id, kind, min_short):
    hits = get_json(pixabay_url(kind, {"id": item_id})).get("hits", [])
    return pixabay_row(hits[0], kind, min_short) if hits else None


# Pexels: key in the Authorization header.
def pexels_headers():
    return {"Authorization": os.environ[KEYS["pexels"]]}


def pexels_row(item, kind, min_short):
    row = {"id": str(item["id"]), "source": "pexels", "kind": kind, "page": item.get("url"),
           "license": LICENCE["pexels"]}
    if kind == "video":
        files = [(f.get("width"), f.get("height"), f.get("link")) for f in item.get("video_files", [])]
        best = smallest_at_least(files, min_short)
        row.update(seconds=item.get("duration"), author=(item.get("user") or {}).get("name"), preview=item.get("image"))
        if best:
            row.update(size=f"{best[0]}x{best[1]}", url=best[2])
    else:
        src = item.get("src") or {}
        row.update(author=item.get("photographer"), tags=(item.get("alt") or "")[:80],
                   size=f"{item.get('width')}x{item.get('height')}", preview=src.get("tiny"),
                   url=(src.get("original") or "").split("?")[0] + "?auto=compress&w=1080" if src.get("original") else None)
    return row


def pexels_search(query, kind, orientation, count, min_short):
    params = {"query": query, "per_page": max(1, min(count, 80))}
    if orientation in ("portrait", "landscape", "square"):
        params["orientation"] = orientation
    base = "https://api.pexels.com/videos/search?" if kind == "video" else "https://api.pexels.com/v1/search?"
    data = get_json(base + urllib.parse.urlencode(params), pexels_headers())
    items = data.get("videos" if kind == "video" else "photos", [])
    return [pexels_row(item, kind, min_short) for item in items][:count]


def pexels_by_id(item_id, kind, min_short):
    base = "https://api.pexels.com/videos/videos/" if kind == "video" else "https://api.pexels.com/v1/photos/"
    return pexels_row(get_json(base + urllib.parse.quote(item_id), pexels_headers()), kind, min_short)


SEARCH = {"pixabay": pixabay_search, "pexels": pexels_search}
BY_ID = {"pixabay": pixabay_by_id, "pexels": pexels_by_id}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:40] or "stock"


def download(row, dest):
    suffix = ".mp4" if row["kind"] == "video" else (Path(urllib.parse.urlparse(row["url"]).path).suffix or ".jpg")
    name = f"{row['source']}-{row['id']}-{slug(row.get('tags'))}{suffix}"
    (dest / name).write_bytes(get(row["url"], timeout=300))
    return name


def import_into(dest, rows):
    out = subprocess.run(["bashcut", "media", "import", str(dest), "--base-rev", "last"], capture_output=True, text=True)
    try:
        ids = {Path(f["path"]).name: f.get("media") for f in json.loads(out.stdout).get("files", [])}
    except (ValueError, AttributeError):
        ids = {}
        print(out.stderr.strip()[:300], file=sys.stderr)
    for row in rows:
        row["media"] = ids.get(row.get("file"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--query", help="search words (Vietnamese works on Pexels; Pixabay is best in English)")
    parser.add_argument("--ids", help="comma-separated IDs from a search to download")
    parser.add_argument("--source", choices=sorted(KEYS), help="default: the first one with a key")
    parser.add_argument("--kind", choices=["photo", "video"], default="photo")
    parser.add_argument("--orientation", choices=["portrait", "landscape", "square", "any"], default="portrait")
    parser.add_argument("--count", type=int, default=10, help="candidates to list")
    parser.add_argument("--min-short", type=int, default=1080, help="shortest side wanted for video, in pixels")
    parser.add_argument("--dest", help="absolute folder for downloads (created); needed with --ids")
    parser.add_argument("--import", dest="import_", action="store_true", help="media import the folder")
    args = parser.parse_args(argv)
    if not args.query and not args.ids:
        parser.error("give --query to search or --ids to download")
    if args.ids and not args.dest:
        parser.error("--ids needs --dest")
    source = pick_source(args.source)
    if not args.ids:
        rows = SEARCH[source](args.query, args.kind, args.orientation, args.count, args.min_short)
        if not rows:
            print(json.dumps({"source": source, "query": args.query, "error": "nothing found"}))
    else:
        dest = Path(args.dest)
        dest.mkdir(parents=True, exist_ok=True)
        rows = []
        for item_id in [i.strip() for i in args.ids.split(",") if i.strip()]:
            try:
                row = BY_ID[source](item_id, args.kind, args.min_short)
                if not row or not row.get("url"):
                    raise LookupError("not found")
                row["file"] = download(row, dest)
                row.pop("preview", None)
            except (OSError, LookupError, ValueError, KeyError) as error:
                row = {"id": item_id, "source": source, "error": str(error)[:120]}
            rows.append(row)
        if args.import_ and any("file" in r for r in rows):
            import_into(dest, rows)
    for row in rows:
        print(json.dumps({k: v for k, v in row.items() if v not in (None, "")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
