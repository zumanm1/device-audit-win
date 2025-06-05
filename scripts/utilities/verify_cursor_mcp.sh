#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Cursor MCP Configuration Verification Script"
echo "============================================="
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Cursor settings file
CURSOR_SETTINGS="$HOME/.config/Cursor/bootssd-2t/User/settings.json"
echo "📁 Checking Cursor settings file..."
if [[ -f "$CURSOR_SETTINGS" ]]; then
    echo -e "${GREEN}✅ Found Cursor settings: $CURSOR_SETTINGS${NC}"
    echo "📄 MCP Servers configured:"
    jq -r '.mcpServers | keys[]' "$CURSOR_SETTINGS" 2>/dev/null | sed 's/^/   - /' || echo "   No mcpServers found"
    echo
else
    echo -e "${RED}❌ Cursor settings file not found${NC}"
    exit 1
fi

# Check Windsurf source configuration
WINDSURF_CONFIG="$HOME/.codeium/windsurf/mcp_config.json"
echo "📁 Checking Windsurf MCP source..."
if [[ -f "$WINDSURF_CONFIG" ]]; then
    echo -e "${GREEN}✅ Found Windsurf MCP config: $WINDSURF_CONFIG${NC}"
    echo "📄 Source MCP Servers:"
    jq -r '.mcpServers | keys[]' "$WINDSURF_CONFIG" 2>/dev/null | sed 's/^/   - /' || echo "   No mcpServers found"
    echo
else
    echo -e "${YELLOW}⚠️  Windsurf MCP config not found${NC}"
fi

# Check if MCP servers are running
echo "🔍 Checking running MCP processes..."
if pgrep -f "mcp-server-playwright" > /dev/null; then
    echo -e "${GREEN}✅ Playwright MCP server is running${NC}"
    echo "   PID: $(pgrep -f 'mcp-server-playwright')"
else
    echo -e "${YELLOW}⚠️  Playwright MCP server not running${NC}"
fi

if pgrep -f "mcp-server-puppeteer" > /dev/null; then
    echo -e "${GREEN}✅ Puppeteer MCP server is running${NC}"
    echo "   PID: $(pgrep -f 'mcp-server-puppeteer')"
else
    echo -e "${YELLOW}⚠️  Puppeteer MCP server not running${NC}"
fi

# Check ports
echo
echo "🌐 Checking network ports..."
if lsof -nP -iTCP:8931 -sTCP:LISTEN &>/dev/null; then
    echo -e "${GREEN}✅ Port 8931 (Playwright Docker) is listening${NC}"
    lsof -nP -iTCP:8931 -sTCP:LISTEN | grep -v COMMAND | head -1 | awk '{print "   Process: " $1 " (PID: " $2 ")"}'
else
    echo -e "${YELLOW}⚠️  Port 8931 (Playwright Docker) not listening${NC}"
fi

# Look for Chrome debugging ports (Puppeteer)
echo
echo "🔍 Checking for Chrome debugging ports..."
CHROME_PORTS=$(lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep chrome | awk '{print $9}' | cut -d: -f2 | sort -u || true)
if [[ -n "$CHROME_PORTS" ]]; then
    echo -e "${GREEN}✅ Chrome debugging ports found:${NC}"
    echo "$CHROME_PORTS" | sed 's/^/   Port: /'
else
    echo -e "${YELLOW}⚠️  No Chrome debugging ports found${NC}"
fi

echo
echo "📚 Documentation: ~/Downloads/MCP-DOC-PLAYWRIGHT-PUPPETEER.md"
echo
echo "🎯 Next Steps:"
echo "1. Restart Cursor to load the MCP configuration"
echo "2. Go to Cursor Settings → Features → MCP servers"
echo "3. Check that all servers show green status"
echo "4. Test with MCP tools in Cursor chat"
echo
echo "✨ Configuration complete!" 