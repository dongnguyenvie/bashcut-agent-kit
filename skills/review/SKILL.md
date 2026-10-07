---
name: review
description: Review a BashCut edit before export as a capped critic loop — set the review profile from sourced ranges, measure, look at the edit in batches, judge findings by what a viewer perceives (blocker, polish, taste, needs user), fix one labelled edit per finding, prove each fix with review verify, keep deliberate choices with a reason, and report what was and was not checked. Also the brief for a fresh critic sub-agent given only a review packet folder. Use at the review stage of any edit, before a draft or export, when the user asks to check or critique a video, or when you were handed a review packet. Triggers: "review", "kiểm tra video", "soát lỗi", "xem lại bản dựng", "chấm bản dựng", "critic", "QC", "trước khi xuất".
---

# Reviewing an edit in BashCut

Reply in the user's language. Core measures, renders evidence, tracks issue identity and rounds, and states what it
did not check. Which findings matter and how many rounds to run are decided here, by you, for this video.

Passing checks is not proof of a good video. One tool's edit had all 29 actions on the beat and every cut on a bar
line, and still had cramped frames, small text and titles over the icons: "the model will satisfy whatever can be
quantified" (T16 §2, guizang). Look at the pixels.

## If you were given a packet

You are a fresh critic: you got a folder from `review packet` and this skill, nothing else. You did not make the
edit and you have none of the maker's reasons, on purpose (T16 §4). Judge what is on screen against the plan.

| File | What it holds | Use it to |
|---|---|---|
| `README` | what the packet is, the project, revision and round | know which round you judge |
| `plan.json` | the brief, the edit plan (sections with length ranges, shots, beats, decisions), the review profile, the outputs | know what the edit promised and for which platforms |
| `digest.json` | what changed since the last review round | in round 2+, check those changes first |
| `issues.json` | the measured issues with severity, frame, fix, and the round diff (fixed, new, persisting) | start from facts; a measured issue is a number, not yet a finding |
| `shots.json` | every shot on Main with the cut into it (kind, framing before and after), rhythm, shares | find jump cuts, same-framing cuts, unintended gaps, monotony |
| `word-landing.json` | words against cuts and titles: offsets, cuts inside words | find clipped words, titles early or late on their word |
| `coverage.json` | the described shot each clip plays; the plan's beats against the words heard | find promised shots or lines that are missing (join the clips with `plan.json` shots) |
| `measured.json` | what was measured and what was not (stale, notChecked, failed, unreliable) | never pass what nobody measured |
| `sheet-*.png` | a contact sheet of every cut and title, labelled `<cell> <m:ss.s>` | see framing, text size and placement, repeated shots |

How to work: read `README`, `plan.json` and `measured.json` first; then `issues.json`, `shots.json`,
`word-landing.json`, `coverage.json`; then every sheet; judge the opening from the first shots, words and cells. Do not edit the project. If you also have the
`bashcut` CLI, read-only commands are fine for a doubt (`ui frame F --phone`, `review window F`), nothing else.

Return, as text, briefed "to roast, not to praise" (T16 §2):

1. A verdict: `pass` (no blocker) or `fail`.
2. Findings, blockers first: time (m:ss.s) or frame, severity (below), what the viewer perceives, the evidence (file
   and field, or sheet cell), and which stage owns the fix (story, rough cut, rhythm, sound, text, colour, effects).
3. The 3–5 fixes to do first (T16 §7).
4. `needs_user`: taste choices and missing material, kept apart from defects.
5. What you could not judge: sound by ear, motion between sheet cells, anything `measured.json` lists as not measured.

## Severity: what the viewer perceives

Define severity by the viewer at normal speed and size on a phone, not by the metric (T16 §4, reelmimic, talkcraft):

- **blocker**: a viewer will notice it at normal speed and it hurts understanding or trust: a black or frozen
  frame, a clipped word, unreadable or covered text, speech drowned by music, a missing promised moment, a hook that
  does not show what the video is about. Core `error` issues (gaps, black picture on Main, a cut inside a word,
  missing glyphs, wrong length or shape for an output) are blockers unless you show they are not real.
