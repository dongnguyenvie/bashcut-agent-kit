#!/bin/sh
# SessionStart hook (matcher compact): after a compaction, put back the user's corrections captured before it, word
# for word, and remind to record lessons and keep notes in BashCut. Prints nothing when no BashCut project is open.
dir=$(dirname "$0")
. "$dir/lib.sh"
input=$(cat)
cli=$(find_cli) || exit 0
"$cli" run checklist >/dev/null 2>&1 || exit 0
session=$(json_word session_id "$input")
file=
[ -n "$session" ] && file=$(state_file "$session.corrections")
if [ -n "$file" ] && [ -s "$file" ]; then
  echo "[bc] Context was compacted. The user's corrections before it, quoted:"
  tail -n 5 "$file" | sed 's/^/- "/; s/$/"/'
  echo "Record those that are not lessons yet with bc:self-learn (knowledge lessons --query first)."
  rm -f "$file" "$file.held"
else
  echo "[bc] Context was compacted: re-read the plan and checklist (context get, run checklist) before the next edit."
fi
exit 0
