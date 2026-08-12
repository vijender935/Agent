#!/bin/bash
# Quick start for Grok Custom Connector
set -e
cd "$(dirname "$0")"

PORT=${1:-8000}

echo "=========================================="
echo "  Local Agent → Grok Custom Connector"
echo "=========================================="
echo ""
echo "1. Starting MCP server on port $PORT ..."
python run_mcp_server.py --http --port "$PORT" &
SERVER_PID=$!
sleep 1

echo "2. Server PID: $SERVER_PID"
echo ""
echo "3. Ab naya terminal kholo aur tunnel chalao:"
echo "   ngrok http $PORT"
echo "   # ya: cloudflared tunnel --url http://localhost:$PORT"
echo ""
echo "4. Jo https://xxxx.ngrok-free.app URL mile,"
echo "   use grok.com/connectors → Custom mein daalo"
echo "   (try with /mcp at the end if needed)"
echo ""
echo "5. Production tip: set AGENT_API_TOKEN in .env"
echo ""
echo "Press Ctrl+C to stop server"
wait $SERVER_PID
