---
name: captions-text
description: Add captions and on-screen text in BashCut — transcribe speech into captions, clean and re-time them, group cues from word timings, captions with a script's exact text timed from speech, import SubRip, word-by-word (highlight, karaoke, reveal) captions, animated titles, Vietnamese-safe fonts and text colour, and pick a text template (stacked keyword, headline + subline, boxed keyword, two-tone pop) for hooks, calls to action, place cards, keyword stickers and chapter cards with the right look, size, contrast and safe-area position. Use when the video needs subtitles, captions are wrong or hard to read, a hook title, location label or chapter card is needed, or the user says "phụ đề", "sub", "chữ trên hình", "nhãn địa điểm", "tiêu đề", "thẻ chương", "font", "phông chữ", "lỗi font tiếng Việt", "màu chữ".
---

# Captions and on-screen text

Reply in the user's language. BashCut draws all text itself (text layers with presets); never render text into
a video with Pillow or ffmpeg. With a `[Scope]` (Send to Agent), work only on those items (`bc:edit-workflow`).
Commands measure and act; the numbers below are ranges with their sources (T09 = the captions study). Look at the
measurement first, choose a value inside the range for this speaker, genre and frame, and say why.

## 1. Words first

```sh
bashcut captions generate --media MEDIA_ID [--replace]   # job; needs a captions.transcribe plugin
bashcut captions generate --media MEDIA_ID --replace --fresh   # transcribe again (after changing the vocabulary)
bashcut captions generate --media MEDIA_ID --from 128 --to 148 --replace   # one stretch again (source seconds)
bashcut media transcript --media MEDIA_ID --as words   # the file's own words: gapBefore, confidence when given
bashcut transcript words --from F --to G          # caption words: index, frames, transcribed/estimated, gapBefore
bashcut transcript words --heard --from F --to G  # words of the stored transcripts, through the clips as they are now
bashcut speech rate --media MEDIA_ID              # syllables (Vietnamese) or words per second, p10/p50/p90
bashcut captions export --as text --format text   # one line per cue: times, seconds, cps | text
bashcut captions export --as json                 # per cue: frames, chars, cps, lines, gapBefore, words with frames
bashcut captions export --format text > /tmp/captions.srt   # edit text by hand, then:
bashcut captions import /abs/captions.srt --base-rev N --replace
```

The whole file is transcribed once and kept (`media transcribe` makes it without placing captions). Captions do
not move when their clips move; `transcript words --heard` does, so time graphics and SFX to it after re-cutting.
Before grouping, read: the language, the lowest-`confidence` words (names, words over noise), the speaker's median
`gapBefore` and `speech rate`. Fix text without moving times; let core own the timings (T09 §4).

- Speech recognition invents text over music, crowds, rooms and screen recordings ("hãy subscribe kênh…",
  "cảm ơn các bạn đã theo dõi", repeated phrases). Delete those cues; trust a clip with only that text as
  having no speech.
- A cue longer than ~10 s, or one word repeated many times ("à à à …"), is a recognition loop: its word timings
  are smeared (one 5 min talk lost 128–237 s to three such cues). Look for them in `captions export` (long cues,
  repeated words); `review run` does not judge text. Don't cut on them;
  transcribe that stretch again in ~20 s pieces (`--from/--to` with `--replace`), which gave clean sentences in
  that project. Whole clip first, then the pieces with `--replace`; a whole-clip run without `--replace` after a
  ranged one added every line of the range a second time.
- Product and place names come out wrong: fix them by hand. Acronyms read out as words ("xê en xê") are shown as
  letters (CNC).

## 2. Group cues

Choose the groups from the measurement, inside these ranges (T09 §3, §7):

| Delivery | Words per cue | Pause that breaks a cue | Characters per line |
|---|---|---|---|
| Energetic vertical (hooks, reactions) | 2–4 | 0.15–0.3 s | vertical: 15–32 Latin |
| Conversational (vlog, review, talking head) | 3–6 | 0.25–0.5 s | vertical: 15–32 Latin |
| Landscape subtitles (tutorial, interview) | 6–8, or full lines | 0.5–0.6 s | 32–42, two lines |

