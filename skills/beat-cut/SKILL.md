---
name: beat-cut
description: Give a BashCut edit rhythm by measurement — read the music's beat grid and energy or the speech's word edges and rate, choose cut points and shot lengths per section from sourced ranges, cut, then check rhythm, runs and beat/word sync (review shots, review sync) and adjust; fake extra shot sizes with punch-in reframes sized from each clip's measured zoom headroom when the footage lacks coverage. Use when editing a vlog or montage to music, when the cut feels flat, slow, rushed or boring, when cuts miss the beat, or when consecutive cuts look the same because the camera was locked off. Triggers: "cắt theo nhịp", "cắt theo beat", "khớp nhạc", "lệch nhịp", "bản dựng phẳng", "nhàm", "punch-in".
---

# Beat cutting and punch-in reframes

Reply in the user's language. The beat gives energy; punch-ins give variety. With a `[Scope]` (Send to Agent),
work only on those items (`bc:edit-workflow`).

The loop: **measure → choose → cut → measure again → adjust**. BashCut measures and acts; the numbers for
choosing are here, as ranges with the reason they vary and where they come from (T07 pacing, T03 shot grammar,
T08 effects: the kit's research notes; the names inside are the editors' kits they were seen in). They are
starting points, not targets: a reference the user gives, measured with `bc:style-study`, wins over them.

## 1. Measure what drives the cuts

| Video | Cuts follow | Measure |
|---|---|---|
| Montage, travel teaser, MV, music-led | the beat grid and the music's energy | `beats detect`, `beats grid`, `audio energy` |
| Talking, review, food with speech, tutorial | sentence and phrase edges; picture follows the words | `transcript words --heard`, `speech rate` |

For speech-led videos, do **not** lay cuts on the grid first (one example: a draft built on the grid had 10
silent gaps, 21 s). Build the chain of spoken lines, cut picture at phrase ends, then let music sit under it.
`transcript words --heard` gives each word's frames through the clips as they are now and the gap before it, so a
cut lands in the pause between sentences. `speech rate` gives each speaker's phrase rate (p10/p50/p90) in the
language's unit: denser speech carries more per shot, so shots can hold longer (T07 §3). When a music hit follows
a line, leave 0.1–0.6 s of air after the voice (bestagentkits ≥0.12 s, video-use 400–600 ms; T07 §3).

Long pauses in one talking clip: the Silence Markers plugin cuts them in one undoable edit (`bashcut plugins run
bashcut.silence-markers.remove --params '{"detect":"auto","minSilenceMs":400,"paddingMs":100}'` with the clip
selected; `mark` only adds section markers). `plugins actions silence` shows its parameters: an older version has
no `detect` and refuses it, so leave it out there. With `detect: auto` it uses the clip's `media speech-map` when
the file is measured and speech separates from the floor, and the dBFS threshold otherwise; `data.detection` says
which and why. `data.removed` lists every cut span longest first with its source seconds: look at the long ones
(`media strip --media ID --from S --to S`) before keeping the edit, since a long "pause" can be a reaction, a laugh
or b-roll sound. The numbers in the example are one starting point: shorter `minSilenceMs` for a fast talker (check
`speech rate`), more `paddingMs` for a slow one. Then measure again (section 6).

## 2. Read the music

Place the music on its layer first, then:

```sh
bashcut beats detect --media MUSIC_MEDIA_ID     # job; needs an audio.beats provider (core audio-analysis)
bashcut jobs wait JOB_ID --timeout 25         # bpm and beat frames; stored as the media's grid
bashcut beats grid --media MUSIC_MEDIA_ID       # strengths, downbeats, confidence, fit, half/double alternates
bashcut audio energy --media MUSIC_MEDIA_ID     # job: the curve — levelDb, onset, fullness per step
```

Judge the grid before cutting on it. You cannot listen, so a weak grid means: ask the user, or cut on phrases.

