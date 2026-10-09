---
name: edit-workflow
description: Plan and run a whole edit in BashCut from raw footage to export — intake, recipe, survey, story options, rough cut, rhythm, script and voiceover, sound, text, colour, effects, review, draft, export, learning — through the user's workflow gates, a checklist with evidence and independent audits, and pick the one skill to read for each stage. Use when the user asks to edit/cut a video, make a vlog, an ad, a review, short or montage from a folder of footage, revise an edit, or asks "where do I start". Also tool demos and tutorials from a screen recording plus a presenter camera. Triggers: "dựng video", "cắt video", "làm vlog", "làm video quảng cáo", "dựng giúp", "sửa lại video", "edit this", "bắt đầu từ đâu", "video giới thiệu tool", "video desktop làm nền", "người đọc ở trên video".
---

# Editing a video in BashCut

Reply in the user's language. Detail (project setup, the brief and plan JSON, story, screen recordings, the
hand-off report) is in `<skill_dir>/REFERENCE.md`.

This skill is the one engine for every edit. A **recipe** (a plugin skill such as `bashcut.vlog:product-ad`) never
re-runs the process: it writes data into the plan (stages, checks, promise, intake questions) that this skill, the
checklist and the critic read. With no recipe, the kit's defaults and generic checks apply.

Editorial numbers are **ranges with their source**, never fixed values: choose within them for this footage and say
why in the plan. Leave a range when the footage or the idea earns it (`"deliberate": true` with the reason); review
keeps that as info. Two edits of the same kind should not come out the same.

## Hard rules

- **Tool rules are BashCut's.** How to call it (read before an edit, `--base-rev`, scope and held edits, error codes
  and `error.data`, `capability_missing`, `agentPermissions`, library first, no ffmpeg pre-renders) comes with
  BashCut's own agent instructions over MCP and `bashcut help`: follow them. This kit says **what to do and why**.
- Edit the timeline without asking: apply, cuts, voice, text, colour and mix need no confirm; stop only at gates.
  Source what the edit needs without asking (music, SFX, images, stock, fonts) and record `--license`, `--source`
  and `--author` (`unknown` when there is none); list the rights in the G5 summary.
- Ask once, then work to the end (Intake below). Never clone a voice that is not the user's. Installing, trusting
  and setting up plugins is the user's job: `plugins search` names what to install; when the recommended plugins
  are missing, tell the user to type `/bc:setup`.
- Plugins teach you: read a plugin's skill (`skills get <plugin-id>:<name>`) before using its feature; its steps
  and limits win over this kit. Plugin skills are read-only: corrections go in a lesson (`bc:self-learn`).
- Load just in time: one recipe at intake, then **one stage skill per stage**, the one `context get` ›
  `workflow.next` names. Never load every skill up front; rules that must outlive the context live in the plan.
- Say why: every `timeline apply` carries a stage label, `--why` and `--evidence`. Resuming or revising, read
  `timeline changes` instead of guessing from the timeline.
- You never certify yourself. A stage is `done` only with evidence; "fixed" only from `review verify`; "exported"
  only from `export status`; a pass only from an audit by someone who did not make the edit (or marked `self`).
  You cannot hear: say which sound you did not check.
- Kit Python scripts run with `uv`; never `pip install` into the system Python. Name files and folders you create
  in English, lowercase with hyphens (`survey/`, `draft-v1`). Seconds → frames with the project fps.

## Stage 0: intake and the recipe

1. `context get` and `knowledge get` (taste, facts, lessons; `<skill_dir>/REFERENCE.md`, "Taste of the user").
2. **Route.** The user named a recipe (or a slash command): read it. Otherwise pick one here and read it with
   `skills get` (`skills list --scope plugin` shows what is installed):

   | Request | With the plugin | Without |
   |---|---|---|
   | ad, TVC, "quảng cáo", "video bán hàng", a channel teaser | `bashcut.vlog:product-ad` | kit defaults |
   | vlog, trip, food, a day, product review, talking head, tutorial, podcast clips | `bashcut.vlog:plan` (picks the recipe) | kit defaults |

   No fitting plugin: go on with kit defaults and name the missing recipe in the hand-off report (`plugins search`).
3. **Ask once.** Before `project create`, one round of at most 4 questions about what the prompt does not say:
   language, platform, length, and the recipe's `askAtIntake` fields (AskUserQuestion in Claude Code, plain
   questions elsewhere). No answer, the user is away or said "don't ask": decide, write the field as `inferred` in
   the brief, and the strategy audit checks the guess. Never ask again later; never guess a name, a handle or a
   claim silently.
