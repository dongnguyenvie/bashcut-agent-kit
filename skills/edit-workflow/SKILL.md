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
- Look at your work: `ui frame F` renders the edit at frame F to a PNG (without moving the user's playhead;
  `--phone` at the width a viewer sees text); read it. You cannot hear: ask the user to listen where sound matters.
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
10. review → fix → export   measure, look, then fix or keep with a reason (1–3 rounds); explain what is left
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
a recipe sets them for you; the Export sheet starts with the first). `platforms list` gives each platform's facts —
shape, longest length, safe zones, loudness target, true peak — and which are outputs. The review checks text
against the zones of every output of the frame's shape (the strictest wins; with none, `layout` is null and zones
are not checked), and each export is normalized to its own preset's loudness target.

`--footage` links the footage folder into the project (it is never modified). Import the clips before the survey,
one file per call: `media import /abs/path/clip.mp4 --base-rev N` (it does not touch the timeline; `bc:footage-survey`
needs them as project media), then place the ones you chose with `media place --media ID --at-frame F` (or import
with `--place`). The CLI resolves relative paths against its own working directory, so pass absolute paths.
Before planning, `context get` › `analysis` lists the media not yet measured, transcribed or described and the
analysis jobs still running: wait for them or say what the plan does not know yet.

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

Every edit ends with a review loop: measure, **look**, then fix, adjust the profile or keep it with a reason.

### The review profile

