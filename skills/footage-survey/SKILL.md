---
name: footage-survey
description: Survey a footage folder before editing in BashCut — probe specs and build contact sheets to SEE which shots actually exist, catch missing coverage, silent audio, broken files and portrait/landscape mixes early, and pick sharp in-points. Use at the start of any edit from raw footage, when choosing clips or moments, or when the cut feels boring and it is unclear whether the problem is the shooting or the editing. Also syncs a camera with a screen recording of the same session by their sound (bashcut media sync). Triggers: "khảo sát footage", "xem footage", "contact sheet", "có những cảnh gì", "đồng bộ", "quay màn hình".
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
2. Offer what can be saved: punch-in reframes (`bc:beat-cut`), stock or illustration images (`bc:stock-images`),
   voiceover over b-roll (`bc:voiceover`).
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

Filename clocks lie (82 s and 101 s apart by name, 2.44 s by sound once the recording had been trimmed). Measure:

```sh
bashcut media sync --media CAMERA_ID --to SCREEN_ID [--item CAMERA_CLIP]   # job: screen time = camera time + offset
bashcut media sync --media SCREEN_ID --to RENDER_ID                        # a render played on screen starts at −offset
bashcut jobs status JOB_ID
```

Both files must be project media (`media import`). It correlates loudness envelopes and checks each half of the
overlap: camera vs screen −2.44 s at 0.785, both halves −2.44; a 46 s render found inside a 5 min screen recording
at 275.74 s (0.97). Use BashCut's number, not one measured with ffmpeg: ffmpeg read the DJI camera's sound 44 ms
later than BashCut (it keeps 2112 samples of AAC priming that BashCut drops) and gave −2.49. `reliable` is false below 0.4 or when the halves are more than 0.02 s apart (`steady`): wrong
match or drifting clocks. Matching caption sentences of the two files instead was too rough (9 matches, −1.5 to
−4.8 s, median −2.94 for −2.44). Then screen in-point = camera in-point + offset; with `--item` the result
gives it as `item.otherSourceIn` (frames of the screen media).

## Time and place from filenames

Cameras put the time in the name: `DJI_20260808201922_0400_D.MP4` → 20:19:22 on 08/08. Use it for the order of
the trip and for place or time labels (`bc:captions-text`). Subfolders may reuse the same clip numbers; the survey
keeps them apart by path.

## Measured record in BashCut

Once clips are project media (`media import`), BashCut measures each file once and keeps the record (by file
content, so later sessions reuse it):

```sh
bashcut media analyze [--media ID]              # job, every video/audio media by default; jobs status JOB_ID
bashcut media list --analysis                   # which media are measured
bashcut media analysis --media ID               # tech, cuts, shots, summary, sound
bashcut media analysis --media ID --samples     # + every picture sample (4 a second)
bashcut media cuts --media ID --add 12.4 --remove 30.1   # correct the cut list (source seconds)
bashcut media speech-map --media ID             # sound spans and gaps, with the floor and separation used
bashcut media transcribe [--media ID]           # job; what is said, kept per file (needs a captions.transcribe plugin)
bashcut media transcript --media ID --as text --format text   # one line per phrase, source seconds
```

What it gives, as numbers (no verdicts; you decide what they mean for this edit):
- `tech`: codec, size, `rotation`, `variableFrameRate` (from the real frame timing; phone screen recordings often
  are), `transferKind` (`pq`/`hlg` = HDR, `log` = needs a grade before it looks right, `unknown` = untagged), bit
  depth, `audioMinusVideoSeconds` (a truncated track).
- `picture.shots`: the camera's own cuts inside a file (a phone edit, a reference video), each with seconds,
  `cutDifference`, `motion` (as in `review shots`) and mean `luma`, `sharpness`, `colourfulness`. One long shot with
  low motion = locked-off: one shot size, as the contact sheet shows. `minScore` (default 0.1) is the cut limit:
  lower it when a soft cut is missing, check the frame, and fix the list with `media cuts`.
- `sound`: `floorDb`, `medianDb`, `peakDb`, `silentShare`, and `active` spans over the floor (sound, not
  necessarily speech: transcribe to know). A clip whose `loudDb` stays near the floor has no usable sound.
- `media speech-map`: the floor and the loud level found in this file, how far apart they are (`separationDb`) and
  the spans and gaps that follow. `separation: none` means the floor and the sound over it do not separate (street
  noise, music under the voice): there are no silences to cut by level there, so read the transcript spans it adds
  (after `media transcribe`) or listen. `levelCoveredByWords` low = loud sound without words (music, wind, crowd).

Use the record for the table's flags and in-points; use the sheet to see what the shots *are*. Only measure what
you will use when the folder is large: `media analyze --media ID` per clip.

## Picking in-points

- Pick by measured sharpness, not by eye on a small sheet: motion blur hides at sheet size (`media analysis
  --samples`: `sharpness` per sample; compare within one clip, it depends on the picture). Look at the frame
  full size before committing to an in-point (`ffmpeg -ss SECONDS -i clip -frames:v 1 /tmp/f.jpg`, then read it;
  once placed, `ui frame F` shows it in the edit).
- Long clips that change inside (timelapse, walks) need more frames: rerun with `--frames 10`.
- Speech: transcribe in BashCut without touching the timeline (`media transcribe --media ID`, then `media
  transcript --media ID --as text --format text`; `--as words` gives each word's `confidence` when the provider
  has it). `captions generate` later reuses it. Speech recognition invents text over music,
  crowd noise and silence ("hãy subscribe kênh…", "cảm ơn các bạn đã theo dõi"): drop lines like that, and treat
  a clip whose only text is that as having no speech. If the speech is in another language than the project,
  say so before cutting on it.

## Into BashCut

After the survey, link and import only the clips you will use (see `bc:edit-workflow`), and write what you found
(coverage gaps, best moments, silent clips) as project facts so later sessions know, for example
`bashcut knowledge set-fact coverage "no wide shot of the market; C0042 has silent audio"`.
