---
name: bashcut-footage-survey
description: Survey a footage folder before editing in BashCut — probe specs and build contact sheets to SEE which shots actually exist, catch missing coverage, silent audio, broken files and portrait/landscape mixes early, and pick sharp in-points. Use at the start of any edit from raw footage, when choosing clips or moments, or when the cut feels boring and it is unclear whether the problem is the shooting or the editing. Also syncs a camera with a screen recording of the same session by their sound (sync.py). Triggers: "khảo sát footage", "xem footage", "contact sheet", "có những cảnh gì", "đồng bộ", "quay màn hình".
---

# Footage survey

Reply in the user's language. Run this **first**, before promising anything about the edit.

```sh
python3 "<skill_dir>/survey.py" /abs/footage [--out DIR] [--frames 4 | --every SECONDS] [--recursive]
python3 "<skill_dir>/survey.py" /abs/render/draft-v1.mp4 --every 2        # review a rendered cut
# <skill_dir> = this SKILL.md's folder
```

Output in `<footage>/_survey/` (or `--out`; inside a project use `<project>/survey`, an English name):
- `SHEET_*.jpg`: grids of frames (8 × 3 portrait, 6 × 6 landscape). Each cell is labelled
  `<cell> <clip ID> <time in clip>`, e.g. `14 c06 0:33`. Clip IDs are the `ID` column of the printed table; the
  label colour switches between yellow and cyan at each new clip.
- `survey.json`: `clips` (duration, size, rotation, orientation, fps, audio level) and `cells` (sheet, cell,
  clip, time of every frame), so a cell number from a sheet maps back to a clip and a time.

Needs ffmpeg and ffprobe; Python standard library only. It reads footage and writes only into the output folder.

**Then actually look at every sheet** with the image reader. That is the whole value of this skill.

## Reading a contact sheet

| You see | Conclusion |
|---|---|
| Frames of one clip clearly differ | the clip has coverage and several usable moments |
| Frames of one clip are identical | locked-off camera: the clip gives **one** shot size |
| Many clips look alike | repeated scenes: the edit will feel monotonous |
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

## Two recordings of one session (camera + screen)

Filename clocks lie (82 s and 101 s apart by name, 2.49 s by sound once the recording had been trimmed). Measure:

```sh
python3 "<skill_dir>/sync.py" /abs/camera.mp4 /abs/screen.mp4      # screen time = camera time + offset
python3 "<skill_dir>/sync.py" /abs/screen.mp4 /abs/render.mp4      # where a render played on screen starts
```

It correlates loudness envelopes and checks each half of the overlap: camera vs screen 0.79 with halves agreeing
to 0.01 s; a 46 s render found inside a 5 min screen recording at 275.74 s (0.97). Below 0.4, or halves more than
0.02 s apart: wrong match or drifting clocks. Matching caption sentences of the two files instead was too rough
(9 matches, −1.5 to −4.8 s, median −2.94 for a true −2.49). Then screen in-point = camera in-point + offset.

## Time and place from filenames

Cameras put the time in the name: `DJI_20260808201922_0400_D.MP4` → 20:19:22 on 08/08. Use it for the order of
the trip and for place or time labels (`bashcut-captions-text`). Subfolders may reuse the same clip numbers; the survey
keeps them apart by path.

## Picking in-points

- Pick by measured sharpness, not by eye on a small sheet: motion blur hides at sheet size. Look at the frame
  full size before committing to an in-point (`ffmpeg -ss SECONDS -i clip -frames:v 1 /tmp/f.jpg`, then read it;
  once placed, `ui frame F` shows it in the edit).
- Long clips that change inside (timelapse, walks) need more frames: rerun with `--frames 10`.
- Speech: transcribe in BashCut (`captions generate --media ID`). Speech recognition invents text over music,
  crowd noise and silence ("hãy subscribe kênh…", "cảm ơn các bạn đã theo dõi"): drop lines like that, and treat
  a clip whose only text is that as having no speech. If the speech is in another language than the project,
  say so before cutting on it.

## Into BashCut

After the survey, link and import only the clips you will use (see `bashcut-edit-workflow`), and write what you found
(coverage gaps, best moments, silent clips) into the project memo with `knowledge memo` so later sessions know.