| Fact | Reads strong | Reads weak → do |
|---|---|---|
| `fit.rmsErrorMs` | small next to a frame (33 ms at 30 fps); other kits gate at mean <10 ms (shotcraft) or median <15 ms (jianshuo) (T07 §3) | tempo drifts or changes: detect per song or section, cut on phrases |
| `confidence` | the tempo stands out; no published threshold, so compare with the alternates | rubato, ambient or speech-heavy: use `audio energy` lifts and drops and phrases |
| `alternates` (half, double) | one tempo clearly stronger | similar strength: pick by how fast the music moves, ask the user. One example: 58.7 BPM detected, truth 117 (the bar, not the beat) |
| `downbeats`, `beatsPerBar`, `phaseScores` | one phase clearly highest | close scores: phase is uncertain; a full-band grid can lock onto hi-hats and put every cut half a beat late (hyperframes; T07 §4). Ask the user to check that a downbeat lands on an audible hit (`ui seek F`) |
| `strengths` | — | a candidate pool, not a cut list: "the hit table is a candidate pool, not a trigger" (shotcraft; T07 §2) |

A mix of several songs has several tempos: detect each media; `beats grid` reads each one.

Find the moments in the `audio energy` curve yourself: a **lift** is levelDb or fullness rising several dB over
~2 s against the 2 s before (onset density usually rises with it), a **drop** the reverse, a **breath** a short dip
(0.5–2 s) before a lift. Snap each to the nearest beat or downbeat (`beats grid`), and place it with `timeline`
(`at` + (second − `fromSeconds`) × fps). They are pointers, not cut points. Use them to plan a section's shape: build →
breath → hit on a downbeat → hold (reelmimic; T07 §2). One breath of 0.5–2 s before the main hit, a payoff hold of
at least 1 s (T07 §7).

## 3. Choose shot lengths and cut points

Pick a band per section, then move inside it by content:

| Genre / section | Median shot | Source |
|---|---|---|
| Fast short-form, montage, ads, food inserts | 0.6–2 s | assafkip, iart, znyupup (T07 §3) |
| Speech-led vertical | 2–4 s | T03 §3 |
| Narrative, vlog, b-roll travel | 2.5–6 s (travel 3–4.5 s) | higgsfield, vox-director, vlog plugin (T07 §3, T03 §3) |
| Calm vs urgent tone | 2–4 s vs 0.4–1 s | saas-motion-kit (T07 §3) |
| Hero hold | one per film, 1.5–2.5× the film's average | higgsfield (T07 §3) |

- **Shorter** with high-motion, low-information shots and on `audio energy` lifts and drops; **longer** with dense
  speech, text to read, landscapes, calm tone, and after a breath (T07 §3).
- Cuts per minute seen: dialogue 14–16 (davinci, "descriptive, NOT a target"), daily vlog 8–12, review 10–14,
  travel 13–16 (vlog plugin), food TikTok 30–40, cinematic vlog 12–20 (style-study) (T07 §3). Compare, don't aim.
- **Beats per shot 2–8**, fewer at peaks; don't cut on every beat (opuscar). Cuts on every beat for more than ~8
  beats usually read as noise (T07 §7). Seconds per shot = beats × 60 / BPM, so the same count feels different
  per song (4 beats: 2 s at 120 BPM, 2.7 s at 90): choose the count from the section's band, not a fixed pattern.
- Vary the rate by section: one acceleration, one breath, a hero hold (T07 §4). Opening: hook first for short
  form, establish first for narrative, real estate or a travel arrival (T03 §3); the plan says which.

One example (a travel/food vlog, not a rule): cold open 6 beats (~2.6 s), busy market and street sections 4 beats
(2 on peaks, ~1.6–2.0 s), quiet ending 4 beats on slow music (~3.5–4 s); a uniform 3.6 s cut felt flat whatever
the content; pieces under ~0.6 s were merged. Its cold open was ~8 s of three shots (the ending shot, the loudest,
the quietest), then chronological with a section marker (`upsertSection`) and a place label (`bc:captions-text`)
at each location change.

## 4. Cut in one apply

Plan in beats and seconds, convert to frames last (shotcraft). A beat's timeline frame = the music item's `at` +
(beat second − its source-in second) × fps at speed 1; `beats grid` also gives `downbeatFrames` on the timeline.
Per section: cut points → assign (clip, in-point) from that section's moments in turn → one `timeline apply` with
`split`/`trim`/`delete` (ripple) or `insert` operations, labelled per section. Spread in-points across the
sources; never reuse one spot. `roll` nudges a cut onto a beat or a word gap without changing the total length;
`slip` changes what a clip shows without moving it.

## 5. Punch-in reframes from measured headroom

