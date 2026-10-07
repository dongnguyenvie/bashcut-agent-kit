---
name: audio-mix
description: Balance sound in a BashCut edit — measure the mix by role first (voice, music under speech and in gaps, SFX against the voice), then clip gain, fades, music bed with ducking under speech, sound effects, choosing and looping music, finding licensed music and SFX (CC0 first, CC BY with a credit line), real speech vs voiceover, and each output's loudness target — using BashCut's own volume, fade, ducking and normalization. Use when loud places drown quiet ones, music comes and goes, voices clash, SFX are needed at cuts, or before export. Triggers: "trộn âm thanh", "cân âm lượng", "nhạc chỗ có chỗ không", "nhạc to quá", "thêm sfx", "âm thanh", "ẩn giọng desktop", "chọn nhạc phù hợp giọng", "tìm nhạc", "nhạc không bản quyền", "nhạc miễn phí", "tải sfx", "meme sound".
---

# Audio mix in BashCut

Reply in the user's language. Mix inside BashCut; never bake a mix with ffmpeg. With a `[Scope]` (Send to Agent),
work only on those items (`bc:edit-workflow`). Commands measure and act; the levels below are ranges with their
source and what moves them. You cannot listen: measure, change, measure again, and report the numbers.

## Tools

| Need | How |
|---|---|
| Clip level | `setProperties` patch `{"volumeDb": -6}` (−120…+24) |
| Fades | `{"fadeIn": 15, "fadeOut": 30}` in frames |
| Volume that changes over time (swell the music at a drop, dip it for one line) | `clip keyframe ITEM --property volume --value -18 --at-frame F` per key (dB, timeline frame inside the item; `--ease linear/in/out/inOut/hold`); keys replace `volumeDb` and stack with fades and ducking. Key audio items, or clips whose sound is not unlinked |
| Silence a clip / a layer | `{"muted": true}` / `layers set TRACK --muted on` |
| Music under speech | music layer: `setTrackProperties` `{"duckingEnabled": true, "duckUnderSpeechDb": -D, "duckAttackFrames": A, "duckReleaseFrames": R}` (ranges below) |
| Loudness per output | `platforms list`: `targets` gives each output preset's target; override one with `setProjectProperties` `{"output": {"targets": {"tiktok": {"integratedLUFS": L, "truePeakDbTP": TP}}}}`; export with `--normalize-audio` (needs `audio.loudness`, core audio-analysis) |
| New layers | `layers add --kind audio --role music` (or `sfx`; voiceover layers: `bc:voiceover`) |

Ducking follows speech on the dialogue and voiceover layers; a muted layer stops ducking music.

## 1. Look before fixing

```sh
bashcut audio mix-measure                  # job, no export, no change: the mix by role
bashcut jobs status JOB_ID
bashcut audio measure --timeline --curve   # job: the whole mix rendered, loudness over time and silent stretches
bashcut audio measure --media ID --curve   # job: one file (a music candidate, a take, an SFX)
```

`audio mix-measure` returns `voice`, `musicUnderSpeech` (voice minus music, LU) and `musicInGaps`, each as
`{median, p10, p90, blocks}`, the same per `speechWindows`, and per sound effect `loudness`, `peakDb`,
`voiceP95` nearby, `deltaDb`, `masked` and onset/peak offsets in frames to the nearest cut, beat and word edge.
Read it before touching any level, decide against the ranges below, change the **ratio** (music `volumeDb`, duck
depth, keyframes), never the master, then measure again (T11 §4). A ducking setting is not the result: a quiet
take can get almost no ducking from the same setting (open-edit, T11 §2), so judge `musicUnderSpeech`, not
`duckUnderSpeechDb`.

## 2. Levels: ranges and what moves them

| Stem | Range (T11 §3) | Moves it |
|---|---|---|
| Voice (real speech or voiceover), per stem before the mix | −16 to −20 LUFS | Level each speaking clip first: cameras can differ by 15–20 dB (kit edits). |
| Music under speech | 5–18 dB under the voice | Less when the music carries the piece (montage-like vlog, sparse speech, low `presenceShare`); more for dense information, a soft voice, music with vocals or strong 1–4 kHz energy, accessibility. Sources: ~5 dB, with ~10 dB reported by viewers as "there is no music" (bestagentkits, outcome); 10–14 (reelmimic); 18–20 (openmontage). |
| Music in speech gaps | gaps longer than ~1.5 s may rise toward voice level; shorter gaps stay ducked | Read `musicInGaps`, not the setting (bestagentkits, video-recap). |
| Duck timing | attack 5–200 ms, release 350–600 ms (frames = ms × fps / 1000) | Fast attack for speech that starts hard; longer release when gaps are short, so the bed does not pump between words. |
| Duck depth (setting) | 6–14 dB | Then check the measured ratio. |
| SFX, relative to the voice's p95 | subtle UI −16…−12, transitions −14…−8, impacts and memes −8…−3 dB | By role (ghost-editor). Files differ by 20 dB, so measure the file. |
| SFX density | 6–12 subtle per minute plus 1–3 memes (ghost-editor); none for a calm tutorial | Genre (T11 §7). Never the same sample twice in a row. |
| SFX sync | audible peak within 2 frames of its anchor | A correctness rule (guizang, shotcraft); `mix-measure` gives the offsets. |
| Joins, music tail | joins 10–40 ms fades; music tail 1–5 s | Tail by ending style. |