- **polish**: visible only when paused, zoomed or compared side by side. Fix when cheap; never a reason for another round.
- **taste**: a choice a viewer could like either way (pace, a look, a transition). Leave it to the user (`needs_user`).
- **needs user**: something only the user can supply or decide (a missing shot, music choice, a name to spell).

A measured warning is not automatically a blocker: a locked-off interview trips "static shot"; a deliberate long
title trips "long still". Decide, then fix, adjust the profile, or accept with a reason.

## Before round 1: the profile

Core has no editorial defaults. The project's `review` object holds the limits (`minShotSeconds`, `maxShotSeconds`,
`maxStillSeconds`, `stillMotion`, `jumpCutChange`, `blackMinSeconds`, `hookSeconds`, `maxSilenceSeconds`,
`maxMusicGapSeconds`, `voiceoverMarginSeconds`, `captionLineChars`, `captionMaxLines`, `minTextSize`,
`minSpeechCoverage`, `loudnessToleranceLU`, `severities`, `platform`). A limit left unset reports only the measured
value, as info, and `review run --summary` lists it under `checks.unsetLimits`. A vlog recipe sets them; otherwise
choose from the ranges below for this genre and footage, write them with `timeline apply` (`setProjectProperties`
`{"review": {…}}`), record each in the plan's `ranges` with its source and reason, and tell the user.

Ranges seen in other review tools (T16 §3), starting points, not defaults:

| Limit | Range | What moves it |
|---|---|---|
| `blackMinSeconds` | 0.1–0.5 s | intended dips to black (a fade-through, an end card) |
| `maxStillSeconds` (exact freeze) | 0.8–1 s | a frozen picture on video media is usually a decode or render fault |
| `maxShotSeconds` with `stillMotion` (static shot) | 3–6 s | genre: a calm daily vlog keeps long stills, a montage does not |
| `maxSilenceSeconds` (dead air, whole mix) | 2–5 s | ASMR or a calm vlog tolerates more; a gap inside speech is another measure (~0.8 s) |
| word landing (caption or title vs its word) | 0.1–0.3 s | correctness, not taste |
| `loudnessToleranceLU` | 1–2 LU | the platform and the delivery file |
| true peak | −1 to −0.5 dBTP | lossy codecs need −1 |
| length vs plan | 2–15 % | strict for ads and fixed slots, loose for vlogs |
| rounds | 1–3 | 1 when the user is waiting and nothing blocks; up to 3 unattended (T00 §3, T16 §3) |

The platform's own numbers (length, loudness target, safe zones) come from `platforms get <id>`, never from here.

## The loop

```sh
bashcut review measure                      # a job: picture checks, plugin checks
bashcut jobs wait <job> --timeout 25       # repeat until completed, failed or cancelled
bashcut review run --summary --min-severity warning
```

Each round:

1. **Measure, then read.** `review run --summary` returns the issues and `checks`: `measured`, `stale` (an older
   revision: measure again), `notChecked` (with how to measure it), `failed` (plugin checks that timed out),
   `unreliable` (picture that barely changes: not a pass) and `unsetLimits`. Errors come first. Info issues
   `voice-text-changed-*`, `captions-source-changed-*` and `beats-source-changed-*` mean a result was made from an
   older text or file: run their fix (speak, transcribe or detect again) before judging that voice, those captions
   or that beat grid.
2. **Look in batches.** `timeline sheet --cuts --text` (and `--outputs all` for safe zones), then
   `review window F --span S --step K` only at cuts in doubt: ±0.4–1.5 s at 10–12 fps, wider for dialogue cuts,
   narrower for beat cuts (T16 §3; at 30 fps about `--span 12`–`45` with `--step 3`). `ui frame F --phone` for text
   at the width a viewer sees (360–420 px, T16 §3). `review coverage` (which described shot each clip plays) and `script check` against the plan.
3. **Critic.** When you can start a sub-agent, run `review packet` and give it only the folder and `bc:review` (the
   section above). It has none of your reasons, so it sees what a viewer sees. Otherwise judge yourself, from the
   evidence, not from what you intended.
