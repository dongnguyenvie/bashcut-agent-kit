---
name: edit-workflow
description: Plan and run a whole edit in BashCut from raw footage to export — survey, story, rough cut, rhythm, sound, captions and text, colour, effects, review — and pick the right skill for each step. Use when the user asks to edit/cut a video, make a vlog, review, short or montage from a folder of footage, or asks "where do I start". Also tool demos and tutorials from a screen recording plus a presenter camera. Triggers: "dựng video", "cắt video", "làm vlog", "dựng giúp", "edit this", "bắt đầu từ đâu", "video giới thiệu tool", "video desktop làm nền", "người đọc ở trên video".
---

# Editing a video in BashCut

Reply in the user's language.

BashCut does the editing. Every change goes through the `bashcut_*` MCP tools (or the `bashcut` CLI on PATH):
one validated, undoable edit per call, visible in the app. BashCut's own agent instructions (sent with its MCP
server) explain each command and the `timeline apply` operations; this kit explains **what to do and why**.

Hard rules:
- Never pre-render picture or sound with ffmpeg to fake an effect, a mix or captions. BashCut does cuts, speed and
  ramps, freeze frames, reframing, transitions, volume, fades, ducking, captions, text presets, colour and
  loudness natively, and measures sound itself (`audio measure`, `media sync`). Scripts in this kit only
  **analyse** (contact sheets, LUT files).
- Never edit `project.bashcut.json` by hand while the app is open; never overwrite original footage.
- Ask before downloading media or installing anything. Installing, trusting and setting up plugins is the
  user's job (`plugins search` tells them what to install).
- Read before you edit: `context get`, then `timeline get --format text`. Track IDs and roles come from the
  read, never from memory. Every edit needs the latest `--base-rev`.
- Respect an attached scope. A request that starts with a `[Scope]` block, or a `scope` list in `context get`,
  names the timeline items the user picked with Send to Agent: change only those (their linked sound or picture
  follows). New items such as a title or an adjustment layer are fine inside their frame range. Ask before
  touching anything else, even a problem you noticed elsewhere. Attaching and removing items is the user's job:
  never run `chat attach` or `chat detach`.
- Look at your work: `ui frame F` renders the edit at frame F to a PNG (without moving the user's playhead);
  read it. You cannot hear: ask the user to listen where sound matters.
- Name every folder and file you create in English, lowercase with hyphens (`survey/`, `renders/`,
  `voiceover/`, `subtitles/`, `draft-v1`), whatever language the chat is in. Only text the viewer sees
  (captions, titles, voiceover lines) follows the video's language.
- Seconds → frames with the project fps from `timeline get` (29.97 → 30000/1001). Frames are integers.

## The order

```
1. bc:footage-survey        look at what was actually shot; say plainly what coverage is missing
2. story                    decide the hook, the sections and what is said (real lines first, then voiceover)
3. rough cut                place clips, trim to the story — lock it before step 5
4. bc:beat-cut              rhythm: cut on beats or on sentences, punch-in reframes for variety
5. bc:audio-mix             levels, fades, music bed with ducking, SFX, loudness target
6. bc:voiceover             (when needed) synthesize lines, check every take, place them
7. bc:captions-text         captions from speech, hook title, place cards, chapter cards
8. bc:color-grade           one look for the video, fixes per clip, faded look for flashbacks
9. bc:effects               only where a moment needs it (transition, speed ramp, freeze, sticker)
   bc:stock-images          pictures the footage lacks; bc:style-study to copy a reference style
10. review + export         `review run`, look at frames, `export start` (the user approves)
11. bc:self-learn           write down what went wrong so it does not happen again
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
- Tool demos and tutorials: the hook is the tool's **output** with its own sound, then the presenter (see
  "Screen recording with a presenter").
- Sections in time order after the hook; mark them with `upsertSection` so the user sees the structure.
- Talking videos: build the timeline as a **chain of spoken lines** (real speech + voiceover, ~0.14 s gaps) and
  cut picture to what is being said. Music-led montages: cut on the beat grid (`bc:beat-cut`).
- Find lines with `captions generate --media ID` on each talking clip (needs a `captions.transcribe` plugin),
  then `captions export` to read them with timings.

## Screen recording with a presenter

Users describe this layout in their own words; map each phrase to the edit:

| The user says | Build |
|---|---|
| "video giới thiệu tool", "demo phần mềm", "tutorial", "N phút" | hook = the tool's output (5–7 s, its own sound, a label like "VIDEO NÀY DO AI DỰNG"), then the presenter: prompt → tool working (fast-forward) → how it works, one panel per sentence → limits and next steps |
| "video desktop làm nền", "màn hình làm nền" | screen recording on the main layer, cut to the same moments as the speech (offset from `media sync`, `bc:footage-survey`); on a portrait canvas a blurred copy below fills the bars (`bc:stock-images`) |
| "người đọc / người nói ở trên video", "khung mặt" | presenter camera on an overlay layer *in front of* the screen, zoom ~0.37 (a 9:16 camera becomes ~400 px wide), at the bottom centre; captions between screen and face. "Ở trên" can mean the layer order or the top of the frame: bottom centre was kept without complaint; ask when unsure |
| "ẩn giọng desktop", "tắt tiếng màn hình" | mute the screen clips; speech comes from the camera (`bc:audio-mix`, "Screen recordings") |
| "chọn nhạc phù hợp giọng" | measure candidates against the voice (`audio measure`, `bc:audio-mix`) |
| (unsaid, always) | zoom onto the panel being talked about, fast-forward waiting and typing (`bc:effects`) |

Real case: a 5 min session (camera + screen) became a 2:00 intro with speech over 92% of the time; dropped:
fillers, muddled lines, reactions to bugs, and sentences where the camera mic heard the laptop playing the output.
The first cut opened on the presenter's "hello"; the user sent it back: "end user muốn biết output".

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

Preferences (length, pace, voice, style) live in BashCut, not in this kit. `context get` summarizes the active
lessons, preferences and project facts: follow them. At the start of every edit also run `knowledge get`:
`userMemo` holds the free-text notes for every project, `memo` and `skills` are this project's own (stored in the
project folder). Record taste with `knowledge set-pref`, project facts with `knowledge set-fact` and lessons with
`knowledge add-lesson` (see bc:self-learn).
