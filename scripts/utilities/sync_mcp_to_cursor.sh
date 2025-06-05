#!/usr/bin/env bash
set -euo pipefail

PROFILE=bootssd-2t                          # change if needed
SRC="$HOME/.codeium/windsurf/mcp_config.json"
DST="$HOME/.config/Cursor/$PROFILE/User/settings.json"

echo "🔄 Syncing MCP configuration from Windsurf to Cursor..."

# Check source file exists
[[ -f $SRC ]] || { echo "❌ $SRC not found"; exit 1; }
echo "✅ Found Windsurf MCP config"

# Create destination directory and file if needed
mkdir -p "$(dirname "$DST")"
[[ -f "$DST" ]] || echo '{}' > "$DST"

# Create backup
cp "$DST" "${DST}.bak-$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
echo "🗄️  Backup created"

# Merge MCP servers using jq
jq --slurpfile src "$SRC" '.mcpServers = $src[0].mcpServers' "$DST" \
  > "${DST}.tmp" && mv "${DST}.tmp" "$DST"

echo "✅ MCP block synced to Cursor profile $PROFILE"
echo
echo "📄 Configured MCP Servers:"
jq -r '.mcpServers | keys[]' "$DST" | sed 's/^/   - /'
echo
echo "🎯 Remember to restart Cursor to load the new configuration!" 