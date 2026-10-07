---
name: color-grade
description: Colour-grade a BashCut edit — measure the footage, pick a look (built-in, custom or a generated .cube LUT such as matte-cinematic, warm-film, faded-memory), try candidates on real frames, check the graded picture for damage against the source and back off, then import the LUT and apply it with adjustment layers, saved looks and style kits. Use when the user says "tone màu", "chỉnh màu", "color grade", "LUT", "màu phim", "màu cinematic", "màu giống kênh X", "hình nhạt", "hình gắt", or when clips look flat, harsh or inconsistent.
---

# Colour grade

Reply in the user's language. With a `[Scope]` (Send to Agent), work only on those items (`bc:edit-workflow`).
Grade after picture lock, before captions (T12 §7).

The loop: **probe → measure → candidates → check → back off**. Every number below is a reading with its
source, not a target: you choose what to change and by how much, from the footage and the intent.

## BashCut's colour tools

| Need | Command |
|---|---|
| Colour stats per clip (0–100) | `color measure` (source), `--graded` (as composed), `--compare source`, `--by clip` |
| Before/after on several frames | `ui frames --compare graded --frames F1,F2,F3` (or `--items A,B`), one PNG grid |
| One frame at phone size | `ui frame F --phone` |
| Transfer of a file (SDR, HLG, PQ, log) | `media analysis --media ID` › `tech.transferKind` (after `media analyze`) |
| A whole-video style (look + caption preset) | `style apply cinematic` / `food-review` / custom kit |
| A grade on a range (grades every layer below) | `adjustment add --look matte-cinematic --at-frame F --duration D` |
| Fix one clip | `setProperties` patch `{"color": {"exposure": 0.3, "contrast": 1.1, "saturation": 0.9, "lut": null}}` |
| Reuse a grade | `looks save ID --title T [--item ITEM]`, `style save ID --title T --look ID --caption-preset P` |
| Bring in a LUT | `luts import /abs/look.cube --name "Matte" --base-rev N` → its ID in `timeline get` `luts` |

Built-in looks: `original`, `vivid`, `muted-film`, `black-white`. Ranges: exposure −10…10 (stops), contrast
and saturation 0…4 (1 = unchanged), lutStrength 0…1. A `color` patch replaces the whole object: send every key
you keep. Grade picture layers only; adjustment items never touch the text layers above them when placed under
them. There is no white balance or black/white point control yet: those need a generated LUT (`grade.py`).

## 1. Probe

`bashcut media analyze` (job), then `bashcut media analysis --media ID` per clip: `tech.transferKind` other
than `sdr` (iPhone shoots HLG by default) needs handling before any look; the looks here were fitted on Rec709.
BashCut has no tone-mapping control yet: tell the user which clips are HLG/PQ/log instead of grading over them
(T12 §4, §5).

## 2. Measure

```sh
bashcut color measure                    # clips on Main: black, p5, mid, p95, white, saturation, tint, clipped/crushed
bashcut color measure --by clip          # each clip's difference from the median clip: the outliers
bashcut color measure --items A,B --samples N   # more frames (default 3) for long or changing clips
```

Per clip: black (luma p1), p5, mid (p50), p95, white (p99), saturation and saturationP95, tint per band
[R−B, G−(R+B)/2] for shadows, mids and highlights, clippedShare and crushedShare. Find the **brightest, darkest
and skin-heavy** clips here; they are the ones to check later. Never judge from one frame (T12 §4).

How to read them:

| Reading | Range seen | What moves it | Source |
|---|---|---|---|
| Mid luma, daylight vlog | ~30–50 | lower on purpose for night, low-key, silhouettes: not "too dark" | T12 §3, §7 |
| Clipped highlights | share near 0 | deliberate sun or sky may clip | T12 §7 |
| Matte blacks / rolled whites | black > 3 reads as matte; white < 90 as rolled | examples, not targets | style-study (T15 §3) |
| Saturation | < 30 reads muted, > 45 punchy | genre: food punchy, cinematic muted | style-study (T15 §3), T12 §3 |
| Split tone | shadow R−B < 0 with highlight R−B > 0 = teal-orange | — | style-study (T15 §3) |
| Shot match | each clip's difference from the median clip | you choose how far to pull an outlier | drama-skills (T12 §3) |

A recipe (`recipe.skill` in `project get`) gives an *intent* such as "bright, warm, skies kept": turn it into
which of these readings matter, never into fixed numbers.

## 3. Candidates

Pick a look as an intent, then pick a strength:

| Look | Use for | Fitted reference (`looks.json`) |
|---|---|---|
| `matte-cinematic` | default cinematic: street, daytime, travel | black ~7, white ~84, sat ~28; teal shadows, peach highlights, greens to olive, skin protected |
| `warm-film` | warm indoor light, late afternoon, personal stories | deep blacks (~2.6), highlights ~66–76, sat ~29, warm mids |
| `faded-memory` | hook, flashback or emotional low point, then back to colour | near black-and-white, lifted blacks |

