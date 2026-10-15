# Edit workflow: reference

Detail for `bc:edit-workflow`; read only the section a step names.

## Starting a project

```sh
bashcut project create --name "Market vlog" --dir ~/Movies/BashCut --footage /abs/path/footage \
  --canvas portrait --fps 29.97 --language <tag>      # the user's language, e.g. en, vi, ja
```

Language is an intake question unless the prompt names it. The user's writing language is a good first option, not
an answer: a Vietnamese prompt can ask for an English video, and footage can speak another language. It drives
captions, speech-rate units, voices (`speaksContentLanguage`) and fonts (`fonts list --covers`). Unknown yet: create
without it, set it once transcribed (`project format --language <tag> --base-rev last`; `plan check` problem
`content-language-unset` names the language heard).

Canvas from where it will be watched: `portrait` for TikTok/Reels/Shorts, `landscape` (16:9) for YouTube and
computers, `square` for feeds. Ask when unclear. Changed later (`project format --canvas`): recheck reframing and
text placement with `ui frame`.

Then the platforms: `project format --outputs reels,tiktok --base-rev N` (first one primary; a recipe sets them).
`platforms get` gives their facts (shape, length, safe zones, loudness) with sources. Review checks text against the
zones of every output of the frame's shape (the strictest wins; no outputs, no zones checked); each export is
normalized to its own preset's loudness. Caption delivery per output is the project's `output.captions`.

`--footage` links the footage folder (never modified). Import it whole before the survey in one call (`media import
/abs/path/footage --base-rev N`; the survey needs project media). Pass absolute paths: the CLI resolves relative
ones against its own working directory. Before planning, `context get` › `analysis` lists media not yet measured,
transcribed or described and running jobs: wait, or say what the plan does not know yet.

## Intake questions

One round, never one by one: AskUserQuestion in Claude Code, a numbered list in plain text elsewhere (Codex, chat
agents). At most 4, in this order; skip any the prompt, brief or knowledge facts answer, drop the least important to
stay at 4 (a dropped one is decided and written `inferred`):

| Question | Your choice, first option | Other options |
|---|---|---|
| Which recipe | the best match from intake step 3, with the reason from step 2 ("a 10 min portrait talk + a screen recording") | the close second; kit defaults |
| The steps | "Đồng ý" with the step list from intake step 4 in the question text (`survey → story → rough-cut → … → export`) | drop a step (name it); add one |
| Length | the range the recipe and the footage support ("1:45–2:15, the best lines") | the platform's usual ranges |
| Where it will be posted | the shape of the footage (portrait → TikTok/Reels/Shorts) | YouTube (landscape); both |
| Language of speech and captions | the language the user writes in, or the one heard | English; other |
| A recipe's `askAtIntake` field (a truth source, a channel name) | only when the footage or knowledge facts give it; else ask without a guess | what the recipe suggests |

Every first option names the concrete choice, never a bare "auto": `AI chọn: talking-head + chèn màn hình
(Recommended)`, with the reason in its description, so the strategy audit can check it. Text-only agents end the
list with "Không trả lời: mình làm theo lựa chọn 1 của mỗi câu".

