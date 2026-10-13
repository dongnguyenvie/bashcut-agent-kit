#!/bin/sh
# PreCompact hook. A compaction keeps only a summary, so the user's exact words in corrections are lost. A manual
# /compact with corrections captured this session (correction.sh) is held once, with a note to the user; the second
# /compact goes on. Automatic compaction is never held (holding it can fail the request); after-compact.sh then puts
# the quotes back into the context.
dir=$(dirname "$0")
. "$dir/lib.sh"
input=$(cat)
[ "$(json_word trigger "$input")" = manual ] || exit 0
session=$(json_word session_id "$input")
[ -n "$session" ] || exit 0
file=$(state_file "$session.corrections") || exit 0
[ -s "$file" ] || exit 0
[ -e "$file.held" ] && exit 0
: >"$file.held"
count=$(wc -l <"$file" | tr -d ' ')
echo "BashCut: $count correction(s) this session may not be lessons yet. Ask the agent to run bc:self-learn (and save the project's notes), or /compact again to go on." >&2
exit 2