Examples from our edits (not targets): SFX peaking around −21 dB were audible without covering words; a soft
piano track (presence share 0.006) sat under a calm male voice ducked 8 dB with nothing to fix.

## Two mixing styles

**Review / food / talking**: one structured song under everything with ducking, a whoosh or pop on the hook's
special transition, SFX matched to on-screen motion. Music sits near the deep end of the range under speech.

**Narrative / cinematic**: music is not a constant bed. Loud in montage, ducked while information is spoken. No
whoosh on ordinary cuts. SFX only with a reason (shutter on a photo cut, real foley pushed up on a montage cut).
Silence is a tool: drop the music 1.5–3 s before the punchline (split the music clip and fade out), leave the most
honest line with no music. Keep the music continuous across section changes.

## Library first

- `bashcut library list --kind audio --tag calm` shows music, SFX and ambience saved in the project, on this Mac or
  in plugin packs, with role, length, BPM, LUFS and loop flag. `bashcut library preview ID` plays one for the user
  (you cannot hear it).
- `bashcut library place ID --at-frame F --duration N --base-rev N` puts it on the Music or SFX layer (added when
  missing); a `loopable` sound fills a longer duration back to back, another plays once.
- Missing BPM, loudness or sound landmarks: `bashcut library analyze ID` (job).
- A track or SFX that worked:
  `bashcut library save-selection --kind audio --name "Lofi bed" --item CLIP --tags calm,lofi` (or `--media ID`).
  Fix wrong tags or flags with `library update ID --tags ...` or `--params '{"loopable": false}'`.
- Nothing fits: `bashcut library search "soft whoosh" --kind audio` when a plugin provides it; check each
  candidate's licence (below), then `library add --from-result JOB:N`. Never generate music.

## Choosing music

- Prefer **one structured track** at least as long as the video (intro → build → drop → break) and align the
  drop with the hook's special moment. A flat loop measured as perfectly even was still judged boring.
