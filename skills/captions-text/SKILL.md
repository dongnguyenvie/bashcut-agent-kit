---
name: captions-text
description: Add captions and on-screen text in BashCut — transcribe speech into captions, clean and re-time them, import SubRip, word-by-word (highlight, karaoke, reveal) captions, animated titles, Vietnamese-safe fonts and text colour, and place hook titles, place cards, keyword stickers and chapter cards with the right preset, size and safe-area position. Use when the video needs subtitles, captions are wrong or hard to read, a hook title, location label or chapter card is needed, or the user says "phụ đề", "sub", "chữ trên hình", "nhãn địa điểm", "tiêu đề", "thẻ chương", "font", "phông chữ", "lỗi font tiếng Việt", "màu chữ".
---

# Captions and on-screen text

Reply in the user's language. BashCut draws all text itself (text layers with presets); never render text into
a video with Pillow or ffmpeg. With a `[Scope]` (Send to Agent), work only on those items (`bc:edit-workflow`).

## Captions from speech

```sh
bashcut captions generate --media MEDIA_ID [--replace]   # job; needs a captions.transcribe plugin
bashcut captions generate --media MEDIA_ID --from 128 --to 148 --replace   # one stretch again (source seconds)
bashcut captions export --format text > /tmp/captions.srt # read and fix
bashcut captions import /abs/captions.srt --base-rev N --replace
bashcut captions export --as text --format text   # one line per cue: times, seconds, cps | text
bashcut captions export --as json                 # per cue: frames, chars, cps, lines, gapBefore, words with frames
bashcut transcript words --from F --to G          # each word: frames, transcribed/estimated, source seconds
```

Reading speed is a measurement, not a rule: `cps` is characters (spaces included) per second on screen. Common
subtitle guides allow up to about 17 cps for adults and 13 for children (Netflix); short-form captions read in a
glance often sit lower. Pick the range for the audience and genre, then fix the cues outside it (split, merge or
re-time) and read the export again. `gapBefore` below a few frames between cues flickers; negative means they overlap.

- Speech recognition invents text over music, crowds, rooms and screen recordings ("hãy subscribe kênh…",
  "cảm ơn các bạn đã theo dõi", repeated phrases). Delete those cues; trust a clip with only that text as
  having no speech.
- A cue longer than ~10 s, or one word repeated many times ("à à à …"), is a recognition loop: its word timings
  are smeared (a 5 min talk lost 128–237 s to three such cues). `review run` flags them ("Possible recognition
  loop"). Don't cut on them; transcribe that stretch again in ~20 s pieces (`--from/--to` with `--replace`, which
  swaps only the captions heard in the piece), which gave clean sentences. Order matters: the whole clip first,
  then the pieces with `--replace`; a whole-clip run without `--replace` after a ranged one added every line of the
  range a second time.
- Product and place names come out wrong: fix them by hand.
- Voiceover you wrote yourself: write the cues from your own text (one cue per phrase), not from the
  transcript; automatic phrase splits broke lines in the middle of phrases ("một căn / nhà hoàn chỉnh").
- Acronyms read out as words in the voice ("xê en xê") are shown as letters (CNC) in captions.
- On a vertical 1080 px frame keep a caption line under ~28–30 characters; two lines at most.

## Word by word

`captions generate --media ID --word-style highlight` (or `karaoke`, `reveal`) makes captions that follow the
speech word by word; on existing captions: `captions words --all --style highlight [--color "#FFD400"]`, or one
item with `captions words ITEM --style reveal`; `--style none` turns it off. Timings come from the transcription
(Whisper returns them) and are estimated from word length for captions without them (typed or edited ones).
`highlight` suits talking heads and reviews; `reveal` suits hooks and short punchlines; keep `none` for
cinematic serif captions.

- Animate titles with `clip motion ITEM --preset pop-in` (fade-in-out, slide-up, zoom-punch); one animated title
  per moment, captions stay still.

## Presets

| Preset | Use for |
|---|---|
| `bold-outline` | default captions: white bold with a thick outline (review, food, talking) |
| `cinematic-serif` | small mustard serif captions for cinematic vlogs |
| `hook-title` | the big title in the first seconds |
| `place-card` | location and time labels |
| `keyword-sticker` | one emphasised word or price |
| `chapter-card` | chapter titles in tutorials and list videos |

