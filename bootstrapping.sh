#!/usr/bin/env bash
###############################################################################
# bootstrapping.sh
#
# Termux ke andar Ubuntu (proot-distro) setup karke Local Agent MCP server
# aur Cloudflare tunnel chalane ke liye poora bootstrap script.
#
# USAGE:
#   1) Termux (bahar, Ubuntu ke andar NAHI) me chalao:
#        pkg install proot-distro -y
#        proot-distro install ubuntu
#        proot-distro login ubuntu
#
#   2) Ab Ubuntu ke andar (root@localhost) is script ko chalao:
#        bash bootstrapping.sh
#
#   3) Agent.zip ko pehle se Termux home me copy kar lo:
#        (Termux side, login se pehle) cp /sdcard/Download/Agent.zip ~/
#
# Ye script:
#   - apt update/upgrade (non-interactive, tzdata Asia/Kolkata)
#   - python3, venv, git, curl, cloudflared install
#   - Agent project ko /root/Agent me copy
#   - venv banake requirements install
#   - mcp/ folder ko mcp_local/ rename (naming collision fix, if needed)
#   - run_mcp_server.py ka path update
#   - server.py me DNS-rebinding-protection fix apply
#   - .env file banata hai (agar exist nahi karti)
###############################################################################

set -e

echo "=========================================="
echo " Step 1: apt update/upgrade (non-interactive)"
echo "=========================================="
export DEBIAN_FRONTEND=noninteractive
ln -fs /usr/share/zoneinfo/Asia/Kolkata /etc/localtime
apt update -y
apt install -y tzdata
dpkg-reconfigure --frontend noninteractive tzdata
apt upgrade -y

echo "=========================================="
echo " Step 2: Zaroori packages install"
echo "=========================================="
apt install -y python3 python3-pip python3-venv python3-full git nano curl

echo "=========================================="
echo " Step 3: cloudflared install (agar already nahi hai)"
echo "=========================================="
if ! command -v cloudflared >/dev/null 2>&1; then
    ARCH=$(uname -m)
    if [ "$ARCH" = "aarch64" ]; then
        CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
    else
        CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    fi
    curl -L "$CF_URL" -o /usr/local/bin/cloudflared
    chmod +x /usr/local/bin/cloudflared
    echo "cloudflared installed."
else
    echo "cloudflared already installed, skipping."
fi

echo "=========================================="
echo " Step 4: Agent project copy karna"
echo "=========================================="
SRC_ZIP_DIR="/data/data/com.termux/files/home"
SRC_DIR="$SRC_ZIP_DIR/Agent"
DEST_DIR="/root/Agent"

if [ -d "$DEST_DIR" ]; then
    echo "Warning: $DEST_DIR already exists, isko delete karke fresh copy kar rahe hain."
    rm -rf "$DEST_DIR"
fi

if [ -d "$SRC_DIR" ]; then
    cp -r "$SRC_DIR" "$DEST_DIR"
    echo "Copied from $SRC_DIR"
elif [ -f "$SRC_ZIP_DIR/Agent.zip" ]; then
    apt install -y unzip
    mkdir -p /root/_agent_extract
    unzip -o "$SRC_ZIP_DIR/Agent.zip" -d /root/_agent_extract
    # Handle both nested Agent/ and flat zip layouts
    if [ -d /root/_agent_extract/Agent ]; then
        mv /root/_agent_extract/Agent "$DEST_DIR"
    else
        mkdir -p "$DEST_DIR"
        mv /root/_agent_extract/* "$DEST_DIR"/
    fi
    rm -rf /root/_agent_extract
    echo "Extracted from Agent.zip"
else
    echo "ERROR: Na to $SRC_DIR mila na $SRC_ZIP_DIR/Agent.zip"
    echo "Pehle Agent folder/zip Termux home me daalo, phir dobara chalao."
    exit 1
fi

cd "$DEST_DIR"

echo "=========================================="
echo " Step 5: naming collision fix (mcp -> mcp_local)"
echo "=========================================="
if [ -d "mcp" ] && [ ! -d "mcp_local" ]; then
    mv mcp mcp_local
    sed -i 's/"mcp" \/ "server.py"/"mcp_local" \/ "server.py"/' run_mcp_server.py
    echo "mcp/ ko mcp_local/ me rename kiya aur run_mcp_server.py update kiya."
else
    echo "mcp_local/ already sahi hai, skip."
fi

echo "=========================================="
echo " Step 6: Python virtual environment + requirements"
echo "=========================================="
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=========================================="
echo " Step 7: mcp package ko v1.x pe pin karna (v2 breaking changes se bachne ke liye)"
echo "=========================================="
pip uninstall mcp -y || true
pip install "mcp<2"

echo "=========================================="
echo " Step 8: DNS rebinding protection fix apply karna"
echo "=========================================="
python3 - <<'PYEOF'
path = "mcp_local/server.py"
with open(path, "r") as f:
    content = f.read()

if "TransportSecuritySettings" not in content:
    content = content.replace(
        "try:\n    from mcp.server.fastmcp import FastMCP\nexcept ImportError:\n    try:\n        from mcp.server import FastMCP  # type: ignore\n",
        "try:\n    from mcp.server.fastmcp import FastMCP\n    from mcp.server.transport_security import TransportSecuritySettings\nexcept ImportError:\n    try:\n        from mcp.server import FastMCP  # type: ignore\n        from mcp.server.transport_security import TransportSecuritySettings\n",
    )
    content = content.replace(
        '        "Prefer relative paths."\n    ),\n)',
        '        "Prefer relative paths."\n    ),\n    transport_security=TransportSecuritySettings(\n        enable_dns_rebinding_protection=False,\n    ),\n)',
    )
    with open(path, "w") as f:
        f.write(content)
    print("DNS rebinding protection fix applied.")
else:
    print("Fix already applied, skip.")
PYEOF

echo "=========================================="
echo " Step 9: .env file banana (agar nahi hai)"
echo "=========================================="
if [ ! -f ".env" ]; then
    RANDOM_TOKEN=$(head -c 24 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 24)
    cat > .env <<EOF
# --- Security ---
AGENT_API_TOKEN=${RANDOM_TOKEN}
REQUIRE_CONFIRMATION=true
REQUIRE_CONFIRMATION_REMOTE=true

# --- Limits / audit ---
MAX_STEPS=12
AUDIT_LOG_PATH=.agent_audit.jsonl
EOF
    echo ".env created. AGENT_API_TOKEN = ${RANDOM_TOKEN}"
    echo "IMPORTANT: Ye token save kar lo."
else
    echo ".env already exists, skip."
fi

echo "=========================================="
echo " DONE! Ab server aur tunnel start karo:"
echo "=========================================="
echo ""
echo "  Terminal 1 (isi session me, ya naye Ubuntu login me):"
echo "    cd /root/Agent && source .venv/bin/activate"
echo "    python3 run_mcp_server.py --http --port 8000"
echo ""
echo "  Terminal 2 (naya Termux session -> proot-distro login ubuntu):"
echo "    cloudflared tunnel --url http://localhost:8000"
echo ""
echo "  Fir tunnel URL + '/mcp' Grok Custom Connector me daalo."
