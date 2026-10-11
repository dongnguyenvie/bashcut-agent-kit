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
- Edit without asking; stop only at gates. Download what the edit needs (music, SFX, pictures, video, fonts)
  without asking; no source or licence records (`--source URL` only when you have it anyway). Never clone a voice
  that is not the user's. Plugins are the user's to install: missing ones → tell them `/bc:setup`.
- Read a plugin's skill before using its feature; plugin skills are read-only (corrections: `bc:self-learn`).
- **Every call is a turn that resends the whole context** (cost ≈ calls × context): one call for many things, the
  cut as one list (`plan.cut`), never clip by clip; read big things in sub-agents, not yourself. After your own
  commands pass `--base-rev last` instead of reading the revision; `context get` again only when a stale error
  says someone else changed the project.
- Say why: every `plan apply` and `timeline apply` carries `--why` (and `--evidence`).
- You never certify yourself: `done` needs evidence, "fixed" needs `review verify`, "exported" needs the job, a
  pass needs an audit by someone else (or marked `self`). You cannot hear: say which sound you did not check.
- Kit scripts run with `uv`. Name files in English, lowercase with hyphens (`draft-v1`).

## The quick path (default)

Unless the user asked for the full process, the video runs over ~3 min, or `plan.mode` is `full` (then FULL.md).
Same gates and audits; the cut is one list BashCut checks. Target: a 45 s ad in about 20 calls.

1. **Intake, one call**: `context get`, `knowledge get`, `workflow gates`, the recipe's working parts
   (`skills get <recipe> --section "Plan data,Ranges,Review notes"` plus any other section you need; recipes are
   plugin skills described "Recipe for", listed as `vlog-<kind>`) and the review limit table
   (`sed -n '/^## Before round 1/,/^## The loop/p' <skill_dir>/../review/SKILL.md`). No recipe plugin: tell the
   user `/bc:setup`, use kit defaults.
2. **Ask once** (at most 4 questions, REFERENCE "Intake questions"), each led by "AI chọn: …". User away: take your
   choices, write them `inferred` in the brief, never ask later.
3. **Project and survey, two calls**: `project create --name N --dir D --footage FOLDER --canvas
   landscape|portrait|square --fps 30 --language <tag> --import` imports the folder and starts transcription and
   analysis (result: `media` IDs, `jobs {transcribe, analyze}`). Portrait for TikTok/Reels/Shorts, landscape for
   YouTube. One named file in a busy folder: no `--import`; `media import FILE`, `media transcribe`, `media analyze`
   in one call. "Unsaved changes" about a project you did not make: `--save-current`. Then the survey sub-agent at
   once, with media and job IDs (it waits): `bc:surveyor` (Claude Code), else a sub-agent briefed with
   `<skill_dir>/../footage-survey/SURVEYOR.md`, else that brief yourself. It returns hook candidates and exact
   quotes with times in under 450 words. **Never print a transcript or digest, never open source frames**; its quotes
   resolve as they are (a few lines around them: `media transcript --media M --ranges 640:652,1050:1058 --as text
   --format text`).
4. **Brief, plan, sound and review limits in one call**: download any music or SFX first (below), `media import`
   them, then `project format --outputs <preset> --base-rev last` (`youtube-1080`, `shorts`, `reels`, `tiktok`…),
   `project set-data brief brief.json --base-rev last` (fields `{value, status: stated|inferred|confirmed, source}`:
   `goal`, `audience`, `outputs`, `angle`, `lengthSeconds {min, max}`, `notes`) and `project set-data plan plan.json
   --merge --base-rev last` with `promise`, `sections` (`{id, label, lengthSeconds {min, max}, reason}`), `recipe`,
   `checks`, `decisions`, `ranges` and **`cut`**:

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

   Clips go in order, by quote (or `from`/`to`, which on a quote move its edges); `cover` lays pictures over a
   line; `zoom` (`pan`, `tilt`) is a punch-in. Titles take a preset (`hook-title`, `place-card`, `stacked-keyword`…)
   and anchor to a `clip` or `section` (+ `offset`), lasting to its end without `seconds`. `style` changes only what
   it names: `size` (share of the short side), `positionY` (baseline from the bottom, 0–1), `positionX`, `align`,
   `font`, `fill`, `stroke`, `strokeWidth` (points), `uppercase`, `background {color, opacity}`, `shadow`. White
   text over daylight measured 1.2–2:1: plate captions and titles now; two texts at once need different
   `positionY`. **Sound**: a `music` bed unless the brief says none; `sfx` only where a moment needs one (whoosh on
   a hard cut, pop as a title lands; `offset` -0.1 peaks on it). Library first (`library list --kind audio`), else
   download without asking: `curl -s "https://api.openverse.org/v1/audio/?q=<mood>&category=music&page_size=10"`
   (`results[].url`, `duration` ms; SFX: no `category`, `q=whoosh`), or Mixkit
   (`https://mixkit.co/free-stock-music/tag/<mood>/`, `https://mixkit.co/free-sound-effects/<whoosh|pop>/`).
   **Review limits** (`review`) come from the recipe's `Ranges` and the review table; `plan check` lists any still
   unset in `review-profile-unset` (`facts.unsetLimits`, `facts.accepts`): set them all, else review stays
   incomplete; a limit no source covers: choose it and say so in `ranges`. Request **G1** with the brief.