4. Create or open the project (`<skill_dir>/REFERENCE.md`, "Starting a project"), write the **brief**, and let the
   recipe write its plan data (below). Request **G1**.

## The plan as data

Brief and plan are project data (`project set-data brief|plan`, `--merge` for one part); `context get` summarises
both, so after a context reset resume from them and `run log`, not from memory. Shapes:
`<skill_dir>/REFERENCE.md`, "The brief and the plan as data". Fields a recipe writes, all optional:

| Field | Holds |
|---|---|
| `recipe` | `{skill, version}`: the recipe in charge; its ranges win over a kit skill's |
| `promise` | `{hook, payoff}`: the question the opening raises and the line that closes it; every video has one |
| `stages` | per stage id, only deviations: `{required, why}`, `{skill}`, `{rules: [...]}` |
| `checks` | at most 8 recipe checks `{id, text, source}`; the kit's generic checks are always added |
| `askAtIntake` | brief fields the recipe will not guess |

Your own fields: `mode`, `stage`, `options`, `sections`, `shots`, `beats`, `visuals`, `decisions`, `ranges`.
`stages` may also add a stage of its own (`{"skill": "…", "after": "<stage id>"}`): BashCut lists it right after
that stage, so new work goes where it belongs (`visuals` after the cut is locked).

## Modes

- **create**: footage and a goal. Compare 2–3 story options before choosing; show them at G2.
- **directed**: the user said what to make. One option; say where the footage cannot support it.
- **revision**: changes to an existing edit. Work **in place** on the same project: re-enter at the stage that owns
  the change, label each edit (`--label "v2: shorter hook"`), mark untouched sections `frozen: true`, and export
  `draft-v2` next to `draft-v1`; undo history and `timeline changes` keep v1. Use `variants create` only for a real
  A/B test that changes one thing (two hooks), never to keep an old version. The latest feedback wins.

## Stages, checklist and gates

Each stage is one or a few labelled edits, so the user can undo it as a whole. Lock the cut (rough-cut, rhythm)
before music and SFX: changing clip lengths later breaks every sync point.

| # | Stage id | Default skill | Gate or audit after it |
|---|---|---|---|
| 0 | `intake` | this skill, the recipe | **G1 brief** |
| 1 | `survey` | `bc:footage-survey` | — |
| 2 | `story`: options, promise, sections (strategy in 4–8 sentences + section table) | this skill (REFERENCE "Story"), the recipe | **strategy audit**, **G2** |
| 3 | `rough-cut`: selects by quote, no music, titles or grade | `bc:rough-cut` | **G3 rough-cut sheet** |
| 4 | `rhythm` | `bc:beat-cut` | — |
| 5 | `voiceover` (when needed) | `bc:voiceover` | **G4 script**, before speech is made |
| 5b | `visuals` (added by the plan when words carry the video, `after: "voiceover"`) | `bc:visual-plan` | — |
| 6 | `sound` | `bc:audio-mix` | — |
| 7 | `captions` and text | `bc:captions-text` | — |
| 8 | `colour` | `bc:color-grade` | — |
| 9 | `effects`, graphics, stock (the rows of `plan.visuals`, else only where a moment needs one) | `bc:effects`, `bc:motion-graphics`, `bc:stock-images` | — |
| 10 | `review` | `bc:review` | **draft audit**, **G5 draft** |
| 11 | `export` per output | this skill | — |
| 12 | `learn` | `bc:self-learn`, `bc:library` | **process audit** first |

At every stage start: `context get` › `workflow.next` gives `{stage, skill, skillRead}`; read that one skill (Skill
tool for `bc:*`, `skills get` for plugin skills) and set `stage` in the plan. Reads are recorded by BashCut and the
kit's hook; an agent without hooks (Codex, chat agents) records its own with `run append skill --name <skill>`.
At every stage end, record the outcome:

```sh
bashcut run append stage --stage survey --status done --evidence "survey/contact-sheet.png;media transcribe job 41"
bashcut run append stage --stage colour --status skipped --reason "screen recording, no grade wanted"
bashcut run checklist
```

`done` without `--evidence` counts as unverified; `skipped` needs `--reason`; a stage the plan marks
`required: false` is `n/a` already. `run checklist` (and `context get` › `workflow.checklist`) derives the list from
the plan and the run log; its `open` list is what still needs attention and starts the hand-off report. If this
BashCut has no `run checklist`, keep the same list yourself in `project set-data checklist` for the process audit.

Missing coverage found at G3 sends you back to survey or effects (stock, generation or a reshoot: ask). At most one
send-back per stage pair; then ask the user.

### Gates