**Library first:** `bashcut library list --kind text-preset` shows these plus the styles saved in the project, on
this Mac or by plugins. Place one with `bashcut library place ID --text "QUÁN NÀY" --at-frame F --base-rev N`, or
restyle a text item with `bashcut library apply ID --item ITEM --base-rev N`. When the user approves a styled
title or label, save it: `bashcut library save-selection --kind text-preset --name "Price tag" --item ITEM`; when
they correct it, `library update ID` (or `--as NEW_ID` for a built-in). The item keeps the preset, the text, its
size, position, outline, font and colours (`textStyle`) and a `clip motion` preset (`bc:library`).

`style apply food-review` or `style apply cinematic` sets the caption preset and look together. Single items:

```json
{"op":"insert","track":"TEXT_TRACK","item":{"id":"hook-1","at":0,"dur":45,"text":"QUÁN NÀY KHÔNG NÊN ĂN","textPreset":"hook-title"}}
{"op":"setProperties","item":"hook-1","patch":{"textStyle":{"size":0.07,"positionY":0.62,"strokeWidth":6}}}
```

`textStyle.positionY` is the baseline from the bottom (0–1); `size` is a fraction of the frame's short side (so a
preset looks the same in portrait and landscape), and a line wider than 90% of the frame shrinks to fit. Patches
replace the whole `textStyle`: send every key you want to keep. Add a text layer with
`layers add --kind text --role overlay` when the captions layer is busy.

## Fonts and colour

`textStyle` also takes `font` (a PostScript name such as `Montserrat-ExtraBold`), `fill`, `stroke` and
`highlight` (`#RRGGBB`; anything else is refused). The presets use Arial Bold and Times, which have every
Vietnamese glyph. Inspector › Text has the same font menu and colours.

- `bashcut fonts list --vietnamese [--query montserrat]` gives the names that draw here (the project's fonts
  first, then the installed ones) and whether each has every Vietnamese letter. A font that is in neither draws as
  Helvetica; `review run` reports it as "Missing font".
- Vietnamese-safe free fonts come from Google Fonts (`https://fonts.google.com/?subset=vietnamese`). Common
  picks for short vertical videos: **Montserrat ExtraBold** for hook titles, **Be Vietnam Pro** (SemiBold or
  Medium) for captions, which stays readable on a phone.
- Download the static files from the family's list (JSON after a 4-character prefix, ~0.1 s):
  `curl -s "https://fonts.google.com/download/list?family=Be%20Vietnam%20Pro" | tail -c +5` →
  `manifest.fileRefs[]` with `filename` (`static/BeVietnamPro-SemiBold.ttf`) and `url`. Licence: SIL Open Font
  License, free in videos. Ask before downloading (like any file), save it under the project's `media/`, then
  `bashcut fonts import /abs/media/BeVietnamPro-SemiBold.ttf`: it goes into the project's `fonts/` folder and
  travels with the project, so the export works on any Mac. Never install fonts into `~/Library/Fonts`.
- Fast-reading captions: yellow fill with a thin black outline
  (`{"fill": "#FFD400", "stroke": "#000000", "strokeWidth": 2}`).
- A title saved as a library text preset keeps its font and colours. A preset saved on this Mac with a project
  font needs that font in the next project too: `fonts import` it there.

## Placement rules

- Keep text inside the safe area (`ui view --safe-area on`): TikTok and Reels cover the bottom ~20% and the
  right edge.
- Never cover faces, and keep labels clear of each other (a top-left step label and a top-right tag collided).
- Hook title: 1–2 s, the only text allowed flashy styling.
- Place card at each location change, with the real place and time (camera filenames give the time).
- Chapter cards only in tutorials and list videos. In a narrative vlog, cards with a flash and boom at every
  section change felt disjointed; a hard cut, a bridging voiceover sentence and a small quiet date label worked
  better.
- Emoji stickers: `library place fire` (or the Stickers panel) adds them as `bold-outline` text items; place
  them off faces (on hair or background) and check a frame per sticker.

## Verify

Render each title and a few captions with `ui frame F` and read the PNGs (position, size, faces, overlaps). `captions export --as text --format text` once more to check timing and cps.
Then `review run`: text under the vertical caption bar is an error with a fix that raises it; the side buttons, the
top bar, landscape title safe, text under 3 % of the short side, captions over two lines or 32 characters (42
landscape), overlapping text and a missing hook in the first 3 s are warnings or notes. `review layout --frame F`
returns each text item's rendered box: `edges` (margin to each frame edge as a share of the frame) next to the
platform's `safeArea`, and `fontShare` next to its `minTextSize`, so you can see how far a caption is from the bar
before moving it.
