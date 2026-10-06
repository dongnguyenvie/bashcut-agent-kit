---
name: stock-images
description: Find, download (with permission) and place licensed stock photos and stock video (Pexels) in a BashCut edit as clearly labelled illustration, or use a blurred copy of the user's own footage as a background. Use when the edit needs a picture the footage lacks, or the user says "ảnh minh hoạ", "video minh hoạ", "ảnh stock", "pexels", "lấy ảnh trên mạng", "thêm hình mô tả".
---

# Stock photos and video

Reply in the user's language.

## 0. Library first

`bashcut library list --kind sticker --query "pot"` may already hold the picture (with its source and licence). A
plugin may search stock for you: `bashcut library search "clay pot" --kind sticker` (job; candidates carry source
and licence). Place a library picture with `bashcut library place ID --at-frame F --size 0.6 --base-rev N`.

## 1. Search

- **Pexels API** (free key at pexels.com/api, 200 requests/hour): with `PEXELS_API_KEY` set,
  `curl -H "Authorization: $PEXELS_API_KEY" "https://api.pexels.com/v1/search?query=<q>&orientation=portrait&per_page=15"`
  (videos: `https://api.pexels.com/videos/search?...`).
- **No key** is not a reason to skip: open `https://www.pexels.com/search/<q>/?orientation=portrait` (videos:
  `/search/videos/<q>/`) in a browser tool, read each result's link and alt text, and look at the thumbnails
  before choosing. Vietnamese queries work.
- Photo ID = the trailing number of `/photo/<slug>-<id>/`. Download URL:
  `https://images.pexels.com/photos/<id>/pexels-photo-<id>.jpeg?auto=compress&w=1080`.

## 2. Ask before downloading

State the files, the source and the size (photos ~100–250 KB at 1080 px; vertical stock video 15–60 MB) and
wait for a yes. Save under the project's `media/stock/` with the source and licence in `media/stock/index.json`.
Pexels License: free, no attribution required, don't sell unaltered copies. Avoid identifiable people. A
picture worth reusing goes to the library with its licence:

```sh
bashcut library add --kind sticker --name "Clay pot" --file /abs/media/stock/x.jpg --source URL --license "Pexels License" --tags food
```

Save the label as a text preset too (`bashcut library save-selection --kind text-preset --name "Stock label"`).

## 3. Place

- **Stock video** imports like any clip: `media import /abs/media/stock/x.mp4 --base-rev N`, then `media place`
  on the main layer (it replaces a moment) or an overlay layer (it illustrates one).
- **Still photos** import directly: `media import /abs/media/stock/photo.jpg --place --track OVERLAY --at-frame F
  --base-rev N` (kind `image`; JPEG, PNG with transparency, HEIC). An image is placed for 3 s; trim it to the words
  it illustrates. Frame it with `transform` (zoom below 1 for a card, pan/tilt to place it), and give it life with
  `clip motion ITEM --preset zoom-in` (or `pan-left`/`pan-right`): a still that does not move looks frozen.
  Never convert photos to video files.

## 4. Rules

- **Never pass stock off as the real place.** Keep the real footage as the main picture; stock goes on top or
  in between with a label "Ảnh minh hoạ · Pexels" / "Video minh hoạ · Pexels" (`keyword-sticker` or
  `place-card` text item), placed where it doesn't collide with other labels.
- Tie each picture to the words it illustrates ("nồi đất" → clay pot); 1.4–2 s each, a soft pop sound.
- 2–3 illustrations per video at most, off faces.

## Free fallback: blurred own footage

For a background (a horizontal clip in a vertical frame, a split moment, an info card), put a copy of the same
clip on the layer below, zoomed to fill (`transform` zoom ~1.8) and graded dark and soft with an adjustment
(`exposure` −1, `saturation` 0.7). Same colours, no licence question.
