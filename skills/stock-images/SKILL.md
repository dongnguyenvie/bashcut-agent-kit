---
name: stock-images
description: Find, download and place stock photos and stock video (Pixabay, Pexels, Internet Archive footage), animated emoji (Noto, OpenMoji), brand logos (Simple Icons) and vector icons (Iconify, as transparent PNG stickers) and open illustration sets in one style (unDraw, Humaaans, Open Peeps, Open Doodles, recoloured to the palette) in a BashCut edit as illustration that blends into the cut, or use a blurred copy of the user's own footage as a background. Use when the edit needs a picture or icon the footage lacks, or the user says "ảnh minh hoạ", "video minh hoạ", "ảnh stock", "pexels", "pixabay", "lấy ảnh trên mạng", "thêm hình mô tả", "icon", "biểu tượng", "sticker minh hoạ", "hình vẽ minh hoạ", "illustration", "tư liệu", "archive", "emoji", "logo".
---

# Stock photos and video

Reply in the user's language.

## 0. Library first

`bashcut library list --kind sticker --query "pot"` may already hold the picture. A plugin may search stock for
you: `bashcut library search "clay pot" --kind sticker` (a job). Place a library picture with `bashcut library place ID --at-frame F --size 0.6 --base-rev N`.

## 1. Search

- **Library first**: `bashcut library list --kind clip --query <words>`; reuse what fits before fetching.
- **Candidates for every stock row at once** (the `plan.visuals` rows that need stock): `slots.json`
  `[{"slot": "pot", "query": "clay pot", "kind": "photo", "orientation": "portrait", "count": 8}, …]`, then
  `uv run <skill_dir>/fetch_stock.py --slots slots.json --dest <project>/media/stock --max-mb <cap>` downloads all,
  saves them to the library and draws numbered sheets (`sheet-N.jpg`, ~6 slots each; a video tile shows its frames). One
  look per sheet, then `--pick "pot=3@120;river=2@300:90"` places candidate n at a frame (:length); a bare n prints
  its ID. Ranges (tune): ≤ 30 s 4–8 slots × 6–8; 30–90 s 8–16 × 6–10; 1.5–5 min 16–40 × 6–10; longer 6–10 slots a
  minute × 5–8; video cap ~150 MB a minute. One lookup: `--query "<q>"` lists, `--ids 1,2 --dest … [--import]` gets.
