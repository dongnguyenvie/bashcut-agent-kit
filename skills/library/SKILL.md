---
name: library
description: Grow and look after the user's BashCut library — make a missing preset, effect, transition, look, sticker or sound when nothing in the library fits (write it with library add, try it on a clip, undo, save), harvest what is worth keeping after an edit (a grade, an effect, a transition, a sound, a sticker), and fix, copy or prune saved items. Use when the user says something is missing ("thiếu hiệu ứng", "không có cái nào hợp", "tạo preset", "làm cho tôi một …"), asks to keep something for later ("lưu lại", "dùng lại lần sau", "để dành"), when an edit is finished ("xong rồi", "làm xong video"), or when the library has unused or duplicate items.
---

# Library: make, harvest, look after

Reply in the user's language. The library holds reusable items in seven kinds: `text-preset`, `sticker`,
`effect-preset`, `transition-preset`, `look`, `audio` and `voice`. Items live in four scopes, searched in this
order: the project (`.bashcut/library`), this Mac (`user`), plugin packs, built-ins. Built-in and plugin items are
read-only.

Scope rules:
- Save to the **project** by default; no approval needed.
- `--scope user` (every project on this Mac) waits for the user's approval in the app. Offer it for things the
  user will clearly want again (their channel's grade, their outro sound), and say it needs their click.
- With a `[Scope]` (Send to Agent), trying an item on the timeline stays inside the scoped items
  (`bc:edit-workflow`).

## 1. Something is missing: make it

The user wants an effect, transition, look, text style, sticker or sound, and nothing fits.

1. **Check first.** `bashcut library list --kind effect-preset --query "shake"` (also `--tag`, `--pack`).
   A close item with other numbers is not missing: apply it with `--set`, or copy it with
   `library update ID --as NEW_ID` and change the copy.
2. **Ask a plugin.** When a provider is installed: `bashcut library search "camera shutter" --kind audio` or
   `bashcut library generate "gold star burst" --kind sticker` (jobs; `jobs status` lists candidates with their
   preview, source and licence). Show the candidates, check the licence, then
   `bashcut library add --from-result JOB:N`. No provider: say so; installing one is the user's job.
3. **Build it on the timeline, then save it.** This is the most reliable way: make the effect with the usual
   commands (`bc:effects`, `bc:color-grade`, `bc:audio-mix`, `bc:captions-text`), let the user approve, then
   `bashcut library save-selection --kind effect-preset --name "Food reveal" --item CLIP`.
4. **Write it with `library add`** when the item is a recipe you can describe in numbers (below), or from a
   file you were given or made (a `.cube` LUT, a PNG, an audio file).
5. **Try it before you call it done.** `library apply` or `library place` it on a real clip, read the result with
   `ui frame F` (several frames for motion), ask the user to listen for sound, then `timeline undo` unless they
   want to keep it. A wrong value: `library update ID --params '{...}'` (a new version).

### Writing each kind

`library get ID` on a built-in shows a working example of every kind. Frames are timeline frames.

**effect-preset**: a recipe of up to 32 steps run in order on the clip, with up to 16 named parameters the user
can change on apply (`--set name=value`). A step value `"$name"` takes the parameter. Positions are `t` (0 = first
frame, 1 = last, so the effect scales with the clip) or `frame` (negative counts from the end).

```sh
bashcut library add --kind effect-preset --name "Shake hit" --tags punch,impact --params '{"parameters": {"zoom": {"default": 1.25, "min": 1.05, "max": 2}}, "steps": [{"op": "keyframes", "keys": {"zoom": [{"frame": 0, "value": "$zoom", "ease": "out"}, {"frame": 6, "value": 1}], "pan": [{"frame": 0, "value": -20}, {"frame": 2, "value": 20}, {"frame": 4, "value": -10}, {"frame": 6, "value": 0}]}}, {"op": "sfx", "sfx": "AUDIO_ITEM_ID", "frame": 0}]}'
bashcut library apply shake-hit --item CLIP --set zoom=1.4 --from 120 --to 150 --base-rev N
```

| op | fields |
|---|---|
| `motion` | `preset` (as `clip motion --preset`), or `focus` `[x, y, w, h]` (fractions of the picture) with `focusTo`, `ease` |
| `keyframes` | `keys` `{property: [{t or frame, value, ease}]}`: zoom, pan, tilt, rotation, opacity; ease linear, in, out, inOut, hold |
| `speed` / `speedCurve` | `speed`, `keepDuration`; `preset` or `points` `[[t, speed], …]` |
| `reverse`, `freeze` | `freeze` holds the frame at `t` or `frame` |
| `patch` | item properties set as they are (`transform`, `opacity`, `crop`…) |
| `sfx` | `sfx` (an audio item ID, or the preset's own `--file`), `t` or `frame`, `volumeDb` |
| `text` | `text`, `textPreset`, `t` or `frame`, `duration` |

Speed steps break lip sync: tag such presets `b-roll`.

**transition-preset**: `kind` (dissolve, whip, blink, zoom, spin, shutter, wipe), `duration` in frames (1–600),
`easing` (linear, in, out, inOut), `sfx` (an audio item ID) or the preset's own sound as `--file`.

```sh
bashcut library add --kind transition-preset --name "Snap whip" --params '{"kind": "whip", "duration": 6, "easing": "in", "sfx": "AUDIO_ITEM_ID"}'
```

**look**: `{"color": {"exposure", "contrast", "saturation", "lutStrength"}}` with an optional `.cube` as `--file`
(make one with `grade.py` in `bc:color-grade`; look at its preview first).

```sh
bashcut library add --kind look --name "Warm market" --file /abs/project/luts-src/warm.cube --params '{"color": {"contrast": 1.05, "lutStrength": 0.85}}'
```

**audio**: needs `--file`. `library add` measures the length and picks music or sfx by it; then
`bashcut library analyze ID` (job) fills BPM and loudness. Tag mood and use (`calm`, `whoosh`, `outro`) after
the user listened (`library preview ID`). Set `{"loopable": true}` only for a bed that loops without a click.

**sticker**: an emoji (`{"emoji": "🎉", "textPreset": "bold-outline"}`), or a file: PNG/WebP with transparency,
or a `.mov` with alpha (HEVC alpha or ProRes 4444), with optional `size` (width, 0.01–1 of the frame), `position`
and `animation` (a clip motion preset). GIFs place as their first frame for now; Lottie is not supported. Pictures
from the web need a licence: `bc:stock-images`.

**text-preset**: `{"textPreset": "<built-in renderer preset>", "text": "sample", "textStyle": {"size": 0.07,
"positionY": 0.62, "strokeWidth": 6}, "animation": "pop-in"}`; `textStyle` (only those three keys, the item property
ranges) and `animation` (a clip motion preset) are optional. `save-selection` keeps the item's size, position,
outline and its motion preset (hand-made keys are dropped); place and apply set them back. Colour and font are
**not** stored: say so, and record them as a preference (`knowledge set-pref`) or keep them in a style kit
(`style save`).

Give every item a clear English `--name` (the ID comes from it), `--tags` for mood and use, `--pack` when it
belongs to a set (the user's channel name), and `--source` / `--license` for anything not made here.

## 2. After an edit: harvest

When the edit is done (after review, before or after export), look for work worth keeping. Do not save silently.

1. Read `timeline get` and list the candidates:
   - a grade the user approved (adjustment or clip colour, with its LUT) → `look`;
   - a keyframed move, speed ramp or freeze you built by hand → `effect-preset`;
   - the same transition kind and length used at 3+ cuts → `transition-preset`;
   - an SFX or music bed that fit and is not already a library item → `audio`;
   - an image or alpha overlay used as a sticker → `sticker`.
2. Skip what came from the library already (you applied or placed it), one-off fixes (a crop for one bad
   shot) and anything the user complained about.
3. `bashcut library list --kind K` and `bashcut library stats --kind K`: skip a candidate that duplicates a saved
   item; when it improves one, propose `library update ID` instead of a new item.
4. Propose a short list (at most five), each with a name, kind, scope and why it is reusable, e.g.
   "Look *Warm market* (project): the grade you approved for all 14 clips." Then save only what they say yes to:

```sh
bashcut library save-selection --kind look --name "Warm market" --item ADJUSTMENT --tags warm,food
bashcut library save-selection --kind audio --name "Market ambience" --item CLIP --tags ambience,market
bashcut library save-selection --kind transition-preset --name "Snap whip" --item CLIP --scope user
```

Nothing worth keeping: say so in one line.

## 3. Look after it

- **Correction.** The user changed an item's result by hand, or undid it right after `library apply` /
  `library place`: propose `bashcut library update ID --params '{...}'` (a new version; the old one stays in its
  history). Built-in or plugin: `bashcut library update ID --as NEW_ID`, and record a preference to use the copy.
- **Wrong place.** `bashcut library move ID --to user` (approval) or `--to project`.
- **Prune.** `bashcut library stats` lists saved items nobody used and duplicates (same kind and content). At the
  end of a session offer to remove or merge them; never remove without a yes:
  `bashcut library remove ID` (user scope waits for approval). Removing keeps files the timeline still uses.
- **Share.** `bashcut library export-pack --output /abs/packs/my-channel --pack "My channel"`; the other side runs
  `bashcut library import-pack /abs/packs/my-channel --scope user`.

## Report

What was made or saved (name, kind, scope), what was tried and undone, what waits for the user's approval.