- Songs with a quiet intro dip ~11 dB every time they loop: trim the intro (`trim` the clip's start or `slip`)
  before repeating it.
- Put song changes and loop points **on a hard picture cut**: the eye takes the scene change and the ear
  ignores the join.
- Under a talking voice, measure the candidates and the voice: `bashcut audio measure --media ID` (a job; `jobs
  status JOB_ID` gives `loudnessRangeLU` and `presenceShare`, the energy share at 1–4 kHz where consonants carry the
  words). Import candidates with `media import` first; they need not be placed. Example: 0.006 (soft piano and
  strings, LRA 2 LU) and 0.046 (lofi, LRA 5.3) against a voice at 0.063; the 0.006 track needed no fix. Compare
  shares between tracks; they are not exact fractions: the band edges fall 24 dB/octave (−6 dB at the edge), so
  tones at 2 and 3 kHz alone read 0.684.
- Under speech use instrumental music; a song with lyrics masks the words. Never use songs from a platform's
  library (TikTok and CapCut trending sounds): they are muted when the video is posted on another platform or
  run as an ad.

## Finding music and SFX online

Policy (decided): **CC0 first; CC BY only with a credit line; no NC.** No Epidemic Sound, no AI music (Suno,
Udio, MusicGen, `library generate` for music). Dead ends: Bensound, BBC SFX, ProductionCrate (T21 §3).

| Source | How | Licence |
|---|---|---|
| **Openverse API** (Jamendo, ccMixter, Freesound, Wikimedia) | `curl`, no key, searchable, gives licence and duration | per file: CC0 free; CC BY needs the credit line (T21 §3) |
| **Pixabay Music / Sound Effects** | no API, blocks `curl`: give the user search links, **the user downloads by hand** | Pixabay Content License: commercial use, no credit; some tracks are registered in Content ID, so keep the page URL as proof (T21) |
| **Mixkit** (music and SFX) | no API: **the user downloads by hand** from category pages | Mixkit free licences: commercial use, no credit; not resold or shared as stand-alone sound (T21) |
| **tiengdong.com** (Vietnamese meme sounds: "ting ting", "bụp bụp", "oh nooo") | the user picks one | "All rights reserved", many clipped from shows: organic posts only, never ads or monetised YouTube (T21) |

- **Openverse**: `curl "https://api.openverse.org/v1/audio/?q=lofi&license=cc0,by&category=music&page_size=20"`
  (SFX: drop `category`) → `results[]` with `title`, `license`, `license_version`, `creator`, `source`, `duration`
  (ms), `url`. Freesound files come from a slow CDN (~12 s for 1 MB); download only the ones you will use.
- **Pixabay** links for the user: `https://pixabay.com/music/search/<q>/`, `https://pixabay.com/sound-effects/search/<q>/`
  (Vietnamese pages under `/vi/`). Good keywords: "lofi chill", "upbeat corporate", "cinematic ambient", "meme".
  **Mixkit**: `https://mixkit.co/free-stock-music/tag/<lo-fi|chill|upbeat|cinematic>/`,
  `https://mixkit.co/free-sound-effects/<whoosh|pop|ding|click>/`.
- Ask before downloading (list the files, source, licence, size). Save under the project's `media/audio/` and
  record source, licence and, for CC BY, the credit line ("Title" by Creator, licence, link) in
  `media/audio/index.json`; tell the user the credit goes in the video description. Files the user downloaded:
  ask for the page URL, import them and record the same. Keep what worked:
  `bashcut library add --kind audio --file /abs/media/audio/x.mp3 --name "Soft pop" --source URL --license "CC0" --tags pop`.

## Real speech vs voiceover

- Never two voices at once. Keep a gap between real speech and AI voiceover (0.3 s in our edits; the project's
  `review.voiceoverMarginSeconds` makes review check it).
- B-roll under voiceover often has people talking: lowering it to −15/−28 dB still left intelligible words.
  Mute those clips' sound under the voiceover (split at the voiceover's edges, mute only that piece), or use a
  vocal-removal plugin if one is installed (`plugins search --capability ...`). Keep the original sound
  everywhere the voiceover is silent: stripping it everywhere made a cameraman's real voice disappear.
- After the mix, report seconds of real speech vs voiceover, and listen to every voiceover window.

## Screen recordings ("ẩn giọng desktop")

- Speech comes from the presenter's camera; mute the screen recording's clips (`{"muted": true}`). Its sound held
  the same voice through the room mic 2.5 s late (an echo) plus the desktop's own sound.
- The camera mic also hears the laptop speaker: when the demo plays the tool's output, drop those sentences;
  they are lines of the output's script, not the presenter's.
- When the output's sound is wanted (a hook showing the result), place the output file itself on an audio layer
  at the offset `media sync` gives (`bc:footage-survey`), never the speaker leak. Start the music bed after it.

## SFX

- Size the sound to the motion: soft whoosh for a slow move, short whoosh for a hard zoom, pop for stickers and
  labels, ding on a final number, hit on the shocking line. Never the same whoosh on every cut.
- The loudest point of a whoosh lands on the cut; a riser ends on the reveal. Check with the `mix-measure`
  offsets; report them, and move an effect only when you decide to.
- `masked: true` means the effect is under the nearby voice level: raise it or move it off the words.
- Use files the user owns or that are licensed (the user's SFX folder, the Audio panel, the library, then the
  sources above). Ask before downloading any.

## Loudness and verify

- **Each export is normalized to its own preset's target**, not one number for all: read `platforms list`
  (`targets`). Values seen: −14 LUFS is the common short-form playback reference, −16 for podcast, web or
  voice-only, broadcast −23/−24; true peak −1 to −1.5 dBTP, lower when the platform re-encodes (T11 §3). Override
  a preset only for a reason the user gave (`output.targets`); a recipe never sets it.
- Before export: `audio measure --timeline --curve` for silences and jumps between sections (one source keeps
  chapters within 2 LU, another warns at ±1 LU, T11 §3), and `review run` (voices too close, music not ducked,
  dead air, a music bed that drops out, speech coverage).
- After a normalized export, read the receipt (`export status`: `lufs`, `truePeakDbTP`); `review run` checks it
  against that export's target. Renderers can move the true peak, so trust the delivered file, not the setting.
- Report the numbers with "I cannot listen", and list the joins and voiceover windows for the user to play
  (`ui seek` takes them there).
