---
name: style-study
description: Learn a creator's or channel's editing style by measurement — cut pacing and rhythm, shot sizes, hook, on-screen text, colour (black/white point, saturation, split-tone tint), sound (music under voice, SFX on cuts, silences), speaking rate — from reference videos or the creator's own channel, check the numbers on frames, write a profile with tolerances and a learn / don't-take note per reference, then turn it into a project memo, a saved BashCut library look and text presets, and rules for the other skills, without copying their text, music or graphics. Use when the user shares reference videos or a channel and says "học style", "phân tích kênh", "làm giống kênh X", "dựng theo phong cách này", "phân tích video của tôi", "kênh của tôi".
---

# Study a style

Reply in the user's language. The workflow is **measure → look at frames → profile with tolerances →
differences**. BashCut measures (no ffmpeg, no scripts); the numbers in the profile come from the references, never
from this skill. Sources are cited as (T15 §n) = style-reference study, (T01) = ideation, (T07) = pacing.

## Sources

Work from videos the user provides, or find and download references yourself (for example with `yt-dlp`)
without asking; rights are the user's to handle. Keep downloaded references in a private folder outside any project
that will be published, and never re-upload them.

How many (T15 §3, T01 §3): one video is enough to mimic that one clip; a channel style needs several, and the
sources disagree (5–15 in one study, 10–30 in another). Label the profile's confidence by sample count: under 10
low, 10–15 medium, above 15 higher (T01 §3, §7). Say the tier next to every number.

## 1. Measure

Keep references in a separate study project, never the one you will publish:

```sh
bashcut project create --name "Study - Channel X" --canvas portrait
bashcut media import /abs/refs/ref01.mp4 --base-rev N      # one file per call
bashcut media analyze                                       # job: cuts, picture, sound levels per file
bashcut media transcribe                                    # job: words per file (needs captions.transcribe)
```

| Facet | Command | Record |
|---|---|---|
| Rhythm | `bashcut review shots --media REF --summary` | mean, median, cv, mode (bin and share), cuts per minute; cuts per 10 s and the shot-length histogram from `media analysis --media REF` |
| Shot sizes, moves | `media describe` the shots you looked at (`bc:footage-survey`), then `review shots --media REF --summary` again | shares of each size, move, direction; runs of the same size and move (count them from the shots) |
| Hook and close | `bashcut media frames --sheet --media REF --from 0 --to 3 --count 6`; `media transcript --media REF --as words --to 5` | first cut, first words (`firstSpeech`), first text on screen, the last seconds |
| Speech | `bashcut speech rate --media REF`; `media speech-map --media REF` | rate p10/p50/p90 (syllables for Vietnamese), pauses (`gapStats`), speech share |
| Sound | `bashcut audio measure --media REF --curve` (job) | integrated LUFS, LRA, true peak; short-term level during words vs in the speech-map gaps |
| Colour | place the references on the study timeline (`media place`), then `bashcut color measure --by clip` | black, white, mid, saturation, tint per band (shadows, mids, highlights), per reference |
| Text | `bashcut media ocr --media REF --step 0.5` (job; built-in `vision.text`), then contact sheets | share of seconds with text, where it sits (box y), line height as a share of the frame, words per card, how long a card holds; case and preset look by eye |
| Faces | `bashcut media subjects --media REF --step 1` (job; built-in `vision.faces`) | share of seconds with a face, face height (box height: a size proxy), where the face sits (box x, y) |

A reference's sound is one mixed track: music under voice is read from the level in the gaps against the level
under words, not as separate stems. `audio mix-measure` splits speech, music and SFX only on our own timeline.

## 2. Look before trusting a number

Numbers flag, eyes decide (T15 §4).

- Cut detection misses dissolves, whips and fades through black, fast camera moves score like cuts, and a hard cut
  in a dark scene can score very low (T15 §2). Look at the cuts: `media frames --sheet --media REF --every 1`
  for structure, `bashcut media strip --media REF --from S --to S2` around a suspect cut, `media analysis --media
  REF --min-score X` for weaker candidates; fix the list with `bashcut media cuts --media REF --add S --remove S2`.
  Shots and statistics follow the corrections.
