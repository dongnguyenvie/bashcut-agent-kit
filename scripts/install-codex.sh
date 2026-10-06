#!/bin/sh
# Make this kit available to Codex: link each skill into ~/.agents/skills as bc-<name> and register BashCut's MCP
# server. Codex shows them as bc:<name> (the plugin name in .claude-plugin/plugin.json).
# Run again after moving the kit. --uninstall removes the links and the MCP entry.
set -e
KIT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
PREFIX="bc-"
mkdir -p "$DEST"

# Remove links that are no longer right: bashcut-<name> links from kits before 0.1.0 (any kit copy), and bc-<name>
# links into this kit that are not a current skill (or all of them on --uninstall). Dangling links of ours go too.
for target in "$DEST"/bashcut-* "$DEST"/"$PREFIX"*; do
    [ -L "$target" ] || continue
    link="$(readlink "$target")"
    name="$(basename "$target")"
    case "$name" in
        bashcut-*) [ -e "$target" ] && [ ! -f "$link/../../.claude-plugin/plugin.json" ] && continue;;
        *) if [ -e "$target" ]; then
               case "$link" in "$KIT"/*) ;; *) continue;; esac
               [ "$1" != "--uninstall" ] && [ -f "$KIT/skills/${name#"$PREFIX"}/SKILL.md" ] && continue
           fi;;
    esac
    rm "$target"
    echo "removed $name"
done

[ "$1" = "--uninstall" ] || for dir in "$KIT"/skills/*/; do
    name="$PREFIX$(basename "$dir")"
    target="$DEST/$name"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        echo "skip $name: $target exists and is not a link from this kit" >&2
        continue
    fi
    ln -sfn "${dir%/}" "$target"
    echo "linked $name"
done

if command -v codex >/dev/null 2>&1; then
    codex mcp remove bashcut >/dev/null 2>&1 || true
    if [ "$1" != "--uninstall" ]; then
        codex mcp add bashcut -- "$KIT/scripts/bashcut-mcp.sh"
        echo "registered MCP server 'bashcut'"
    fi
else
    echo "codex not found: add the MCP server later with" >&2
    echo "  codex mcp add bashcut -- \"$KIT/scripts/bashcut-mcp.sh\"" >&2
fi
