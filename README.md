# BashCut agent kit

Editing skills for Claude Code and Codex that drive the [BashCut](https://github.com/dongnguyenvie/BashCut)
video editor. BashCut makes video editable by agents (CLI, MCP, undoable edits); this kit says **how to edit
well**: what to look at, where to cut, how to mix, which effect fits which moment.

Every edit goes through BashCut's own commands. The kit never pre-renders picture or sound; its two scripts
only analyse (contact sheets, LUT files).

## Skills

| Skill | Use it for |
|---|---|
| `bashcut-edit-workflow` | The whole edit from footage to export, and which skill to use when |
| `bashcut-footage-survey` | Contact sheets and specs before editing; coverage, silent or broken clips (`survey.py`) |
| `bashcut-beat-cut` | Cutting on the beat grid or on sentences; punch-in reframes |
| `bashcut-audio-mix` | Levels, fades, ducking, music choice, SFX, loudness |
| `bashcut-voiceover` | Text-to-speech lines that read right, checked and placed |
| `bashcut-captions-text` | Captions from speech, hook titles, place and chapter cards |
| `bashcut-color-grade` | Looks, LUTs (`grade.py`: matte-cinematic, warm-film, faded-memory), adjustment layers, style kits |
| `bashcut-effects` | Which effect for which moment, made with native transitions, speed ramps, freeze, reframe |
| `bashcut-stock-images` | Licensed stock photos and video, labelled as illustration |
| `bashcut-style-study` | Measuring a reference style and turning it into a memo, look and style kit |
| `bashcut-self-learn` | Recording lessons in the project memo, project skills or kit changes |

## Requirements

- BashCut running (its MCP server talks to the open app).
- Claude Code or Codex.
- For the scripts: `ffmpeg` and `ffprobe`; `uv` for `grade.py` (it installs numpy and Pillow on first run).
- Skills that use capabilities need the matching BashCut plugin: captions (`captions.transcribe`), beats
  (`audio.beats`, built in), loudness (`audio.loudness`, built in), voice (`voice.synthesize`, e.g. VieNeu TTS).

## Install

**Inside BashCut's terminals** nothing is needed once BashCut loads the kit itself (planned).

**Claude Code**

```sh
/plugin marketplace add dongnguyenvie/bashcut-agent-kit
/plugin install bashcut@bashcut-agent-kit
```

Skills appear as `/bashcut:bashcut-<name>`, and the plugin starts BashCut's MCP server
(`scripts/bashcut-mcp.sh` finds `bashcut-mcp` in `/Applications` or `~/Applications`; set `BASHCUT_MCP` to
override). To try a local checkout for one session: `claude --plugin-dir /path/to/bashcut-agent-kit`.

**Codex**

```sh
git clone https://github.com/dongnguyenvie/bashcut-agent-kit
sh bashcut-agent-kit/scripts/install-codex.sh      # links skills into ~/.agents/skills, adds the MCP server
sh bashcut-agent-kit/scripts/install-codex.sh --uninstall
```

## Layout

```
.claude-plugin/plugin.json        plugin "bashcut"
.claude-plugin/marketplace.json   marketplace "bashcut-agent-kit"
.mcp.json                         BashCut MCP server for Claude Code
skills/bashcut-*/SKILL.md         the skills (Agent Skills format, shared by Claude Code and Codex)
scripts/bashcut-mcp.sh            finds and starts bashcut-mcp
scripts/install-codex.sh          Codex setup
scripts/check.py                  checks every skill's frontmatter, size and referenced files
```

## Writing skills

- English instructions; trigger phrases in the description may be in any language users speak.
- Say what to do and why; leave command syntax to BashCut's own agent instructions.
- No personal presets, voices or download sources: those belong in a user's project memo.
- Only rules that were observed (a measurement, an error, a user's correction), with the number that proves it.
- Run `python3 scripts/check.py` before committing.
