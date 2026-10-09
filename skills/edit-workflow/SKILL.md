---
name: edit-workflow
description: Plan and run a whole edit in BashCut from raw footage to export — intake, recipe, survey, story options, rough cut, rhythm, script and voiceover, sound, text, colour, effects, review, draft, export, learning — through the user's workflow gates, a checklist with evidence and independent audits, and pick the one skill to read for each stage. Use when the user asks to edit/cut a video, make a vlog, an ad, a review, short or montage from a folder of footage, revise an edit, or asks "where do I start". Also tool demos and tutorials from a screen recording plus a presenter camera. Triggers: "dựng video", "cắt video", "làm vlog", "làm video quảng cáo", "dựng giúp", "sửa lại video", "edit this", "bắt đầu từ đâu", "video giới thiệu tool", "video desktop làm nền", "người đọc ở trên video", "talking head", "talk head", "video nói chuyện".
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
- Load just in time: one recipe at intake, then a stage skill only when the stage does more than the commands
  named here. Rules that must outlive the context live in the plan.
- **Every call is a turn** that resends the whole conversation (cost ≈ turns × context): batch ("Working
  efficiently") and build the cut from one list (`plan.cut`), never clip by clip.
- Say why: every `timeline apply` and `plan apply` carries `--why` (and `--evidence`); resuming, read `timeline changes`.
- You never certify yourself. A stage is `done` only with evidence; "fixed" only from `review verify`; "exported"
  only from `export status`; a pass only from an audit by someone who did not make the edit (or marked `self`).
  You cannot hear: say which sound you did not check.
- Kit scripts run with `uv`, never `pip install`. Name new files in English, lowercase with hyphens (`draft-v1`).

## Stage 0: intake and the recipe

Intake always runs these steps, in order, before any edit, even when the request looks simple:

1. `context get` and `knowledge get` (taste, facts, lessons; `<skill_dir>/REFERENCE.md`, "Taste of the user").
2. **Look at what was given.** The files or folder the prompt names: shape, length, speech, and what else sits next
   to them (a screen recording of the same session, a second camera). Read only; nothing is imported yet.
3. **Match a recipe.** `skills list --scope plugin`: the recipes are the plugin skills whose description starts
   with "Recipe for". Match the request and step 2 against each description; keep the best match and a close
   second. Read the best match now with `skills get` (its Plan data and `askAtIntake` shape the questions). The
   user named a recipe or a slash command: take it. No recipe listed: `plugins list` says whether the recipe
   plugin is installed but untrusted or off; tell the user (`/bc:setup`) and never read its files from disk.
   Nothing installed: kit defaults, and `plugins search` names the missing recipe for the hand-off report.
4. **Draft the steps.** The stage table below, minus what the recipe marks `required: false`, plus what it adds.
   When words carry the video (talking head, tutorial, explainer, review, podcast clip, voiceover), add
   `visuals` after `voiceover` yourself if the recipe did not.
5. **Ask once, suggesting.** One round of at most 4 questions (`<skill_dir>/REFERENCE.md`, "Intake questions"):
   the recipe, the steps, then what the prompt does not say (length, platform, language, the recipe's
   `askAtIntake` fields). Every question's first option is your own choice, "AI chọn: <the concrete choice>",
   marked recommended. No answer, the user is away or said "don't ask": take those choices, write each as
   `inferred` in the brief, and the strategy audit checks them. Never ask again later; never guess a name, a
   handle or a claim silently.
6. Create or open the project (`<skill_dir>/REFERENCE.md`, "Starting a project"), write the **brief**, then the
   plan: the recipe's plan data (below; a recipe that runs after a plugin planner such as `bashcut.vlog:plan`:
   read the planner, telling it which recipe was chosen) and the steps as answered in `stages`. `run checklist`
   must list the same steps. Request **G1**.

From here the steps drive the work: at each stage start read the skill `workflow.next` names through the Skill
tool or `skills get`, never from disk, even when you think you know it.

## The quick path (default)

