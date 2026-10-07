---
name: effects
description: Pick the right editing effect for the moment and genre (food, travel, daily vlog, review/unboxing, product ad, talking head, real estate, event/MV) after reading what the cut already uses (review shots), and make it with BashCut's native tools — camera-like moves (punch-in, Ken Burns, keyframe zoom/pan, focus on a screen panel), speed and time (speed ramps, fast-forward, slow motion, freeze, reverse), graphic moves and transitions (dissolve, whip, blink, zoom, spin, shutter, wipe, animated titles, stickers, word-by-word captions) with matching SFX, and reframes that crop only to what matters in the frame — or say plainly when an effect is not possible yet. Use when the user asks "hiệu ứng", "effect", "chuyển cảnh", "transition", "speed ramp", "freeze", "chữ nhảy", "làm giống CapCut", "zoom vào màn hình", "tua nhanh", "cắt khung dọc", "reframe", or when a cut feels flat or repetitive and needs emphasis.
---

# Effects: look, then when, then how

Reply in the user's language. Decide **when** first; most cuts should stay hard cuts. With a `[Scope]` (Send to
Agent), work only on those items (`bc:edit-workflow`).

Numbers here are ranges with where they come from (T08 effects, T07 pacing, T19 reframing: the kit's research
notes; the names inside are the editors' kits they were seen in). They are starting points: a measured reference
(`bc:style-study`) or the user's taste wins. Look before fixing: measure → choose → act → measure again.

## 1. Read what the cut already does

```sh
bashcut review measure              # job: picture motion per shot (needed for motion in review shots)
bashcut review shots --summary      # per shot: motion, cameraMove (perSecond, ease), speed, described size/move, and the cut
                                    # into it: kind, framingBefore/After, sameFraming; transitionIn {kind, duration, easing}; shares
```

Count kinds and runs yourself from each shot's `cut.kind`. Look for runs of one transition kind, neighbouring cuts with `sameFraming`, every shot with the same
`cameraMove` (one failure seen: all 12 shots a push-in, vox-director; T08 §2), one ease on most moves, and long
stretches with no motion. For each, decide **motif or mistake**; a motif is fine when it is a choice. Other kits
warn on: the same transition on two consecutive cuts, one kind used more than 2× in a film under 60 s (3 when
longer), fewer than 3 families when there are 5+ cuts, one ease on more than half the moves (saas-motion-kit
`variety_audit`; T08 §2). Treat them as prompts to look, not rules.

## 2. When

- **Effects serve a moment, not the whole video.** Special transitions: 1–3 per minute of short form, 0–1 in
  documentary or cinematic work (saas-motion-kit, openmontage, hyperframes; T08 §3). Everything else is a hard cut
  on a sentence, a beat or an action. Sources disagree on hard cuts: speech-led, documentary and cinematic edits
  keep most cuts hard; motion-graphic and short-form ads rotate flavours (T08 §3).
- **Choose by what the cut means**, never by rotating through kinds by shot number (student-kit; T08 §4): new place
  → whip, shutter or cover-the-lens; same place with a time skip → blink, dissolve or a jump cut; product or dish
  reveal → speed ramp, freeze or zoom-hit into it. A dissolve says time passed; between takes of one sentence use a
  snap punch-in instead (ghost-editor; T08 §3).
- **Never use a flash or transition to hide a missing action** or a moment that should be seen (ReelMimic; T08 §2).
- **Every visible move gets a matching sound**, sized to it (`bc:audio-mix`). One example: on a punchline, cutting
  all music and SFX for 1–2 s worked.
- Cinematic style: hard cuts, no whoosh on cuts, the colour look and serif captions carry the feel.

| Genre | Fits |
|---|---|
| Food / travel | whip, cut on action, place cards, pop stickers, speed ramp on food action, build-up → reveal |
| Review / ads | freeze + label, price as a keyword sticker, reverse-into-hand hook |
| Talking head | jump cuts with punch-in, keyword stickers, few transitions |
| Real estate | slow speed, keyword stickers for price and area |
| Event / MV | beat cuts, flash, blink, speed ramps |

## 3. Motion in three families

**Camera-like moves** (zoom, pan, tilt, rotation over a shot). Sources mix three different moves (T08 §3):

| Move | Range | Source |
|---|---|---|
| Slow drift, Ken Burns | 0.3–1.5 %/s, about 1.03–1.07 over a shot; alternate direction between shots | talkcraft, jianshuo, digitalsamba |
| Snap punch on a word | 1.1–1.15 | kinocut, ghost-editor |
| Size change at a cut | 1.15–1.3, capped by headroom | vlog talking-head recipe, kit beat-cut; see `bc:beat-cut` |
| Beat pulse | ≤2% as texture; full-frame impacts at most 3 per film, ≥16 beats apart | bestagentkits, guizang |

- The ceiling is resolution, not taste: read `scale.maxZoomNative` and `pixelRatio` per clip in `timeline get` or
  `review shots`; past 1 output pixel per source pixel it upscales, so look at `ui frame F` before keeping it.
- State drift as a rate so short and long shots feel alike: end zoom = 1 + rate × seconds (0.5 %/s over 8 s ≈ 1.04).
- Two moves in a row read as a glitch: merge them into one gesture and front-load the travel (student-kit). Ease
  out on entrances, ease in on exits, linear only for a constant drift (T08 §3).
- After applying, `review shots` shows each `cameraMove` with `perSecond`: check it against the range you chose.

**Speed and time.** Speed changes break lip sync: use them on b-roll and action, not on talking shots.

- Real slow motion needs 50/60/120 fps sources (`media analysis --media ID` tech facts); slowing 30 fps footage
  below ~0.5× stutters (our edits; T08 §3).
- A clip a few frames short: slow it slightly instead of freezing on its last frame (vox-director stretches by
  ~1.02–1.1; T08 §3).
- Fast-forward: 1.5–2× when narrated over, 4–20× for silent waiting (digitalsamba, vlog tutorial; T19 §3).
  `setSpeed` takes up to 16×. One example: a 65 s typing stretch read clearly at 18× (3.6 s) with no presenter
  or captions and one label saying what happens.

**Graphic moves and transitions.** Durations in seconds: frames change meaning with fps (T08 §3).

| Kind | Length | Source |
|---|---|---|
| Whip | 0.2–0.4 s; 1–2 per short; same direction on both sides, never back and forth in a row | assafkip, saas-motion-kit |
| Dissolve | 0.3–1.0 s; bookend fades 0.5–1.0 s | openmontage |
| Blink, shutter, zoom, spin, wipe | quick ~0.2–0.5 s, standard ~0.7–1.5 s | digitalsamba (two tables in one repo disagree) |
| Text or sticker entrance / exit | entrance 0.2–0.6 s, exit shorter | talkcraft |
| Impact (slam, flash, hit) | 0.10–0.25 s after its target is fully visible | assafkip |

`upsertTransition` takes `duration` in frames: frames = seconds × the project fps (`project get`).

## 4. Reframe: crop only to what matters

A crop decides what the viewer loses. Check the frame first, never crop blind.

1. **Facts**: `timeline get` / `review shots` `scale` (`fit`, `frameCoverage`, `maxZoomNative`); `review layout
   --frame F` lists the pictures on screen at F with their scale and coverage.
2. **Look** at what matters at the start, middle, end and action peaks of each shot (nateherkai; T19 §2):
   `media frame --media ID --at S` (source size, so you can read a rectangle in source pixels), `ui frame F` for
   the edit, `ui frames --compare source --items CLIP` for source next to edit. Faces and people come from
   `bashcut media subjects --media ID --from S --to S2` (job): `box` `[x, y, w, h]` as shares of the source picture
   from the top left, so multiply by the media's width and height for a rectangle in source pixels; check it on
   `media frame` at that `frame`. `review layout` `faceOverlap` stays null (unknown, not "no face"); `media
   describe` subjects are your own tags.
3. **Crop when what matters fits**: `clip motion ITEM --focus x,y,w,h` around the subject, locked for the shot
   ("don't move unless you must", hotclip; T19 §2). Leave 0.3–0.5 of the face size around a face, more for a
   gesturing presenter (openmontage, hotclip; T19 §3). `--focus-to` only when the subject really moves; no smooth
   drift on a talking head (jianshuo). Check `pixelRatio` afterwards.
4. **Fall back to fit** when it does not fit (two people far apart, a wide landscape, a sign): the clip's `fill`
   false (`setProperties`) or `project format --clips fit`. A blurred backdrop suits screens and slides, not footage
   with a subject (nateherkai; T19 §3). Order: fit → a fixed crop at a position you checked → keep the original
   shape. A centre crop without a frame check is the anti-pattern (openmontage; T19 §4).

## Library first

- `bashcut library list --kind effect-preset` (also `transition-preset`, `sticker`). Built-ins: `ken-burns-in`,
  `ken-burns-out`, `zoom-punch-in`, `punch-in`, `speed-ramp`, `slow-motion`; transitions `soft-dissolve`,
  `quick-whip`, `zoom-punch`; emoji stickers. `library get ID` shows a preset's parameters and ranges: set them
  from sections 3–4, not the defaults.
- Effect preset: `bashcut library apply ID --item CLIP --set zoom=1.12 --from F --to T --base-rev N` (every step
  in one undo).
- Transition preset: `bashcut library apply ID --item CLIP --base-rev N` sets kind, duration, easing and its sound
  at the cut beside the clip.
- Sticker: `bashcut library place ID --at-frame F --position top-right --size 0.25 --base-rev N`.
- An effect the user liked: `bashcut library save-selection --kind effect-preset --name "Food reveal" --item CLIP`
  (or `transition-preset`, `sticker`). A correction: `library update ID --params '{...}'`, or `--as NEW_ID` for a
  built-in or plugin preset.
- A sticker or sound the library lacks: `bashcut library search "fire" --kind sticker` (or `library generate`)
  when a plugin provides it; a job, then `library add --from-result JOB:N`.

## How, in BashCut

| Effect | Make it with |
|---|---|
| Transition | `{"op":"upsertTransition","id":"t-hook","kind":"whip","from":"A","to":"B","duration":9}` (frames; clips adjacent on one video layer; kinds: dissolve, whip, blink, zoom, spin, shutter, wipe) |
| Speed ramp | `{"op":"setSpeedCurve","item":"ITEM","preset":"hero"}` (montage, hero, bullet, jump-cut, flash-in, flash-out) or `"points":[{"t":0,"speed":1},{"t":0.5,"speed":3},{"t":1,"speed":1}]` |
| Constant speed | `{"op":"setSpeed","item":"ITEM","speed":2}` (0.1–16; length follows, `"keepDuration":true` keeps it) |
| Reverse | `clip reverse ITEM` (job) |
| Freeze frame | select the clip, playhead on the frame, `ui action clip.freeze` |
| Punch-in / reframe | `setProperties` `{"reframePreset":"custom","transform":{"zoom":Z,"pan":P,"tilt":T}}`, Z from the clip's headroom (`bc:beat-cut`) |
| Picture in picture, split moment | the second clip on an overlay layer with `transform` zoom below 1 and pan/tilt |
| Black-and-white moment | `adjustment add --look black-white` over the range |
| Pop text, labels, prices | text items with `hook-title`, `keyword-sticker`, `place-card` (`bc:captions-text`) |
| Stickers | `library place ID --position top-right --size 0.25` (image, alpha movie or emoji) |
| Fade from/to black | `dissolve` against a black clip, or audio `fadeIn`/`fadeOut` for sound |
| Ken Burns, slow push-in | `clip motion ITEM --preset zoom-in` (also zoom-out, pan-*), or keyframes at the drift rate above |
| Animated title or label | `clip motion TEXT_ITEM --preset pop-in` (fade-in-out, slide-up, zoom-punch) |
| Custom move | `clip motion ITEM --keyframes '{"zoom":[{"frame":0,"value":1},{"frame":45,"value":1.08,"ease":"out"}]}'` (frames from the item's start; eases linear, in, out, inOut, hold) or one key: `clip keyframe ITEM --property pan --value -80 --at-frame F` |
| Zoom onto a panel of a screen recording | `clip motion ITEM --focus x,y,w,h [--focus-to x,y,w,h] [--ease out]`: the panel's rectangle in the recording's pixels (origin top left, size from `media list`). One panel per sentence; draw the rectangle around the panel only. One example: at zoom 1.9 a 1920 px recording showed 1010 px and a neighbouring window crept in; 2.6 isolated the panel. Confirm with `ui frame` |
| Presenter box over a screen recording | `setProperties` `{"crop": {"left": 0.2, "right": 0.2, "top": 0.1, "bottom": 0.3, "radius": 0.15}}` on the camera clip (fractions; `radius` 0.5 = circle), then `transform` zoom/pan/tilt to size and place it: 0.25–0.6 of the width, smaller when the screen text is dense, larger when the face carries the story (T19 §3). The visible part keeps its place in the picture: an uneven crop (one example: left 0.28, right 0) left the face box off-centre until pan moved it back by (left − right) / 2 × canvas width × zoom |
| Word-by-word captions | `captions words --all --style highlight` (karaoke, reveal); see `bc:captions-text` |

## Not possible yet — say so and offer the alternative

- Typewriter text, counting numbers, shake, glitch, film grain.
- Segmentation (text behind a person, cut-outs), motion tracking, face-aware auto reframe, AI-generated
  transitions.

When the user needs one of these, note it as a feature request for BashCut (or a plugin action) rather than faking
it with a pre-rendered file.

## Verify

Run `review shots --summary` again: the runs and repeats you meant to break are gone, and the
ones left are motifs you can name. Render frames just before, inside and after each effect with `ui frame F` (for
motion: the first, middle and last frame of the item) or one `review window F` across a transition, and read them;
for a reframe, check that what matters is still in the frame. Ask the user to listen to the matching sound.
