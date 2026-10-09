# Edit workflow: reference

Detail for `bc:edit-workflow`. Read the section you need; the stage order, gates and rules are in SKILL.md.

## Starting a project

```sh
bashcut project create --name "Market vlog" --dir ~/Movies/BashCut --footage /abs/path/footage \
  --canvas portrait --fps 29.97 --language <tag>      # the user's language, e.g. en, vi, ja
bashcut media list                        # media IDs, fps, frames, hasAudio, proxy state
```

A new project has no default language. Before `project create`, read what the prompt already says and ask the
rest in **one** round of at most 4 questions (AskUserQuestion in Claude Code, plain questions in Codex), never one
by one. The recipe's `askAtIntake` fields join the round; drop the least important question to stay at 4:

| Question | Skip it when | Options to offer |
|---|---|---|
| Language of the speech and captions | the prompt or a project brief names it | the language the user writes in first, then English, then "Other" |
| Where it will be posted | the prompt names the platform or shape | TikTok/Reels/Shorts (portrait), YouTube (landscape), both |
| Length | the prompt gives a length or range | the platform's usual ranges |
| A recipe's `askAtIntake` field (a truth source, a channel name) | the prompt or the knowledge facts give it | what the recipe suggests |

The language the user writes in is a good first option, not an answer: a Vietnamese prompt can ask for an English
video, and footage can speak another language. Pass the answer as `--language` (BCP 47: `vi`, `en`, `en-US`, `ja`).
It drives captions, speech-rate units, voices (`capabilities get --voices` › `speaksContentLanguage`) and fonts
(`fonts list --covers`). When the user does not know yet, create the project without it and set it once the footage
is transcribed (the transcript names the spoken language). Write the answers into the brief as `stated`. Questions
left unanswered are decided by you and written as `inferred` with the reason in `source`; the strategy audit's
packet lists them so the critic checks each guess. They are not asked again later.

Pick the canvas from where the video will be watched: `portrait` for TikTok/Reels/Shorts, `landscape` (16:9)
for YouTube and computers, `square` for feeds. Ask when it is not clear. It can change later with
`project format --canvas landscape` (one undoable edit), but reframing and text placement must then be checked
again with `ui frame`.

Then name the platforms: `project format --outputs reels,tiktok --base-rev N` (export presets, first one primary;
a recipe sets them for you; the Export sheet starts with the first). `platforms get` gives each platform's facts —
shape, longest length, safe zones, loudness target, true peak — and which are outputs; `platforms get <id>` gives one
platform's facts with their source and whether each is hard or a recommendation. The review checks text against the
zones of every output of the frame's shape (the strictest wins; with none, `layout` is null and zones are not
checked), and each export is normalized to its own preset's loudness target. Caption delivery per output (burned in,
a sidecar file, both or none) is the project's `output.captions` setting; the export follows it.

`--footage` links the footage folder into the project (it is never modified). Import the clips before the survey,
one file per call: `media import /abs/path/clip.mp4 --base-rev N` (it does not touch the timeline; `bc:footage-survey`
needs them as project media), then place the ones you chose with `media place --media ID --at-frame F` (or import
with `--place`). The CLI resolves relative paths against its own working directory, so pass absolute paths.
Before planning, `context get` › `analysis` lists the media not yet measured, transcribed or described and the
analysis jobs still running: wait for them or say what the plan does not know yet.

## The brief and the plan as data

The brief (`project set-data brief brief.json --base-rev N`) holds what the edit is for. Each field is
`{value, status, source?}`: `stated` (the user said it), `inferred` (you guessed it from the footage or the
platform) or `confirmed` (the user approved your guess at G1). Fields: `goal`, `audience`, `outputs`, `angle`,
`lengthSeconds` (`{min, max}`), `notes`, plus `ideas` and `references` lists.

```json
{
  "goal": {"value": "Show the night market in 60 s", "status": "stated", "source": "prompt"},
  "outputs": {"value": ["reels", "tiktok"], "status": "stated", "source": "prompt"},
  "lengthSeconds": {"value": {"min": 45, "max": 75}, "status": "inferred", "source": "Reels, a food vlog"},
  "audience": {"value": "friends who were not there", "status": "inferred"}
}
```

