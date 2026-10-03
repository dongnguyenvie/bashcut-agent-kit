#!/bin/sh
# Make this kit available to Codex: link each skill into ~/.agents/skills and register BashCut's MCP server.
# Run again after moving the kit. --uninstall removes the links and the MCP entry.
set -e
KIT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
mkdir -p "$DEST"

for dir in "$KIT"/skills/*/; do
    name="$(basename "$dir")"
    target="$DEST/$name"
    if [ "$1" = "--uninstall" ]; then
        [ -L "$target" ] && case "$(readlink "$target")" in "$KIT"/*) rm "$target"; echo "removed $name";; esac
        continue
    fi
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
