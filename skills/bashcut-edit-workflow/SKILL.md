---
name: bashcut-edit-workflow
description: Plan and run a whole edit in BashCut from raw footage to export — survey, story, rough cut, rhythm, sound, captions and text, colour, effects, review — and pick the right skill for each step. Use when the user asks to edit/cut a video, make a vlog, review, short or montage from a folder of footage, or asks "where do I start". Triggers: "dựng video", "cắt video", "làm vlog", "dựng giúp", "edit this", "bắt đầu từ đâu".
---

# Editing a video in BashCut

Reply in the user's language.

BashCut does the editing. Every change goes through the `bashcut_*` MCP tools (or the `bashcut` CLI on PATH):
one validated, undoable edit per call, visible in the app. BashCut's own agent instructions (sent with its MCP
server) explain each command and the `timeline apply` operations; this kit explains **what to do and why**.

Hard rules:
- Never pre-render picture or sound with ffmpeg to fake an effect, a mix or captions. BashCut does cuts, speed and
  ramps, freeze frames, reframing, transitions, volume, fades, ducking, captions, text presets, colour and
  loudness natively. Scripts in this kit only **analyse** (contact sheets, LUT files).
- Never edit `project.bashcut.json` by hand while the app is open; never overwrite original footage.
- Ask before downloading media or installing anything. Installing, trusting and setting up plugins is the
  user's job (`plugins search` tells them what to install).
- Read before you edit: `context get`, then `timeline get --format text`. Track IDs and roles come from the
  read, never from memory. Every edit needs the latest `--base-rev`.
- Look at your work: `ui frame F` renders the edit at frame F to a PNG (without moving the user's playhead);
  read it. You cannot hear: ask the user to listen where sound matters.
- Name every folder and file you create in English, lowercase with hyphens (`survey/`, `renders/`,
  `voiceover/`, `subtitles/`, `draft-v1`), whatever language the chat is in. Only text the viewer sees
  (captions, titles, voiceover lines) follows the video's language.
- Seconds → frames with the project fps from `timeline get` (29.97 → 30000/1001). Frames are integers.

## The order

```
1. bashcut-footage-survey   look at what was actually shot; say plainly what coverage is missing
2. story                    decide the hook, the sections and what is said (real lines first, then voiceover)
3. rough cut                place clips, trim to the story — lock it before step 5
4. bashcut-beat-cut         rhythm: cut on beats or on sentences, punch-in reframes for variety
5. bashcut-audio-mix        levels, fades, music bed with ducking, SFX, loudness target
6. bashcut-voiceover        (when needed) synthesize lines, check every take, place them
7. bashcut-captions-text    captions from speech, hook title, place cards, chapter cards
8. bashcut-color-grade      one look for the video, fixes per clip, faded look for flashbacks
9. bashcut-effects          only where a moment needs it (transition, speed ramp, freeze, sticker)
   bashcut-stock-images     pictures the footage lacks; bashcut-style-study to copy a reference style
10. review + export         `review run`, look at frames, `export start` (the user approves)
11. bashcut-self-learn      write down what went wrong so it does not happen again
```

Lock the cut (steps 3–4) before laying music and SFX: changing clip lengths afterwards breaks every sync point.
Each step is one or a few labelled edits (`--label "Rough cut: market section"`), so the user can undo a step
as a whole.

## Starting a project

```sh
bashcut project create --name "Market vlog" --dir ~/Movies/BashCut --footage /abs/path/footage \
  --canvas portrait --fps 29.97 --language vi
bashcut media list                        # media IDs, fps, frames, hasAudio, proxy state
```

Pick the canvas from where the video will be watched: `portrait` for TikTok/Reels/Shorts, `landscape` (16:9)
for YouTube and computers, `square` for feeds. Ask when it is not clear. It can change later with
`project format --canvas landscape` (one undoable edit), but reframing and text placement must then be checked
again with `ui frame`.

`--footage` links the footage folder into the project (it is never modified). Then add the clips you chose
after the survey, one file per call: `media import /abs/path/clip.mp4 --base-rev N` (add `--place` to also put
it on the timeline, or place it later with `media place --media ID --at-frame F`). The CLI resolves relative
paths against its own working directory, so pass absolute paths.

## Story first

- **Hook in the first 1–3 s**: the best or most surprising moment, often the ending shot or the loudest moment,
  then go back to the start. A cold open of three shots (~8 s) worked well for travel and food vlogs.
- Sections in time order after the hook; mark them with `upsertSection` so the user sees the structure.
- Talking videos: build the timeline as a **chain of spoken lines** (real speech + voiceover, ~0.14 s gaps) and
  cut picture to what is being said. Music-led montages: cut on the beat grid (`bashcut-beat-cut`).
- Find lines with `captions generate --media ID` on each talking clip (needs a `captions.transcribe` plugin),
  then `captions export` to read them with timings.

## Review before export

```sh
bashcut review run                        # structure, gaps, speech coverage
bashcut ui frame 120                      # PNG of the edit at frame 120: read it
bashcut export start --preset quick-draft --name draft-v1 --include-srt --normalize-audio
bashcut export status
python3 <footage-survey skill>/survey.py /abs/draft-v1.mp4 --every 2 --out /abs/project/survey/draft-v1
```

The last line puts the whole draft on one labelled sheet (a frame every 2 s): read it to check the pace,
repeated shots and where text sits before asking the user to watch.

Check: no unintended gaps on the main layer, no two voices at once, captions inside the safe area
(`ui view --safe-area on`), loudness normalised. Exports wait for the user's approval in the app.

## Taste of the user

Preferences (length, pace, voice, style) belong in the **project memo**, not in this kit:
`knowledge get` reads it, `knowledge memo FILE` replaces it. Read it at the start of every edit.
