---
name: bashcut-self-learn
description: Turn problems hit while editing in BashCut into lasting fixes — record a project-specific lesson or the user's taste in the project memo or a project skill, and draft a change to this skill kit when the lesson is general (a wrong rule, a missing step, a trigger that did not fire). Use right after a step failed or had to be redone, when the user corrected the approach, when a workaround was found, or at the end of an editing session. Triggers: "rút kinh nghiệm", "học từ lỗi này", "nhớ lần sau", "lần sau đừng", "cập nhật skill", "self-learn".
---

# Self-learn

Reply in the user's language. A problem solved in chat but not written down **will happen again**.

Run it after the problem is solved (you need the real cause), not in the middle of the user's step. At the end
of a session, sweep the conversation for anything missed.

## 1. Write the lesson

Symptom → cause → what to do, with the number or error text that proves it.

| Good | Bad |
|---|---|
| "Whip transition refused: clips were not adjacent on one layer. Close the gap first (`timeline close-gap`)." | "Transitions are tricky." |
| "Music dipped 11 dB at every loop: the song has a quiet intro. Trim 2.6 s off its start before repeating." | "Watch the music." |

Only what was **observed** in this session (an error, a measurement, the user's words). A guess is not a
lesson.

## 2. Put it in the right place

| The lesson is about | Goes to |
|---|---|
| This project (its footage, people, places, what the user approved) | project memo: `knowledge get`, edit, `knowledge memo FILE` |
| The user's taste (length, pace, voice, style) | project memo, or the agent's own memory for all projects |
| A repeated workflow for this project | a project skill: `knowledge skill NAME FILE` (shared with Claude and Codex) |
| A rule in this kit that is wrong, missing or too vague | a proposed change to the kit (step 3) |
| A skill that should have loaded but didn't | the skill's `description` (add the user's real words), via step 3 |
| BashCut itself (a bug, a missing command or effect) | a note for the BashCut maintainers with the command, input and error |

## 3. Changing the kit

Installed skills are a copy managed by the plugin system; edits there are lost on update. Instead:

1. Write the change as a small diff to the skill's `SKILL.md` (a few lines, never a rewrite; check the rule
   isn't already there).
2. Show it to the user. If they agree and the kit repository is available locally, apply it there on a branch
   and open a pull request; otherwise save the diff in the project memo under "Proposed kit changes".

Keep skills short: a SKILL.md over ~250 lines moves detail into a `REFERENCE.md` next to it.

## Report

Short: what went wrong → where the lesson went → the lines added. If nothing was worth recording, say so in one
line.
