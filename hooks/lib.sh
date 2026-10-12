# Shared by the kit's hooks (sourced, POSIX sh). Every hook must exit 0 silently when anything is missing.

# The CLI of the running app first (it must match the app it talks to), then $BASHCUT_CLI, then PATH.
find_cli() {
  running=$(ps -axo comm= 2>/dev/null | grep '/BashCut.app/Contents/MacOS/BashCutApp$' | head -n 1 | sed 's|/BashCutApp$|/bashcut|')
  for candidate in "$BASHCUT_CLI" "$running" "$(command -v bashcut 2>/dev/null)"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then printf '%s\n' "$candidate"; return 0; fi
  done
  return 1
}

# Per-session notes of the hooks (corrections captured since the last compaction), outside any project.
state_file() {
  dir="${BASHCUT_KIT_STATE:-${TMPDIR:-/tmp}/bashcut-kit}"
  mkdir -p "$dir" 2>/dev/null || return 1
  printf '%s/%s\n' "$dir" "$1"
}

# A JSON string field of the hook input, sanitised to [A-Za-z0-9_-] (session_id, trigger, source).
json_word() {
  printf '%s' "$2" | tr -d '\n' | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([A-Za-z0-9_-]*\)\".*/\1/p" | head -n 1
}