Core has no editorial defaults. Editorial limits live in the project's `review` object: `minShotSeconds`,
`maxShotSeconds`, `maxStillSeconds`, `stillMotion`, `jumpCutChange`, `blackMinSeconds`, `hookSeconds`,
`maxSilenceSeconds`, `maxMusicGapSeconds`, `voiceoverMarginSeconds`, `captionLineChars`, `captionMaxLines`,
`minTextSize`, `minSpeechCoverage`, `loudnessToleranceLU`, `severities` (check ID or prefix → error, warning, info,
off) and `platform` (overrides when an app changes its interface). A check without its limit reports only the
measured value, as info. So set a profile before the first review: a vlog recipe (`bashcut.vlog:plan`) writes one
for its genre; otherwise choose values from the genre's ranges in the kit's skills and the survey, write them with
`timeline apply` (`setProjectProperties` `{"review": {…}}`), and tell the user which values and why ("static
shots up to 3 s: a fast food montage; the interview's long shots stay info").

Ranges other review tools use, as starting points, not defaults (T16; platform facts come from the outputs):

| Limit | Range | What moves it |
|---|---|---|
| `blackMinSeconds` | 0.1–0.5 s | intended dips to black (a fade-through, an end card) |
| `maxStillSeconds` (exact freeze) | 0.8–1 s | a frozen picture is usually a decode or render fault |
| `maxShotSeconds` with `stillMotion` (static shot) | 3–6 s | genre: a calm daily vlog keeps long stills, a montage does not |
| `maxSilenceSeconds` (dead air) | 2–5 s | ASMR or a calm vlog tolerates more |
| `loudnessToleranceLU` | 1–2 LU | the platform and the delivery file |

### The loop

```sh
bashcut review measure                    # a job: renders the picture checks, runs plugin review checks
bashcut jobs status <job>                 # wait until completed; measure again after every edit
bashcut review run --summary --min-severity warning
```

`review run --summary` returns `{issues, summary: {errors, warnings, infos, passed}}`; `passed` means no error.
Each issue has `severity`, `frame` (and `endFrame` for a stretch), `source` when a plugin found it, and usually a
`fix`. An issue is a number held against your profile, not proof: a 0.004 picture change can be a deliberate
locked-off interview. **For each issue, look before fixing:**

1. Look at the moment and read the measurement behind it (table below): `ui frame F` (`--phone` for text), or
   `review window F` for the frames around a cut or a stretch with the cuts, the sound level and the words.
2. Is it a real problem **for this footage and this profile**? Would a viewer notice it at normal speed on a phone?
3. Fix it (one labelled edit), adjust the profile when the limit is wrong for this video (say so), or keep it and
   note why (a long still title the user asked for, a deliberate locked-off shot).

| Issue | Look and measure | Fix with |
|---|---|---|
| black, frozen picture, long static shot | `ui frame F`, `review picture --from F --to G`, `review shots --summary` | `bc:beat-cut`, `bc:effects` (Ken Burns, slow punch-in); black: offline media or a hiding layer (`media list`, `timeline get`) |
| jump cut, repeated framing, gap | `review window F`, `review cuts`, `review shots --summary` | `bc:beat-cut` (punch-in, cutaway, trim) |
| cut or text off the beat or the word | `review window F`, `review sync --events cuts,text` | `bc:beat-cut`, `bc:captions-text` |
| text in a zone, too small, too many lines, overlap, contrast | `ui frame F --phone`, `review layout --frame F --contrast`, `timeline sheet --text --outputs all` | `bc:captions-text` |
| no hook, slow opening | `review hook`, `ui frame` on its first seconds | story, `bc:captions-text` |
| dead air, music drops out or not ducked, voiceover near speech | `review window F`, `audio mix-measure` (a job) | `bc:audio-mix` |
| loudness, true peak | the normalized draft (below), `platforms list` | `bc:audio-mix` |
| colour jumps between clips | `color measure --by clip`, `ui frame F` | `bc:color-grade` |
| a plugin's issue (`source`) | that plugin's skill (`skills list --scope plugin`) | its `fix`, like the built-in ones |

Applying a `fix`: `timeline.apply` → write `fix.arguments.ops` to a file and run `timeline apply ops.json --base-rev
N --label "<fix.arguments.label or the issue title>"`; `timeline.close-gap` → `timeline close-gap --at-frame <atFrame>
--base-rev N` (`--track` when given); `review.measure` → not measured for this revision: measure, then review again;
`export.start` → loudness comes from a normalized export, last (below); `fonts.import`, `captions.generate` → run it
(`bc:captions-text`); a `hint` only → do it with that area's skill, or ask the user when it is a matter of taste.

After a round's edits, measure and review again: the revision changed, so earlier measurements no longer count.
Run 1–3 rounds (1 when the user is waiting and nothing blocks, up to 3 when working alone); stop when a round
fixes nothing. From round 2 on, only a new problem a viewer would notice is worth another round; new nitpicks are
not. Passing checks is not proof of a good video: one tool's edit had every cut on the beat and still had cramped
frames, small text and titles over the icons (T16).

### See the whole edit, then the draft

```sh
bashcut timeline sheet --cuts --text              # contact sheets of the composed edit: a cell at every cut and title
bashcut timeline sheet --every 2 --outputs all    # a cell every 2 s, plus one set per output with its zones shaded
```

No export needed; `cells` maps each `<cell> <m:ss.s>` label to its frame, items and text. Read every sheet for pace,
repeated shots and where text sits (a cell every 0.5–2 s, shorter for fast cuts, T16), then `ui frame` the cells
that look wrong. Loudness comes from the last normalized export of this revision, so make the draft last:

```sh
bashcut export start --preset quick-draft --name draft-v1 --include-srt --normalize-audio
bashcut export status
bashcut review run --summary --min-severity warning     # now includes loudness and true peak
```

The export waits for the user's approval in the app unless `agentPermissions.autoApprove` is on.

### Report

Never call the video done while an error is unexplained: explain every remaining error to the user. Report the
loop in a few lines: the rounds, what was fixed (issue → edit), profile changes with the reason, every kept issue
with its reason, and what was not checked (sound not listened to). Example: "Review: 2 rounds. Closed a 1.2 s black gap
at 0:41, raised the caption out of the Reels bar. Profile: static shots up to 6 s, a calm travel vlog. Kept: the
9 s shot at 0:12, the hook you chose. Not listened to: the music under your voice."

## Taste of the user

Preferences (length, pace, voice, style) live in BashCut, not in this kit. `context get` summarizes the active
lessons, preferences and project facts: follow them. At the start of every edit also run `knowledge get`:
`userMemo` holds the free-text notes for every project, `memo` and `skills` are this project's own (stored in the
project folder). Record taste with `knowledge set-pref`, project facts with `knowledge set-fact` and lessons with
`knowledge add-lesson` (see bc:self-learn).
