#!/bin/sh
# PostToolUse hook on the Skill tool: record the loaded skill in BashCut's run log
# (`bashcut run append skill --name <name> --verified-by hook`). BashCut keeps only its own: kit skills (`bc:*`)
# and plugin skills by their agent name (`vlog-product-ad`, recorded as `bashcut.vlog:product-ad`). Never blocks: every failure exits 0 silently
# (no bashcut on PATH, no project open, an older BashCut without the skill kind).
input=$(cat)
name=$(printf '%s' "$input" | tr -d '\n' |
  sed -n 's/.*"tool_input"[[:space:]]*:[[:space:]]*{[^}]*"skill"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -n "$name" ] || exit 0
case "$name" in
  *[!A-Za-z0-9:._-]*) exit 0 ;;
esac
. "$(dirname "$0")/lib.sh"
cli=$(find_cli) || exit 0
"$cli" run append skill --name "$name" --verified-by hook >/dev/null 2>&1
exit 0
