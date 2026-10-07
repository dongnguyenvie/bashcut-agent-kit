---
name: rough-cut
description: Build the rough cut in BashCut by choosing moments by what is said — read the transcript, pick lines by quote, resolve each quote to a word-exact source range, store it as a select with its quote, reason and evidence, let the user override in the Media panel, then place the kept selects in story order. Also long → short — finding self-contained clips in a podcast, talk, stream or long recording, a blind second pass with verdict tiers, the standalone test, length and padding ranges, and one derived project per short. Use at the rough-cut stage of a talking video, tutorial or interview, when cutting a long recording into shorts, or when cuts land inside words. Triggers: "cắt thô", "rough cut", "chọn đoạn", "lọc câu hay", "cắt podcast thành short", "cắt clip ngắn từ video dài", "highlight", "selects", "cắt giữa chữ".
---

# Rough cut by quote

Reply in the user's language. With a `[Scope]` (Send to Agent), work only on those items (`bc:edit-workflow`).

You choose by **text**; BashCut turns the text into frames and tells you where an edge falls inside a word or a
sentence. Never type timestamps from memory or from SRT lines: tools that let the model write times are off by
0.6–1.5 s (T06 §4). Core resolves and measures; it never ranks or picks. The ranges below are starting points with
their source; choose within them for this footage.

A rough cut is selection and order only: no music, titles, grade or effects unless the user asks (T06 §4). Be
generous on the first pass and tighten later: a discarded moment is slow to find again (T06 §2).

## Before selecting

1. Transcripts: `media transcribe --media ID` (a job; needs a `captions.transcribe` plugin) for each talking file,
   then read it in its own seconds: `media transcript --media ID --as text --format text` (one line per phrase).
2. Sound and gaps: `media speech-map --media ID` gives speech spans and gaps with the calibration it used. When it
   says there is no separation (music or noise under the voice), it gives no gaps: do not invent them.