4. **Decide each finding** by severity: fix it (one labelled edit; the issue's `fix` when it has one), change the
   profile when the limit is wrong for this video (say so and why), accept it with a reason, or list it for the user.
5. **Verify each fix.** `review verify <id>` re-measures the issue's range and returns before and after numbers, the
   status (fixed or persisting) and a strip. Say "fixed" only with that result: "looks better" does not count (T16 §2).
6. **Log the round**: `run append round --round 1 --fixed 3 --left 2`.

Applying a `fix`: `timeline.apply` → write `fix.arguments.ops` to a file and run `timeline apply ops.json --base-rev
N --label "<the issue title>"`; `timeline.close-gap` → `timeline close-gap --at-frame <atFrame> --base-rev N`;
`review.measure` → measure, then review again; `export.start` → loudness comes from a normalized draft, last;
`selects.place` → place it or unmark it with a reason (`bc:rough-cut`); a `hint` only → do it with that area's skill,
or ask the user when it is taste. Never hide a failure with a transition or a flash (T16 §4).

| Issue | Look and measure | Fix with |
|---|---|---|
| black, frozen picture, long static shot | `ui frame F`, `review picture --from F --to G`, `review shots --summary` | `bc:beat-cut`, `bc:effects`; black: offline media or a hiding layer |
| jump cut, repeated framing, gap, cut in a word | `review window F`, `review shots` (`cut`), `timeline apply --dry-run` (`cutsInsideWord`) | `bc:rough-cut`, `bc:beat-cut` |
| cut or text off the beat or the word | `review window F`, `review sync --events cuts,text` | `bc:beat-cut`, `bc:captions-text` |
| text in a zone, too small, overlap, contrast | `ui frame F --phone`, `review layout --frame F --contrast` | `bc:captions-text` |
| no hook, slow opening | `review shots --to F`, `review layout --to F --ink`, `transcript words --to F`, the first cells of the sheet | story (`bc:edit-workflow`), `bc:captions-text` |
| dead air, music gaps, voice drowned | `review window F`, `audio mix-measure` (a job) | `bc:audio-mix` |
| loudness, true peak | the normalized draft, `platforms get <id>` | `bc:audio-mix` |
| colour jumps between clips | `color measure --by clip`, `ui frame F` | `bc:color-grade` |
| a promised shot or line missing | `review coverage`, `script check` | `bc:rough-cut`, `bc:stock-images`, ask |
| a reference style drifts | `review compare --reference ID --ours ID` | `bc:style-study` |
| a plugin's issue (`source`) | that plugin's skill | its `fix` |

## Rounds and stopping

- Cap: 1–3 rounds (T00 §3, T16 §3), never more than `workflow gates` › `maxReviewRounds` (the user's setting).
- From round 2, run `review run --summary --since-rev R` (R = the revision of the previous round): it returns
  `diff {fixed, new, persisting}` and the round number. First confirm the previous fixes; then **only a new blocker
  fails the round**. New polish and taste findings are listed, not chased (T16 §2, reelmimic): rubric creep is how
  loops never end.
- Stop early when a round fixes nothing. Whatever is left goes to the user with reasons, never silently shipped.

## Accept with a reason

A warning or info that is right for this video is kept on purpose:
`review accept <id> --reason "locked-off interview, chosen" --base-rev N`. Later runs show it with the reason, leave
it out of the counts, and the export report lists it. Errors cannot be accepted: fix them, or change their severity
in `review.severities` with a reason and tell the user. `review accept <id> --remove --base-rev N` counts it again.

## The draft

Loudness and the delivered file are measured from a normalized export of this revision, so make it last, then
review once more and request G5 (`bc:edit-workflow`):

```sh
bashcut export start --preset quick-draft --name draft-v1 --include-srt --normalize-audio
bashcut export status                      # also the delivered-file checks: stream starts, drift, fps, size
bashcut review run --summary --min-severity warning
```

## Report

Report the loop in a few lines, from `run log` and the last `review run --summary`: rounds; what was fixed
(issue → edit → `review verify` numbers); profile changes with the reason; every accepted issue with its reason;
`needs_user`; and coverage: copy `checks.notChecked`, `failed` and `unreliable`, and say "not listened to" for sound
you could not hear. Example: "Review: 2 rounds. Closed a 1.2 s black gap at 0:41 (verified: 0 black frames), raised
the caption out of the Reels bar. Kept: the 9 s shot at 0:12 (locked-off interview). Not checked: the music under
your voice by ear; the face-overlap check (no provider)." Log it: `run append measured --measured … --not-measured …`.
