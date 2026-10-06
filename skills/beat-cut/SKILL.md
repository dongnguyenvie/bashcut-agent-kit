---
name: beat-cut
description: Give a BashCut edit rhythm — cut picture on the music's beat grid or on sentence boundaries, vary the cut rate by section, and fake extra shot sizes with punch-in reframes when the footage lacks coverage. Use when editing a vlog or montage to music, when the cut feels flat, slow or boring, or when consecutive cuts look the same because the camera was locked off. Triggers: "cắt theo nhịp", "cắt theo beat", "bản dựng phẳng", "nhàm", "punch-in".
---

# Beat cutting and punch-in reframes

Reply in the user's language. The beat gives energy; punch-ins give variety. Use both. With a `[Scope]` (Send to Agent), work only on those items (`bc:edit-workflow`).

## 1. Choose what drives the cuts

| Video | Cut on |
|---|---|
| Montage, travel teaser, music-led | the beat grid |
| Talking, review, food with speech, tutorial | sentence and phrase boundaries; picture follows the words |

For speech-led videos, do **not** lay cuts on the grid first: one draft built on the grid had 10 silent gaps
(21 s). Build the chain of spoken lines, then cut picture at phrase ends, then let music sit under it.

## 2. Beat grid

Place the music on its layer first, then:

```sh
bashcut beats detect --media MUSIC_MEDIA_ID        # job; needs an audio.beats provider (core audio-analysis)
bashcut jobs status JOB_ID                         # bpm and beat frames; also stored as the media's beatGrid
```

- A result under ~75 BPM is usually the **bar**, not the beat (measured 58.7, truth 117). Double it when the
  music clearly moves faster.
- Right BPM with the wrong phase still misses. You cannot listen: ask the user to check that the first beat
  lands on an audible hit (`ui seek` puts the playhead there for them).
- A mix of several songs has several tempos: detect per song.

## 3. Beats per cut

Vary the cut rate by section, never one rate for the whole video:

| Section | Beats per cut | Real result |
|---|---|---|
| Cold open | 6 | ~2.6 s, slow enough to orient |
| Busy section (market, street, food) | 4 (or 2 on peaks) | ~1.6–2.0 s |
| Quiet ending | 4 on slow music | ~3.5–4 s |

A uniform 3.6 s cut felt flat whatever the content. Merge pieces shorter than ~0.6 s.

## 4. Build the cut in one apply

Per section: cut points from the grid → assign (clip, in-point) from that section's moments in turn → one
`timeline apply` with `split`/`trim`/`delete` (ripple) or `insert` operations, labelled per section. Spread
in-points across the sources; never reuse one spot. Use `roll` to nudge a cut onto a beat without changing the
total length, and `slip` to change what a clip shows without moving it.

## 5. Punch-in reframes

The most effective single change when footage has one angle. Give consecutive cuts different shot sizes:

```json
{"op":"setProperties","item":"CLIP","patch":{"reframePreset":"close","transform":{"zoom":1.3,"pan":0,"tilt":0}}}
```

Presets: `wide` 1.0, `medium` 1.15, `close` 1.3, `left` 1.22 / pan −120, `right` 1.22 / pan +120. A rotation
that worked, as (zoom, pan, tilt): (1.00,0,0) (1.28,60,−25) (1.14,−50,15) (1.22,0,30) (1.00,0,0) (1.18,70,10)
(1.26,−65,−20) (1.10,40,25). Never give two neighbouring cuts the same framing.

- Up to ~1.28 when source and output are the same resolution; beyond that it gets soft. 4K sources in a 1080
  project allow up to 2×.
- Pan and tilt only when zoomed; at 1.0 there is no margin.
- Never punch in on signs or text: 1.28 cut "Lẩu Bò Nồi Đất" to "Nồi Đấ".
- Patches replace the whole `transform`: always send zoom, pan and tilt together.

## 6. Structure that worked

Cold open ~8 s with three shots: the ending shot, the loudest shot, the quietest shot. Then chronological, a
section marker (`upsertSection`) and a place label (`bc:captions-text`) at each location change.

## Verify

Render three consecutive cuts in one scene with `ui frame F` and read the PNGs: three different shot sizes? Then
`review measure`, then `review run`: gaps, jump cuts (a punch-in fix), very short shots, long static shots and frozen
picture. Lock the cut before `bc:audio-mix`.