3. Classify the source (T06 §4): **words** (the content is what is said: talks, interviews, tutorials), **reactions**
   (laughter, surprise: watch the picture; laughter and "clip that" lag the moment they react to) or **visual**
   (demonstrations, sport: the transcript is weak evidence, use the survey's descriptions).
4. Read the brief and plan (`project brief`, `plan get`): the length range, the outputs and the sections decide
   what is worth keeping.

## The select-by-quote loop

For each moment you want:

```sh
bashcut media resolve-range M3 --quote "the first time I opened the app it crashed"
```

It returns `from`/`to` seconds, in and out frames, the matched text, and for each edge `midWord`, `midSentence`
(inside a transcript phrase) and the nearest word and sentence edges before and after. Equal matches are listed in
`alternatives`, in order, never ranked: pick by context. Instead of a quote you can give `--words FIRST-LAST`
(indices from `media transcript --as words`) or rough `--from`/`--to` seconds, which snap outwards to the words.

- `matched` is the share of the quote's words heard in place. Under 1, read `text`: a misheard word is fine, but a
  range that holds only one or two of your words means the quote is not there; never place it.

- An edge `midSentence` is allowed only when you mean it (a deliberate interruption). Otherwise move it to the
  nearest sentence edge the result gives and resolve again.
- **Padding** (T06 §3): start 50–150 ms before the first word, end 80–300 ms after the last. Tighter for montage
  energy; looser for documentary, trailing reactions, and synthesized or AI speech. Never past the next word's start.
- **Gaps as cut points** (T06 §3, video-use): ≥400 ms of quiet is a clean cut; 150–400 ms needs a look at the picture;
  <150 ms is unsafe. Whisper-style word ends hide pauses, so trust `media speech-map` gaps over word ends (T06 §4).
- **Takes**: default to the last complete take ("people warm up", T06 §3), then confirm by reading or asking. A
  fluent take is not always the better one.
- **Long lifts**: removing more than 10–20 s at once needs a look (T06 §3): quiet is not empty picture in a screen demo.

Store what you chose as selects, with your reasons, as one edit:

```sh
bashcut selects set selects.json --base-rev N
```

```json
[
  {"media": "M3", "from": 61.42, "to": 74.9, "quote": "the first time I opened the app it crashed",
   "reason": "hook: the problem in one sentence", "evidence": "resolve-range: edges on sentence ends; gap after 0.6 s"},
  {"media": "M3", "from": 210.1, "to": 236.3, "quote": "so we rebuilt the import from scratch",
   "reason": "section 2: the fix", "evidence": "last complete take of three", "mustKeep": true}
]
```

New selects get an ID and status `candidate`. `order` sets the placing order (default: source start), so give it
when the story order differs from the recording order. The user sees the selects in the Media panel (Selects) and
can keep, reject or reorder them there: before placing, read `selects list` again and follow their choices. Never
undo a user's rejection; ask instead.

Keep and reject with a reason: `selects mark S1,S4 --status kept --reason "hook and payoff" --base-rev N`. Mark the
lines the edit cannot lose: `selects mark S2 --must-keep true --base-rev N`; a must-keep select that no clip plays
becomes a review warning after every later change.

## Blind second pass (long → short, or many candidates)

Propose about 2× the clips you need (T06 §3): 30–45 % of AI picks are duds (hotclip, T06 §3). Then judge them
blind: a fresh sub-agent (or you, deliberately ignoring your reasons) gets each candidate's text with one sentence
of context on each side (`media transcript --media ID --from S --to E`) and returns a verdict with one sentence why:

- **publish**: stands alone and pays off; mark `kept`.
- **review**: promising but needs a trim, a different start or the user's eye; keep `candidate` with the note.
- **drop**: fails the standalone test or quote-mines; mark `rejected` with the reason.

Prefer these tiers to a weighted score (T06 §3). Ranking by score breaks story order; a highlight batch kept in
recording order hides the best clips: order by narrative for one video, by strength for a batch (T06 §2).

### The standalone test

A clip shown without the rest must make sense (T06 §2, openmontage):
- no unresolved "he", "this", "that one" pointing to something outside the clip;
- no reference to earlier context ("as I said");
- no long lead-in before the point; the setup, turn and payoff are inside;
- it does not stop before the payoff or on a comma;
- a stitch of two ranges never makes a meaning that was not said: do not stitch across a "but" or "however" (T06 §2).

## Length

Length follows the moment: setup + turn + payoff, then capped by the platform (T06 §3).

| Kind | Range | What moves it |
|---|---|---|
| vertical short | 15–90 s | one-liners shorter, story arcs longer; cap from `platforms get <id>` (hard vs recommended) |
| topic or chapter clip | 1–6 min | source length and platform |
| sum of selects vs the plan's length | ±10–15 % | report the drift; strict for fixed slots (T06 §3) |
| yield from a long source | no quota; often about 1 per 2–10 min | report the candidate count and why you kept N (T06 §3) |

Never cut natural speech short to hit a quota or a "sweet spot" (T06 §4).

## Placing and checking

```sh
bashcut selects place --base-rev N                 # kept selects on Main, in order, one undoable edit
bashcut timeline get --format text
bashcut timeline sheet --cuts
```

For one range without selects: `media place --media M3 --from 61.42 --to 74.9 --base-rev N`. Before any later
trim, `timeline apply ops.json --base-rev N --dry-run` reports `cutsInsideWord`; fix those before applying.
`captions find "words as said"` finds where a line now plays on the timeline. A cut inside a word is a review error
(`bc:review`); look at doubtful cuts with `review window F`.

Then request **G3** (`bc:edit-workflow`): `checkpoint request G3 --summary "<duration> against <plan range>, N
selects, what was dropped and why" --attach <sheet path>`. Wait for the user's answer before rhythm, sound and text.

## Several shorts from one source

Make one project per short instead of cutting them all on one timeline:

```sh
bashcut selects list --status kept
bashcut project derive                              # a sibling project per kept select
bashcut variants list                               # the derived projects and variants next to this one
```

Each derived project has the same canvas, outputs, review profile, brief and layers, only that media and the
select's range on Main, and records where it came from. `project derive --ids S1,S5` derives only those. The open
project does not change: open each derived project (`project open <path>`) and finish it through the stages of
`bc:edit-workflow` (its own hook, captions and review). To compare two versions of one short, `variants create`
records what one variant changes, and `variants diff` shows the difference.

Log it: `run append stage --stage rough-cut --text "20 candidates, 9 kept, 3 shorts derived"`.
