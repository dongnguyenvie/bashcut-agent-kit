---
name: motion-graphics
description: Add designed, animated graphics to a BashCut edit — checklist and stat cards, counters, lower thirds, simple diagrams and kinetic type over footage — decide whether a sentence needs one, anchor it to the payoff word, hold it through the narration, and render anything native text cannot do as a transparent HyperFrames overlay (.mov with alpha) placed on the Overlay layer. Use when the user asks for "đồ hoạ", "motion graphic", "thẻ thông tin", "card", "checklist", "số liệu chạy", "counter", "lower third", "infographic", "animation chữ", or when an explainer, tutorial or review needs the example, number or relationship the words don't show.
---

# Motion graphics

Reply in the user's language. With a `[Scope]` (Send to Agent), work only on those items (`bc:edit-workflow`).
Numbers below are ranges with their sources (T13 = the motion-graphics study, T22 = the renderer study); choose
inside them from this video's speech, genre and frame, and say why. Captions and plain titles are
`bc:captions-text`; transitions and punch-ins are `bc:effects`.

## 1. Does this sentence need a graphic?

A graphic shows what the words don't: the example, the number, the relationship, the consequence. Before adding
one, read the words (`transcript words --from F --to F2`) and ask what the speaker just made the viewer imagine.
- Skip it when the card would restate the caption: captions and on-screen text take one role each, never both
  (openmontage). Leave some sentences bare so the next card lands (ghost-editor).
- Change the graphic when the content changes, never on a timer ("every 15 s" is an anti-pattern, digitalsamba).
- Graphics over talk keep the voice under them; never cut to a silent standalone card (vibetube).
- Vary the device; the same card on every point reads as a template (T13 anti-patterns).

## 2. Pick the cheapest tool that does it

1. **Native text** (`bc:captions-text`): titles, labels, keyword stickers, place and chapter cards, with
   `textStyle` plates, accent bars, keyframes and motion presets. Editable, no render. First choice.
2. **A library item**: `library list --panel stickers` / `--kind text-preset` for a saved card or alpha movie.
3. **A HyperFrames overlay** (below): layout and motion text items can't do — a checklist that ticks, a counter, a
   bar chart, a diagram that builds. Rendered once into a `.mov` with alpha; re-render after its words change.
Say which you chose and why.

## 3. Timing (anchor to words, not seconds)

| What | Range | Sources and why it varies |
|---|---|---|
| Entrance lands on the payoff word | entrance end = the word's start; entrance 0.15–0.6 s | video-use, vibetube (~0.4 s), student-kit (0.15–0.6 s); shorter for energetic cuts, ≤0.15 s for impacts |
| Hold, one idea | 3–8 s, and at least its narration + about 1 s | video-use (floor 3, simple 5–7), vibetube (≥ narration + 1 s), openmontage (3–5 s). **Contradiction:** openmontage's 3–5 s cap vs vibetube's "cover the whole narration": tie the hold to the narration span |
| Hold, diagram that builds | 8–14 s | video-use; complexity and words on it |
| Accent hit | 0.5–2 s, recognisable not readable | video-use, openmontage; only for emphasis or music hits |
| Final-frame hold | 0.5–1.5 s | video-use (≥1 s); longer for a number the viewer must remember |
| Stagger between elements | 0.06–0.10 s opener, 0.3–0.4 s narrative, 0.5–0.6 s dramatic | student-kit; one new element at a time when each is read |
| Entrance / exit | 0.2–0.8 s / 0.15–0.5 s, entrance stronger | talkcraft |
| Words on a card | ≤ about 2–3 per second of hold | student-kit, guizang (6–9 CJK chars/s); measure the real text |
| Density, talking footage | 3–8 graphics a minute, sparser for long videos | openmontage (3–6/min), hyperframes (card every 6–20 s by length); high for tutorials and explainers, low for vlogs and when the face carries the emotion |
| First graphic | within the first ~5 s, usually the hook title | vibetube |

Taste stated as law ("never linear", "no bounce") is not a rule: linear is right for constant pans and counters;
overshoot 1.05–1.12 suits playful, none suits calm or premium (shotcraft, saas).

Steps: `transcript words` → the payoff word's timeline frame W → entrance length E (frames) → overlay starts at
W − E (the composition's own entrance takes E) → hold until the narration it illustrates ends + 0.5–1 s.

## 4. Render a HyperFrames overlay

HyperFrames (Apache-2.0) renders HTML/CSS + GSAP in headless Chrome. Needs Node.js (`npx`); without it, use native
text and say so. `render-overlay.sh` renders RGBA frames and encodes HEVC with alpha (small) or ProRes 4444
(`--codec prores`, ≈75× larger) with AVFoundation; telemetry is off.

```bash
S="<skill_dir>"                                   # the folder this SKILL.md is in
mkdir -p /abs/project/graphics && cp -R "$S/card" /abs/project/graphics/packing   # a starting point
# edit /abs/project/graphics/packing/index.html: size on html/body/#root = the project canvas, data-duration = hold
"$S/render-overlay.sh" /abs/project/graphics/packing /abs/project/graphics/renders/packing.mov \
  --fps 30 --variables '{"title":"Đồ cần mang","items":["Hộ chiếu","Sạc dự phòng"]}'
bashcut library add --kind sticker --name "Packing card" --file /abs/project/graphics/renders/packing.mov
bashcut library place packing-card --at-frame F --size 1 --position center --base-rev N
```

- Place it through `library add --kind sticker` (it checks the alpha channel and marks the media `alpha`, so the
  preview keeps the transparency); `media import` does not.
- `--size 1` when the composition is the full canvas (the card's position lives in the HTML). Match the canvas and
  fps of the project (`project get`); a 1080×1920 4 s card renders in about 10–20 s and is about 0.5 MB as HEVC.
- Composition rules (hyperframes): every frame is a pure function of time — one paused GSAP timeline registered in
  `window.__timelines["main"]`, no clocks, `Math.random`, video or network; fonts and scripts local. The body stays
  transparent; the card carries its own plate (opacity 0.75–0.9 reads over busy footage).
- Text: Vietnamese needs a font with full diacritics (system Helvetica Neue / Arial / SF work); keep 60 px+ from
  the frame edges and out of the platform's bottom band (`platforms get <id>` › safe zones).
- `npx --yes hyperframes@0.8.140 lint <dir>` before rendering; `check` also measures contrast and overflow.
- The user's own Remotion or HyperFrames project: they render it themselves (ProRes 4444 or HEVC with alpha) and you
  import the file as above. Never run Remotion renders for them (its licence, T22).

## 5. Check

- Look at the landing frame and a strip across the entrance: `ui frame W --phone`, `ui frames --frames
  W-E,W,W+15`. The card must be readable at phone size, land on the word and leave the face clear (`media subjects`
  boxes vs the card's rectangle).
- `review layout --from F --to F2` for the native text around it; `review shots` sees the overlay as a layer.
- Re-timing the voice moves words but not the overlay: after cuts in that range, re-read `transcript words` and move
  or re-render the card.

## Report

Which sentences got a graphic and why, the tool for each (native, library, rendered), its timing against the word,
the render numbers (seconds, size) and what was left bare on purpose.
