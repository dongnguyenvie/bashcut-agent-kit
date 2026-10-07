---
name: style-study
description: Learn a creator's or channel's editing style by measurement — cut pacing, shot sizes, hook, on-screen text, colour (black/white point, saturation, split-tone tint), sound design (music under voice, SFX on cuts, silences) — from reference videos, then turn the findings into a project memo, a saved BashCut look and style kit, and rules for the other skills. Use when the user shares reference videos or a channel and says "học style", "phân tích kênh", "làm giống kênh X", "dựng theo phong cách này".
---

# Study a style

Reply in the user's language.

## Sources

Work from videos the user provides or has the right to analyse. Downloading a channel (for example with
`yt-dlp`) is the user's decision: ask first, keep the files in a private folder outside any project that will
be published, and never re-upload them.

## Measure

For each reference video (10–30 is enough):

| What | How | Read it as |
|---|---|---|
| Cuts per minute, shot length | `media import` the video into a study project, `media analyze --media ID`, then `media analysis --media ID`: `picture.summary` (cutsPerMinute, median, histogram, cutCurve per 10 s) | food-review TikTok ≈ 30–40 cuts/min (1.4–1.8 s); cinematic vlog ≈ 12–20 (3–5 s) |
| Shot sizes, hook, text | contact sheet: `python3 <skill_dir>/../footage-survey/survey.py DIR --frames 10`, then look | what the first 3 s show; where and how text appears |
| Colour | `uv run <skill_dir>/../color-grade/grade.py measure v.mp4` | black > 3 = matte; white < 90 = rolled highlights; sat < 30 muted, > 45 punchy; shadow tint R−B < 0 with highlight R−B > 0 = teal-orange |
| Speech vs music | transcribe in BashCut or listen; `media analysis --curve` gives the level per second | music buried (−20 dB), bed (−10), present (−6), leading (> 0) |
| SFX on cuts | listen at 5–10 cuts | hits on most cuts = SFX-driven style; random = none |

The summary uses the same statistics as `review shots --summary` on your own timeline, so the two compare directly.
Cut detection finds hard cuts to the frame but misses dissolves and whips, and fast camera moves can score like
cuts: look at the frames at a few cuts (`--samples`, or a contact sheet), lower `--min-score` when cuts are missing,
and fix the list with `media cuts` before counting. Keep reference videos in a separate study project, not the one
you will publish. Speech recognition invents text over music: trust your ears over a transcript.

## Turn it into BashCut

`bashcut library list --pack "Channel X"` first: the style may have been studied before.

1. **Project memo** (`knowledge memo`): a short table of the numbers and 5–10 rules ("hard cuts only, one
   special transition", "music 12 dB under voice", "captions small serif, lower third").
2. **Look**: start from the closest look in `bc:color-grade`, adjust its params toward the measured numbers,
   preview, import the LUT and `looks save`; then `style save ID --title T --look ID --caption-preset P` so
   `style apply ID` gives the whole style in one step.
3. **Library pack**: save the pieces in one pack so other videos reuse them. Build each once on the timeline, then
   `bashcut library save-selection --kind look --name "Channel X look" --item ADJUSTMENT --pack "Channel X"` (also
   `text-preset` for its captions and titles, `transition-preset` and `effect-preset` for its signature moves,
   `audio` for its SFX). Add `--scope user` for every project; it waits for the user's approval.
4. **Rules for skills**: if a finding is general (true beyond this project), propose it as a change to this kit
   with `bc:self-learn`.

Tell the user which rules matter most, with the numbers behind them.
