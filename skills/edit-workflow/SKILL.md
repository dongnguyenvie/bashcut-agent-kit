---
name: edit-workflow
description: Plan and run a whole edit in BashCut from raw footage to export — brief, survey, story options, rough cut, rhythm, script and voiceover, sound, text, colour, effects, review, draft, export, learning — through the user's workflow gates, and pick the right skill for each stage. Use when the user asks to edit/cut a video, make a vlog, review, short or montage from a folder of footage, revise an edit, or asks "where do I start". Also tool demos and tutorials from a screen recording plus a presenter camera. Triggers: "dựng video", "cắt video", "làm vlog", "dựng giúp", "sửa lại video", "edit this", "bắt đầu từ đâu", "video giới thiệu tool", "video desktop làm nền", "người đọc ở trên video".
---

# Editing a video in BashCut

Reply in the user's language. Detail (project setup, the brief and plan JSON, story, screen recordings, the
hand-off report) is in `<skill_dir>/REFERENCE.md`.

BashCut does the editing. Every change goes through the `bashcut_*` MCP tools (or the `bashcut` CLI on PATH):
one validated, undoable edit per call, visible in the app. BashCut's own agent instructions explain each command;
this kit explains **what to do and why**. Core measures and acts; editorial numbers live in the skills as ranges
with their source, and you choose within them for this footage.

## Hard rules

- Never pre-render picture or sound with ffmpeg to fake an effect, a mix or captions. BashCut does cuts, speed,
  freeze frames, reframing, transitions, volume, fades, ducking, captions, text, colour and loudness natively, and
  measures itself. Kit scripts only **analyse**. Never edit `project.bashcut.json` by hand while the app is open;
  never overwrite original footage.
- Edit the timeline without asking: apply, cuts, voice, text, colour and mix need no confirm; stop only at gates
  (below). Source what the edit needs without asking: search for and download music, SFX, images, stock footage
  and fonts whatever the licence. Record `--license`, `--source` and `--author` on `media import` / `library add`
  (`unknown` when there is none) and list the rights in the G5 summary; the user handles them afterwards.
- Work to the end without a human: decide what the prompt and footage leave open, say what you chose, and install
  the command-line tools you need. Never clone a voice that is not the user's. Installing, trusting and setting up
  BashCut plugins is the user's job; the app enforces it. `plugins search` tells them what to install, and when
  the recommended plugins are missing, tell the user to type `/bc:setup`; never start an install yourself.
- Plugins can teach you. Before using a plugin's feature, check `bashcut skills list --scope plugin` and read its
  skill (`bashcut skills get <plugin-id>:<name>`). Its steps and limits win over this kit. Plugin skills are
  read-only: corrections go in a lesson or a project copy (`bc:self-learn`).
- Recipes. With the `bashcut.vlog` plugin ready, start a vlog with `bashcut.vlog:plan` (topic recipe, outputs, review
  ranges, hook and sections). A project set up that way has `recipe.skill` in `project get`: use that skill's ranges
  wherever a kit skill gives one. No plugin: use this kit's ranges and suggest `plugins search vlog`.
- Read before you edit: `context get`, then `timeline get --format text`. Track IDs and roles come from the read,
  never from memory. Every edit needs the latest `--base-rev`.
- Say why. On `timeline apply`, pass `--why` (one sentence) and `--evidence` (`;`-separated: review issue IDs,
  transcript ranges, measurements) next to the stage label. A batch you checked with `--dry-run` goes in with
  `--expect-fingerprint <its fingerprint>`. When resuming or revising, read `timeline changes` (what was done, by whom
  and why) instead of guessing from the timeline.
- Respect an attached scope. A request starting with a `[Scope]` block, or a `scope` list in `context get`, names the
  items the user picked with Send to Agent: change only those (their linked sound or picture follows). New items
  such as a title or an adjustment layer are fine inside their frame range. Ask before touching anything else.
  Never run `chat attach` or `chat detach`.