- Fast talkers (high `speech rate`, short median gap) need the low end of the pause range; set the break near the
  speaker's own median gap, not a house number. Cue length 0.5–5 s for social, up to ~7 s for subtitles; one cue
  on screen at a time; bridge tiny gaps so captions do not flicker (T09 §3).
- Character limits depend on font width and size: CJK counts double, and rendered width matters more than the count
  (T09 §3). Lines: 1–2; one for punchy vertical styles.
- Contradictions in the sources, so no single number is "right": "3 words per caption, always" (ShortGPT,
  ghost-editor) against an anti-pattern rule that fixed counts fight the cadence (hyperframes); a 500 ms pause in
  one hyperframes file and 250 ms in another; this kit once said ~28–30 characters per vertical line while review
  used 32 (T09 §3, §5).
- Reading speed is a fact, not an error: about 15–20 Latin characters per second is comfortable and above ~25 is
  hard (T09 §3). Captions of real speech follow the speech; look again at cues above ~20 cps and split or merge
  them, but do not paraphrase.

Then let core re-time the groups in one undoable edit:

```sh
bashcut captions group /abs/groups.json --base-rev N          # [[0,1,2],[3,4,5,6],…] word indices from transcript words
bashcut captions group /abs/groups.json --source heard --base-rev N   # indices from transcript words --heard
bashcut captions group --max-chars C --max-seconds S --break-gap G --from F --to G2 --base-rev N   # rule mode
```

Groups are runs of word `index` values, in order, each word once; cover every word of the stretch (the captions
those words fall in are replaced, their style kept). Break at meaning (phrase ends, commas), not only at the limit.
Rule mode needs all three limits, chosen from the table; core has no default. Read the result: each cue's seconds,
chars and cps, and the gaps and overlaps between cues in frames. Fix outliers by regrouping, or `timeline undo`.

**After every cut, regroup from what is heard:** `captions group --source heard` with indices from `transcript
words --heard`. Captions made before the cut keep the words of lines that were cut away (one edit showed half a
dropped sentence).

## 3. Script text, speech timing

When a script or voiceover text exists, show the script's exact words, never the recogniser's paraphrase (T09 §2,
§4). One line of the script is one cue:

```sh
bashcut captions align --media MEDIA_ID --text "$(cat /abs/script-lines.txt)" --replace   # job
```

The result gives `score` (matched words over the longer count) and the `unmatched` words with their times: read
them; a low score means the take does not follow the script (ad-libs, a cut line). Hand-written cues get
estimated word timings; aligned cues get the speech's.

## Word by word

`captions generate --media ID --word-style highlight` (or `karaoke`, `reveal`) makes captions that follow the
speech word by word; on existing captions: `captions words --all --style highlight [--color "#FFD400"]`, or one
item with `captions words ITEM --style reveal`; `--style none` turns it off. Timings come from the transcription
and are estimated from word length for typed or edited captions. `highlight` suits talking heads and reviews;
`reveal` suits hooks and short punchlines; keep `none` for cinematic serif captions. Emphasis: 0–25 % of words
depending on style, fewer is the safer default; one highlight span per line (T09 §3).

- Animate titles with `clip motion ITEM --preset pop-in` (fade-in-out, slide-up, zoom-punch); one animated title
  per moment, captions stay still.

## Looks: templates and presets

Text is text: a hook, a call to action, a label and a caption differ in role, not in kind. Pick the **look** for the
video (tone, platform, footage), then use it for whatever role the line plays, and keep one title look per video.

| Template (library) | Look | Suits |
|---|---|---|
| `stacked-keyword` | heavy condensed lines, the keyword line large and yellow | vlog, travel, food, Shorts hooks |
| `headline-subline` | wide caps headline over a small sentence | tutorials, lists, explainers |
| `boxed-keyword` | one huge word or number on a light plate | list counts, prices, scores |
| `two-tone-pop` | short lines alternating white/yellow, hard offset shadow | playful, kids, comedy, energetic edits |