Also `bashcut library list --kind look`: project, this Mac, plugin and built-in looks (`bright-airy`, `moody`, …).

- **Strength** 0.5–1.0; 0.6–0.8 is typical (openmontage). Lower for log-like or already saturated footage,
  skin-heavy shots and mixed light (T12 §3).
- **One look for the video**, then fix outliers with per-clip `color` or a second adjustment over their range
  (T12 §4).
- A LUT is half the look; the other half is light when shooting. Harsh noon sun stays harsh after a LUT: say so
  instead of pushing the grade until skin breaks.
- A matte look lifts pure black backgrounds to dark grey; use another look over those ranges if true black matters.

### Generated looks (`grade.py`)

```sh
G="<skill_dir>/grade.py"           # the folder this SKILL.md is in; run with uv (installs numpy + Pillow)
uv run "$G" looks
uv run "$G" match /abs/clip.mp4 matte-cinematic                      # JSON report, writes nothing
uv run "$G" match /abs/clip.mp4 matte-cinematic --exposure S --wb R,G,B   # try the values you chose
uv run "$G" lut matte-cinematic --exposure S --wb R,G,B -o /abs/project/luts-src/matte.cube
uv run "$G" preview /abs/clip.mp4 /abs/project/luts-src/matte.cube -o /tmp/prev.jpg --n 6
```

`match` measures the footage and the footage through the look (plus only the `--exposure`/`--wb` you pass) and
reports each field against the look's `ref` and `range` in `looks.json`: `minusRef`, and `outside` (0 inside,
negative below, positive above, null with no range); each range has its `why`. It corrects nothing. You decide
the exposure (stops added to the look's) and white balance (R,G,B multipliers on the look's), try them with
`match` again, then write the LUT with `lut`. Leave the white balance alone on scenes meant to be coloured
(sunset, neon, screen recordings, graphics): the reference tint is the look's, not the scene's (T12 §4).
`match` runs on the source file only; the real check is BashCut's composite in step 4. Never read a `.cube`
body; judge a LUT by its frames (T12 §4).

Write your own look as a params JSON (keys in `grade.py -h`) and pass its path instead of a look name.

```sh
bashcut luts import /abs/project/luts-src/matte.cube --name "Matte cinematic" --base-rev N
bashcut looks save matte --title "Matte cinematic" --lut LUT_ID --lut-strength 0.8 --base-rev N
bashcut adjustment add --look matte --at-frame 0 --duration TOTAL_FRAMES --base-rev N
```

## 4. Check

```sh
bashcut color measure --compare source        # per clip: the edit without colour vs as graded, and the change
bashcut ui frames --compare graded --frames F1,F2,F3   # brightest, darkest, skin-heavy: before | after
bashcut ui frame F --phone                    # how it reads on a phone
```

`change` holds black, mid, white, saturation, tintMids and the damage facts: `clippedGrowth`, `crushedGrowth`,
`chromaRatio` (graded over source chroma), `blackLift` and `meanDeltaE` (CIE76). Read them **relative to the
source**, then look at the frames. One worked example of flags (DaVinci Resolve's grade checker, its thresholds
are parameters): clipping growth 0.5 % of pixels, washed-out chroma ratio 0.60, milky black lift L* 8, and a
grade that moved ΔE 6 without any flag "is worth a second opinion": undamaged is not the same as good (T12 §2,
§3). A matte look lifts blacks on purpose; a warm look moves the mid tint on purpose: compare with the intent.

Check every sampled clip, not the average; name the clip and frame that fails.

## 5. Back off

On damage, lower before adding: `lutStrength` first, then the exposure or white balance you passed. Resolve
backs off ×0.8 per try down to 0.5 (T12 §2). Change the adjustment's `color` (send every key) or `timeline undo`
and add it again. **At most 3 attempts.** Then stop: show the user `ui frames --compare graded` of the gentlest
attempt with its numbers and ask (`ui view --compare on` toggles before/after in the viewer for them).

## Keep what worked

- `bashcut library place ID --at-frame 0 --duration TOTAL_FRAMES --base-rev N` adds a library look as an
  adjustment; `bashcut library apply ID --item ITEM --base-rev N` replaces one clip's grade. Either copies its LUT
  into the project in the same undo step.
- Once the user approves: `bashcut library save-selection --kind look --name "Matte cinematic" --item ADJUSTMENT`,
  or from a LUT: `bashcut library add --kind look --name "Matte" --file /abs/matte.cube`.
- A correction: `library update ID --params '{"color": {...}}'`, or `--as NEW_ID` for a built-in or plugin look.
- Matching a reference channel: measure several of its frames with `grade.py measure --json` (videos the user
  has the right to use), compare with your footage, and move a look's params toward them; see `bc:style-study`.