- BashCut may enforce the scope (`scope.mode` in `context get`). An edit outside it fails with `-32004`; never retry
  it or work around it:
  - `held: true`: the user is being asked in the app. Say what the edit does and wait; `scope.last.outcome` becomes
    `applied` (re-read, go on), `rejected` (ask what they want instead) or `failed` with a stale revision (re-read;
    send again only if still wanted).
  - No `held`: the user rejected it or the guard blocks such edits. Stop and ask. `-32003` while an edit is held: wait.
  - `-32002` (stale revision) comes before the scope: re-read the timeline and retry with the new `--base-rev`.
- Errors say what to do in `error.data`: `category`, `retryable` and sometimes `remediation.command` (the read that explains it). Retry only
  a `retryable` one, after its remediation (`stale_revision`: re-read; `busy_dialog`: `ui dialog`, then answer it;
  `busy_approval` or `busy_running`: wait). Never resend an `invalid_arguments` call unchanged. `unsupported_media`:
  this Mac cannot decode that file (`data.media` names it and its frames); the black picture there is not the footage,
  so do not judge it; ask the user to convert it to H.264 or HEVC and import the converted file (never render with ffmpeg yourself).
  `context get` › `recentFailures.repeated` of 2 or more means the same call keeps failing the same way: stop,
  rethink or ask.