Answers go into the brief as `stated`; a first option taken because the user did not answer is `inferred` with your
reason in `source` (the strategy audit checks each guess), never asked again. The chosen steps become `plan.stages`
(`required: false` with the user's reason for a dropped one, `{"skill", "after"}` for an added one).

## The brief and the plan as data

The brief holds what the edit is for. Each field is `{value, status, source?}`: `stated` (user said it), `inferred`
(your guess from footage or platform) or `confirmed` (approved at G1). Fields: `goal`, `audience`, `outputs`,
`angle`, `lengthSeconds` (`{min, max}`), `notes`, plus `ideas` and `references` lists.

```json
{
  "goal": {"value": "Show the night market in 60 s", "status": "stated", "source": "prompt"},
  "outputs": {"value": ["reels", "tiktok"], "status": "stated", "source": "prompt"},
  "lengthSeconds": {"value": {"min": 45, "max": 75}, "status": "inferred", "source": "Reels, a food vlog"},
  "audience": {"value": "friends who were not there", "status": "inferred"}
}
```

The plan holds how: `mode` (create, directed, revision), `stage`, `options` (story options compared), `sections`
(`{id, label, lengthSeconds {min, max}, reason, frozen}`), `shots` (planned shots: `purpose`, `size`, `mustShow`,
`source` footage, stock, graphic or generated), `beats` (script lines: `{id, section, text}`), `visuals` (per line,
`bc:visual-plan`), `decisions` (`{text, …}`, with the alternatives and the reason), `ranges` (the review limits you
chose, `{min, max, source, reason}`) and `notes`. Match `review coverage` (described shot per clip) with planned
shots yourself; `script check` compares the beats with the words heard.

A recipe adds only what differs from the defaults:

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

`stages` keys are stage ids (never a skill name); `skill` replaces the stage's default skill; another key adds a
stage, right after the stage its `after` names (else before review);
`required: false` with `why` marks a stage `n/a` up front. `checks` are the recipe's own (at most 8); the kit's
generic checks (`bc:review`) are always added. `promise` is generic: every video opens a question and must close
it. `context get` summarises all this, so it survives a reset without re-reading the recipe.

Update `stage` in the stage's one plan write (`project set-data plan --merge`), so plan and run log agree; never
a write just for it.

## Story

- **Hook in the first 1–3 s**: the best or most surprising moment, often the ending or loudest shot, then back to
  the start. A cold open of three shots (~8 s) worked well for travel and food vlogs.
- Tool demos, tutorials: hook on the tool's **output** with its own sound, then the presenter ("Screen recording
  with a presenter").
- Sections in time order after the hook, each a section marker with a length range and its reason in the plan.
- Talking videos: a **chain of spoken lines** (real speech + voiceover, ~0.14 s gaps), picture cut to what is said,
  lines selected by quote (`bc:rough-cut`). Music-led montages: cut on the beat grid (`bc:beat-cut`).
- Lines come from `media transcribe` (needs a `captions.transcribe` plugin) and `media transcript` (the surveyor
  reads it); once cut, `transcript words --heard` and `captions find "words as said"` place them on the timeline.
- CREATE mode: 2–3 story options in `plan.options` (T00 §3: ≥2 compared before choosing), each a few lines on what
  the footage supports and lacks. The G2 strategy is 4–8 sentences plus the section table (T00 §3).

## Screen recording with a presenter

Map the user's phrase to the edit:

| The user says | Build |
|---|---|
| "video giới thiệu tool", "demo phần mềm", "tutorial", "N phút" | hook = the tool's output (5–7 s, its own sound, a label like "VIDEO NÀY DO AI DỰNG"), then the presenter: prompt → tool working (fast-forward) → how it works, one panel per sentence → limits and next steps |
| "video desktop làm nền", "màn hình làm nền" | screen recording on the main layer, cut to the same moments as the speech (offset from `media sync`, `bc:footage-survey`); on a portrait canvas a blurred copy below fills the bars (`bc:stock-images`) |
| "người đọc / người nói ở trên video", "khung mặt" | presenter camera on an overlay layer *in front of* the screen, zoom ~0.37 (a 9:16 camera becomes ~400 px wide), at the bottom centre; captions between screen and face. "Ở trên" can mean the layer order or the top of the frame: bottom centre was kept without complaint; ask when unsure |
| "ẩn giọng desktop", "tắt tiếng màn hình" | mute the screen clips; speech comes from the camera (`bc:audio-mix`, "Screen recordings") |
| "chọn nhạc phù hợp giọng" | measure candidates against the voice (`audio measure`, `bc:audio-mix`) |
| (unsaid, always) | zoom onto the panel being talked about, fast-forward waiting and typing (`bc:effects`) |

Real case: a 5 min session (camera + screen) became a 2:00 intro, speech over 92% of it; dropped: fillers, muddled
lines, reactions to bugs, sentences where the camera mic heard the laptop playing the output. The first cut opened
on the presenter's "hello"; the user sent it back: "end user muốn biết output".

## Taste of the user

Preferences (length, pace, voice, style) live in BashCut, not this kit. Run `knowledge get` at the start of every
edit: `userMemo` is notes for every project, `memo` and `skills` this project's own. Recording taste, facts and
lessons: `bc:self-learn`.

## Working efficiently

Measured on real runs: one ad took 778 calls (159 `context get`); a quick-path ad (0.1.27) 108 turns and 13.4M,
context 34k → 180k because every transcript, image and skill it read stayed. In the #553 bench (0.1.46) the editor
starts at ~45k, so each call costs that: one run made 13 `plan check`, 10 `set-data` and 9 `project get` calls,
and 6–7 idle wake-ups per run (0.5–0.7M) waited on sub-agents through `SendMessage`. In the system-diagram benches
(0.1.52) the editor made 48 and 25 calls at 45k → 123k (4.4M and 1.9M); about half were avoidable: 7 `help`/`--help`
and 4 `schema get` lookups, 2–3 extra bootstrap reads (recipe sections, the plan shapes), 2–3 reads of a widget's
variables or HTML, 2–3 music searches, 2 extra plan writes, re-reads of the plan, frames of the sub-agents' work, a
second voice round for length, and a hand caption regroup that cost 4 calls plus 8 to recover from. The 12–18
`project get` calls were the graphics sub-agent's, reading the whole document for `rev` and one list.

- **One call for many things** (BashCut's batching rules), plus `media transcribe` without `--media` (every media),
  `plan apply --sheet` (build, review, storyboard); in a shell chain commands whose output you skip (`run append …
  && run append …`); with MCP send independent calls together.
- **Sub-agents read, you decide**, in the foreground: one call returns the answer, a fix round is a new call with
  the findings (no `SendMessage`, no turn ended to wait). `bc:*` agents run on a cheaper model; others brief their
  own sub-agent with the file. Plan from the surveyor's answer; never print a transcript, whole digest or source
  frames (run 6's 25k-character transcript was paid again by 25 later turns); apply the critic's patch without
  reading the packet. No sub-agents: follow the briefs yourself, the digest a stretch at a time (`--from/--to`).
- **Catch it in the plan, not in a critic round.** Set every limit `review-profile-unset` names in `plan.cut.review`
  before the build, so `plan apply` and `review measure` report small text and low contrast. Loudness waits for the
  normalized export (`atExport`), not holding review back.
- **Look in batches.** One image costs about 1000 tokens; one contact sheet of 12–24 cells is ~15× cheaper per frame
  (T20 §3, §7): `timeline sheet --cuts --text` for continuity and text, `timeline sheet --every 2` for pace, `media
  frames --sheet` for footage, `timeline sheet --at F1,F2,…` for a few frames. Single frames (`ui frame F --phone`)
  only on doubt, `review window F` only at a decision point (T16 §2). Text results before images.
- **Wait, don't poll.** `jobs wait` again only on `timedOut`; an export is a job too (never loop on `export
  status`). After ~30 min give the user the job ID. Start long jobs together; do work that does not need them
  meanwhile.
- **Read once, read little.** `context get` on start, resume and after a gate, and keep it: no `project get` or
  `timeline get` between steps (`plan check` and `review run` say what you need). One `plan check`, one patch.
  Filter big JSON in the same call; `schema get` only for a field no command description names. A loaded skill stays
  for the run.

## Syntax the runs looked up

Each of these cost one to eight calls of `help`, `schema get` or trial and error in a bench:

| Need | Call |
|---|---|
| Revision for an edit | `--base-rev last` (after any command of yours, reads included); never `project get \| jq .rev` |
| One plan list | `bashcut project data plan \| jq -c '.cut.voiceover'` (the value itself: no `.plan` or `.data`) |
| Fields of `plan.cut` | SKILL step 4 and "The brief and the plan as data" (both in the bootstrap); never `help plan check` |
| Fix built items | `plan apply --patch '{"music": {"volumeDb": -4}}' --base-rev last --why "…"` (by entry ID; keeps grouped captions); never `timeline apply` on plan-built items |
| A clip's gain off the plan | `clip volume ITEM --db -4 --base-rev last`; a timeline op is `{"op": "setProperties", "item": ID, "patch": {…}}` |
| Captions by rule | `captions group --max-chars 24 --max-seconds 3 --break-gap 0.3 --base-rev last` |
| Captions by hand | one call: `transcript words \| jq` to a file, a script writing `groups.json` (`[[0,1,2],[3,4]]`, runs of word indices), `captions group groups.json --base-rev last` |
| A sound measurement job | `J=$(bashcut audio mix-measure \| jq -r .job); bashcut jobs wait $J --done --timeout 110` |
| Frames | `ui frame F --phone --out /abs/f.png` (frames, not seconds), several in one call |

## Run log

```sh
bashcut run append start --text "Market vlog, create mode, reels + tiktok"
bashcut run append round --round 1 --fixed 3 --left 2
bashcut run append measured --measured picture,loudness,layout --not-measured sound-by-ear
bashcut run append end --text "Draft approved, exports queued"
```

Stage entries: FULL "Stages, checklist and gates". The two audits (strategy, draft) are always yours; gate entries
come from `checkpoint request` and the user's answer, never you. End with `end`, then the hand-off report.

## The hand-off report

Build it from `run checklist` and `run log`, not chat memory. Start with the checklist's `open` items
(required stages skipped, `done` without evidence, missing audits), then each audit's verdict (say "self-audited"
for `by: self`), the missing recipe if none was installed, stages run, each gate with the user's answer, the review
rounds (fixed, left), what was measured and what was not (sound not listened to, plugin checks that timed out),
every kept issue with its reason and the `needs_user` items. Example: "Review: 2 rounds. Closed a 1.2 s black gap at
0:41, raised the caption out of the Reels bar. Profile: static shots up to 6 s, a calm travel vlog. Kept: the 9 s
shot at 0:12, the hook you chose. Not listened to: the music under your voice."
