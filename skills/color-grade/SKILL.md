---
name: color-grade
description: Colour-grade a BashCut edit — pick a look (built-in, custom or a generated .cube LUT such as matte-cinematic, warm-film, faded-memory), match it to the footage, preview before/after on real frames, import the LUT and apply it with adjustment layers, saved looks and style kits. Use when the user says "tone màu", "chỉnh màu", "color grade", "LUT", "màu phim", "màu cinematic", "màu giống kênh X", "hình nhạt", "hình gắt", or when clips look flat, harsh or inconsistent.
---

# Colour grade

Reply in the user's language. With a `[Scope]` (Send to Agent), work only on those items (`bc:edit-workflow`).

## BashCut's colour tools

| Need | Command |
|---|---|
| A whole-video style (look + caption preset) | `style apply cinematic` / `food-review` / custom kit |
| A grade on a range (grades every layer below) | `adjustment add --look matte-cinematic --at-frame F --duration D` |
| Fix one clip | `setProperties` patch `{"color": {"exposure": 0.3, "contrast": 1.1, "saturation": 0.9, "lut": null}}` |
| Reuse a grade | `looks save ID --title T [--item ITEM]`, `style save ID --title T --look ID --caption-preset P` |
| Bring in a LUT | `luts import /abs/look.cube --name "Matte" --base-rev N` → its ID in `timeline get` `luts` |

Built-in looks: `original`, `vivid`, `muted-film`, `black-white`. Ranges: exposure −10…10 (stops), contrast
and saturation 0…4 (1 = unchanged), lutStrength 0…1. A `color` patch replaces the whole object: send every key
you keep. Grade picture layers only; adjustment items never touch the text layers above them when placed under
them.

## Generated looks (`grade.py`)

```sh
G="<skill_dir>/grade.py"           # the folder this SKILL.md is in; run with uv (installs numpy + Pillow)
uv run "$G" looks
uv run "$G" measure /abs/clip.mp4                       # black/white point, saturation, tint per band
uv run "$G" match /abs/clip.mp4 matte-cinematic -o /abs/project/luts-src/matte.cube   # look + auto exposure/WB
uv run "$G" preview /abs/clip.mp4 /abs/project/luts-src/matte.cube -o /tmp/prev.jpg --n 6
```

`match` neutralises the footage's white balance from its mid tones; on graphics, screen recordings or scenes
that are meant to be coloured (sunset, neon) it shifts colours wrongly: use `lut` there instead.

Look at `prev.jpg` (left original, right graded) on the **brightest and darkest** clips before applying. The
preview is for looking only. Then:

```sh
bashcut luts import /abs/project/luts-src/matte.cube --name "Matte cinematic" --base-rev N
bashcut looks save matte --title "Matte cinematic" --lut LUT_ID --lut-strength 0.9 --base-rev N
bashcut adjustment add --look matte --at-frame 0 --duration TOTAL_FRAMES --base-rev N
```

| Look | Use for |
|---|---|
| `matte-cinematic` | default cinematic: street, daytime, travel. Lifted blacks ~7, whites rolled to ~84, saturation ~28, teal shadows, peach highlights, greens to olive, skin protected |
| `warm-film` | warm indoor light, late afternoon, personal stories. Deep blacks, highlights compressed, warm mids |
| `faded-memory` | hook, flashback or emotional low point, then return to colour. Near black-and-white, lifted blacks |

Write your own look as a params JSON (keys in `grade.py -h`) and pass its path instead of a look name.

## Rules

- **A LUT is half the look.** The other half is light when shooting: golden hour, backlight, shade, slight
  under-exposure, muted wardrobe. Harsh noon sun stays harsh after a LUT: say so instead of pushing the grade
  until skin breaks.
- Grade the whole video with one look, then fix clips that stand out (night, indoor) with per-clip `color`
  or a second adjustment over their range.
- A matte look lifts pure black backgrounds to dark grey; use another look over those ranges if true black
  matters.
- Matching a reference channel: measure several of its frames with `grade.py measure` (from videos the user
  has the right to use), compare with your footage, and adjust a look's params toward its numbers; see
  `bc:style-study`.

## Verify

Render the brightest, darkest and skin-heavy shots with `ui frame F` and read the PNGs; `ui view --compare on`
shows the user before/after in the viewer.
