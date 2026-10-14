---
name: setup
description: Set up BashCut's recommended plugins (captions, Vietnamese voice, silence markers, pre-production, AI Editor), trusted automatically unless the user turned that off (then with one approval in the app), and check they work. Only when the user types /bc:setup. Triggers: "/bc:setup", "cài plugin đề xuất", "setup BashCut".
disable-model-invocation: true
---

# Setting up BashCut's recommended plugins

Reply in the user's language, in plain words: the user may not be technical. Never paste raw JSON at them.

The user typed `/bc:setup`, so they want the recommended plugins. BashCut trusts plugins automatically by default
(Settings › Plugins › Trust plugins automatically): the install runs at once. Only when the user turned that off does
it show an approval that the user answers in the app. Never turn a plugin on that the user turned off, never change
that setting, and never ask for API keys or passwords in the chat.

## 1. See what is missing

```sh
bashcut plugins bundles
```

The `starter` bundle (Recommended) lists each plugin with `installable` (this Mac does not have it yet), `default`
(checked in the approval), `reason` when it is left out (already installed, or not for this Mac) and its sizes.
If nothing is installable, say everything is already installed and go to step 4.

## 2. Tell the user what they get

One short line per installable plugin, from its name: what it does for their videos, not its ID. Say which ones
start unchecked (for example Antigravity) and the total download size. If the user already said they do not want
some, check only the rest with `--only`.

## 3. Install

```sh
bashcut plugins install --bundle starter
bashcut plugins install --bundle starter --only bashcut.whisper-captions,bashcut.vieneu-tts
```

It returns a job; `bashcut jobs wait JOB` gives `approval`:
- `approved`: plugins are trusted automatically, so the install already runs, with the plugins checked by default
  (or the `--only` ones). Say it is installing.
- `pending`: the user turned automatic trust off, so the Plugins window shows one list with a checkbox per plugin.
  Tell the user: "Kiểm tra danh sách rồi bấm **Install** trong cửa sổ Plugins" (or the same in their language).
  They can uncheck any plugin.
- `queued` with `position`: another install is waiting or running; this one starts after it. Do not ask again.
- `none`: everything is installed.

The install itself runs as the user's job (`plugins.install`) and can take minutes (models download). Wait for it
with `bashcut jobs status` (after `pending`, or ask the user to tell you when the Plugins window says it is
installed), then go to step 4. Never start another install while one runs.

## 4. Check they work

```sh
bashcut plugins list --health
bashcut capabilities get
```

For each plugin that is not `ready`, explain the health detail in one sentence and what comes next:
- An API key or login: the user enters it in Plugins › the plugin › Options (or signs in where the detail says).
  Do not ask them to send it to you.
- A missing tool or a failed setup: run `bashcut plugins setup PLUGIN` once. `approval: approved` runs the setup
  at once: wait for the job, then check `plugins list --health` again. `pending`: the user approves it in the app
  (Plugins › the plugin › Set Up…). If it fails again, say what the detail says instead of retrying.

Finish with what they can do now, for example "gõ: làm phụ đề cho video này" or "đọc lồng tiếng đoạn này".

## 5. Drive a plugin's panel when no command does the job

Prefer the typed command (`voice speak`, `captions generate`, `beats detect`, a plugin skill's own script) and then
`plugins run ACTION` (`plugins actions` lists them). Only a plugin with nothing else needs its view:
1. `bashcut plugins list --views`: each plugin's views and where they live (panel, dock tab, sheet, inspector).
2. `bashcut plugins view PLUGIN --view VIEW`: the components as JSON (texts, lists, inputs with values, buttons by
   `id`). Read it instead of taking a screenshot.
3. `bashcut plugins view-event PLUGIN --view VIEW --node ID [--type change|submit|select|action --value V]` acts
   by node id and returns the new components: no second `view` call. A colour picker takes `#RRGGBB`, a font
   picker a font name.
4. `--open` (or `plugins show-view`) only when the user should see it. `plugins invoke CAPABILITY --params JSON`
   runs a capability raw (a job) when no command wraps it.
