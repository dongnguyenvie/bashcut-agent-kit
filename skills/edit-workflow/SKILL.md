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
  cut as one list (`plan.cut`), never clip by clip; read big things in sub-agents, not yourself. After your own
  commands pass `--base-rev last` instead of reading the revision; `context get` again only when a stale error
  says someone else changed the project.
- Say why: every `plan apply` and `timeline apply` carries `--why` (and `--evidence`).
- You never certify yourself: `done` needs evidence, "fixed" needs `review verify`, "exported" needs the job, a
  pass needs an audit by someone else (or marked `self`). You cannot hear: say which sound you did not check.
- Kit scripts run with `uv`. Name files in English, lowercase with hyphens (`draft-v1`).

## The quick path (default)

For every edit unless the user asked for the full process, the video runs over ~3 min, or `plan.mode` is `full`
(then FULL.md). Same gates and audits, but the cut is one list checked by BashCut. Target: a 45 s ad in about 25–30
calls.

1. **Intake, one call**: `context get`, `knowledge get` and `workflow gates` together, plus the recipe: recipes are
   plugin skills whose description starts "Recipe for" (your skill list shows them as `vlog-<kind>`; else `skills
   list --scope plugin`). Read only its working parts, `skills get <recipe> --section "Plan data,Ranges,Review
   notes"` (the result lists all its `sections`; fetch others you need, such as an ad's brief, arc and truth rules,
   in the same call), and the review limit table `sed -n '/^## Before round 1/,/^## The loop/p'
   <skill_dir>/../review/SKILL.md`. No recipe plugin: `plugins list`, tell the user `/bc:setup`, use kit defaults.
2. **Ask once** (at most 4 questions, REFERENCE "Intake questions"), each led by your own choice "AI chọn: …".
   User away or "don't ask": take your choices and write them `inferred` in the brief. Never ask again later.
3. **Project and survey, two calls**: `project create --name N --dir D --footage FOLDER --canvas
   landscape|portrait|square --fps 30 --language <tag> --import` creates the project, imports every file in the
   folder and starts transcription and picture analysis; the result has each file's `media` ID, `seconds` and
   `jobs {transcribe, analyze}`. The canvas follows where it is watched (portrait for TikTok/Reels/Shorts,
   landscape for YouTube); the language is the user's answer or the prompt's. When the prompt names one file in a
   folder holding others, leave out `--import` and run `media import FILE`, `media transcribe` and `media analyze`
   in one call. An "unsaved changes" error names a project you did not make: `--save-current`. Then hand the survey
   to a sub-agent at once, with the media IDs and both job IDs (it waits for them; never poll yourself): the
   `bc:surveyor` agent when your agent has it (Claude Code), else your own sub-agent given
   `<skill_dir>/../footage-survey/SURVEYOR.md` as its brief (Codex), else do it yourself by that brief. It reads
   the whole transcript, describes the shots into the project and returns hook candidates and exact quotes with
   times in under 450 words. **You never print a transcript or a whole digest and never open source frames**: its
   answer is what you plan from (a 23-min transcript is ~10k tokens that every later turn pays again). Its quotes
   are copied from the transcript and resolve as they are; to read a few lines around them anyway, all windows in
   one command: `media transcript --media M --ranges 640:652,1050:1058 --as text --format text`.
4. **Brief, plan and review limits in one call**: `project format --outputs <preset> --base-rev last` (export
   preset IDs: `youtube-1080`, `shorts`, `reels`, `tiktok`…), `project set-data brief brief.json --base-rev last`
   (each field `{value, status: stated|inferred|confirmed, source}`: `goal`, `audience`, `outputs`, `angle`,
   `lengthSeconds {min, max}`, `notes`) and `project set-data plan plan.json --merge --base-rev last` with `promise`,
   `sections` (`{id, label, lengthSeconds {min, max}, reason}`), `recipe`, `checks`, `decisions`, `ranges` and
   **`cut`**: clips in order by quote (`{media, quote, section}`), `cover` for pictures over a line, `zoom` (with
   `pan`, `tilt`) on a clip or cover for a punch-in, `titles` by preset name (`hook-title`, `place-card`, a template
   ID such as `stacked-keyword`), `captions: {from: "speech"}` when words should show, one
   `music` bed with `duckDb`. The shape:

   ```json
   {"cut": {"clips": [{"id": "c1", "media": "M", "quote": "exact words as transcribed", "section": "hook"},
                      {"id": "c2", "media": "M", "from": 642.8, "to": 648.0, "section": "proof",
                       "cover": [{"media": "M", "from": 950.0}]}],
            "titles": [{"id": "t1", "text": "HOOK LINE", "clip": "c1", "preset": "hook-title"},
                       {"id": "t2", "text": "Place", "section": "proof", "offset": 0.5, "seconds": 2.5,
                        "preset": "place-card", "style": {"positionY": 0.8}}],
            "captions": {"from": "speech", "style": {"background": {"color": "#000000", "opacity": 0.6}}},
            "music": {"media": "S", "duckDb": -14},
            "review": {"minTextSize": 0.035, "minTextContrast": 3, "minShotSeconds": 0.6}}}
   ```

   `style` changes only the fields it names: `size` (share of the short side), `positionY` (baseline from the
   bottom, 0–1) and `positionX`, `align`, `font`, `fill`, `stroke`, `strokeWidth` (points, unlike `size`),
   `uppercase`, `background {color, opacity}`, `shadow`. Plain white text over daylight footage measured 1.2–2:1
   contrast in past runs: decide plates for captions and titles here, not after review. A title anchors to a `clip`
   or a `section` (plus `offset`) and without `seconds` lasts to its end; two texts on screen at once need different
   `positionY`. **Review limits** go in the same list (`review`), each chosen from the recipe's `Ranges` and the
   review table you read at intake; `plan apply` writes them into the project. `plan check` warns
   `review-profile-unset` with `facts.unsetLimits` (every limit this edit needs) and `facts.accepts`; set them all
   before the build, or review stays incomplete. A limit no source gives a range for: choose one for this video and
   say so in `ranges`. Words the transcript misheard (names, places): `captions.replace` `{"misheard": "right"}`.
   Request **G1** with the brief. No music in `library list --kind audio` and no music plugin: leave the bed out and
   list it as open; do not search the disk.