5. **Check, no edit**: `plan check` resolves quotes on a scratch copy: clip edges, titles (`textShare`, chars per
   second), problems, the review as it would be. Fix by `plan check --patch '{"clips": {"c2": {"to": 953.0}}}'`
   (merges by entry ID; never rewrite plan files with scripts) until `ok`: `cut-in-word` gives `facts.before/after`
   to move the edge to; `same-framing` is a jump cut to come (give the second clip a `zoom` 1.15–1.3, `bc:beat-cut`
   §5, never over text, or a `cover`); `unknown-field` changes nothing. The **strategy audit** is yours (`--by
   self`): promise, sections, `inferred` brief fields, recipe checks.
6. **Build in the call that records it**: `run append audit --point strategy --verdict pass --findings N --by self
   --evidence "…"`, G2 unless skipped (`checkpoint request G2 --summary "…"`), `plan apply --base-rev last --sheet
   --why "…"` (with `--patch` holding the check's fixes: a check saves nothing). It returns the review's errors and
   warnings and the storyboard: look at that one sheet for G3. Every later change is `plan apply --patch …`.
7. **Only what the plan cannot say**: voiceover (no usable speech, or the brief asks: `bc:voiceover`), colour,
   effects, a mix `audio mix-measure` finds off.
8. **Review**: `review run --measure --summary` measures and reviews in one call. Fix a kind of problem for every
   entry it touches, **in the list** (`plan apply --patch`; never `timeline apply` on plan-built items), with
   `review run --measure --summary` and `review verify all` in the same call. **Draft audit**: `bc:critic` (else a
   sub-agent briefed with `<skill_dir>/../review/CRITIC.md`, else `--by self`) builds the packet itself and returns
   one `plan.cut` patch; give it the project, revision and your suspicions. Never open the packet: in **one call**
   `run append audit --point draft --by critic …`, `plan apply --patch … --base-rev last`, `review run --measure
   --summary`, `review verify all`. Positions, sizes and overlaps are measured; open a sheet (`timeline sheet
   --entries …`) only for what no measurement covers; a second critic look only for an unproven blocker.
9. **Draft**: `export start --preset quick-draft --name draft-v1 --include-srt --normalize-audio --wait --save`,
   then **G5** and the hand-off report (REFERENCE "The hand-off report").

## The plan as data

Brief and plan are project data (`project set-data brief|plan`, `--merge` for one part); `context get` summarises
both, so after a reset resume from them and `run log`, not from memory. Shapes: REFERENCE "The brief and the plan
as data". A recipe writes `recipe {skill, version}`, `promise {hook, payoff}`, `stages` (deviations only), `checks`
(at most 8) and `askAtIntake`; you write `mode`, `stage`, `options`, `sections`, `shots`, `beats`, `visuals`,
`decisions`, `ranges` and `cut`.

## Checklist, gates and audits in short

Stage ids: `intake`, `survey`, `story`, `rough-cut`, `rhythm`, `voiceover`, `visuals`, `sound`, `captions`,
`colour`, `effects`, `review`, `export`, `learn` (table and skills: FULL "Stages, checklist and gates"). BashCut
writes `intake` (the brief set), `survey` (every media described), `story`, `rough-cut` and `captions` (plan
apply), `review` (a review run that passes) and `export` (an export that lands). Optional stages you leave out
need no entry; a stage you do by hand: `run append stage --stage colour --status done --evidence "a;b"` in the call
that finishes it. Gates (`workflow gates`) are `ask`, `notify` or `skip`; request every one with
something cheap to look at (`checkpoint request G2 --summary "…" --attach sheet.png`, then `checkpoint status --wait
100` while `awaiting_user`). Only the user answers a gate. A skipped G2 needs the strategy audit and a skipped G5
the draft audit; BashCut refuses the rough cut without the recipe read and the strategy audit, and a final export
without a passing draft audit: run what the error names. Details: FULL "Gates" and "Audits". `review run` status
`incomplete` is never a pass.
