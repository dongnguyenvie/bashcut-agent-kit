# BashCut agent kit

Editing skills for Claude Code and Codex that drive the [BashCut](https://github.com/dongnguyenvie/BashCut)
video editor. BashCut makes video editable by agents (CLI, MCP, undoable edits); this kit says **how to edit
well**: what to look at, where to cut, how to mix, which effect fits which moment.

Every edit goes through BashCut's own commands. The kit never pre-renders picture or sound; its scripts
only analyse (contact sheets, LUT files). Sound is measured by BashCut itself (`audio measure`, `media sync`).

## Skills

| Skill | Use it for |
|---|---|
| `bashcut-edit-workflow` | The whole edit from footage to export, and which skill to use when |
| `bashcut-footage-survey` | Contact sheets and specs before editing; coverage, silent or broken clips (`survey.py`); camera ↔ screen sync (`media sync`) |
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

- BashCut running (its MCP server talks to the open app), a version with `ui frame` (BashCut PR #14).
- Claude Code or Codex.
- For the scripts: `ffmpeg` and `ffprobe`; `uv` for `grade.py` (it installs numpy and Pillow on first run).
- Skills that use capabilities need the matching BashCut plugin: captions (`captions.transcribe`), beats
  (`audio.beats`, built in), loudness (`audio.loudness`, built in), voice (`voice.synthesize`, e.g. VieNeu TTS).

## Install

**Inside BashCut** nothing is needed: BashCut ships the kit and loads it in its Claude and Codex tabs.
Settings › Agents (or `bashcut agent setup claude|codex`) also sets up Claude Code and Codex outside
BashCut from that copy, including configuration folders moved with `CLAUDE_CONFIG_DIR` or `CODEX_HOME`.

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

## Verification

CI runs skill checks, checker unit tests and explicit CLI example validation against the generated BashCut
command reference in `reference/commands.md`. Its source commit is recorded in `reference/source.json`; it is
vended here because the app repository is private and the public kit's CI cannot check it out. Refresh both
files when adopting app command changes. In a sibling checkout, validate directly against the app with:

```sh
python3 scripts/check_commands.py --reference ../bash-cut/docs/reference/commands.md
python3 -m unittest discover -s tests
```

Pull requests that change `skills/` must increase `.claude-plugin/plugin.json`'s semantic version.
The version check compares against the PR base; it never rewrites a contributor's branch.
Claude Code caches an installed plugin per version, so an unchanged version keeps serving the old skills even
after BashCut refreshes its copy. Codex links the skill folders and sees changes at once.

## Releases and in-app updates

BashCut's Settings › Agents checks `releases.json` on `main` and offers newer kits as **Download & Update**
(`bashcut agent kit-check`, `bashcut agent kit-update`). To publish one, merge the version bump, then push its tag:

```sh
git tag v0.0.2 && git push origin v0.0.2
```

`.github/workflows/release.yml` checks the skills, runs `scripts/release.py` to zip the committed kit files, signs
the archive digest with the BashCut publisher key (repository secret `BASHCUT_SIGNING_KEY`, the same key as
`bashcut-plugins`), attaches it to the GitHub Release and adds the version to `releases.json`. BashCut installs only
archives whose SHA-256 and first-party signature match. `python3 scripts/release.py` builds the archive locally
without signing.

## License

MIT. See [LICENSE](LICENSE).
