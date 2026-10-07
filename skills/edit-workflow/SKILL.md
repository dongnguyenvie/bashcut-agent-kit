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
- Plugins can teach you. Before using a plugin's feature (its action, option or capability, such as
  `captions generate` through a transcription plugin), check `bashcut skills list --scope plugin` and read the
  plugin's skill (`bashcut skills get <plugin-id>:<name>`; your session's knowledge also lists them with their
  paths). Its steps and limits win over general advice here. Plugin skills are read-only: put a correction in a
  lesson or a project copy (`bc:self-learn`), never in the plugin's folder.
- Recipes. A vlog follows a recipe when the `bashcut.vlog` plugin is ready (`skills list --scope plugin`): start with
  `bashcut.vlog:plan`, which picks the topic recipe, sets the project's outputs and review profile and plans the
  hook and sections. A project set up that way has `recipe.skill` in `project get`: read that skill and use its
  values (cut rate, caption and title presets, look intent, music level) wherever a kit skill gives a default. No
  plugin: follow this kit's defaults and suggest installing it (`plugins search vlog`).
- Read before you edit: `context get`, then `timeline get --format text`. Track IDs and roles come from the
  read, never from memory. Every edit needs the latest `--base-rev`.
- Respect an attached scope. A request that starts with a `[Scope]` block, or a `scope` list in `context get`,
  names the timeline items the user picked with Send to Agent: change only those (their linked sound or picture
  follows). New items such as a title or an adjustment layer are fine inside their frame range. Ask before
  touching anything else, even a problem you noticed elsewhere. Attaching and removing items is the user's job:
  never run `chat attach` or `chat detach`.
- BashCut may enforce the scope (the scope guard, `scope.mode` in `context get`). An edit outside it fails with
  `-32004` (`data.outOfScope` item IDs, `data.projectWide` changes). Never retry it or work around it:
  - `held: true`: the user is being asked in the app. Tell them what the edit does and wait; `context get` shows
    it as `scope.held`, then `scope.last.outcome` is `applied`, `rejected` or `failed`. `applied`: re-read and go
    on. `rejected`: leave it and ask what they want instead. `failed` with a stale revision (the project changed
    while it waited): re-read, and send it again only if it is still wanted.
  - No `held`: the user rejected it or the guard blocks such edits. Stop and ask.
  - `-32003` while an edit is held: wait for the user's answer first.
  - `-32002` (stale revision) is checked before the scope: re-read the timeline and retry with the new `--base-rev`.