The most effective change when the footage has one angle. Read each clip's `scale` in `timeline get` (also on
every row of `review shots`): `fit`, `baseScale`, `zoom`, `maxZoom`, `pixelRatio` and `pixelRatioAtMaxZoom`
(output pixels per source pixel; over 1 is upscaled), `maxZoomNative` (the largest zoom before upscaling) and
`frameCoverage`.

- **Headroom is `maxZoomNative`**, per clip: about 2 for 4K in a 1080 landscape project, 1.0 for same-resolution
  footage (every punch-in upscales), about 1.125 for a 4K landscape clip filling a 1080×1920 frame.
- **The step** depends on what it is for (T08 §3): a size change at a cut 1.15–1.3, a snap punch on a word
  1.1–1.15, a slow drift 1.03–1.07 over the shot. Aim for one described size step (wide → medium → close, T03 §7)
  and stay within the headroom where you can.
- Past the headroom it is a judgement, not a limit: look at `ui frame F` (and `ui frames --compare source --items
  CLIP`) before keeping it. One example: on same-resolution footage 1.28 still looked acceptable; beyond it got soft.
- Pan and tilt need margin: at zoom 1.0 with `frameCoverage` 1 there is none. Place the crop on what matters, seen
  in the frame, never a blind centre (`bc:effects`, Reframe).
- Never punch in on signs or text (one example: 1.28 cut "Lẩu Bò Nồi Đất" to "Nồi Đấ").
- A patch replaces the whole `transform`: always send zoom, pan and tilt together.

```json
{"op":"setProperties","item":"CLIP","patch":{"reframePreset":"custom","transform":{"zoom":1.2,"pan":40,"tilt":-20}}}
```

Neighbouring cuts should not keep the same framing unless it is a choice. One example rotation as (zoom, pan, tilt),
from one edit: (1.00,0,0) (1.28,60,−25) (1.14,−50,15) (1.22,0,30) (1.00,0,0) (1.18,70,10)
(1.26,−65,−20) (1.10,40,25). Talking heads: punch-ins every 4–6 s were seen (vlog talking-head recipe; ghost-editor
4–6 per 60 s reel; T08 §3); time them to sentence starts, not a clock.

## 6. Measure again, then adjust

```sh
bashcut review measure                                    # job: motion per shot, both sides of every hard cut
bashcut review shots --summary                            # rhythm, shares; per shot the cut: kind, framing, sameFraming
bashcut review sync --bins                                # cuts against beats and word edges, with p10/p90
bashcut review sync --events cuts,sfx --rendered          # after an export of this revision
```

- **Rhythm** (`rhythm.overall` and per section): median, cv and cutsPerMinute against the band you chose.
  6+ consecutive shots whose lengths vary under ~0.15 cv (davinci; compute it from the shots' `seconds`) or a `mode`
  share over ~60% (saas-motion-kit) is monotony: break it unless the calm is intended (T07 §3).
- **Runs of the same described size and move** (count them from each shot's `described`): 2 in a row → look; 3+ → change size, angle or relation, or say
  why (a motif, a locked-off talk) (higgsfield; T03 §3). A talking head is one setup: punch-ins make the change.
- **Cut facts**: `sameSetup` with a small `sourceGapSeconds` is a jump cut (punch-in or cutaway); `sameFraming` in
  the shot's `cut` means the punch-in is missing; `motion` and `cameraMove` show stillness and repeated moves.
- **Sync to beats**: hard cuts within ±1–2 frames; 3 frames is perceptible (shotcraft pass ≤3 f, ideal ≤1.5 f;
  T07 §3). A median offset away from 0 with a tight p10–p90 means the grid's phase or the whole music is off: shift
  once or recheck the downbeat, not cut by cut. A wide spread means cuts were placed off the grid: `roll` them.
- **Sync to words**: a cut that falls `inside` a word clips it; move it into the gap.
- **Rendered**: `lagMs` and `driftMsPerMinute` show whether the export still lands where the timeline does.

Then look: `ui frame F` on three consecutive cuts in one scene (three different shot sizes?) and `review window F`
across a doubtful cut (frames, cuts, level and words in one picture). `review run` lists gaps, jump cuts, very
short shots, long static shots and frozen picture. Adjust with `roll`/`slip`, measure again; stop after 3 rounds
or when a round changes nothing, and say what is left and why. Lock the cut before `bc:audio-mix`.
