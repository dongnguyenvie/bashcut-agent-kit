---
name: bashcut-effects
description: Pick the right editing effect for the moment and genre (food, travel, daily vlog, review/unboxing, product ad, talking head, real estate, event/MV) and make it with BashCut's native tools — transitions (dissolve, whip, blink, zoom, spin, shutter, wipe), speed ramps, freeze frames, reverse, punch-in, split moments, text presets, stickers and matching SFX — or say plainly when an effect is not possible yet. Use when the user asks "hiệu ứng", "effect", "chuyển cảnh", "transition", "speed ramp", "freeze", "chữ nhảy", "làm giống CapCut", or when a cut feels flat and needs emphasis.
---

# Effects: when, then how

Reply in the user's language. Decide **when** first; most cuts should stay hard cuts.

## When

- **Effects serve a moment, not the whole video.** One or two special transitions per video (the hook, a
  location change); everything else is a hard cut on a sentence, a beat or an action.
- **Choose the transition by how different the shots are:** new place → whip, shutter or cover-the-lens; same
  place with a time skip → blink or a jump cut; product or dish reveal → speed ramp or freeze into the reveal
  with a hit.
- **Every visual motion gets a matching sound**, sized to it (see `bashcut-audio-mix`). Punchline → cut all music and
  SFX for 1–2 s.
- Whip pans move the same direction on both sides of the cut.
- Cinematic style is the opposite: hard cuts, no whoosh on cuts, one special transition per video; the colour
  look and serif captions carry the feel.

| Genre | Fits |
|---|---|
| Food / travel | whip, cut on action, place cards, pop stickers, speed ramp on food action, build-up → reveal |
| Review / ads | freeze + label, price as a keyword sticker, reverse-into-hand hook |
| Talking head | jump cuts with punch-in, keyword stickers, few transitions |
| Real estate | slow speed, keyword stickers for price and area |
| Event / MV | beat cuts, flash, blink, speed ramps |

## How, in BashCut

| Effect | Make it with |
|---|---|
| Transition | `{"op":"upsertTransition","id":"t-hook","kind":"whip","from":"A","to":"B","duration":12}` (clips adjacent on one video layer; kinds: dissolve, whip, blink, zoom, spin, shutter, wipe) |
| Speed ramp | `clip speed-curve ITEM --preset hero` (montage, hero, bullet, jump-cut, flash-in, flash-out) or `--points '[[0,1],[0.5,3],[1,1]]'` |
| Constant speed | `clip speed ITEM --speed 2` (length follows; `--keep-duration` keeps it) |
| Reverse | `clip reverse ITEM` (job) |
| Freeze frame | select the clip, playhead on the frame, `ui action clip.freeze` |
| Punch-in / reframe | `setProperties` `{"reframePreset":"close","transform":{"zoom":1.3,"pan":0,"tilt":0}}` |
| Picture in picture, split moment | the second clip on an overlay layer with `transform` zoom below 1 and pan/tilt |
| Black-and-white moment | `adjustment add --look black-white` over the range |
| Pop text, labels, prices | text items with `hook-title`, `keyword-sticker`, `place-card` (`bashcut-captions-text`) |
| Stickers | Stickers panel (emoji text items) |
| Fade from/to black | `dissolve` against a black clip, or audio `fadeIn`/`fadeOut` for sound |

Speed changes break lip sync: use them on b-roll and action, not on talking shots. Real slow motion needs
50/60/120 fps sources; slowing 30 fps footage below ~0.5× stutters.

## Not possible yet — say so and offer the alternative

- Animated position, scale or opacity over time (keyframes): no Ken Burns, sliding text or zoom animation.
  Alternatives: a speed ramp, a static punch-in on the next cut, or a `zoom` transition.
- Word-by-word animated captions, typewriter, counting numbers, shake, glitch, film grain.
- Segmentation (text behind a person, cut-outs), motion tracking, AI-generated transitions.
- Still images on the timeline (see `bashcut-stock-images` for the workaround).

When the user needs one of these, note it as a feature request for BashCut (or a plugin action) rather than
faking it with a pre-rendered file.

## Verify

Render frames just before, inside and after each effect with `ui frame F` and read them; `timeline get` lists
the transitions you added. Ask the user to listen to the matching sound.
