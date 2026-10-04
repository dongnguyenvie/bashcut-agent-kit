---
name: bashcut-audio-mix
description: Balance sound in a BashCut edit — clip gain, fades, music bed with ducking under speech, sound effects, choosing and looping music, real speech vs voiceover, and the final loudness target — using BashCut's own volume, fade, ducking and normalization. Use when loud places drown quiet ones, music comes and goes, voices clash, SFX are needed at cuts, or before export. Triggers: "trộn âm thanh", "cân âm lượng", "nhạc chỗ có chỗ không", "nhạc to quá", "thêm sfx", "âm thanh", "ẩn giọng desktop", "chọn nhạc phù hợp giọng".
---

# Audio mix in BashCut

Reply in the user's language. Mix inside BashCut; never bake a mix with ffmpeg.

## Tools

| Need | How |
|---|---|
| Clip level | `setProperties` patch `{"volumeDb": -6}` (−120…+24) |
| Fades | `{"fadeIn": 15, "fadeOut": 30}` in frames |
| Volume that changes over time (swell the music at a drop, dip it for one line) | `clip keyframe ITEM --property volume --value -18 --at-frame F` per key (dB, timeline frame inside the item; `--ease linear/in/out/inOut/hold`); keys replace `volumeDb` and stack with fades and ducking. Key audio items, or clips whose sound is not unlinked |
| Silence a clip / a layer | `{"muted": true}` / `layers set TRACK --muted on` |
| Music under speech | music layer: `setTrackProperties` `{"duckingEnabled": true, "duckUnderSpeechDb": -12, "duckAttackFrames": 6, "duckReleaseFrames": 15}` |
| Final loudness | `setProjectProperties` `{"audio": {"targetLUFS": -14, "normalizeEnabled": true}}`, export with `--normalize-audio` (needs `audio.loudness`, core audio-analysis) |
| New layers | `layers add --kind audio --role music` (or `sfx`, `bashcut-voiceover`) |

Ducking follows speech on the dialogue and voiceover layers; a muted layer stops ducking music.

## Levels that worked

| Stem | Level |
|---|---|
| Real speech / location sound | around −16 to −20 dB RMS while talking, always above music |
| Voiceover | ~−16 LUFS |
| Music under speech | 10–18 dB below the voice (median ~12) |
| Music alone (montage) | at or above voice level |
| SFX | peaks ~−21 dB: audible, never covering words |
| Final | −14 LUFS, true peak ≤ −1 dBTP |

Real sound from different cameras can differ by 15–20 dB: level each spoken clip with `volumeDb` first, then
let normalization set the total.

## Two mixing styles

**Review / food / talking**: one structured song under everything with ducking, a whoosh or pop on the hook's
special transition, SFX matched to on-screen motion.

**Narrative / cinematic**: music is not a constant bed. Loud in montage, ducked 10–14 dB while information is
spoken. No whoosh on ordinary cuts. SFX only with a reason (shutter on a photo cut, real foley pushed up on a
montage cut). Silence is a tool: drop the music 1.5–3 s before the punchline (split the music clip and fade
out), leave the most honest line with no music. Keep the music continuous across section changes.

## Choosing music

- Prefer **one structured track** at least as long as the video (intro → build → drop → break) and align the
  drop with the hook's special moment. A flat loop measured as perfectly even was still judged boring.
- Songs with a quiet intro dip ~11 dB every time they loop: trim the intro (`trim` the clip's start or `slip`)
  before repeating it.
- Put song changes and loop points **on a hard picture cut**: the eye takes the scene change and the ear
  ignores the join.
- Under a talking voice, measure the candidates and the voice: `bashcut audio measure --media ID` (a job; `jobs
  status JOB_ID` gives `loudnessRangeLU` and `presenceShare`, the energy share at 1–4 kHz where consonants carry the
  words). Import candidates with `media import` first; they need not be placed. Measured 0.006 (soft piano and
  strings, LRA 2 LU) and 0.046 (lofi, LRA 5.3) against a voice at 0.063: the 0.006 track sat under a calm male
  voice ducked 8 dB with nothing to fix (−13.7 LUFS export). Compare shares between tracks; they are not exact
  fractions: the band edges fall 24 dB/octave (−6 dB at the edge), so tones at 2 and 3 kHz alone read 0.684.
- Check the music's licence before using it in a published video.

## Real speech vs voiceover

- Never two voices at once. Keep ≥ 0.3 s between real speech and AI voiceover.
- B-roll under voiceover often has people talking: lowering it to −15/−28 dB still leaves intelligible words.
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
  at the offset `media sync` gives (`bashcut-footage-survey`), never the speaker leak. Start the music bed after it.

## SFX

- Size the sound to the motion: soft whoosh for a slow move, short whoosh for a hard zoom, pop for stickers and
  labels, ding on a final number, hit on the shocking line. Never the same whoosh on every cut.
- The loudest point of a whoosh lands on the cut; a riser ends on the reveal.
- Use files the user owns or that are licensed (the user's SFX folder, the Audio panel). Ask before
  downloading any.

## Verify

You cannot listen, so: `review run` (voices too close, speech coverage), list the joins and voiceover windows
for the user to play (`ui seek` takes them there), and read the loudness in
the export receipt (`export status`: `lufs`, `truePeakDbTP`).
