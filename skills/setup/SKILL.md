---
name: setup
description: Set up BashCut's recommended plugins (captions, Vietnamese voice, silence markers, pre-production, AI Editor) with one approval in the app, then check they work. Only when the user types /bc:setup. Triggers: "/bc:setup", "cài plugin đề xuất", "setup BashCut".
disable-model-invocation: true
---

# Setting up BashCut's recommended plugins

Reply in the user's language, in plain words: the user may not be technical. Never paste raw JSON at them.

The user typed `/bc:setup`, so they want the recommended plugins. You only **show** the install approval; the user
approves it in the app. Never trust, enable or set up a plugin yourself, and never ask for API keys or passwords in
the chat.

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

## 3. Show the approval

```sh
bashcut plugins install --bundle starter
bashcut plugins install --bundle starter --only bashcut.whisper-captions,bashcut.vieneu-tts
```

It returns a job; `bashcut jobs wait JOB` gives `approval`:
- `pending`: the Plugins window shows one list with a checkbox per plugin. Tell the user: "Kiểm tra danh sách rồi bấm
  **Install** trong cửa sổ Plugins" (or the same in their language). They can uncheck any plugin.
- `queued` with `position`: another install is waiting or running; this one opens after it. Do not ask again.
- `none`: everything is installed.

The install itself runs as the user's job (`plugins.install`) and can take minutes (models download). Check on it
with `bashcut jobs status`, or ask the user to tell you when the Plugins window says it is installed. Never start
another install while it runs.

## 4. Check they work

```sh
bashcut plugins list --health
bashcut capabilities get
```

For each plugin that is not `ready`, explain the health detail in one sentence and what the user should do:
- An API key or login: the user enters it in Plugins › the plugin › Options (or signs in where the detail says).
  Do not ask them to send it to you.
- A missing tool or a failed setup: Plugins › the plugin › Set Up… (`bashcut plugins setup PLUGIN` opens that
  approval for them).

Finish with what they can do now, for example "gõ: làm phụ đề cho video này" or "đọc lồng tiếng đoạn này".
