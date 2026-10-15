---
name: edit-workflow
description: The engine for every BashCut edit, raw footage to export: intake, recipe, survey, the cut as one plan, sound, text, review, draft, through the user's gates with evidence and audits; names the skill per stage. Triggers: "dựng video", "cắt video", "làm vlog", "dựng giúp", "sửa lại video", "edit this", "bắt đầu từ đâu", "video quảng cáo".
---

# Editing a video in BashCut

Read **one section** when a step names it, never a whole file
(`sed -n '/^## Starting/,/^## [A-Z]/p' <skill_dir>/REFERENCE.md`):

- `<skill_dir>/REFERENCE.md`: Starting a project, Intake questions, The brief and the plan as data, Story, Screen
  recording with a presenter, Taste of the user, Working efficiently, Run log, The hand-off report.
- `<skill_dir>/FULL.md`: Modes, Stages, checklist and gates, Gates, Audits, Review, draft and export, Learn.

A **recipe** (plugin skill, e.g. `bashcut.vlog:product-ad`) writes data into the plan; this skill runs the process.
Editorial numbers are **ranges with their source**: choose within them for this footage, say why in the plan
(`"deliberate": true` with the reason to leave one).

## Hard rules

- **Tool rules are BashCut's** (its instructions, `bashcut help`): `--base-rev`, [Scope], errors, library first,
  downloads, no ffmpeg. Stop only at gates.
- Downloads need no source or licence records (`--source URL` only when you have it anyway). Install a plugin the
  edit needs (`plugins search --capability`, `plugins install`). Plugin skills are read-only (fixes:
  `bc:self-learn`).
- **Every call resends the whole context** (cost ≈ calls × context): the cut as one list (`plan.cut`), never clip
  by clip; sub-agents do big reads. After your own commands pass `--base-rev last`; `context get` again only
  when a stale error says someone else changed the project. Every `plan apply`/`timeline apply` carries `--why`
  (and `--evidence`).
- You never certify yourself: `done` needs evidence, "fixed" needs `review verify`, "exported" needs the job, a
  pass needs an audit by someone else (or marked `self`). You cannot hear: say which sound you did not check.
- Kit scripts run with `uv`. Files named in English, lowercase, hyphens (`draft-v1`).

## The quick path (default)

Unless the user asked for the full process, the video runs over ~3 min, or `plan.mode` is `full` (then FULL.md).
Same gates and audits. Target: a 45 s ad in about 20 calls.

1. **Intake, one call**: `context get`, `knowledge get`, `workflow gates`, the recipe (`skills get
   <recipe> --section "Plan data,Ranges,Review notes"` plus any you need; recipes are plugin skills `vlog-<kind>`),
   the review limit table (`sed -n '/^## Before round 1/,/^## The loop/p' <skill_dir>/../review/SKILL.md`). No
   recipe plugin: tell the user `/bc:setup`, use kit defaults.
2. **Ask once** (≤4 questions, REFERENCE "Intake questions"), each led by "AI chọn: …". User away: write your
   choices `inferred`, never ask later.
3. **Project and survey, two calls**: `project create --name N --dir D --footage FILE_OR_FOLDER --canvas
   landscape|portrait|square --fps 30 --language <tag> --import` (`--save-current` on "unsaved changes" of a
   project not yours). Then at once the survey sub-agent (media and job IDs; it waits): `bc:surveyor`,
   else one briefed with `<skill_dir>/../footage-survey/SURVEYOR.md`, else that brief yourself. **Never
   print a transcript or digest, never open source frames**; its quotes resolve as they are (around them: `media
   transcript --media M --ranges 640:652,1050:1058 --as text --format text`).
