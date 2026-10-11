---
name: edit-workflow
description: Plan and run a whole edit in BashCut from raw footage to export — intake, recipe, survey, story, cut, sound, text, colour, effects, review, draft, export — through the user's gates, a checklist with evidence and independent audits, picking the one skill to read per stage. Use when the user asks to edit or cut a video, make a vlog, ad, review, short or montage from footage, revise an edit, or asks where to start; also tool demos from a screen recording plus a presenter. Triggers: "dựng video", "cắt video", "làm vlog", "làm video quảng cáo", "dựng giúp", "sửa lại video", "edit this", "bắt đầu từ đâu", "video giới thiệu tool", "talking head", "video nói chuyện".
---

# Editing a video in BashCut

Reply in the user's language. Two files hold the rest; read **one section** when a step names it, never a whole
file (`sed -n '/^## Starting/,/^## [A-Z]/p' <skill_dir>/REFERENCE.md`):

- `<skill_dir>/REFERENCE.md`: Starting a project, Intake questions, The brief and the plan as data, Story, Screen
  recording with a presenter, Taste of the user, Working efficiently, Run log, The hand-off report.
- `<skill_dir>/FULL.md`: Modes, Stages, checklist and gates, Gates, Audits, Review, draft and export, Learn.

A **recipe** (a plugin skill such as `bashcut.vlog:product-ad`) writes data into the plan (stages, checks, promise,
ranges); this skill runs the process. Editorial numbers are **ranges with their source**: choose within them for
this footage and say why in the plan (`"deliberate": true` with the reason to leave one).

## Hard rules

- **Tool rules are BashCut's** (MCP instructions, `bashcut help`): `--base-rev`, scope, error codes, library first,
  no ffmpeg pre-renders. This kit says what to do and why.
- Edit without asking; stop only at gates. Source what the edit needs (music, SFX, images, fonts) with `--license`,
  `--source`, `--author` (`unknown` when there is none). Never clone a voice that is not the user's. Plugins are
  the user's to install: missing ones → tell them `/bc:setup`.
- Read a plugin's skill before using its feature; plugin skills are read-only (corrections: `bc:self-learn`).
- **Every call is a turn that resends the whole context** (cost ≈ calls × context): one call for many things, the
  cut as one list (`plan.cut`), never clip by clip; read big things in sub-agents, not yourself.
- Say why: every `plan apply` and `timeline apply` carries `--why` (and `--evidence`).
- You never certify yourself: `done` needs evidence, "fixed" needs `review verify`, "exported" needs the job, a
  pass needs an audit by someone else (or marked `self`). You cannot hear: say which sound you did not check.
- Kit scripts run with `uv`. Name files in English, lowercase with hyphens (`draft-v1`).

## The quick path (default)

For every edit unless the user asked for the full process, the video runs over ~3 min, or `plan.mode` is `full`
(then FULL.md). Same gates and audits, but the cut is one list checked by BashCut. Target: a 45 s ad in about 25–30
calls.

1. **Intake, one call**: `context get` and `knowledge get` together; `ls`/`ffprobe` the files the prompt names
   (shape, length, speech, a screen recording or second camera next to them). Match a recipe: `skills list --scope
   plugin` (recipes start "Recipe for"); read only its working parts:
   `skills get <recipe> --section "Plan data,Ranges,Review notes"`; the result lists all its `sections`, so fetch
   any other you need the same way (an ad's brief, arc and truth rules).
   No recipe plugin: `plugins list`, tell the user `/bc:setup`, use kit defaults.
2. **Ask once** (at most 4 questions, REFERENCE "Intake questions"), each led by your own choice "AI chọn: …".
   User away or "don't ask": take your choices and write them `inferred` in the brief. Never ask again later.
3. **Project and survey, batched**: `project create` (REFERENCE "Starting a project"), `media import <folder>`,
   `media transcribe` and `media analyze` (every media), then `jobs wait ID1,ID2 --done --timeout 100` until both
   end. Hand the survey to a sub-agent: the `bc:surveyor` agent when your agent has it (Claude Code), else your own
   sub-agent given `<skill_dir>/../footage-survey/SURVEYOR.md` as its brief (Codex), else do it yourself by that
   brief. It describes the shots into the project and returns candidates in under 300 words. You read
   `media digest` (one short read of shots and words, `--from/--to` for a stretch), never a whole transcript, and
   you never open frames yourself before the build.
4. **Brief, plan and review limits in one call**: `project set-data brief`, `project set-data plan --merge` with
   `promise`, `sections` (length ranges), `recipe`, `checks` and **`cut`**: clips in order by quote (`{media, quote,
   section}`), `cover` for pictures over a line, `titles` by preset name (`hook-title`, `place-card`, a template ID
   such as `stacked-keyword`; `style` only to change a field: `size` is a share of the short side, `strokeWidth` is
   in points), `captions: {from: "speech"}` when words should show, one `music` bed with `duckDb`. Then
   `project set-data review` with the recipe's review ranges (`minTextSize`, `minTextContrast`, shot lengths,
   `hookSeconds`…): without them review stays incomplete. Request **G1** with the brief. No music in `library list --kind audio` and no music
   plugin: leave the bed out and list it as open; do not search the disk.
