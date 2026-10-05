---
name: bashcut-self-learn
description: Turn problems hit while editing in BashCut into lasting fixes — record a structured lesson (symptom, cause, fix) for this project or every project, the user's taste as preferences, project facts, a project skill for a repeated workflow, and draft a change to this skill kit when the lesson is general (a wrong rule, a missing step, a trigger that did not fire). Use right after a step failed or had to be redone, when the user corrected the approach, when a workaround was found, or at the end of an editing session. Triggers: "rút kinh nghiệm", "học từ lỗi này", "nhớ lần sau", "lần sau đừng", "cập nhật skill", "self-learn".
---

# Self-learn

Reply in the user's language. A problem solved in chat but not written down **will happen again**.

Run it after the problem is solved (you need the real cause), not in the middle of the user's step. At the end
of a session, sweep the conversation for anything missed.

Signals worth recording: the user corrects you ("không, dùng X", "thật ra…", "X chứ không phải Y") or rejects an
action you proposed; the user says to remember ("nhớ là…", "lần sau đừng…"); a `bashcut` command fails or a
result had to be redone. A question, a one-off instruction for this clip or vague feedback ("chưa ổn") is not a
lesson.

## 1. Write the lesson

Symptom → cause → what to do, with the number or error text that proves it.

| Good | Bad |
|---|---|
| "Whip transition refused: clips were not adjacent on one layer. Close the gap first (`timeline close-gap`)." | "Transitions are tricky." |
| "Music dipped 11 dB at every loop: the song has a quiet intro. Trim 2.6 s off its start before repeating." | "Watch the music." |

Only what was **observed** in this session (an error, a measurement, the user's words). A guess is not a
lesson. Before adding one, look for it by tag and keyword (`bashcut knowledge lessons --tag transitions`,
`--query "close-gap"`); the same problem is often worded differently. If it exists, update it with
`knowledge update-lesson ID` and add the new occurrence to its evidence ("seen again rev 52") instead of adding a
second one. A project lesson seen again in another project belongs to every project (`--scope user`).

## 2. Put it in the right place

BashCut keeps knowledge as structured entries. Every session starts with a summary of the active lessons,
preferences and facts (`context get` → `knowledge`), so a recorded entry is followed next time without anyone
re-reading a memo.

| The lesson is about | Goes to |
|---|---|
| This project: something that went wrong and how to avoid it | a project lesson (below) |
| This project: people, places, footage notes, what the user approved | a fact: `bashcut knowledge set-fact host "Lan, speaks fast"` |
| The user's taste (length, pace, voice, style) | a preference: `bashcut knowledge set-pref pace calm` (for every project; waits in the Knowledge inbox, below). `--scope project` for this project only |
| A mistake that will happen in any project | a lesson for every project: `--scope user`; it waits in the user's proposals |
| A workflow repeated two or three times in this project | a project skill: `bashcut skills save NAME FILE` (shared with Claude and Codex) |
| A workflow the user repeats in every project | a skill for every project: `bashcut skills save NAME FILE --scope user` (needs the user's approval) |
| A rule in this kit that is wrong, missing or too vague | a proposed change to the kit (step 3) |
| A skill that should have loaded but didn't | the skill's `description` (add the user's real words), via step 3 |
| BashCut itself (a bug, a missing command or effect) | a note for the BashCut maintainers with the command, input and error |

A lesson:

```bash
bashcut knowledge add-lesson "Whip refused on non-adjacent clips" \
  --symptom "transition add failed: clips not adjacent" --cause "a 3-frame gap on v1" \
  --fix "timeline close-gap before adding a transition" --evidence "rev 41, error text" \
  --tags transitions --status proposed
```

- **Status:** `active` (the default) when the cause is proven; `--status proposed` when you are unsure, so the user
  reviews it first. A lesson for every project is always proposed.
- **Tags:** one or two of the area (captions, audio, pacing, color, transitions, export…), so `--tag` finds them.
- **Session:** pass `--session ID` when you know your agent session ID.
- **Keys:** short, lowercase, stable (`pace`, `caption.style`, `music.genre`, `host`), so a later `set-pref`
  replaces the value instead of adding a near-duplicate.
- **Preference for every project:** `set-pref` usually returns `"approval": "proposed"` with a `p-…` ID: the
  change waits in the Knowledge inbox and is **not applied yet**. Tell the user it is waiting there; do not repeat
  the command or treat the value as set. (It applies at once only when the user lets agents act without
  confirmation.) A newer proposal for the same key replaces the older one. `knowledge proposals` lists what waits.

Project entries live in the project folder, so a project that was never saved refuses project writes; save it
first. The free-text memos (`knowledge memo`) are for longer notes such as a style study's measurements; do not
append lessons to them. If `knowledge get` shows `legacy` (an older memo from the agent workspace or home folder),
tell the user; the Knowledge sheet can move it into the notes or this project.

Wrong or outdated: `knowledge update-lesson ID --status disabled` (kept for the record) or `remove-lesson ID`;
`set-pref KEY --remove`.

A lesson about a BashCut bug or workaround can stop being true after an app update: if the plain way works now,
disable the lesson and say so in its evidence. Do not retire lessons just because they are old.

**Undo a change.** Every change to lessons, preferences, facts, memos and skills is in `knowledge history`, with
who made it and a diff. When a change was a mistake (yours or one the user wants back), find it and revert it
rather than re-typing the old value:

```bash
bashcut knowledge history --kind lesson --target LESSON_ID --limit 5
bashcut knowledge revert CHANGE_ID   # the change's id from history
```

A revert brings back a removed entry, removes an added one or undoes an edit (later changes to the same entry
too). Reverting a change for every project waits for the user's approval like any other `--scope user` write.

**Splitting an old memo.** `knowledge get` shows `memoSplit` per scope: `pending` means a memo was never split into
entries. Only when the user asks (the Knowledge sheet's **Ask the agent to split it** button sends that request),
read the memo, write a JSON file and queue it once:

```bash
bashcut knowledge split-memo entries.json            # the project memo
bashcut knowledge split-memo notes.json --scope user  # the notes for every project (no facts)
```

`{"lessons": [{"title", "symptom", "cause", "fix", "evidence", "tags"}], "prefs": [{"key", "value"}],
"facts": [{"key", "value"}]}`: one short entry per idea, only what the memo says. Long notes such as style
measurements stay in the memo; do not edit it. Everything waits in the Knowledge inbox, and existing entries are
skipped. `--keep` keeps the memo as notes and stops offering the split.

## 3. Changing the kit

Installed skills are a copy managed by the plugin system; edits there are lost on update. Instead:

1. Read the current text: `bashcut skills get NAME --scope kit`. Make a small change to a copy (a few lines, never
   a rewrite; check the rule isn't already there), each line backed by what happened.
2. Show the change to the user. If they agree and the kit repository is available locally, apply it there on a
   branch and open a pull request.
3. Otherwise propose it so it is not lost:

   ```bash
   bashcut skills propose bashcut-beat-cut SKILL.md --summary "close gaps before a transition" \
     --reason "whip refused twice on a 3-frame gap"
   ```

   BashCut stores the line diff against the kit's `SKILL.md` as a lesson for every project tagged `kit`, waiting in
   the Knowledge inbox. The installed kit is not changed.

Keep skills short: a SKILL.md over ~250 lines moves detail into a `REFERENCE.md` next to it.

## Report

Short: what went wrong → where the lesson went → the lines added. If nothing was worth recording, say so in one
line.
