#!/bin/sh
# Start BashCut's MCP server. BashCut must be running; the server talks to it over its local socket.
# Lookup order: $BASHCUT_MCP, bashcut-mcp on PATH (BashCut's own terminals), the running BashCut app
# (wherever it was opened from), then the usual install locations.
running_app() {
    ps -axo comm= 2>/dev/null | grep '/BashCut.app/Contents/MacOS/BashCutApp$' | head -n 1 | sed 's|/BashCutApp$|/bashcut-mcp|'
}
for candidate in "$BASHCUT_MCP" "$(command -v bashcut-mcp 2>/dev/null)" "$(running_app)" \
    "/Applications/BashCut.app/Contents/MacOS/bashcut-mcp" \
    "$HOME/Applications/BashCut.app/Contents/MacOS/bashcut-mcp"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
        exec "$candidate" "$@"
    fi
done
echo "bashcut-mcp not found. Open BashCut (or install it in /Applications), or set BASHCUT_MCP to its bashcut-mcp binary." >&2
exit 1
