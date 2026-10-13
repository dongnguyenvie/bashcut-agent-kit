# Edit workflow: the full path and the rules behind the quick path

Read a section when SKILL.md sends you here (`sed -n '/^## Gates/,/^## [A-Z]/p' <skill_dir>/FULL.md`), never the
whole file. The full path (the user asked for it, the video runs over ~3 min, or `plan.mode: "full"`) runs every
stage below with its stage skill and a fresh critic sub-agent at each audit.

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
| 5 | `voiceover` (when needed) | agent `bc:voice` | **G4 script**, before speech is made |
| 5b | `visuals` (added by the plan when words carry the video, `after: "voiceover"`) | `bc:visual-plan` | — |
| 6 | `sound` | `bc:audio-mix` | — |
| 7 | `captions` and text | `bc:captions-text` | — |
| 8 | `colour` | `bc:color-grade` | — |
| 9 | `effects`, graphics, stock (the rows of `plan.visuals`, else only where a moment needs one) | `bc:effects`, agent `bc:graphics`, `bc:stock-images` | — |
| 10 | `review` | `bc:review` | **draft audit**, **G5 draft** |
| 11 | `export` per output | this skill | — |
| 12 | `learn` | `bc:self-learn`, `bc:library` | **process audit** first |

When you start or resume: `context get` › `workflow.next` gives `{stage, skill, skillRead}`; read that skill when
the stage needs it (Skill tool for `bc:*`, `skills get` for plugin skills). Reads are recorded by BashCut and the
kit's hook; an agent without hooks (Codex, chat agents) records its own with `run append skill --name <skill>`.
BashCut records `intake` (brief set), `survey` (every media described), `story`, `rough-cut` and `captions` (plan
apply), `review` (a passing review run) and `export` itself (`auto: true`). Record the other stages you work on at
their end (several in one shell command when they are ready together):

```sh
bashcut run append stage --stage survey --status done --evidence "survey/contact-sheet.png;media transcribe job 41"
bashcut run append stage --stage colour --status skipped --reason "screen recording, no grade wanted"
bashcut run checklist
```

`done` without `--evidence` counts as unverified; `skipped` needs `--reason`; a stage the plan marks
`required: false` is `n/a` already. `run checklist` (and `context get` › `workflow.checklist`) derives the list from
the plan and the run log; its `open` list is what still needs attention and starts the hand-off report.

Missing coverage at G3 sends you back to survey or effects (stock, generation, a reshoot: ask), once per pair.

## Gates

Read `workflow gates` at intake: each gate is `ask`, `notify` or `skip` (skip unless the user changed it), plus
`maxReviewRounds`. At every gate, whatever its mode, request it with something cheap to look at:

```sh
bashcut checkpoint request G2 --summary "Strategy: one message — …; hook → payoff …" --attach renders/story-sheet.png
bashcut checkpoint status --wait 100
```

- `ask`: repeat `checkpoint status --wait 100` while `awaiting_user` (it returns when the user answers). `approved`:
  go on; `changes`: apply the note, request again; `rejected`: stop and ask; `stale`: request again.
- `notify`: the user is told and you go on. `skip`: nothing is shown.
- Only the user answers a gate: never treat silence or an earlier "go ahead" as approval, never loosen a gate. A
  skill may add its own (`checkpoint request music-pick …`) only for a real decision the user must make.
- Show: G2 a sheet of the hook and section shots, G3 `timeline sheet --cuts` with the duration against the plan, G4
  the script, G5 the normalized draft. Never render an export only to earn a gate a sheet can show.

## Audits: a skipped gate is replaced by its audit

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