- What you may do without asking is in `context get` `agentPermissions`: `edits` (false: you cannot edit; tell the
  user), `autoApprove` (exports, kit setup, library items and preferences for every project run at once instead of
  waiting for the user), `scopeGuard` (`ask`, `block` or `off`) and `allowAll` (the user's "Dangerously allow all
  agent actions"). Even with `allowAll`, keep to the scope and say what you changed outside it. Only the user can
  change these switches.
- Library first. Before building a text style, effect, transition, look, sound or sticker, check
  `bashcut library list --kind K` (the project, this Mac, plugin packs, built-ins) and reuse a fit with
  `library place` or `library apply`. Save a result the user liked with `library save-selection` (project scope
  by default; `--scope user` waits for the user's approval). When the user corrects a saved item,
  `library update ID` saves a new version; built-in and plugin items are read-only, so save a copy with `--as NEW_ID`.
  Nothing fits and the user wants one: make it with `bc:library`.
- Look at your work: `ui frame F` renders the edit at frame F to a PNG (without moving the user's playhead);
  read it. You cannot hear: ask the user to listen where sound matters.
- The kit's Python scripts run with `uv` (`uv run`, `uvx`). Inside BashCut your terminal points uv at BashCut's
  shared runtime folders (`UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR`, shared with its plugins): keep them, never run
  `uv cache clean` or `pip install` into the system Python; the user clears them in Settings › Storage.
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
10. review → fix → export   measure, review, apply fixes, repeat (at most 3 rounds); export only with no error
11. bc:library              harvest: propose what to keep (a grade, an effect, a sound) for the next video
12. bc:self-learn           write down what went wrong so it does not happen again
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

Then name the platforms: `project format --outputs reels,tiktok --base-rev N` (export presets, first one primary;
a recipe sets them for you). The review checks the first one's platform — its safe zones (Reels' caption bar is the
tallest, 20 %), smallest text and longest length (Reels and Shorts: 3 minutes) — and the Export sheet starts with
it. Without outputs the review assumes TikTok for portrait and YouTube for landscape.

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
- Find lines before cutting: `media transcribe` (a job, needs a `captions.transcribe` plugin) on the talking clips,
  then `media transcript --media ID --as text --format text` to read each file's phrases in its own seconds. Once
  cut, `transcript words --heard` gives each word's timeline frames through the clips as they are now (time a
  graphic, an SFX or a cut to a word from one read); `captions generate` places captions from the same transcript.

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

Every edit ends with a review loop. Do not export, and do not tell the user the video is done, while the review
has an error.

```sh
bashcut review measure                    # a job: renders the picture checks, runs plugin review checks
bashcut jobs status <job>                 # wait until completed; measure again after every edit
bashcut review run --summary --min-severity warning
```

`review run --summary` returns `{issues, summary: {errors, warnings, infos, passed}}`; `passed` means no error.
Issues come errors first (a recipe's `review.severities` may have raised or lowered some checks on purpose); each has `severity`, `frame` (and `endFrame` for a stretch), `source` when a plugin found
it, and usually a `fix`:

| `fix` | What to do |
|---|---|
| `command: timeline.apply` | write `fix.arguments.ops` to a file and run `timeline apply ops.json --base-rev N --label "<fix.arguments.label or the issue title>"` |
| `command: timeline.close-gap` | `timeline close-gap --at-frame <atFrame> --base-rev N` (with `--track` when given) |
| `command: review.measure` | the picture (or plugin checks) were not measured for this revision: measure, then review again |
| `command: export.start` | loudness is measured from a normalized export: do it last (see below) |
| `command: fonts.import`, `captions.generate` | run it as the issue says (`bc:captions-text`) |
| `hint` only | do what it says with the skill for that area (the table below), or ask the user when it is a choice of taste |

Read the numbers, not only the issues. The issues are verdicts with built-in limits; these commands return the
measurements behind them, so you can judge against the plan and the genre's range:

```sh
bashcut review picture --samples false     # per hard cut: difference across it (near 0 = the same picture)
bashcut review picture --from F --to G     # per sample: luma, spread, change, peak (fractions of full scale)
bashcut review shots --summary             # per shot: seconds, source, zoom, speed, motion; count, median, cuts/min
bashcut review layout --frame F            # per text item: rendered bounds, font share, margin to each edge + zones
bashcut transcript words --from F --to G   # per spoken word: frames, gap before, source seconds of its clip
bashcut media analysis --media ID          # a source file: tech facts, its shots and motion, sound spans (media analyze first)
bashcut media speech-map --media ID        # a source file's sound spans and gaps, with the floor and separation used
bashcut transcript words --heard           # stored transcript words through the clips now (media transcribe first)
```

`review picture` and `review shots` motion come from the last `review measure` (`current` / `pictureMeasured`
false: measure again). Values are facts, not verdicts: a 0.004 change can be a deliberate locked-off interview. Look
at the frame (`ui frame F`) before fixing anything the numbers point to.

One round: fix every error, then the warnings that are clearly wrong (a caption under the platform's buttons, a
jump cut, music not ducked); a fix is one labelled edit, so the user can undo it. Then measure and review again: the
revision changed, so earlier measurements no longer count. Stop after 3 rounds, or when a round fixes nothing, and
tell the user what is left and why (a warning that is a deliberate choice, such as a long still title the user asked
for, stays).

| Issue | Skill |
|---|---|
| gap, repeated framing, jump cut, very short or long static shot, frozen picture | `bc:beat-cut` (punch-in, cutaway, trim), `bc:effects` (Ken Burns, slow punch-in) |
| black picture | offline media or a layer hiding the picture: `media list`, `timeline get`, `ui frame` |
| text in the caption bar or side buttons, too small, too many lines, overlap, missing font, no hook | `bc:captions-text` |
| loudness, true peak, music not ducked, dead air, music drops out, voiceover near speech | `bc:audio-mix` |
| a plugin's issue (`source`) | read that plugin's skill first (`skills list --scope plugin`); its `fix` works like the built-in ones |

Loudness is measured from the last normalized export of the same revision, so it comes last: when the rest passes,
make the draft with normalization, then review once more:

```sh
bashcut export start --preset quick-draft --name draft-v1 --include-srt --normalize-audio
bashcut export status
bashcut review run --summary --min-severity warning     # now includes loudness and true peak
bashcut ui frame 120                                    # PNG of the edit at frame 120: read it
python3 <footage-survey skill>/survey.py /abs/draft-v1.mp4 --every 2 --out /abs/project/survey/draft-v1
```

The last line puts the whole draft on one labelled sheet (a frame every 2 s): read it to check the pace,
repeated shots and where text sits before asking the user to watch. Exports wait for the user's approval in the app
unless `agentPermissions.autoApprove` is on.

Report the loop to the user in a few lines: the rounds, what was fixed (issue → edit), and what is left with the
reason. Example: "Review: 2 rounds. Fixed a 1.2 s black gap at 0:41 (closed), raised the caption out of the bottom
bar, punched in on the jump cut at 1:05. Left: one 9 s shot at 0:12, kept because it is the hook you chose."

## Taste of the user

Preferences (length, pace, voice, style) live in BashCut, not in this kit. `context get` summarizes the active
lessons, preferences and project facts: follow them. At the start of every edit also run `knowledge get`:
`userMemo` holds the free-text notes for every project, `memo` and `skills` are this project's own (stored in the
project folder). Record taste with `knowledge set-pref`, project facts with `knowledge set-fact` and lessons with
`knowledge add-lesson` (see bc:self-learn).
