---
name: audio-mix
description: Balance sound in a BashCut edit — clip gain, fades, music bed with ducking under speech, sound effects, choosing and looping music, finding licensed music and SFX online (Mixkit, Openverse, Pixabay), real speech vs voiceover, and the final loudness target — using BashCut's own volume, fade, ducking and normalization. Use when loud places drown quiet ones, music comes and goes, voices clash, SFX are needed at cuts, or before export. Triggers: "trộn âm thanh", "cân âm lượng", "nhạc chỗ có chỗ không", "nhạc to quá", "thêm sfx", "âm thanh", "ẩn giọng desktop", "chọn nhạc phù hợp giọng", "tìm nhạc", "nhạc không bản quyền", "nhạc miễn phí", "tải sfx", "meme sound".
---

# Audio mix in BashCut

Reply in the user's language. Mix inside BashCut; never bake a mix with ffmpeg. With a `[Scope]` (Send to Agent), work only on those items (`bc:edit-workflow`).

## Tools

| Need | How |
|---|---|
| Clip level | `setProperties` patch `{"volumeDb": -6}` (−120…+24) |
| Fades | `{"fadeIn": 15, "fadeOut": 30}` in frames |
| Volume that changes over time (swell the music at a drop, dip it for one line) | `clip keyframe ITEM --property volume --value -18 --at-frame F` per key (dB, timeline frame inside the item; `--ease linear/in/out/inOut/hold`); keys replace `volumeDb` and stack with fades and ducking. Key audio items, or clips whose sound is not unlinked |
| Silence a clip / a layer | `{"muted": true}` / `layers set TRACK --muted on` |
| Music under speech | music layer: `setTrackProperties` `{"duckingEnabled": true, "duckUnderSpeechDb": -12, "duckAttackFrames": 6, "duckReleaseFrames": 15}` |
| Final loudness | `setProjectProperties` `{"audio": {"targetLUFS": -14, "normalizeEnabled": true}}`, export with `--normalize-audio` (needs `audio.loudness`, core audio-analysis) |
| New layers | `layers add --kind audio --role music` (or `sfx`; voiceover layers: `bc:voiceover`) |

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

A quick three-tier check that matches the table (peaks while playing): voice −5 to −3 dB, SFX around −12 dB,
music around −22 dB when nothing ducks it. If the music bed peaks above about −18 dB under speech, it is too loud.

## Two mixing styles

**Review / food / talking**: one structured song under everything with ducking, a whoosh or pop on the hook's
special transition, SFX matched to on-screen motion.

**Narrative / cinematic**: music is not a constant bed. Loud in montage, ducked 10–14 dB while information is
spoken. No whoosh on ordinary cuts. SFX only with a reason (shutter on a photo cut, real foley pushed up on a
montage cut). Silence is a tool: drop the music 1.5–3 s before the punchline (split the music clip and fade
out), leave the most honest line with no music. Keep the music continuous across section changes.

## Library first

- `bashcut library list --kind audio --tag calm` shows music, SFX and ambience saved in the project, on this Mac or
  in plugin packs, with role, length, BPM, LUFS and loop flag. `bashcut library preview ID` plays one for the user
  (you cannot hear it).
- `bashcut library place ID --at-frame F --duration N --base-rev N` puts it on the Music or SFX layer (added when
  missing); a `loopable` sound fills a longer duration back to back, another plays once.
- Missing BPM or loudness: `bashcut library analyze ID` (job).
- A track or SFX that worked:
  `bashcut library save-selection --kind audio --name "Lofi bed" --item CLIP --tags calm,lofi` (or `--media ID`).
  Fix wrong tags or flags with `library update ID --tags ...` or `--params '{"loopable": false}'`.
- Nothing fits: `bashcut library search "soft whoosh" --kind audio` (or `library generate`) when a plugin provides
  it; check each candidate's licence, then `library add --from-result JOB:N`.

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
- Check the music's licence before using it in a published video (see "Finding music and SFX online").
- Under speech use instrumental music; a song with lyrics masks the words. Never use songs from a platform's
  library (TikTok and CapCut trending sounds): they are muted when the video is posted on another platform or
  run as an ad.

## Finding music and SFX online

When the library has nothing that fits, try the sources in this order (tested October 2026 with `curl`):

| # | Source | Access | Licence |
|---|---|---|---|
| 1 | **Mixkit** (music and SFX) | `curl` works, no key; pages respond in ~0.3 s and files download in < 0.5 s | Mixkit free licences: commercial use, no credit; not resold as stand-alone sound |
| 2 | **Openverse API** (Freesound, Jamendo, …) | `curl`, no key, searchable, gives licence and duration | per file: CC0 is free; CC BY needs a credit line in the description; `license_type=commercial` filters out NC |
| 3 | **Pixabay Music / Sound Effects** (290k+ tracks, many instrumental Lo-Fi, Upbeat, Cinematic) | blocks `curl` (403): use a browser tool or ask the user to download | Pixabay Content License: commercial use, no credit; a few tracks are registered with Content ID, so keep the track's page URL as proof |
| 4 | **tiengdong.com** (Vietnamese meme sounds: "ting ting", "bụp bụp", "oh nooo") | `curl` works, direct mp3 links in the page | "All rights reserved", and many memes are clipped from shows: only when the user picks one, only for organic posts, never ads |

- **Mixkit**: SFX by category `https://mixkit.co/free-sound-effects/<whoosh|pop|ding|click|swoosh|…>/`, music by
  tag `https://mixkit.co/free-stock-music/tag/<lo-fi|chill|upbeat|cinematic|…>/` (redirects to the genre page).
  The page HTML holds the files: `grep -oE 'https://assets\.mixkit\.co/[^"]+\.mp3'` (SFX `…-preview.mp3` is the
  whole sound at ~300 kbps; music `music/<id>/<id>.mp3` is the whole track at 256 kbps). The site search finds
  little; use categories and tags.
- **Openverse**: `curl "https://api.openverse.org/v1/audio/?q=whoosh&license_type=commercial&page_size=20"` →
  `results[]` with `title`, `license`, `license_version`, `source`, `duration` (ms), `url`. Freesound files come
  from a slow CDN (~12 s for 1 MB); download only the ones you will use.
- **Pixabay**: `https://pixabay.com/music/search/<q>/`, `https://pixabay.com/sound-effects/search/<q>/` (Vietnamese
  pages under `/vi/`). Good keywords: "lofi chill", "upbeat corporate", "cinematic ambient", "meme".
- Ask before downloading (list the files, source, licence, size). Save under the project's `media/audio/` with
  source and licence in `media/audio/index.json`, then keep what worked:
  `bashcut library add --kind audio --file /abs/media/audio/x.mp3 --name "Soft pop" --source URL --license "Mixkit SFX Free License" --tags pop`.

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
  at the offset `media sync` gives (`bc:footage-survey`), never the speaker leak. Start the music bed after it.

## SFX

- Size the sound to the motion: soft whoosh for a slow move, short whoosh for a hard zoom, pop for stickers and
  labels, ding on a final number, hit on the shocking line. Never the same whoosh on every cut.
- The loudest point of a whoosh lands on the cut; a riser ends on the reveal.
- Use files the user owns or that are licensed (the user's SFX folder, the Audio panel, the library, then the
  sources above). Ask before downloading any.

## Verify

You cannot listen, so: `review run` (voices too close, speech coverage), list the joins and voiceover windows
for the user to play (`ui seek` takes them there), and read the loudness in
the export receipt (`export status`: `lufs`, `truePeakDbTP`).