- **Sources** (`--source`; default the first with a key, else `free`): `pexels`, `pixabay` (free keys
  `PEXELS_API_KEY`, `PIXABAY_API_KEY`, environment only; the only vertical stock video; Pexels takes Vietnamese),
  `free` = Wikimedia + Openverse photos (licence per file), `nasa` (space, science; public domain). No video key:
  say so, use stills with motion. Never place a Pixabay URL. `archive` (Internet Archive photos and footage:
  newsreels, NASA, home movies; `--year 1960-1975` or a slot's `"year"`, `--public-domain`); `documentary` = archive
  + Wikimedia + Openverse, for a news documentary only. Archive tiles show year, length and MB; the file comes at
  `--pick` (~0.3 MB/s, largest MP4 within `--file-mb`); prefer short items, trim to the moment.
- **No key** is not a reason to skip: open `https://www.pexels.com/search/<q>/?orientation=portrait` (videos:
  `/search/videos/<q>/`) in a browser tool, read each result's link and alt text, and look at the thumbnails
  before choosing. Photo ID = the trailing number of `/photo/<slug>-<id>/`. Download URL:
  `https://images.pexels.com/photos/<id>/pexels-photo-<id>.jpeg?auto=compress&w=1080`.

## 2. Download

Download what the edit needs without asking, whatever the licence (photos ~100–250 KB at 1080 px; vertical stock
video 15–60 MB) into the project's `media/stock/`; record nothing (`--source URL` only when at hand), the user
handles rights. Avoid identifiable people. A picture worth reusing goes to the library:

```sh
bashcut library add --kind sticker --name "Clay pot" --file /abs/media/stock/x.jpg --tags food
```

## 3. Place

- **No credits** on the video or in its description unless the user asks; then import with `--origin stock` (or
  `--origin web` for a file taken from someone's own page, such as a CC BY clip) `--license … --source URL --author
  "Name"` (a second `media import` adds them to a file already in) and write the
  lines from `project credits`.
- **Stock video** imports like any clip: `media import /abs/media/stock/x.mp4 --base-rev N`, then `media place`
  on the main layer (it replaces a moment) or an overlay layer (it illustrates one).
- **Still photos** import directly: `media import /abs/media/stock/photo.jpg --place --track OVERLAY --at-frame F
  --base-rev N` (kind `image`; JPEG, PNG with transparency, HEIC). An image is placed for 3 s; trim it to the words
  it illustrates. Frame it with `transform` (zoom below 1 for a card, pan/tilt to place it), and give it life with
  `clip motion ITEM --preset zoom-in` (or `pan-left`/`pan-right`): a still that does not move looks frozen.
  Never convert photos to video files.

- **Generated B-roll** (only when a provider serves it: `capabilities get library.generate --kind clip`; none is
  not a reason to skip stock): `library generate "<shot, framing, light>" --kind clip --request-id broll-1
  [--params '{...}']` (paid providers: `--dry-run` first and say the price; model options such as length and aspect
  are the provider's, read them from its options). Save the one the user picks with `library add --from-result
  JOB:N`, then `library place ID --track OVERLAY --at-frame F --duration N --base-rev N`. It is AI picture: the
  rules below apply as for stock, and `project credits` counts it in the AI share.

## 4. Rules

- **No labels on the picture.** Never write "minh hoạ", "stock", "AI", a source or a licence on the video: it makes
  the cut feel unnatural. Keep the real footage as the main picture and let stock read as illustration by context
  (on top of or between real shots, tied to the words), not by a caption. Never present stock as the real place in
  the narration or titles.
- Tie each picture to the words it illustrates ("nồi đất" → clay pot); 1.4–2 s each, a soft pop sound.
- How many: the `stock` and `icon` rows of `plan.visuals` (`bc:visual-plan` balances them over the video). Without a
  visual plan, 2–3 illustrations per video at most. Always off faces.

## Icons (Iconify)

For a small illustration (money, location pin, clock, check mark, arrow), an icon reads better than a photo. Iconify serves 200k+ vector icons through a free API (no key, ~0.2 s per call, tested
October 2026):

```sh
curl -s "https://api.iconify.design/search?query=cash&limit=20"           # → icons ["mdi:cash", "solar:wallet-bold", …]
curl -s "https://api.iconify.design/collections?prefixes=mdi,solar"       # → each set's licence
curl -s -o cash.svg "https://api.iconify.design/mdi/cash.svg?color=%23FFD400&height=512"
rsvg-convert -w 512 -h 512 cash.svg -o cash.png    # transparent PNG; or: magick -background none -density 1536 cash.svg -resize 512x512 cash.png
```

- BashCut imports PNG, not SVG: convert first. Never use `qlmanage` for this: it paints a white background.
- Prefer filled sets (names with `solid`, `fill`, `bold`, or `fluent-emoji-flat` for colour emoji): thin outline
  icons disappear on a phone. `?color=` recolours one-colour icons; colour emoji keep their own colours.
- Download without asking, like photos. Save under `media/stock/icons/`, place like a still
  (`media import … --place --track OVERLAY`), 512 px, small (`transform` zoom ~0.25–0.4), with a pop sound, and
  keep the good ones: `bashcut library add --kind sticker --name "Cash" --file /abs/media/stock/icons/cash.png --tags money`.

## Emoji for keyword pops (Noto Animated, OpenMoji)

All the pops of a video in one call: `uv run <skill_dir>/fetch_emoji.py --words "wow,money,fire,tiền" --dest
<project>/media/emoji` (English or Vietnamese words) draws one sheet, a row per word, animated Noto first (`png` =
OpenMoji still). One look, then `--pick "wow=1@120:30;money=2@300:30" [--place-size 0.2 --position top]` saves each as
a library sticker and places it (animated WebP → movie with alpha). Land it on the payoff word, off faces, with a pop
sound; length from `bc:effects`.

## Brand and tool logos (Simple Icons)

`uv run <skill_dir>/fetch_logos.py --brands "figma@120:90,notion@210:90" --dest <project>/media/logos --on dark`:
an exact name, slug or alias renders a PNG in the brand colour (white/black when the colour is under 3:1 on `--on`),
saves a library sticker and places it at @frame:length; no look needed. A name Simple Icons lacks comes in its own
colours from Iconify (logos, devicon); a near miss prints close slugs and one sheet: run again with the slug. Logos
are trademarks: use one only to name the product shown or reviewed, never to suggest sponsorship, endorsement or a
partnership, never recoloured into the channel's palette or altered.

## Illustrations in one style (open sets)

For explainers and promos, an open set beats `image.generate`: no generation cost, no AI disclosure, and every
picture in one style. Use `library generate` / `image.generate` only for a subject no set draws (a named place, a
product, a mascot). Sets: `undraw` (~1,800 flat scenes by topic: finance, shopping, ideas, charts, apps, travel;
one accent colour; the widest for explainer topics), `humaaans` (90 flat people: walking, jogging, pointing,
wheelchair), `open-peeps` (93 hand-drawn people: bust, standing, sitting; faces), `open-doodles` (33 sketchy
scenes). One set per video; the first `--set` is stored in project data and reused, never mix sets.

`slots.txt` holds `slot: words` lines, then `uv run <skill_dir>/fetch_illustrations.py --slots slots.txt --dest
<project>/media/illustrations --set undraw --palette "#accent,#second"` (palette: the brand kit's, else two
colours from the plan) fetches the set once, recolours it and draws numbered sheets. One look per sheet, then
`--pick "hook=1@0:90;idea=3@300:75" [--place-size 0.5 --position bottom]` renders a transparent PNG, saves a
library sticker and places it; a bare n prints its ID and file (HyperFrames input). Never write or read SVG.

Generated pictures (an `image.generate` plugin installed): set the style once with `bashcut image style --style
"<style>" --references <character.png> --disclosure "Ảnh tạo bằng AI"`, then every scene in one job: `bashcut image
generate prompts.json` (scene prompts only; the lock adds the style). One look at its contact sheet, re-generate only
the `failed` or off-model scenes, place with `media place`, then `bashcut image disclose` once (review flags
`ai-undisclosed`). Mascot poses for the brand: `bashcut library brand-pose <kit> --pose thinking --image photo.jpg`.

## Free fallback: blurred own footage

For a background (a horizontal clip in a vertical frame, a split moment, an info card), put a copy of the same
clip on the layer below, zoomed until it fills the frame, and darken and soften it with an adjustment until the
subject in front reads clearly. There is no right value: footage, text and grade all change it. As an example
only, zoom ~1.8 with `exposure` −1 and `saturation` 0.7 has worked; a bright, busy background needs more, a dark
one less. Check with `ui frame F` and `ui frame F --phone` (text and edges at the size a viewer sees them) and
adjust. Same colours, no licence question.
