#!/bin/sh
# UserPromptSubmit hook: when the user's message reads like a correction, keep it as a lesson candidate (the
# BashCut run log, kind `correction`, with the words quoted; and a per-session note for after a compaction) and add
# one line of context pointing at bc:self-learn. Silent (no tokens) for any other message, when no BashCut project is
# open, or when anything fails.
dir=$(dirname "$0")
. "$dir/lib.sh"
input=$(cat)
quote=$(printf '%s' "$input" | perl "$dir/correction.pl" 2>/dev/null)
[ -n "$quote" ] || exit 0
cli=$(find_cli) || exit 0
"$cli" run append correction --text "$quote" >/dev/null 2>&1 || exit 0
session=$(json_word session_id "$input")
if [ -n "$session" ] && file=$(state_file "$session.corrections"); then
  printf '%s\n' "$quote" >>"$file"
fi
echo "[bc] Possible correction, kept as a lesson candidate (run log: correction). Once solved, record it with bc:self-learn, the user's words quoted."
exit 0
