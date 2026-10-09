---
name: motion-graphics
description: Add designed, animated graphics to a BashCut edit — checklist and stat cards, counters, lower thirds, simple diagrams and kinetic type over footage — decide whether a sentence needs one, anchor it to the payoff word, hold it through the narration, and make anything native text cannot do with a graphics plugin (`graphics.render`, such as HyperFrames Graphics: a composition the agent designs, rendered to a .mov with alpha). Use when the user asks for "đồ hoạ", "motion graphic", "thẻ thông tin", "card", "checklist", "số liệu chạy", "counter", "lower third", "infographic", "animation chữ", or when an explainer, tutorial or review needs the example, number or relationship the words don't show.
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
3. **A designed graphic from a `graphics.render` plugin** (§4): any layout and motion text items can't do — kinetic
   type, a counter or chart, a pointer that clicks, a mock screen, a full-frame card, a diagram that builds, the
   speaker shrinking into a card. Rendered once into a `.mov` with alpha; re-render after its words change.
Say which you chose and why. Designing well beats the cheapest tool when the reference or the genre is
graphics-led: a dense explainer short built on designed type and cards needs §4 for most of its sentences.

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
| Density, talking footage | 3–8 graphics a minute, sparser for long videos; a measured reference replaces it | openmontage (3–6/min), hyperframes (card every 6–20 s by length); high for tutorials and explainers, low for vlogs and when the face carries the emotion. Graphics-led explainer shorts run far above: one measured reference changed the picture every ~1.6 s with about 30 graphics a minute (blycreativs before/after, 2026-10-09). Take the number from `bc:style-study` when the user gives a reference |
| First graphic | within the first ~5 s, usually the hook title | vibetube |

Taste stated as law ("never linear", "no bounce") is not a rule: linear is right for constant pans and counters;
overshoot 1.05–1.12 suits playful, none suits calm or premium (shotcraft, saas).

Steps: `transcript words` → the payoff word's timeline frame W → entrance length E (frames) → overlay starts at
W − E (the composition's own entrance takes E) → hold until the narration it illustrates ends + 0.5–1 s.

## 4. Make it with a graphics plugin

Graphics that native text cannot make come from a plugin that provides `graphics.render`; this kit only decides
what, where and when. `bashcut plugins list` shows whether one is ready:

- **HyperFrames Graphics** (`bashcut.hyperframes`): its skill `bashcut.hyperframes:hyperframes` is the toolkit —
  design the composition for this video (HTML/CSS + GSAP, its examples and a catalog of 390+ blocks as raw
  material), look at frames (`snapshot`, also against a reference), render (`bashcut plugins invoke graphics.render`)
  and place it. Read that skill before building the first graphic.
- None ready: `bashcut plugins search --capability graphics.render` names one to install; installing, trusting and
  Install Dependencies… are the user's (`bc:edit-workflow`). Meanwhile use native text and say what is missing.
- The user's own Remotion or After Effects project: they render it themselves (ProRes 4444 or HEVC with alpha) and
  you import it with `library add --kind sticker --file` (keeps the alpha). Never run Remotion renders for them (its
  licence, T22).

Hand the plugin a brief, not a template: the words and the payoff word's frame, what the viewer should see, the
hold, and the look (style profile, reference frames, the video's own titles).

## 5. Check

- Look at the landing frame and across the entrance: `ui frame W --phone`, `review window W --span E`. The card must be readable at phone size, land on the word and leave the face clear (`media subjects`
  boxes vs the card's rectangle).
- `review layout --from F --to F2` for the native text around it; `review shots` sees the overlay as a layer.
- Re-timing the voice moves words but not the overlay: after cuts in that range, re-read `transcript words` and move
  or re-render the card.

## Report

Which sentences got a graphic and why, the tool for each (native, library, rendered), its timing against the word,
the render numbers (seconds, size) and what was left bare on purpose.