5. **Check, no edit**: `plan check` resolves every quote and builds a scratch copy: clips (edges inside words),
   titles (`textShare`, chars per second), problems and the review as it would be. Fix the list and check again
   until `ok` and every warning is one you mean. The **strategy audit** is yours here (`--by self`): judge the
   promise, sections, the `inferred` brief fields and the recipe checks from the check's result, then
   `run append audit --point strategy --verdict pass --findings N --by self` in the same call as G2
   (`checkpoint request G2 --summary "…"`) and the apply.
6. **Build once**: `plan apply --base-rev N --sheet --why "…"` builds it as one undoable edit and returns the
   review's errors and warnings plus the storyboard sheet: look at that one sheet for G3. A change is a change to
   `plan.cut` and another apply (it replaces only what an apply built).
7. **Finish only what the plan cannot say**: voiceover, colour, effects, a mix `audio mix-measure` finds off; the
   stage skill for anything beyond one command.
8. **Review**: `review measure` (`jobs wait --done`; it measures picture and text contrast), `review run --summary`,
   fix in `plan.cut` and apply again, `review verify` each fix. Then the **draft audit**: `review packet --point
   draft`, and the `bc:critic` agent (or your sub-agent given `<skill_dir>/../review/CRITIC.md`, else `--by self`)
   judges the packet. Fix its findings; send it back for a second look only for a blocker that no measurement
   proves (`review verify` proves the rest). Record each verdict with `run append audit --point draft`.
9. **Draft and hand-off**: `export start --preset quick-draft --name draft-v1 --include-srt --normalize-audio`
   returns the job: `jobs wait JOB --done --timeout 100`, then **G5** and the hand-off report (REFERENCE "The
   hand-off report"). Record stage outcomes in one call where they happen (below).

## The plan as data

Brief and plan are project data (`project set-data brief|plan`, `--merge` for one part); `context get` summarises
both, so after a reset resume from them and `run log`, not from memory. Shapes: REFERENCE "The brief and the plan
as data". A recipe writes `recipe {skill, version}`, `promise {hook, payoff}`, `stages` (deviations only), `checks`
(at most 8) and `askAtIntake`; you write `mode`, `stage`, `options`, `sections`, `shots`, `beats`, `visuals`,
`decisions`, `ranges` and `cut`.

## Checklist, gates and audits in short

Stage ids: `intake`, `survey`, `story`, `rough-cut`, `rhythm`, `voiceover`, `visuals`, `sound`, `captions`,
`colour`, `effects`, `review`, `export`, `learn` (table and skills: FULL "Stages, checklist and gates"). Record
outcomes several at a time: `run append stage --stage survey --status done --evidence "a;b"`, `--status skipped
--reason "…"`. Gates: `workflow gates` at intake; each is `ask`, `notify` or `skip`; request every one with
something cheap to look at (`checkpoint request G2 --summary "…" --attach sheet.png`, then `checkpoint status --wait
100` while `awaiting_user`). Only the user answers a gate. A skipped G2 needs the strategy audit and a skipped G5
the draft audit; BashCut refuses the rough cut without the recipe read and the strategy audit, and a final export
without a passing draft audit: run what the error names. Details: FULL "Gates" and "Audits". `review run` status
`incomplete` is never a pass.
