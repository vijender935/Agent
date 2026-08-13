# Local Agent for Grok (Custom MCP Connector)

Sandboxed local **file + shell agent** jo **Grok Custom Connector** ke through Grok se connect hota hai.

```
Grok → (public tunnel URL) → aapka MCP server → workspace files / commands
```

Optional: local Grok agent (xAI API) same tools use karta hai.

---

## Architecture

```
Local-Agent-MCP/
├── core/                 # Domain logic (model-agnostic)
│   ├── workspace.py      # Path sandbox (multi-root support)
│   ├── safety.py         # Risky command detection
│   └── tools/            # filesystem + shell + clipboard + registry
├── security/             # Auth, confirmation, audit log
├── mcp_local/            # MCP server (named to avoid shadowing `mcp` package)
│   └── server.py
├── agent/                # Local Grok agent (optional)
│   ├── loop.py
│   └── providers/grok.py
├── config/settings.py
├── run_mcp_server.py     ← Grok Custom Connector ke liye
├── run_agent.py          ← Local agent
├── start_for_grok.sh
└── bootstraping.sh       # Termux/Ubuntu proot bootstrap helper
```

**Design goals**
- MCP pehle, local agent secondary
- Security by default (token, confirmation, audit)
- Clear separation of concerns
- Tools model-agnostic
- Multi-root workspace support (`AGENT_EXTRA_ROOTS`)

---

## Quick Start (Grok Custom Connector)

### 1. Setup

```bash
cd Local-Agent-MCP
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # optional edits
```

Workspace fix (optional):
```bash
export AGENT_WORKSPACE=/path/to/your/folder
# Optional extra roots (colon-separated):
# export AGENT_EXTRA_ROOTS=/sdcard/Download:/sdcard/DCIM
```

### 2. MCP Server

```bash
python run_mcp_server.py --http --port 8000
```

### 3. Public tunnel

```bash
ngrok http 8000
# ya
cloudflared tunnel --url http://localhost:8000
```

### 4. Grok mein Custom Connector

1. [https://grok.com/connectors](https://grok.com/connectors)
2. **New Connector** → **Custom**
3. Server URL: `https://YOUR-TUNNEL-URL/mcp`  
   (kabhi-kabhi bina `/mcp` bhi try karo)
4. Save / Connect

### 5. Test in Grok

```
list my files
create a folder called test
create hello.txt with content "Hello from Grok"
```

---

## Security (important)

| Feature | Default | Env |
|---------|---------|-----|
| Path sandbox | Always on | — |
| Bearer token auth | Off (hard-disabled for Grok UI) | `AGENT_API_TOKEN=...` |
| Local confirmation for delete / risky cmds | On | `REQUIRE_CONFIRMATION=true` |
| Block destructive tools for remote MCP | Off | `REQUIRE_CONFIRMATION_REMOTE=true` |
| Audit log (JSONL) | On | `AUDIT_LOG_PATH=.agent_audit.jsonl` |

**Production tips**
- Tunnel short time / trusted network only
- Prefer `REQUIRE_CONFIRMATION_REMOTE=true` agar aap delete/risky commands remote se nahi chalana chahte
- Audit log check karte raho

> Note: Grok Custom Connector UI currently only supports OAuth.  
> Plain Bearer auth is hard-disabled in the server so the connector can connect without showing the OAuth form.  
> For stronger protection use a reverse proxy or keep the tunnel private.

---

## Available Tools

| Tool | Description |
|------|-------------|
| `list_files` | List dir (non-recursive) |
| `create_folder` | Create folder (+ parents) |
| `create_file` | Create / overwrite text file |
| `read_file` | Read text file |
| `write_file` | Overwrite existing file |
| `copy_file` | Copy file |
| `move_file` | Move / rename |
| `delete_path` | Delete file or folder |
| `run_command` | Shell command in workspace |
| `get_clipboard` | Read Android/Termux clipboard |
| `set_clipboard` | Write to Android/Termux clipboard |
| `agent_status` | Status + workspace info |

Sab tools allowed roots ke andar sandboxed hain.

---

## Local Grok Agent (optional)

```bash
# .env
XAI_API_KEY=your_key_from_console.x.ai
# GROK_MODEL=grok-4.5

python run_agent.py
```

Yeh multi-step tool loop chalata hai (confirmation + audit included).

---

## Environment reference

```bash
AGENT_WORKSPACE=...
AGENT_EXTRA_ROOTS=/sdcard/Download:/sdcard/DCIM   # optional
AGENT_API_TOKEN=...
REQUIRE_CONFIRMATION=true
REQUIRE_CONFIRMATION_REMOTE=false
XAI_API_KEY=...
GROK_MODEL=grok-4.5
GROK_BASE_URL=https://api.x.ai/v1
MAX_STEPS=12
AUDIT_LOG_PATH=.agent_audit.jsonl
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Grok tools nahi dikha raha | URL end mein `/mcp` try karo; server + tunnel dono running? |
| Connection failed | Port / tunnel check karo |
| Import error | Project root se chalao + `pip install -r requirements.txt` |
| XAI_API_KEY error | Local agent ke liye `.env` mein key daalo |
| ngrok limit | Cloudflare Tunnel use karo |

---

Made for **Grok Custom MCP Connector** with a clean, security-conscious architecture.
