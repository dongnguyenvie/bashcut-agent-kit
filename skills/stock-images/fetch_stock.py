#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10.1"]
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

Candidates, to choose from one look instead of one preview at a time:

    uv run fetch_stock.py --slots slots.json --dest /abs/project/media/stock [--max-mb 150]
    uv run fetch_stock.py --query "clay pot" --candidates 8 --dest /abs/project/media/stock
    uv run fetch_stock.py --dest /abs/project/media/stock --pick "pot=3;river=2,5"

--slots is a JSON list of {"slot", "query", "kind", "orientation", "count"}. Every candidate is downloaded in
parallel (videos until --max-mb, the rest kept for --pick), saved to the project library (`library add --kind
clip`, tags = stock, slot, words) and drawn on numbered contact sheets, about --sheet-slots slots a sheet (a video
tile shows the provider's frames). It prints one line per slot and the sheet paths; look at the sheets, then
`bashcut library place ID` the ones you choose (IDs in DEST/candidates.json, or from --pick, which also
downloads a chosen video that was over the cap). The rest stay in the library for later edits.
"""
import argparse
import concurrent.futures
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
        row.update(seconds=item.get("duration"), author=(item.get("user") or {}).get("name"), preview=item.get("image"),
                   frames=[p.get("picture") for p in item.get("video_pictures", []) if p.get("picture")][:3])
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


def file_name(row):
    suffix = ".mp4" if row["kind"] == "video" else (Path(urllib.parse.urlparse(row["url"]).path).suffix or ".jpg")
    return f"{row['source']}-{row['id']}-{slug(row.get('tags') or row.get('words'))}{suffix}"


def download(row, dest):
    name = file_name(row)
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


def bashcut(*args):
    try:
        out = subprocess.run(["bashcut", *args], capture_output=True, text=True)
    except FileNotFoundError:
        return {"error": "bashcut is not on PATH"}
    try:
        return json.loads(out.stdout)
    except ValueError:
        return {"error": (out.stderr or out.stdout).strip()[:200] or f"bashcut exit {out.returncode}"}


def library_add(row, dest, scope):
    """Save a downloaded candidate as a library clip; fills row['id'] (or row['error'])."""
    tags = ",".join(t for t in ["stock", row.get("slot"), *slug(row.get("words")).split("-")] if t)
    wanted = slug(f"{row['source']}-{row['id']}")
    args = ["library", "add", "--kind", "clip", "--file", str(dest / row["file"]), "--scope", scope,
            "--name", f"{row.get('slot')} #{row.get('n')} {row.get('tags') or ''}"[:80].strip(), "--tags", tags]
    args += ["--id", wanted]
    for flag, key in (("--source", "page"), ("--license", "license"), ("--author", "author")):
        if row.get(key):
            args += [flag, str(row[key])]
    added = bashcut(*args)
    item = added.get("item") if isinstance(added.get("item"), dict) else added
    if added.get("error") and "already has" in str(added["error"]):
        row["libraryId"] = f"{scope}:{wanted}"  # the same picture, fetched before
    elif added.get("error"):
        row["libraryError"] = str(added["error"])[:120]
    else:
        found = item.get("reference") or item.get("id")
        row["libraryId"] = found if ":" in str(found) else f"{scope}:{found}"


def fetch_body(url, timeout=300):
    try:
        return get(url, timeout=timeout)
    except OSError as error:
        print(json.dumps({"skipped": url.split("?")[0], "error": str(error)[:80]}), file=sys.stderr)
        return None


def read_slots(args):
    if args.slots:
        slots = json.loads(Path(args.slots).read_text())
    else:
        slots = [{"slot": slug(args.query), "query": args.query}]
    for i, slot in enumerate(slots):
        slot.setdefault("slot", slug(slot.get("query")) or f"slot{i + 1}")
        slot.setdefault("kind", args.kind)
        slot.setdefault("orientation", args.orientation)
        slot["count"] = int(slot.get("count") or args.candidates)
    return slots


def gather(slots, source, dest, max_mb, min_short, scope, use_library):
    """Search every slot, download photos (and videos up to max_mb), save them to the library."""
    def search(slot):
        try:
            return SEARCH[source](slot["query"], slot["kind"], slot["orientation"], slot["count"], min_short)
        except (OSError, ValueError) as error:
            return [{"error": str(error)[:120]}]

    with concurrent.futures.ThreadPoolExecutor(6) as pool:
        found = list(pool.map(search, slots))
    rows, left = [], None if max_mb is None else max_mb * 1_000_000
    for slot, hits in zip(slots, found):
        for n, row in enumerate([h for h in hits if h.get("url")], 1):
            row.update(slot=slot["slot"], words=slot["query"], n=n, file=file_name(row))
            rows.append(row)
        if not any(h.get("url") for h in hits):
            rows.append({"slot": slot["slot"], "words": slot["query"],
                         "error": next((h["error"] for h in hits if h.get("error")), "nothing found")})
    wanted = [r for r in rows if r.get("url")]
    photos = [r for r in wanted if r["kind"] == "photo"]
    videos = [r for r in wanted if r["kind"] == "video"]
    with concurrent.futures.ThreadPoolExecutor(6) as pool:
        for row, body in zip(photos, pool.map(lambda r: fetch_body(r["url"]), photos)):
            if body is None:
                row["error"] = "download failed"
            else:
                (dest / row["file"]).write_bytes(body)
        # videos in slot order, so the cap cuts the last candidates of a slot, not whole slots
        videos.sort(key=lambda r: (r["n"], r["slot"]))
        for row in videos:
            if left is not None and left <= 0:
                row["deferred"] = True
                continue
            body = fetch_body(row["url"])
            if body is None:
                row["error"] = "download failed"
                continue
            (dest / row["file"]).write_bytes(body)
            if left is not None:
                left -= len(body)
        tiles = [r for r in videos if r.get("frames") or r.get("preview")]
        thumbs = dest / ".thumbs"
        thumbs.mkdir(exist_ok=True)

        def thumb(row):
            paths = []
            for i, url in enumerate(row.get("frames") or [row["preview"]]):
                body = fetch_body(url, timeout=30)
                if body:
                    path = thumbs / f"{row['source']}-{row['id']}-{i}.jpg"
                    path.write_bytes(body)
                    paths.append(str(path))
            row["thumbs"] = paths

        list(pool.map(thumb, tiles))
    if use_library:
        for row in wanted:
            if (dest / row["file"]).exists() and not row.get("deferred") and not row.get("error"):
                library_add(row, dest, scope)
    return rows, left is not None and left <= 0


def draw_sheets(rows, dest, slots_per_sheet):
    """Contact sheets: one row of numbered tiles per slot; returns the sheet paths."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps

    tile_w, tile_h, label_h, pad = 220, 220, 22, 6
    by_slot = {}
    for row in rows:
        if row.get("n"):
            by_slot.setdefault(row["slot"], []).append(row)
    names, paths = list(by_slot), []
    font = ImageFont.load_default(size=15)
    for page in range(0, len(names), slots_per_sheet):
        group = names[page:page + slots_per_sheet]
        columns = max(len(by_slot[n]) for n in group)
        width = pad + columns * (tile_w + pad)
        height = pad + len(group) * (label_h + tile_h + label_h + pad)
        sheet = Image.new("RGB", (width, height), (24, 24, 24))
        draw = ImageDraw.Draw(sheet)
        y = pad
        for name in group:
            draw.text((pad, y + 2), f"{name}: {by_slot[name][0].get('words', '')}"[:120], fill=(255, 210, 0), font=font)
            y += label_h
            for i, row in enumerate(by_slot[name]):
                x = pad + i * (tile_w + pad)
                picture = None
                try:
                    if row.get("kind") == "video" and row.get("thumbs"):
                        frames = [Image.open(p).convert("RGB") for p in row["thumbs"]]
                        strip_w = tile_w // len(frames)
                        picture = Image.new("RGB", (tile_w, tile_h))
                        for j, frame in enumerate(frames):
                            picture.paste(ImageOps.fit(frame, (strip_w, tile_h)), (j * strip_w, 0))
                    elif (dest / row["file"]).exists():
                        picture = ImageOps.contain(Image.open(dest / row["file"]).convert("RGB"), (tile_w, tile_h))
                except OSError:
                    picture = None
                if picture:
                    sheet.paste(picture, (x + (tile_w - picture.width) // 2, y + (tile_h - picture.height) // 2))
                else:
                    draw.rectangle([x, y, x + tile_w, y + tile_h], outline=(90, 90, 90))
                draw.rectangle([x, y, x + 30, y + 22], fill=(0, 0, 0))
                draw.text((x + 5, y + 3), str(row["n"]), fill=(255, 255, 255), font=font)
                info = row.get("size", "")
                if row.get("seconds"):
                    info += f" {row['seconds']}s"
                if row.get("deferred"):
                    info += " · later"
                if row.get("error"):
                    info = row["error"]
                draw.text((x, y + tile_h + 3), info[:30], fill=(200, 200, 200), font=font)
            y += tile_h + label_h + pad
        path = dest / f"sheet-{page // slots_per_sheet + 1}.jpg"
        sheet.save(path, quality=82)
        paths.append(str(path))
    return paths


def pick(dest, spec, scope):
    """--pick "slot=3;other=2,5": the chosen candidates' library IDs, downloading a deferred video first."""
    manifest = dest / "candidates.json"
    rows = json.loads(manifest.read_text())
    chosen = []
    for part in [p for p in spec.split(";") if p.strip()]:
        slot, _, numbers = part.partition("=")
        for n in [int(x) for x in numbers.split(",") if x.strip()]:
            row = next((r for r in rows if r.get("slot") == slot.strip() and r.get("n") == n), None)
            if row is None:
                chosen.append({"slot": slot.strip(), "n": n, "error": "no such candidate"})
                continue
            if row.get("deferred"):
                body = fetch_body(row["url"])
                if body is None:
                    chosen.append({"slot": row["slot"], "n": n, "error": "download failed"})
                    continue
                (dest / row["file"]).write_bytes(body)
                row.pop("deferred")
            if not row.get("libraryId"):
                library_add(row, dest, scope)
            chosen.append({"slot": row["slot"], "n": n, "id": row.get("libraryId"),
                           **{k: row.get(k) for k in ("file", "kind", "size", "seconds", "libraryError")}})
    manifest.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    return chosen


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
    parser.add_argument("--slots", help="JSON file: [{slot, query, kind, orientation, count}]; needs --dest")
    parser.add_argument("--candidates", type=int, default=0, help="with --query and --dest: download this many")
    parser.add_argument("--max-mb", type=float, help="cap on the video download, in MB (photos are small)")
    parser.add_argument("--sheet-slots", type=int, default=6, help="slots per contact sheet")
    parser.add_argument("--pick", help='"slot=3;other=2,5": library IDs of the chosen candidates')
    parser.add_argument("--no-library", dest="library", action="store_false", help="do not save to the library")
    parser.add_argument("--scope", choices=["project", "user"], default="project", help="library scope")
    args = parser.parse_args(argv)
    if args.pick:
        if not args.dest:
            parser.error("--pick needs --dest")
        for row in pick(Path(args.dest), args.pick, args.scope):
            print(json.dumps({k: v for k, v in row.items() if v not in (None, "")}, ensure_ascii=False))
        return
    if args.slots or (args.query and args.candidates and args.dest):
        if not args.dest:
            parser.error("--slots needs --dest")
        dest = Path(args.dest)
        dest.mkdir(parents=True, exist_ok=True)
        rows, capped = gather(read_slots(args), pick_source(args.source), dest, args.max_mb, args.min_short,
                              args.scope, args.library)
        sheets = draw_sheets(rows, dest, max(1, args.sheet_slots))
        (dest / "candidates.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
        for slot in dict.fromkeys(r["slot"] for r in rows):
            mine = [r for r in rows if r["slot"] == slot]
            line = {"slot": slot, "candidates": len([r for r in mine if r.get("n")]),
                    "inLibrary": len([r for r in mine if r.get("libraryId")]),
                    "deferred": len([r for r in mine if r.get("deferred")]) or None,
                    "error": next((r["error"] for r in mine if r.get("error") and not r.get("n")), None)}
            print(json.dumps({k: v for k, v in line.items() if v not in (None, 0) or k == "candidates"}))
        print(json.dumps({"sheets": sheets, "manifest": str(dest / "candidates.json"),
                          "capped": capped or None}, ensure_ascii=False))
        return
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
