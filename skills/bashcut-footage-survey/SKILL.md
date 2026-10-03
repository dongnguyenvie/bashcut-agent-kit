---
name: bashcut-footage-survey
description: Survey a footage folder before editing in BashCut — probe specs and build contact sheets to SEE which shots actually exist, catch missing coverage, silent audio, broken files and portrait/landscape mixes early, and pick sharp in-points. Use at the start of any edit from raw footage, when choosing clips or moments, or when the cut feels boring and it is unclear whether the problem is the shooting or the editing. Triggers: "khảo sát footage", "xem footage", "contact sheet", "có những cảnh gì".
---

# Footage survey

Reply in the user's language. Run this **first**, before promising anything about the edit.

```sh
python3 "<skill_dir>/survey.py" /abs/footage [--out DIR] [--frames 4] [--recursive]   # <skill_dir> = this SKILL.md's folder
```

Output in `<footage>/_survey/`: `SHEET_*.jpg` (one row per clip, same order as the printed table),
`survey.json` (duration, size, rotation, orientation, fps, audio level) and `frames/`. Needs ffmpeg and ffprobe;
Python standard library only. It reads footage and writes only into `_survey/`.

**Then actually look at every sheet** with the image reader. That is the whole value of this skill.

## Reading a contact sheet

| You see | Conclusion |
|---|---|
| Frames in one row clearly differ | the clip has coverage and several usable moments |
| Frames in one row are identical | locked-off camera: the clip gives **one** shot size |
| Many rows look alike | repeated scenes: the edit will feel monotonous |
| Rows with texture and no people (smoke, rain, objects, hands) | often the best cutaways: prioritise them |

## When coverage is missing, say so

No editing technique creates shots that were never filmed. Real case: two 4-minute clips, 22–24 frames each,
all nearly identical — 9 minutes of footage gave two shot sizes. Then:

1. State the limit, with the contact sheet as evidence.
2. Offer what can be saved: punch-in reframes (`bashcut-beat-cut`), stock or illustration images (`bashcut-stock-images`),
   voiceover over b-roll (`bashcut-voiceover`).
3. Give a shot list for next time. Per location, 4 shots × 10 s: hands doing something (close, fill the
   frame); the shop front or sign before entering; the food or product right when it arrives; walking feet or a
   slow pan of the space.

## Things the table flags

- **STUB**: empty or broken files (camera cards hold ~1 KB stub `.MP4`s). Leave them out.
- **Silent audio** (mean below about −70 dB; −91 dB = no sound at all): plan voiceover or music for those
  clips; don't expect real speech.
- **Portrait and landscape mixed**: check `orientation` (rotation is already applied) before choosing the
  project canvas. Phones often report 1920×1080 with rotation −90: that clip is portrait.
- **fps**: clips at another rate than the project play fine in BashCut, but true slow motion needs 50/60/120 fps
  sources.

## Time and place from filenames

Cameras put the time in the name: `DJI_20260808201922_0400_D.MP4` → 20:19:22 on 08/08. Use it for the order of
the trip and for place or time labels (`bashcut-captions-text`). Subfolders may reuse the same clip numbers; the survey
keeps them apart by path.

## Picking in-points

- Pick by measured sharpness, not by eye on a small sheet: motion blur hides at sheet size. Look at the frame
  full size (`ui source MEDIA_ID --in F`, then a viewer frame) before committing to an in-point.
- Long clips that change inside (timelapse, walks) need more frames: rerun with `--frames 10`.
- Speech: transcribe in BashCut (`captions generate --media ID`). Speech recognition invents text over music,
  crowd noise and silence ("hãy subscribe kênh…", "cảm ơn các bạn đã theo dõi"): drop lines like that, and treat
  a clip whose only text is that as having no speech. If the speech is in another language than the project,
  say so before cutting on it.

## Into BashCut

After the survey, link and import only the clips you will use (see `bashcut-edit-workflow`), and write what you found
(coverage gaps, best moments, silent clips) into the project memo with `knowledge memo` so later sessions know.
