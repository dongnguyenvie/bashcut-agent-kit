---
name: bashcut-voiceover
description: Write and produce voiceover in BashCut — prepare the text so text-to-speech reads it right, synthesize several takes with a voice.synthesize provider (for example VieNeu-TTS for Vietnamese, preset or cloned voices), check every take, place it on the Voiceover layer and fit it to the picture. Use for narration, voiceover, fixing a flubbed line without re-recording, or when the user says "lồng tiếng", "thuyết minh", "đọc lời", "giọng AI", "clone giọng", "text to speech", "TTS".
---

# Voiceover

Reply in the user's language.

## Provider

`voice speak` uses the project's `voice.synthesize` provider. Check with `plugins list`; if there is none,
`plugins search --capability voice.synthesize` and ask the user to install one (for Vietnamese: VieNeu TTS).
Voice choice, cloning from a reference file and variation are the plugin's options:

```sh
bashcut plugins options bashcut.vieneu-tts
bashcut plugins option bashcut.vieneu-tts --option voice --value <voice>
```

Only clone the user's own voice or a voice whose owner agreed. If viewers could take the AI voice for a real
recording, suggest disclosing it.

## 1. Prepare the text

Spell out what gets misread:
- Numbers, years, times: `2026` → "hai nghìn không trăm hai mươi sáu", `7h30` → "bảy giờ ba mươi".
- Units and symbols: km, %, °C, `k` (nghìn đồng).
- Acronyms as letters ("xê en xê" for CNC); show them as letters again in captions.
- English or unusual words: rephrase in plain words rather than respelling ("chill" was read "chiều").
- Very short exclamations (≤ 5 words) with an expressive voice fail often; use a calm voice or a longer line.

When a phrase is misread in every take, **rewording beats regenerating** ("kín xe" → "chật cứng xe"). Change
approved text minimally and tell the user which words changed.

## 2. Synthesize

```sh
bashcut voice speak "Text of one line" --takes 3 --at-frame F   # job; inserts the best take on Voiceover
bashcut voice speak "Text" --takes 6 --keep-takes              # keep every take, insert nothing
bashcut jobs status JOB_ID                                     # chosen take, its score and all take scores
```

- One call per line or short paragraph, placed where it belongs; it becomes one undoable edit.
- Generation is random: 3 takes for normal lines, 5–6 for important or difficult ones.
- With `--keep-takes`, pick a take and place it with `media import /abs/take.wav --kind audio --place --track
  VOICEOVER_TRACK --at-frame F`.

## 3. Check every kept take

The model sometimes misreads, drops or repeats words, mostly **at the start** of a line. A text match score
barely drops for repeated words. Transcribe the kept takes (`captions generate --media TAKE_MEDIA`, or listen)
and compare with the text; regenerate or reword failures. Recognition also mishears some regional accents
(s→x, final n→ng): count only errors a listener would hear.

## 4. Fit to picture

- Never over real speech; keep ≥ 0.3 s from real voices (`bashcut-audio-mix`).
- Give each voiceover section b-roll that is longer than the line; a too-short source clip made the voiceover
  run into the next spoken cut.
- Captions for voiceover: write them from your text (`bashcut-captions-text`).
- Level ~−16 LUFS with music 12–18 dB under (ducking on the music layer).
