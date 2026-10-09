---
name: visual-plan
description: Decide what the viewer sees on every line of a video where words carry it, before building anything — read the script or the transcript line by line, give each line one treatment (the speaker, a punch-in, own B-roll, stock, an icon, native text, a designed graphic, a generated shot, a screen, or nothing on purpose) with what it shows, the word it lands on and why, research and look at candidates, balance density, variety and the speaker's presence over the whole video from the reference or the recipe, write plan.visuals, then hand each row to the skill that builds it. Use after the cut is locked in a talking head, tutorial, explainer, review, podcast clip or an ad with voiceover, when a reference is graphics-led, or when the user asks what to show over a script. Triggers: "minh hoạ", "kế hoạch hình ảnh", "câu này hiện gì", "b-roll cho script", "visual plan", "illustrate the script", "làm giống video mẫu", "thêm hình cho lời nói".
---

# Visual plan

Reply in the user's language. With a `[Scope]` (Send to Agent), plan only those lines (`bc:edit-workflow`).
Each building skill (`bc:stock-images`, `bc:motion-graphics`, `bc:effects`, `bc:captions-text`) decides well for
one moment; this skill decides for the whole video first, so the treatments vary, land on the words and add up to
the density and the look the video needs. It plans and researches; the building skills build.

## 0. When and where

The stage `visuals`, added by the plan after the cut is locked (the words and their frames no longer move) and before
sound and captions (SFX and the caption mode depend on it):

```sh
# --merge replaces top-level fields whole: read plan.stages (context get), add the key, write all of stages back.
# stages.json: {"stages": {…the recipe's stages…, "visuals": {"after": "voiceover", "required": true, "why": "talking video"}}}
bashcut project set-data plan stages.json --merge --base-rev N
```

Add it at the story stage for any video whose words carry it; skip it (no stage) for a music montage or a vlog told
by the pictures. A BashCut that ignores `after` lists the stage before review: do it after the cut anyway.

## 1. Read what is said and what exists

- The lines: `bashcut transcript words --from F --to F2` (or the script's beats with their ON SCREEN notes from
  `bashcut.vlog:hook-script`). Split into lines at sentence or idea boundaries; keep each line's first and last word
  frames.
- What the footage already shows: the survey's described shots (`bashcut review coverage`, `media describe`), and
  `timeline sheet --cuts --text` for what is on screen now.
- The targets: a reference's measured profile (`bc:style-study`: picture change interval, graphics a minute, share
  of time the speaker is on screen, text mode), else the recipe's ranges, else the kit's (`bc:motion-graphics` §3,
  `bc:effects`). Write each target with its source.

## 2. One treatment per line

Ask of every line: what does the viewer imagine here, and does the picture already show it? Then choose.

| Treatment | Shows | Built with |
|---|---|---|
| `speaker` | the face carries it: an opinion, a feeling, the punchline | nothing added |
| `punch-in` | the same shot, closer, on the line's strongest word | `bc:beat-cut`, `bc:effects` |
| `own-broll` | a shot from the user's footage of what is said | `bc:rough-cut`, `media place` |
| `stock` | a photo or video of a thing, place or action the footage lacks | `bc:stock-images` |
| `icon` | a small symbol: money, time, place, yes/no, an arrow | `bc:stock-images` (Iconify) |
| `text` | the keyword, a number or a label as native text | `bc:captions-text` |
| `graphic` | designed motion: kinetic type, a counter or chart, a pointer clicking, a mock screen, a card, a diagram, the speaker shrinking into a card | `bc:motion-graphics` → a `graphics.render` plugin |
| `generated` | a shot that cannot be filmed or found | `bashcut.vlog:scene-prompt`, `library generate` |
| `screen` | a screen recording or screenshot of what is explained | `media place`, `bc:effects` (focus) |
| `none` | the line stays bare on purpose so the next one lands | — |

These are the common ones, not a closed list: a new treatment is fine with a name, what it shows and who builds it.
Combinations are one treatment (a `stock` photo with a `text` keyword on it is `stock`, with `show` saying both).