5. **Check, no edit**: `plan check` resolves every quote and builds a scratch copy: clips (edges inside words),
   titles (`textShare`, chars per second), problems and the review as it would be. `same-framing` (two clips of one
   camera at one size back to back) is a jump cut to come: give the second a `zoom` punch-in (a size change at a
   cut is 1.15–1.3, `bc:beat-cut` §5, within the clip's headroom; never over signs or text) or a `cover`, now rather than after review. `unknown-field` means
   a field changes nothing. Fix with `plan check --patch
   '{"clips": {"c2": {"to": 953.0}}}'` (it merges by entry ID and checks the result; never rewrite plan files with
   scripts) until `ok` and every warning is one you mean; a `cut-in-word` gives the word's `before`/`after` edges
   in `facts`, so move the edge there in the same patch. The **strategy audit** is yours here (`--by self`): judge
   the promise, sections, the `inferred` brief fields and the recipe checks from the check's result.
6. **Build once, in the call that records the audit**: `run append audit --point strategy --verdict pass --findings
   N --by self --evidence "…"`, G2 (`checkpoint request G2 --summary "…"` unless skipped), then `plan apply --base-rev last --sheet
   --why "…"` (with `--patch '…'` carrying the changes that made the check ok: a check saves nothing): it builds the list as one undoable edit
   and returns the review's errors and warnings plus the storyboard sheet; look at that one sheet for G3. Later
   changes are `plan apply --patch …` too: only what changes, by entry ID (`null` removes one), checked, saved to
   `plan.cut` and built in one call.
7. **Finish only what the plan cannot say**: voiceover, colour, effects, a mix `audio mix-measure` finds off; the
   stage skill for anything beyond one command.
8. **Review**: `review run --measure --summary` measures this revision (picture and text contrast) and reviews it in
   one call. Fix a kind of problem once for every entry it touches (all titles get the plate, not one) **in the edit
   list**: `plan apply --patch` (titles, caption style, review limits, cover shots), never `timeline apply` on items
   the plan built (the next apply replaces them), then in the same call `review run --measure --summary` and
   `review verify all`. Then the **draft audit**: the `bc:critic` agent (or your sub-agent given
   `<skill_dir>/../review/CRITIC.md`, else `--by self`) builds the draft packet itself, judges it and returns its
   fixes as one `plan.cut` patch; give it the project, the revision and what you suspect, not the packet. Do not open
   the packet yourself: in **one call** record the verdict (`run append audit --point draft --by critic`), apply the
   patch (`plan apply --patch … --base-rev last`), `review run --measure --summary` and `review verify all`. Text
   positions, sizes and overlaps are measured there; open a sheet (`timeline sheet --entries` of the changed entries)
   only for a change no measurement covers. Send it back for a second look only for a blocker that no measurement
   proves.
9. **Draft and hand-off**: `export start --preset quick-draft --name draft-v1 --include-srt --normalize-audio --wait
   --save` returns the finished job and saves the project, then **G5** and the hand-off report (REFERENCE "The
   hand-off report"). BashCut records the stages itself (below); the two audits are yours.

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
(rhythm, voiceover, sound, colour, effects…) need no entry; a stage you do by hand: `run append stage --stage
colour --status done --evidence "a;b"` in the call that finishes it. Gates: `workflow gates` at intake; each is `ask`, `notify` or `skip`; request every one with
something cheap to look at (`checkpoint request G2 --summary "…" --attach sheet.png`, then `checkpoint status --wait
100` while `awaiting_user`). Only the user answers a gate. A skipped G2 needs the strategy audit and a skipped G5
the draft audit; BashCut refuses the rough cut without the recipe read and the strategy audit, and a final export
without a passing draft audit: run what the error names. Details: FULL "Gates" and "Audits". `review run` status
`incomplete` is never a pass.