Write template text in short lines (`\n`), 2–3 lines, the keyword alone on its line: the last of two lines or the
middle one is emphasised; `textStyle.emphasis.line` picks another (negative counts from the bottom). Busy or bright
footage: keep the shadow, or give the emphasis a `plate`. Check the frame (`ui frame`) and change `fill`, `font` or
`emphasis` for the video rather than settling for the default.

| Renderer preset | Look |
|---|---|
| `bold-outline` | white bold with a thick outline: plain captions (review, food, talking) |
| `cinematic-serif` | small mustard serif: cinematic captions |
| `hook-title` | the stacked-keyword look (no plate); older projects keep working |
| `place-card` | dark plate with a yellow bar, left-aligned |
| `keyword-sticker` | dark text on a yellow sticker |
| `chapter-card` | cream serif between thin gold rules |

**Library first:** `bashcut library list --kind text-preset` shows these plus the styles saved in the project, on
this Mac or by plugins. Place one with `bashcut library place ID --text "THIS PLACE\nIS A TRAP" --at-frame F --base-rev N`, or
restyle a text item with `bashcut library apply ID --item ITEM --base-rev N`. When the user approves a styled
title or label, save it: `bashcut library save-selection --kind text-preset --name "Price tag" --item ITEM`; when
they correct it, `library update ID` (or `--as NEW_ID` for a built-in) (`bc:library`).

A whole-video style is a look (`bc:color-grade`) plus one restyle of every caption: one `patchItems` op with
`"select": {"trackRole": "captions"}` and the preset or `textStyle` (see below). Single items:

```json
{"op":"insert","track":"TEXT_TRACK","item":{"id":"hook-1","at":0,"dur":45,"text":"DON'T EAT\nHERE","textPreset":"hook-title"}}
{"op":"setProperties","item":"hook-1","patch":{"textStyle":{"size":0.07,"positionY":0.62,"strokeWidth":6}}}
{"op":"patchItems","select":{"trackRole":"captions"},"patch":{"textPreset":"bold-outline","textStyle":{"fill":"#FFD400","background":{"color":"#000000","opacity":0.5,"padding":0.3}}}}
```

`setProperties` replaces each field it names; `patchItems` merges objects key by key (`null` deletes a key).

`textStyle.positionY` is the baseline from the bottom (0–1); `size` is a fraction of the frame's short side, and a
line wider than 90% of the frame shrinks to fit. Patches replace the whole `textStyle`: send every key you keep.
Add a text layer with `layers add --kind text --role overlay` when the captions layer is busy.

Size (T09 §3): captions 3–6 % of frame **height** (measured glyphs), secondary text at least 3 %, hook text 6–9 %.
The sources disagree on the minimum (3 % to 5.2 %), and BashCut's `size` and `fontShare` measure the short side,
not the height: on 9:16 a height share is 16/9 times larger as a short-side share. Judge the result on a phone-size
frame, not the number.

## Fonts and colour

`textStyle` also takes `font` (a PostScript name such as `Montserrat-ExtraBold`), `fill`, `stroke` and
`highlight` (`#RRGGBB`); `emphasis {line, fill, scale, plate}` (or `false`) and `lineFills [colors]` shape titles.
The templates use Helvetica Neue Condensed Black, Verdana Bold and Marker Felt Wide, the presets Arial Bold and Times;
all ship with macOS and cover Latin and Vietnamese (check `fonts list --covers` for other languages). Arial and
Times also cover Greek and Cyrillic, but not CJK or Thai (Times not Arabic either).

- `bashcut fonts list --covers [--query montserrat]` gives the names that draw here (project fonts first) that have
  every letter of the project's content language (`--language TAG` for another one); without `--covers` each font
  says `covers` true or false. A font that is in neither draws as Helvetica; `review run` reports it, and reports
  text whose characters the chosen font lacks.
- Free fonts for a language come from Google Fonts, filtered by its subset
  (`https://fonts.google.com/?subset=<subset>`: `latin-ext`, `vietnamese`, `cyrillic`, `japanese`, `thai`…);
  check the result with `fonts list --covers` after importing.
