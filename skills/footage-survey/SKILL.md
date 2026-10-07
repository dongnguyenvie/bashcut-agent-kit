---
name: footage-survey
description: Survey footage before editing in BashCut — inventory the clips (capture time, place, orientation, speech) and build contact sheets with BashCut to SEE which shots actually exist, describe them in a closed vocabulary, catch missing coverage, silent audio, broken files and portrait/landscape mixes early, and pick sharp in-points. Use at the start of any edit from raw footage, when choosing clips or moments, or when the cut feels boring and it is unclear whether the problem is the shooting or the editing. Also syncs a camera with a screen recording of the same session by their sound (bashcut media sync). Triggers: "khảo sát footage", "xem footage", "contact sheet", "có những cảnh gì", "đồng bộ", "quay màn hình".
---

# Footage survey

Reply in the user's language. Run this **first**, before promising anything about the edit. Everything here is a
BashCut command on project media: no ffmpeg, no scripts. Import the clips first (`media import /abs/clip --base-rev
N`, one file per call, absolute paths, without `--place`); importing does not touch the timeline.

```sh
bashcut context get                               # analysis: running jobs, media not measured/transcribed/described
bashcut media inventory                           # per clip, folder and project: length, size, orientation, capture
                                                  # time, GPS, device, speech, what is measured/transcribed/described
bashcut media analyze                             # job: measure every file once (kept by content); jobs status JOB_ID
bashcut media frames --sheet                      # contact sheets of every clip with a picture (8 frames each)
bashcut media frames --sheet --media A,B --count 12   # more frames for clips that change inside (walks, timelapses)
bashcut media frames --sheet --every 2 --media ID     # a frame every 2 s of one file (a long take, a rendered draft)
```

`media frames --sheet` returns `sheets [{path, cells}]`: grids of frames (8 × 3 portrait, 6 × 6 landscape;
`--columns`, `--rows`, `--size` change them). Each cell is labelled `<cell> <file> <m:ss.s>`, e.g. `14 C0042
0:33.0`; the label colour switches between yellow and cyan at each new clip, and `cells` maps every cell number back
to its media ID, exact source frame and second.

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

## Things the inventory flags

- **Broken files**: `media import` refuses a file it cannot read (camera cards hold ~1 KB stub `.MP4`s); a moved
  file shows `fileMissing`. Leave them out.
- **Silent audio**: `hasAudio: false`, or a `media analysis` `sound` whose `loudDb` stays near `floorDb` (−91 dB
  = no sound at all): plan voiceover or music for those clips; don't expect real speech.
- **Portrait and landscape mixed**: `orientation` is the picture as shown (rotation applied; phones often store
  1920×1080 with rotation −90, which is portrait). Check it before choosing the project canvas.
- **fps**: clips at another rate than the project play fine in BashCut, but true slow motion needs 50/60/120 fps
  sources (`media list`: `fps`).
- **Not measured yet**: `totals.notMeasured`, `notTranscribed`, `notDescribed` (and `context get` › `analysis`)
  list what you have not looked at. Say so instead of planning around it.

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

## Time and place

`media inventory` gives `capturedAt` and `location` as the file records them (phones write both; most action
cameras write neither), with `capturedFrom/To` and the places grouped about 100 m apart (`--location-grid` in
degrees) per folder and for the project: "12 min of speech, 3 places, 5 clips not described" comes from one call.
When a file has no capture time, cameras often put it in the name: `DJI_20260808201922_0400_D.MP4` → 20:19:22 on
08/08. Use it for the order of the trip and for place or time labels (`bc:captions-text`). Subfolders may reuse the
same clip numbers; `folder` keeps them apart.

## Describe what you saw

After looking at the sheets, write down each clip's shots so other skills and later sessions can use them without
looking again. Facts only, in a closed vocabulary (unknown fields and values are rejected):

```sh
bashcut media describe /abs/shots.json --media ID --base-rev N    # [--merge] adds to what is there; --clear removes
bashcut media description                                          # coverage: "describedMedia/totalMedia", missing
bashcut media description --media ID                               # the shots, and the measured shots not described
```

```json
[{"start": 0, "end": 4.2, "size": "WS", "angle": "eye", "move": "pan", "direction": "left",
  "subjects": ["market", "vendor"], "people": 3, "onScreenText": false, "confidence": 0.8,
  "bestMoment": 2.6, "looked": [0.5, 2.6, 4.0]},
 {"start": 4.2, "end": 9.0, "size": "CU", "move": "handheld", "subjects": ["bánh mì"], "bestMoment": null}]
```

- Seconds are source seconds of the file (`cells[].seconds`); shots may not overlap. Follow the measured shots
  (`media analysis` › `picture.shots`) where the camera cut; one long take can be split where the picture changes.
- `size` ECU, CU, MCU, MS, MWS, WS, EWS, insert; `angle` eye, high, low, top, dutch, pov, ots; `move` static, pan,
  tilt, push, pull, track, orbit, handheld, zoom, crane; `direction` left, right, toward, away, none.
- `confidence` is how sure you are from what you saw (one frame of a fast move is a guess); `looked` lists the
  frames you actually looked at. No pairings or verdicts ("good opener", "cuts well with C0042"): those belong to
  the plan, not the footage.
- `review shots` then shows each clip's `described` facts on the timeline, so runs of the same size and move are
  visible (`bc:beat-cut`).

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
  full size before committing to an in-point (`bashcut media frame --media ID --at SECONDS`, or `--index N` for an
  exact frame, `--edge first|last`; then read the PNG; once placed, `ui frame F` shows it in the edit).
- Long clips that change inside (timelapse, walks) need more frames: `media frames --sheet --media ID --count 12`,
  or `--from S --to S` for one part.
- One clip's sound and words over time: `bashcut media strip --media ID [--from S --to S]` draws frames, the level,
  the speech-map gaps and the transcript's words on one image.
- Speech: transcribe in BashCut without touching the timeline (`media transcribe --media ID`, then `media
  transcript --media ID --as text --format text`; `--as words` gives each word's `confidence` when the provider
  has it). `captions generate` later reuses it. Speech recognition invents text over music,
  crowd noise and silence ("hãy subscribe kênh…", "cảm ơn các bạn đã theo dõi"): drop lines like that, and treat
  a clip whose only text is that as having no speech. If the speech is in another language than the project,
  say so before cutting on it.

## Into BashCut

After the survey, place only the clips you will use (`media place`, see `bc:edit-workflow`), and write what you found
(coverage gaps, best moments, silent clips) as project facts so later sessions know, for example
`bashcut knowledge set-fact coverage "no wide shot of the market; C0042 has silent audio"`.