- Open the 3–5 longest shots and the opening on frames before writing anything about them.
- Speech recognition invents text over music: check the words against the strip before counting speech.
- OCR and face boxes are raw: a logo, a sign or a reflection reads as text, a poster as a face. Check boxes
  against `media frame` at the reported `frame` before counting them; which text is a caption is yours to decide.
- Mark anything you estimated (by eye, from a few frames) as `est.` (T15 §4).

## 3. Profile with tolerances

Per facet, write the median and p25–p75 across the references (not only a mean), with n, the files and the date
(T15 §3, §4). Then the tolerance:

- ±20–40 % for shot length, cut rate and duration, framed as a **preference**, not a gate (T15 §3). The sources
  contradict: one treats ±30 % as a must, another as ×0.7–1.3 "a preference, not a hard rule". Tighten when the user
  says "exactly like X"; widen when our footage has less coverage than the reference or the length differs a lot.
- Keep the cut **rate** per section type (hook, body, payoff), not the total number of cuts, when our video is
  longer or shorter (T15 §3, T07 §7). Hand the band to the recipe or `bc:beat-cut` as a range.
- Priority: the user's instruction > what our footage allows > the reference (T15 §2, §7).
- Colour and sound are raw values (black/white point, saturation, tint; level under words and in gaps), not labels
  like "matte" or "punchy" (T15 §3).

## Own-channel mode

When the references are the creator's own videos, their own history is the benchmark, not genre averages (T01 §2,
§4). If the user gives view counts, rank each video by its **multiple over the channel's own median**, which needs at
least 4 videos (T01 §2, §3); report the multiple and let the creator judge (one source flags 1.5–3×, T01 §3). The
multiple says a video did well, not why: compare the measured profile of the outliers with the rest and say it is a
pattern to test, with its confidence tier. Without view counts, the profile is simply "how you edit now".

## 4. Differences, not a copy

- Per reference, one learn / don't-take note: what to learn (rhythm, structure, transition type, camera idea,
  where the hold is) and what not to take (T01 §2, T15 §2).
- Never reproduce their text, music, graphics, logos or characters, their exact sequence of shots, or a look so
  close it passes for theirs (T15 §2, §4).
- Before planning, list 3–5 deliberate differences across structure, opening, signature move, look, music and
  ending; one source asks that at least 4 of these 6 differ (T15 §3).
- After the cut, measure ours with the same functions: `bashcut review shots --summary` against the reference's
  `review shots --media REF --summary`, `bashcut color measure --graded` against the reference clips, `bashcut
  audio mix-measure` against the reference's gap and word levels. Compare pictures with
  `bashcut media frames --reference REF --media OURS --count 6` (REF row above OURS, cell for cell; OURS is a
  source clip or an imported draft export). Then check the differences list: still there?

## 5. Turn it into BashCut

`bashcut library list --pack "Channel X"` first: the style may have been studied before.

1. **Project memo** (`knowledge memo`): the profile table (facet, median, p25–p75, tolerance, n, confidence,
   source file and date), the learn / don't-take notes, the differences list and 5–10 rules, each with the number
   behind it.
2. **Look**: start from the closest look in `bc:color-grade`, move its params toward the measured values, preview,
   import the LUT and grade an adjustment with it; save the look in step 3. The whole style is that look plus
   one `patchItems` caption restyle (`bc:captions-text`).
3. **Library pack**: build each piece once on the timeline, then `bashcut library save-selection --kind look --name
   "Channel X look" --item ADJUSTMENT --pack "Channel X"` (also `text-preset` for its captions and titles,
   `transition-preset` and `effect-preset` for its signature moves, `audio` for SFX you have the rights to). Add
   `--scope user` for every project; it waits for the user's approval.
4. **Review limits**: when the user wants the style checked, set the project's `review` keys (`minShotSeconds`,
   `maxShotSeconds`, caption limits) from the profile's range (`bc:captions-text`, `bc:beat-cut`).
5. **Rules for skills**: if a finding is general (true beyond this channel), propose it as a change to this kit
   with `bc:self-learn`.

Tell the user which rules matter most, with the numbers, n and confidence behind them, and the differences you
will keep.