- Download the static files from the family's list (JSON after a 4-character prefix):
  `curl -s "https://fonts.google.com/download/list?family=<Family%20Name>" | tail -c +5` →
  `manifest.fileRefs[]` with `filename` and `url`. Licence: SIL Open Font License. Download without asking (any
  font the look needs, whatever its licence; record it), save
  under the project's `media/`, then `bashcut fonts import /abs/media/<Family>-SemiBold.ttf` (it travels with
  the project). Never install fonts into `~/Library/Fonts`. A library text preset saved with a project font needs
  that font imported in the next project too.
- Contrast is measured, not assumed: `review layout --contrast` gives each item's WCAG ratio and `lightRatio` /
  `darkRatio` (fill and outline against the picture behind). Below about 4.5 (the AA level one source checks,
  T09 §3), change fill or stroke, thicken the outline or move the text, then measure again.

## Placement

- Safe zones are facts per output: `bashcut platforms get` gives each platform's `safeArea` and `layout`, the
  strictest zones of all the project's outputs of that shape. Do not carry one platform's numbers to another.
- Vertical caption height is the biggest contradiction in T09 (from 55–60 % down to near the bottom bar across a
  dozen sources): decide from the zones, faces, a picture-in-picture camera and product cards on this frame, and
  keep one zone per sequence (T09 §3, §4). `review layout` `faceOverlap` stays null: read face boxes with `bashcut media subjects --media ID --from S
  --to S2` (source shares from the top left) and keep captions off them; check on the frame.
- Keep labels clear of each other (a top-left step label and a top-right tag collided in one project).
- Sync (T09 §3): captions start 0–0.15 s before the word; cards and graphics lead by 0.15–0.6 s. Read
  `speech.onsetOffsetFrames` instead of assuming.
- Hold authored text at least its reading time, plus 1–1.5 s after its animation ends; a hook can be shorter when
  the same words are spoken (T09 §3). The kit's old "hook title 1–2 s" and review's 3 s hook window disagreed:
  `review layout --to F` shows the titles and captions of the opening with their hold, `transcript words --to F` the
  first words, and the project sets `hookSeconds`.
- Copy budget (T09 §3): hook text 3–8 words, overlays ≤ 6; on-screen text repeats only the key word or number of
  the spoken line.
- **No captions while a title or card is on screen.** Remove or shorten the cues under a hook title, a price card
  or a CTA card: the same words twice read as a mistake (captions repeated the title and the price card in one ad;
  the critic flagged it). `review layout` `captionOverlap` finds them.
- Place card at each location change, with the real place and time. Chapter cards only in tutorials and list
  videos: in one narrative vlog, cards with a flash and boom at every section felt disjointed; a hard cut, a
  bridging voiceover sentence and a small quiet date label worked better.
- Emoji stickers: `library place fire` adds them as `bold-outline` text items; keep them off faces.

## Review limits are the project's

Core has no caption limits of its own: without them the caption checks report facts only. When the genre needs a
check, set the limits from the range you chose, in one `timeline apply`:

```json
{"op":"setProjectProperties","patch":{"review":{"captionLineChars":C,"captionMaxLines":L,"minTextSize":S}}}
```

`minTextSize` is a share of the short side (see Size). The patch replaces the whole `review` object, and a recipe
may already have set it (`bashcut.vlog`): read `timeline get` first and send every key you keep.

## Verify

```sh
bashcut review layout --contrast          # every text item: lines, longestLineChars, fontShare, edges, holdSeconds,
                                          # wordsPerSecond, speech onset/narrationShare, captionOverlap, templateRepeats
bashcut review layout --frame F           # one frame, with the pictures on screen
bashcut review layout --to F --ink       # text of the opening with its hold; ink of frame 0 (luma, inkShare)
bashcut ui frame F --phone                # 390 px wide: read it as a viewer would
```

Read `edges` next to the zones, `density` (titles and captions per minute), `captionOverlap` (a title over a
caption), and `templateRepeats` (one preset used many times on a layer). Render the longest-line cue and every title
with `ui frame --phone` and look: can it be read at that size, does it cover a face, does it collide? Then
`captions export --as text --format text` for cps and gaps, and `review run`. Stop after about three rounds of
fixes and show the user what is left (T09 §7).