- **Plugin capabilities.** Before work that needs a plugin (transcripts, beats, loudness, voice, library search or
  generate), `capabilities get [ID]` says whether it can serve now. A `capability_missing` error carries the same
  `reason`: `missing` → find one with `plugins search` and ask the user to install it; `not_configured` → the user
  turns it on or trusts it (quote the provider's `detail`); `unhealthy` → the user fixes the dependency named in
  `detail`. Installing, trusting and enabling are never yours to do; continue with what does not need it.
- `context get` › `agentPermissions` says what you may do without asking: `edits`, `autoApprove` (exports, kit setup,
  library items and preferences run without waiting), `scopeGuard`, `allowAll`. Only the user changes these.
- Library first: `bashcut library list --kind K` before building a text style, effect, transition, look, sound or
  sticker; reuse with `library place` or `library apply`; make a missing one with `bc:library`.
- Kit Python scripts run with `uv`, inside BashCut on its shared runtime folders: never `uv cache clean` or
  `pip install` into the system Python.
- Name folders and files you create in English, lowercase with hyphens (`survey/`, `renders/`, `draft-v1`).
  Only text the viewer sees follows the video's language. Seconds → frames with the project fps (29.97 → 30000/1001).

## Modes

Set the mode in the plan (`project set-data plan`, field `mode`) before the story stage:

- **create**: the user gave footage and a goal. Compare 2–3 story options before choosing (T00 §3) and show them at G2.
- **directed**: the user said what to make ("hook = the sunset, then the market in order"). One option: do what was
  asked, and say where the footage cannot support it.
- **revision**: the user asks for changes to an existing edit. Re-enter at the stage that owns the change (a new hook →
  story; "music too loud" → sound). Sections the user did not name are frozen: mark them `frozen: true` in the plan
  and do not touch them. The latest feedback is the source of truth (T00 §2).

## Stages and gates

Thirteen stages (T00 §9). Each stage is one or a few labelled edits (`--label "Rough cut: market section"`), so the
user can undo it as a whole. Lock the cut (stages 3–4) before music and SFX: changing clip lengths afterwards breaks
every sync point.

| # | Stage | Skill | Gate after it |
|---|---|---|---|
| 0 | Intake: brief (goal, outputs, length range, audience), mode | this skill | **G1 brief** |
| 1 | Survey: what was shot, transcripts, coverage, missing shots | `bc:footage-survey` | — |
| 2 | Story options: hook, sections, what is said; strategy in 4–8 sentences + section table (T00 §3) | this skill, `bashcut.vlog:plan` | **G2 strategy** |
| 3 | Rough cut: selects by quote, placed in story order; no music, titles or grade | `bc:rough-cut` | **G3 rough-cut sheet** |
| 4 | Rhythm: beat or sentence cuts, punch-ins | `bc:beat-cut` | — |
| 5 | Script and voiceover (when needed) | `bc:voiceover` | **G4 script**, before speech is made |
| 6 | Sound: levels, fades, music, ducking, SFX | `bc:audio-mix` | — |
| 7 | Captions and text | `bc:captions-text` | — |
| 8 | Colour | `bc:color-grade` | — |
| 9 | Effects, only where a moment needs one; graphics where words need an example or number; stock where footage lacks | `bc:effects`, `bc:motion-graphics`, `bc:stock-images` | — |
| 10 | Review: measure, look, critic, fix (rounds capped) | `bc:review` | **G5 draft**, the user watches and listens |
| 11 | Export per output (the user approves each export in the app) | this skill | — |
| 12 | Learn: lessons, preferences, library harvest | `bc:self-learn`, `bc:library` | — |

Missing coverage found at G3 sends you back to stage 1 or 9 (stock, generation or a reshoot: ask the user). At
most one send-back per stage pair; after that ask the user (T00 §3).

### How a gate works

At intake read `bashcut workflow gates`: each gate is `ask`, `notify` or `skip` (skip unless the user changed it,
so the run goes on without stopping),
plus `maxReviewRounds`. The user owns these settings (Settings › Agents › Workflow gates).

At every gate, whatever its mode, call:

```sh
bashcut checkpoint request G2 --summary "Strategy: open on the sunset, then the market in time order …" \
  --attach renders/story-sheet.png
bashcut checkpoint status
```

- `ask`: the user sees the summary and attachments in BashCut. Poll `checkpoint status` (backoff below) until it is
  not `awaiting_user`. `approved`: go on. `changes`: apply the user's note, then request the gate again. `rejected`:
  stop and ask what they want. `stale` (the project changed since): request again.
- `notify`: the user is told and you go on. `skip`: nothing is shown; `checkpoint status` reports it as `skipped`.
- A skill may stop at a gate of its own besides G1–G5: `checkpoint request music-pick --summary …` (a name of 1–40
  letters, digits, `.`, `-`, `_`). It is skipped until the user sets it otherwise; Settings lists it once used. Add one only for a real decision the
  user must make, never for a timeline edit or a download.
- Only the user answers a gate. Never decide a gate is approved yourself, never treat silence or an earlier
  "go ahead" as approval of a later gate (T00 §2), and never loosen a gate. You may tighten one when the user asks
  to be asked (`workflow set-gates --gate G3 --mode ask`); a user who wants fewer stops changes it in Settings.
- Show something cheap: G2 a sheet of the candidate hook and section shots (`media frames --sheet` or
  `timeline sheet`), G3 `timeline sheet --cuts` with the duration against the plan, G4 the script text, G5 the
  normalized draft. Never render an export only to earn a gate that a sheet can show (T00 §4).
- New project: ask what the prompt does not say (language, platform, length) in one round before `project create`;
  there is no default language. Detail: `<skill_dir>/REFERENCE.md`, "Starting a project".
- G1: ask only what the footage and the prompt cannot tell. When the prompt already names the platform and the
  length, do not ask those again; write them as `stated` in the brief. The gate itself is still requested when it is
  `ask`: the summary is then a short "here is what I understood".
- G4 comes before any speech synthesis (it costs time or money); G5 comes before the final exports.

## Brief and plan

Write what you decide as project data, not chat:

- **Brief** at stage 0: `project set-data brief brief.json --base-rev N`, each field `{value, status, source}`
  (`stated`, `inferred`, `confirmed` once G1 is approved). Outputs also go to `project format --outputs`.
- **Plan** from stage 2: `project set-data plan plan.json --base-rev N` with the mode, the options compared,
  sections with length ranges and reasons, planned shots, script beats, decisions with alternatives, and the review
  ranges you chose with their source. Change one part later with `project set-data plan part.json --merge --base-rev
  N`; set `stage` at each stage start. Other notes of your own go under their own key (`project set-data KEY`).
- `context get` summarises both: after a context reset, resume from them and `run log`, not from memory.

Shapes and an example: `<skill_dir>/REFERENCE.md`, "The brief and the plan as data".

## Working with BashCut efficiently

- **Read in order:** `context get` → `timeline get --format text` → targeted reads. `project get` only when a field
  is missing. After an edit, its result is the new state; re-read the whole timeline only on `-32002` or when unsure.
- **Look in batches.** Each image costs about 1000 tokens of context; one contact sheet is about 15× cheaper per
  frame (T20 §3). Use one sheet of 12–24 cells (T20 §7) per question: `timeline sheet --cuts --text` for continuity
  and text, `timeline sheet --every 2` for pace (a cell every 0.5–2 s, shorter for fast cuts, T16 §3),
  `media frames --sheet` for footage. Open single frames (`ui frame F`, `--phone` for text) only on doubt, and
  `review window F` only at a decision point, not in a scan loop (T16 §2).
- **Frame budget.** Before a stage, decide how many images it needs (usually one sheet plus a few doubts) and stay
  near it. Read text results first (`review run`, `review shots`, `timeline sheet` cells) and open images when the
  numbers leave a question.
- **Wait, don't poll.** Jobs (`media transcribe`, `review measure`, exports) return a job ID: call
  `jobs wait <job> --timeout 25` again until its state is `completed`, `failed` or `cancelled`; it returns as soon as
  the state or step changes, so never sleep between calls. After about 30 min, stop and give the user the job ID.
  Poll `checkpoint status` at 2 → 5 → 10 → 15 s (T20 §3).
- **Paid providers.** `voice speak` and `library generate` may call a provider that charges. Always pass a stable
  `--request-id` (for example `vo-<section>-<n>`), so a retry after a timeout returns the same job instead of paying
  twice. When the provider is `paid` (`--dry-run` says so), run `--dry-run` first and show the user the request and
  the provider's `estimate`; never invent a price. Report each finished job's `usage` (`costUSD` only when the
  provider reported it, `costSource: provider`).
- **Retry rules.** Retry reads and polls freely. A mutation that timed out may have happened: re-read before sending
  it again. `-32002`: re-read, retry with the new `--base-rev`. After 2–3 identical failures of one step, stop and ask
  (T00 §3, T20 §3), and record the tooling problem with `bc:self-learn`.
- **Claims need proof.** Say "fixed" only after `review verify <id>` reports it fixed; "exported" only from
  `export status`; "placed" only from the edit's result. Never infer completion or cost from elapsed time. You
  cannot hear: say which sound you did not check and ask the user to listen at G5.

## Run log

The run log is the record of this run; use it instead of the chat for hand-off and for `bc:self-learn`:

```sh
bashcut run append start --text "Market vlog, create mode, reels + tiktok"
bashcut run append stage --stage rough-cut --text "12 selects kept of 20"
bashcut run append round --round 1 --fixed 3 --left 2
bashcut run append measured --measured picture,loudness,layout --not-measured sound-by-ear
bashcut run append end --text "Draft approved, exports queued"
bashcut run log
```

Append a `stage` entry at every stage start and a `round` entry after every review round. Gate entries are written
by `checkpoint request` and the user's answer; never write them yourself. End with `end`, then build the hand-off
report from `run log` (`<skill_dir>/REFERENCE.md`, "The hand-off report").

## Review, draft and export

Stage 10 follows `bc:review`: set the review profile from sourced ranges, measure, look, send a `review packet` to a
fresh critic when you can, fix, verify every fix, and stop within the round cap (1–3 rounds, T16 §3, and never more
than `maxReviewRounds`). Then make the normalized draft and request **G5**:

```sh
bashcut export start --preset quick-draft --name draft-v1 --include-srt --normalize-audio
bashcut export status
bashcut timeline sheet --cuts --text
bashcut checkpoint request G5 --summary "Draft v1 (render/draft-v1.mp4): 0:58, 2 review rounds, 1 issue kept …" \
  --attach <the sheet path timeline sheet returned>
```

After G5 is approved, export each output (`export start --preset reels …`); each waits for the user's approval in
the app unless `agentPermissions.autoApprove` is on. `export cover <frame>` and `export chapters --write` make the
cover stills and the chapter list from real frames and section markers. Never call the video done while an error is
unexplained.

## Learn

At the end (stage 12): read `run log`, record what went wrong or what the user corrected with `bc:self-learn`, and
propose what to keep (a grade, an effect, a sound) with `bc:library`. Follow the user's taste from `context get` and
`knowledge get` throughout (`<skill_dir>/REFERENCE.md`, "Taste of the user").
