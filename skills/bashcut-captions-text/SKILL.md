---
name: bashcut-captions-text
description: Add captions and on-screen text in BashCut — transcribe speech into captions, clean and re-time them, import SubRip, and place hook titles, place cards, keyword stickers and chapter cards with the right preset, size and safe-area position. Use when the video needs subtitles, captions are wrong or hard to read, a hook title, location label or chapter card is needed, or the user says "phụ đề", "sub", "chữ trên hình", "nhãn địa điểm", "tiêu đề", "thẻ chương".
---

# Captions and on-screen text

Reply in the user's language. BashCut draws all text itself (text layers with presets); never render text into
a video with Pillow or ffmpeg.

## Captions from speech

```sh
bashcut captions generate --media MEDIA_ID [--replace]   # job; needs a captions.transcribe plugin
bashcut captions export --format text > /tmp/captions.srt # read and fix
bashcut captions import /abs/captions.srt --base-rev N --replace
```

- Speech recognition invents text over music, crowds, rooms and screen recordings ("hãy subscribe kênh…",
  "cảm ơn các bạn đã theo dõi", repeated phrases). Delete those cues; trust a clip with only that text as
  having no speech.
- Product and place names come out wrong: fix them by hand.
- Voiceover you wrote yourself: write the cues from your own text (one cue per phrase), not from the
  transcript; automatic phrase splits broke lines in the middle of phrases ("một căn / nhà hoàn chỉnh").
- Acronyms read out as words in the voice ("xê en xê") are shown as letters (CNC) in captions.
- On a vertical 1080 px frame keep a caption line under ~28–30 characters; two lines at most.

## Presets

| Preset | Use for |
|---|---|
| `bold-outline` | default captions: white bold with a thick outline (review, food, talking) |
| `cinematic-serif` | small mustard serif captions for cinematic vlogs |
| `hook-title` | the big title in the first seconds |
| `place-card` | location and time labels |
| `keyword-sticker` | one emphasised word or price |
| `chapter-card` | chapter titles in tutorials and list videos |

`style apply food-review` or `style apply cinematic` sets the caption preset and look together. Single items:

```json
{"op":"insert","track":"TEXT_TRACK","item":{"id":"hook-1","at":0,"dur":45,"text":"QUÁN NÀY KHÔNG NÊN ĂN","textPreset":"hook-title"}}
{"op":"setProperties","item":"hook-1","patch":{"textStyle":{"size":0.07,"positionY":0.62,"strokeWidth":6}}}
```

`textStyle.positionY` is the baseline from the bottom (0–1); `size` is a fraction of the frame height. Patches
replace the whole `textStyle`: send every key you want to keep. Add a text layer with
`layers add --kind text --role overlay` when the captions layer is busy.

## Placement rules

- Keep text inside the safe area (`ui view --safe-area on`): TikTok and Reels cover the bottom ~20% and the
  right edge.
- Never cover faces, and keep labels clear of each other (a top-left step label and a top-right tag collided).
- Hook title: 1–2 s, the only text allowed flashy styling.
- Place card at each location change, with the real place and time (camera filenames give the time).
- Chapter cards only in tutorials and list videos. In a narrative vlog, cards with a flash and boom at every
  section change felt disjointed; a hard cut, a bridging voiceover sentence and a small quiet date label worked
  better.
- Emoji stickers: the Stickers panel adds them as `bold-outline` text items; place them off faces (on hair or
  background) and check a frame per sticker.

## Verify

Seek to each title and a few captions (`ui seek`) and look. `captions export` once more to check timing.
