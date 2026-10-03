#!/bin/sh
# Start BashCut's MCP server. BashCut must be running; the server talks to it over its local socket.
# Lookup order: $BASHCUT_MCP, bashcut-mcp on PATH (BashCut's own terminals), then the usual app locations.
for candidate in "$BASHCUT_MCP" "$(command -v bashcut-mcp 2>/dev/null)" \
    "/Applications/BashCut.app/Contents/MacOS/bashcut-mcp" \
    "$HOME/Applications/BashCut.app/Contents/MacOS/bashcut-mcp"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
        exec "$candidate" "$@"
    fi
done
echo "bashcut-mcp not found. Install BashCut in /Applications, or set BASHCUT_MCP to its bashcut-mcp binary." >&2
exit 1