Use it for every edit unless the user asked for the full process, the video runs over ~3 min, or the recipe sets
`plan.mode: "full"`. It runs the same stages and gates, but the cut is **one list** checked by BashCut, not
hundreds of single edits. A 45 s ad should take about 25–30 turns.

1. **Intake** as above (one round of questions).
2. **Survey in batches**: `project create`, `media import <folder>` (the whole folder in one call),
   `media transcribe` (every media with sound), `jobs wait ID1,ID2 --timeout 30`, `media inventory`, then one or two
   `media frames --sheet` (`bc:footage-survey` only when the footage is long or mixed).
3. **Story as data**: the brief, then the plan with `promise`, `sections` (with length ranges) and **`cut`**: clips in
   order by quote (`{media, quote, section}`), `cover` for pictures over a line (B-roll), `titles` anchored to a
   clip, one `music` bed (the shape is in `plan check`'s own description). Write it with `project set-data plan --merge`.
4. **Check, no edit**: `plan check` resolves every quote, places everything on a scratch copy and returns the clips
   (edges inside words, described size, orientation), titles (chars per second), problems and the review of the
   edit as it would be. Fix the list and check again until `ok` is true and the warnings are ones you mean.
   Then the strategy audit from the packet (`review packet --point strategy`, `--by self` here) and **G2** with the
   promise and the section table from the check.
5. **Build once**: `plan apply --base-rev N --why "…"` (one undoable edit), then `timeline sheet --cuts --text`
   as the storyboard for **G3**. A change ("hook ngắn lại", "đổi cảnh 3") is a change to `plan.cut` and another
   `plan apply`: it replaces only what an apply built.
6. **Finish only what the plan needs**: voiceover, captions (`captions generate`), sound (`audio mix-measure`,
   ducking), colour, effects. Read the stage skill for a stage you run beyond one command.
7. **Review**: `review run --summary`, fix, `review verify`; a self draft audit from the packet; the normalized
   draft and **G5**; export.

The full path adds a fresh critic sub-agent at each audit (`bc:review`) and every stage skill.

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

Your own fields: `mode`, `stage`, `options`, `sections`, `shots`, `beats`, `visuals`, `decisions`, `ranges`,
`cut` (the edit list `plan check` and `plan apply` read).
`stages` may also add a stage of its own (`{"skill": "…", "after": "<stage id>"}`): BashCut lists it right after
that stage, so new work goes where it belongs (`visuals` after the cut is locked).

## Modes

- **create**: footage and a goal. Compare 2–3 story options before choosing; show them at G2.
- **directed**: the user said what to make. One option; say where the footage cannot support it.
- **revision**: changes to an existing edit, **in place** on the same project. Built by `plan apply`: change
  `plan.cut` and apply again. Otherwise re-enter at the stage that owns the change, label each edit
  (`--label "v2: shorter hook"`), mark untouched sections `frozen: true`, export `draft-v2` next to `draft-v1`.
  `variants create` only for a real A/B test that changes one thing. The latest feedback wins.

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

When you start or resume: `context get` › `workflow.next` gives `{stage, skill, skillRead}`; read that skill when
the stage needs it (Skill tool for `bc:*`, `skills get` for plugin skills). Reads are recorded by BashCut and the
kit's hook; an agent without hooks (Codex, chat agents) records its own with `run append skill --name <skill>`.
At every stage end, record the outcome (several in one shell command when they are ready together):

```sh
bashcut run append stage --stage survey --status done --evidence "survey/contact-sheet.png;media transcribe job 41"
bashcut run append stage --stage colour --status skipped --reason "screen recording, no grade wanted"
bashcut run checklist
```

`done` without `--evidence` counts as unverified; `skipped` needs `--reason`; a stage the plan marks
`required: false` is `n/a` already. `run checklist` (and `context get` › `workflow.checklist`) derives the list from
the plan and the run log; its `open` list is what still needs attention and starts the hand-off report.

Missing coverage at G3 sends you back to survey or effects (stock, generation, a reshoot: ask), once per pair.

### Gates

Read `workflow gates` at intake: each gate is `ask`, `notify` or `skip` (skip unless the user changed it), plus
`maxReviewRounds`. At every gate, whatever its mode, request it with something cheap to look at:

```sh
bashcut checkpoint request G2 --summary "Strategy: one message — …; hook → payoff …" --attach renders/story-sheet.png
bashcut checkpoint status --wait 30
```

- `ask`: repeat `checkpoint status --wait 30` while `awaiting_user` (it returns when the user answers). `approved`:
  go on; `changes`: apply the note, request again; `rejected`: stop and ask; `stale`: request again.
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
audit still runs and its verdict goes in the gate summary. The quick path audits itself from the packet only
(`--by self`: it counts, reported as self-audited); the full path gives each audit to a fresh critic. BashCut
refuses a non-draft `export start` without a passing draft audit (`audit_missing`, remediation `review packet --point draft`), and the rough cut without the
recipe read (`recipe_unread`) or the strategy audit: run what the error names, never work around it.

## Working efficiently

Measured on real runs: one ad took 778 BashCut calls (159 `context get`, 119 `media import`, 110 `jobs wait`, 37
`export status`, 36 `ui frame`); a vlog spent 12M tokens before its first cut. Every one of those calls was a turn.

- **One call for many things.** `media import <folder>`; `media transcribe` without `--media` (every media);
  `jobs wait ID1,ID2,…`; the cut as `plan.cut` + `plan apply`; several `timeline apply` ops in one call. In a shell,
  chain commands whose output you do not need to read (`run append … && run append …`); with MCP tools, send
  independent calls together in one turn.
- **Look in batches.** One image costs about 1000 tokens; one contact sheet of 12–24 cells is ~15× cheaper per frame
  (T20 §3, §7): `timeline sheet --cuts --text` for continuity and text, `timeline sheet --every 2` for pace,
  `media frames --sheet` for footage, `timeline sheet --at F1,F2,…` for a few frames. Single frames
  (`ui frame F --phone`) only on doubt; `review window F` only at a decision point (T16 §2). Read text results
  before images.
- **Wait, don't poll.** Jobs: `jobs wait <job> --timeout 30` until `completed`, `failed` or `cancelled`; an export
  is a job too (never loop on `export status`). Gates: `checkpoint status --wait 30`. After about 30 min, give the
  user the job ID.
- **Read once.** `context get` when you start or resume and after a gate, not before every command; `timeline get`
  only before hand-written ops (`plan check` and `review run` already say what you need).
- **Paid providers** (`voice speak`, `library generate`): a stable `--request-id`; `--dry-run` first when the
  provider is `paid`, show its `estimate`, never invent a price; report each job's `usage`.
- After 2–3 identical failures of one step, stop and rethink or ask, and record it with `bc:self-learn`.

**Run log**: `run append start|round|measured|end` frame the run; the hand-off report comes from `run checklist`
and `run log` (`<skill_dir>/REFERENCE.md`, "Run log", "The hand-off report").

## Review, draft and export

Stage 10 follows `bc:review` (profile, measure, look, fix, verify, rounds capped by `maxReviewRounds`), then the
draft audit, then the normalized draft and **G5**:

```sh
bashcut export start --preset quick-draft --name draft-v1 --include-srt --normalize-audio   # then jobs wait JOB
bashcut checkpoint request G5 --summary "Draft v1: 0:58, 2 review rounds, draft audit pass, 1 issue kept …" \
  --attach renders/draft-sheet.png
```

`review run` status `incomplete` is never a pass. After G5, export each output (`export start --preset reels …`);
`export cover <frame>` and `export chapters --write` make covers and chapters from real frames. Never call the video
done while an error is unexplained.

## Learn

Stage 12: run the process audit (`review packet --point process`), then `bc:self-learn` turns its findings and the
user's corrections into lessons, and `bc:library` proposes what to keep (a grade, an effect, a sound).