The plan (`project set-data plan plan.json --base-rev N`, later `--merge` to change one field) holds how you mean to make it:
`mode` (create, directed, revision), `stage`, `options` (the story options you compared), `sections`
(`{id, label, lengthSeconds {min, max}, reason, frozen}`), `shots` (planned shots: `purpose`, `size`, `mustShow`,
`source` footage, stock or generated), `beats` (script lines: `{id, section, text}`), `decisions`
(`{text, …}`, with the alternatives and the reason), `ranges` (the review limits you chose, `{min, max, source,
reason}`) and `notes`. `context get` summarises both, so a later session (or you after a context reset) resumes from
them; `review run` compares section lengths and the brief's length and outputs with the edit, as info;
`review coverage` says which described shot each clip plays (match it with the planned shots yourself), and
`script check` the beats (or `--beats`/`--text` you give) with the words heard.

A recipe adds its data to the same plan, only what differs from the defaults:

```json
{
  "recipe": {"skill": "bashcut.vlog:product-ad", "version": "0.0.2"},
  "promise": {"hook": "Can one prompt cut a whole ad?", "payoff": "Yes — follow @handle for the next one"},
  "stages": {
    "voiceover": {"required": true},
    "effects": {"required": true, "skill": "bc:motion-graphics", "why": "price card, CTA card"},
    "captions": {"rules": ["no captions while a title or card is on screen"]},
    "colour": {"required": false, "why": "screen recording"}
  },
  "checks": [
    {"id": "cta-handle", "text": "@handle and logo visible through the CTA", "source": "bashcut.vlog:product-ad"}
  ],
  "askAtIntake": ["truthSource", "placement", "channelName"]
}
```

`stages` keys are the stage ids of SKILL.md (never a skill name); `skill` replaces the stage's default skill;
`required: false` with `why` marks a stage `n/a` up front. `checks` are
the recipe's own (at most 8); the kit's generic checks (`bc:review`) are always added. `promise` is generic: every
video opens a question and must close it. `context get` summarises the recipe, the promise, the checks count and the
required or `n/a` stages, so these rules survive a context reset without re-reading the recipe.

Update `stage` with `project set-data plan --merge` at each stage start, so the plan and the run log agree.

## Story

- **Hook in the first 1–3 s**: the best or most surprising moment, often the ending shot or the loudest moment,
  then go back to the start. A cold open of three shots (~8 s) worked well for travel and food vlogs.
- Tool demos and tutorials: the hook is the tool's **output** with its own sound, then the presenter (see
  "Screen recording with a presenter").
- Sections in time order after the hook; mark them with `upsertSection` so the user sees the structure, and give
  each a length range with its reason in the plan.
- Talking videos: build the timeline as a **chain of spoken lines** (real speech + voiceover, ~0.14 s gaps) and
  cut picture to what is being said; select the lines by quote (`bc:rough-cut`). Music-led montages: cut on the
  beat grid (`bc:beat-cut`).
- Find lines before cutting: `media transcribe` (a job, needs a `captions.transcribe` plugin) on the talking clips,
  then `media transcript --media ID --as text --format text` to read each file's phrases in its own seconds. Once
  cut, `transcript words --heard` gives each word's timeline frames through the clips as they are now, and
  `captions find "words as said"` finds where a line is heard on the timeline.
- CREATE mode: write 2–3 story options (T00 §3: ≥2 options compared before choosing), each in a few lines with what
  the footage supports and what it lacks, into `plan.options`. The strategy at G2 is 4–8 sentences plus the section
  table (T00 §3).

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

## Taste of the user

Preferences (length, pace, voice, style) live in BashCut, not in this kit. `context get` summarizes the active
lessons, preferences and project facts: follow them. At the start of every edit also run `knowledge get`:
`userMemo` holds the free-text notes for every project, `memo` and `skills` are this project's own (stored in the
project folder). Record taste with `knowledge set-pref`, project facts with `knowledge set-fact` and lessons with
`knowledge add-lesson` (see `bc:self-learn`).

## The hand-off report

Build it from `run checklist` and `run log`, not from memory of the chat. Start with the checklist's `open` items
(required stages skipped, `done` without evidence, missing audits), then each audit's verdict (say "self-audited"
for `by: self`), the missing recipe when none was installed, the stages run, each gate with the user's answer, the review
rounds (fixed, left), what was measured and what was not (sound not listened to, plugin checks that timed out),
every kept issue with its reason and the `needs_user` items. Example: "Review: 2 rounds. Closed a 1.2 s black gap at
0:41, raised the caption out of the Reels bar. Profile: static shots up to 6 s, a calm travel vlog. Kept: the 9 s
shot at 0:12, the hook you chose. Not listened to: the music under your voice."
