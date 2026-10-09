#!/bin/sh
# PostToolUse hook on the Skill tool: when a bc:* skill was loaded, record it in BashCut's run log
# (`bashcut run append skill --name bc:<name> --verified-by hook`). Never blocks: every failure exits 0 silently
# (no bashcut on PATH, no project open, an older BashCut without the skill kind).
input=$(cat)
name=$(printf '%s' "$input" | tr -d '\n' |
  sed -n 's/.*"tool_input"[[:space:]]*:[[:space:]]*{[^}]*"skill"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
case "$name" in
  bc:*) ;;
  *) exit 0 ;;
esac
case "$name" in
  *[!A-Za-z0-9:._-]*) exit 0 ;;
esac
cli=${BASHCUT_CLI:-bashcut}
command -v "$cli" >/dev/null 2>&1 || exit 0
"$cli" run append skill --name "$name" --verified-by hook >/dev/null 2>&1
exit 0