Guides, not rules:
- Concrete words (a thing, a number, a place, a step, a comparison) can be shown; abstract or emotional lines are
  usually the speaker's.
- A number reads best counted or written; a process as steps or a diagram; a comparison side by side; a named object
  as the user's own shot first, then stock, then an icon.
- Anchor each row to one word (`at`): the visual lands on it, entrances end on its first frame. Hold until the idea's
  narration ends, unless the treatment is an accent.
- Text and captions never say the same thing twice: decide the caption mode here (full captions, keywords only,
  none) and write it into `stages.captions.rules` (with the rest of `stages`, as in §0).

## 3. Balance the whole video

Lay the rows end to end and check them against the targets before researching anything:
- **Density and interval**: picture changes and graphics per minute within the target; nothing in the hook's first
  1–3 s that does not serve the hook.
- **Variety**: the same treatment on three lines in a row reads as a template unless the reference does exactly
  that; vary the device within a treatment too (a counter, then a card, then type).
- **Presence**: the share of time the speaker is on screen within the target; keep the face on lines that carry
  emotion, the hook's promise and the payoff.
- **Faces and safe areas**: nothing covers the face while it speaks the point (`media subjects`).

Change rows until it fits, and say which targets you left on purpose (`"deliberate": true` with the reason).

## 4. Research and look

For rows that need something the project does not have:
- `stock`, `icon`: 3–6 candidates per row (`bc:stock-images` §1 and Icons), all candidates of a batch on one
  contact sheet; look, pick, import the pick (`media import`, its licence and source go on the media as usual).
- `own-broll`: the matching described shots; check the frame (`media frames --sheet`).
- `graphic`: the graphics plugin's examples and catalog (`bashcut.hyperframes:hyperframes` §1); note which one each
  row starts from, or that it is new. Design happens when it is built.
- `generated`: say the prompt idea; generation and any price wait for the build (paid providers: `--dry-run`).

A row with no good candidate changes treatment (often to `text` or `speaker`) rather than keeping a weak picture.

## 5. Write the plan

```sh
bashcut project set-data plan visuals.json --merge --base-rev N
```

`visuals` is a list of rows, in time order:

```json
{"visuals": [
  {"line": "one of the best ways", "from": 0, "to": 36, "at": 12, "treatment": "graphic",
   "show": "serif lead-in, 'Best ways' slams in lime", "why": "the hook's claim, made to read in 1 s"},
  {"line": "to start getting more views", "from": 36, "to": 81, "at": 66, "treatment": "graphic",
   "show": "paper card turns in, 'more views' builds word by word", "why": "pattern break after 1.2 s of face"},
  {"line": "which can boost", "from": 186, "to": 216, "at": 201, "treatment": "punch-in",
   "show": "1.12× on 'boost'", "why": "a strong verb the face sells"}
]}
```

`from`/`to`/`at` are timeline frames; `show` is one phrase of what the viewer sees; `why` is the line's need, not the
treatment's name. Where the picture comes from and its licence live on the imported media, not here.

Gate: when the brief asks to approve visuals, or rows need paid generation, request
`bashcut checkpoint request visuals --summary "<rows by treatment, targets>" --attach <contact sheet>`; otherwise go
on (`bc:edit-workflow`, Gates).

## 6. Hand off and close

Build in this order, each row by its skill, reading `plan.visuals` for its rows: picture that replaces a moment
(`own-broll`, `stock` video, `screen`) → `graphic` → `stock` photos and `icon` → `text` → `punch-in`. Sound for each
visual (a pop, a whoosh, a click) is `bc:audio-mix`'s, at the row's `at`.

```sh
bashcut run append stage --stage visuals --status done --evidence "plan.visuals 24 rows;renders/visuals-candidates.jpg"
```

The draft review compares the timeline with `plan.visuals` (a row not built, a visual off its word by more than
0.3 s, a row built over a face).

## Report

The targets and where they came from, the rows by treatment with the shares (speaker on screen, graphics a minute,
mean picture change), what you researched and rejected, the caption mode, and the targets you left on purpose.