4. **Brief, plan, sound, limits in one call**: music and SFX downloaded (below) and imported first, then
   `project format --outputs <preset> --base-rev last`, `project set-data brief brief.json --base-rev last` (fields
   `{value, status: stated|inferred|confirmed, source}`) and `project set-data plan plan.json --merge --base-rev
   last` with `promise`, `sections`, `recipe`, `checks`, `decisions`, `ranges` and **`cut`**:

   ```json
   {"cut": {"clips": [{"id": "c1", "media": "M", "quote": "exact words as transcribed", "section": "hook"},
                      {"id": "c2", "media": "M", "from": 642.8, "to": 648.0, "section": "proof", "zoom": 1.2,
                       "cover": [{"media": "M", "from": 950.0}]}],
            "titles": [{"id": "t1", "text": "HOOK LINE", "clip": "c1", "preset": "hook-title"},
                       {"id": "t2", "text": "Place", "section": "proof", "offset": 0.5, "seconds": 2.5,
                        "preset": "place-card", "style": {"positionY": 0.8}}],
            "captions": {"from": "speech", "style": {"background": {"color": "#000000", "opacity": 0.6}},
                         "replace": {"misheard": "right"}},
            "music": {"media": "S", "duckDb": -14}, "sfx": [{"media": "W", "on": "t1", "offset": -0.1}],
            "review": {"minTextSize": 0.035, "minTextContrast": 3, "minShotSeconds": 0.6}}}
   ```

   White text over daylight measured 1.2–2:1: plate captions and titles now; two texts at once need different
   `positionY`. **Sound**: a `music` bed unless the brief says none; `sfx` only where a moment needs one (`offset`
   -0.1 peaks on it; `bc:audio-mix` "SFX"). Not in the library: `uv run <skill_dir>/../audio-mix/fetch_audio.py
   --dest <project>/media/audio --music "<mood words>" --sfx whoosh,pop --import`. **Review limits** (`review`) come
   from the recipe's `Ranges` and the review table; set all `plan check` lists in `review-profile-unset`, else
   review stays incomplete; one no source covers: choose it, say so in `ranges`. Request **G1** with the brief.
5. **Check**: `plan check` resolves quotes on a scratch copy. Fix with `plan check --patch '{"clips": {"c2":
   {"to": 953.0}}}'` (merges by entry ID; never rewrite plan files with scripts) until `ok`: `cut-in-word` gives
   `facts.before/after` to move the edge to; `same-framing` is a jump cut to come (give the second clip a `zoom`
   1.15–1.3, `bc:beat-cut` §5, never over text, or a `cover`). The **strategy audit** is yours (`--by self`):
   promise, sections, `inferred` brief fields, recipe checks.
6. **Build in the call that records it**: `run append audit --point strategy --verdict pass --findings N --by self
   --evidence "…"`, G2 unless skipped (`checkpoint request G2 --summary "…"`), `plan apply --base-rev last --sheet
   --why "…"` (`--patch` holds the check's fixes: a check saves nothing). Its storyboard sheet is for G3. Every
   later change is `plan apply --patch …`.
7. **Voice and graphics go to sub-agents** (recipe steps too), lines and rows in the plan: `bc:voice`, then
   `bc:graphics` (else sub-agents briefed with `<skill_dir>/../voiceover/VOICE.md` and
   `<skill_dir>/../motion-graphics/GRAPHICS.md`, else yourself). Give each the kit folder (`<skill_dir>/..`),
   project, IDs, facts, look, limits; never read their skills, results or renders. Then only what the plan
   cannot say: colour, effects, a mix `audio mix-measure` finds off.
8. **Review**: `review run --measure --summary`. Fix a kind of problem for every entry **in the list**
   (`plan apply --patch`, never `timeline apply` on plan-built items), re-running it and `review verify all` in the
   same call. **Draft audit**: `bc:critic` (else a sub-agent briefed with `<skill_dir>/../review/CRITIC.md`, else
   `--by self`) gets the project, revision and your suspicions, and returns one `plan.cut` patch. Never open the
   packet: in **one call** `run append audit --point draft --by critic …`, `plan apply --patch … --base-rev last`,
   `review run --measure --summary`, `review verify all`. A sheet (`timeline sheet --entries …`) only for what no
   measurement covers; a second critic look only for an unproven blocker.
9. **Draft**: `export start --preset quick-draft --name draft-v1 --include-srt --normalize-audio --wait --save`,
   then **G5** and REFERENCE "The hand-off report".

## The plan as data

Brief and plan are project data that `context get` summarises: after a reset resume from them and `run log`, not
memory. A recipe writes `recipe`, `promise`, `stages` (deviations only), `checks` (≤8), `askAtIntake`; you the rest.
Shapes: REFERENCE "The brief and the plan as data".

## Checklist, gates and audits in short

Stage ids: `intake`, `survey`, `story`, `rough-cut`, `rhythm`, `voiceover`, `visuals`, `sound`, `captions`,
`colour`, `effects`, `review`, `export`, `learn` (FULL "Stages, checklist and gates"). BashCut records `intake`,
`survey`, `story`, `rough-cut`, `captions`, `review`, `export`; optional stages left out need no entry; one by hand:
`run append stage --stage colour --status done --evidence "a;b"` in the call that finishes it. A long stage shows in
the run panel: `run append stage --stage cut --text "Cutting 12 shots" --eta 120`. Request every gate, any mode,
with something cheap to look at (`checkpoint request G2 --summary "…" --attach sheet.png`, then `checkpoint status
--wait 100` while `awaiting_user`). Only the user answers a gate. Skipped G2 needs the strategy audit, skipped
G5 the draft audit. Details: FULL "Gates" and "Audits". `review run` `incomplete` is never a pass.