Read `workflow gates` at intake: each gate is `ask`, `notify` or `skip` (skip unless the user changed it), plus
`maxReviewRounds`. At every gate, whatever its mode, request it with something cheap to look at:

```sh
bashcut checkpoint request G2 --summary "Strategy: one message — …; hook → payoff …" --attach renders/story-sheet.png
bashcut checkpoint status
```

- `ask`: poll `checkpoint status` at 2 → 5 → 10 → 15 s until it is not `awaiting_user`. `approved`: go on;
  `changes`: apply the note, request again; `rejected`: stop and ask; `stale`: request again.
- `notify`: the user is told and you go on. `skip`: nothing is shown.
- Only the user answers a gate: never treat silence or an earlier "go ahead" as approval, never loosen a gate. A
  skill may add its own (`checkpoint request music-pick …`) only for a real decision the user must make.
- Show: G2 a sheet of the hook and section shots, G3 `timeline sheet --cuts` with the duration against the plan, G4
  the script, G5 the normalized draft. Never render an export only to earn a gate a sheet can show.

### Audits: a skipped gate is replaced by its audit

A fresh agent that did not make the edit checks it from a packet only (`bc:review`, "If you were given a packet"):

| Point | When | Checks |
|---|---|---|
| `strategy` | after story, before the rough cut | one message; `promise.payoff` answers `promise.hook`; fits the brief; the `inferred` brief fields; recipe checks that apply to a plan |
| `draft` | review stage, before G5 | the generic checks + `plan.checks`, as a viewer |
| `process` | learn stage | the checklist, run log and timeline changes: skipped required stages, `done` without evidence, claims not backed by the log |

```sh
bashcut review packet --point strategy        # the folder for the auditor
bashcut run append audit --point strategy --verdict changes --findings 2 --by critic
```

G2 `skip` → the strategy audit is required; G5 `skip` → the draft audit is required. With `ask` or `notify` the
audit still runs and its verdict goes in the gate summary. No sub-agent: audit yourself from the packet only, record
`--by self`; it counts, but is reported as self-audited. BashCut refuses a non-draft `export start` without a
passing draft audit (`audit_missing`, remediation `review packet --point draft`), and the rough cut without the
recipe read (`recipe_unread`) or the strategy audit: run what the error names, never work around it.

## Working efficiently

- **Look in batches.** One image costs about 1000 tokens; one contact sheet of 12–24 cells is ~15× cheaper per frame
  (T20 §3, §7): `timeline sheet --cuts --text` for continuity and text, `timeline sheet --every 2` for pace,
  `media frames --sheet` for footage. Single frames (`ui frame F --phone`) only on doubt; `review window F` only at
  a decision point (T16 §2). Decide each stage's frame budget first; read text results before images.
- **Wait, don't poll.** Jobs return an ID: `jobs wait <job> --timeout 25` until `completed`, `failed` or
  `cancelled`. After about 30 min, give the user the job ID.
- **Paid providers** (`voice speak`, `library generate`): a stable `--request-id`; `--dry-run` first when the
  provider is `paid`, show its `estimate`, never invent a price; report each job's `usage`.
- After 2–3 identical failures of one step, stop and rethink or ask, and record it with `bc:self-learn`.

## Run log

```sh
bashcut run append start --text "Market vlog, create mode, reels + tiktok"
bashcut run append round --round 1 --fixed 3 --left 2
bashcut run append measured --measured picture,loudness,layout --not-measured sound-by-ear
bashcut run append end --text "Draft approved, exports queued"
```

Stage entries come from the checklist commands above; gate entries from `checkpoint request` and the user's answer,
never from you. End with `end`, then build the hand-off report from `run checklist` › `open` and `run log`
(`<skill_dir>/REFERENCE.md`, "The hand-off report").

## Review, draft and export

Stage 10 follows `bc:review` (profile, measure, look, fix, verify, rounds capped by `maxReviewRounds`), then the
draft audit, then the normalized draft and **G5**:

```sh
bashcut export start --preset quick-draft --name draft-v1 --include-srt --normalize-audio
bashcut export status
bashcut checkpoint request G5 --summary "Draft v1: 0:58, 2 review rounds, draft audit pass, 1 issue kept …" \
  --attach renders/draft-sheet.png
```

`review run` status `incomplete` is never a pass. After G5, export each output (`export start --preset reels …`);
`export cover <frame>` and `export chapters --write` make covers and chapters from real frames. Never call the video
done while an error is unexplained.

## Learn

Stage 12: run the process audit (`review packet --point process`), then `bc:self-learn` turns its findings and the
user's corrections into lessons, and `bc:library` proposes what to keep (a grade, an effect, a sound).
