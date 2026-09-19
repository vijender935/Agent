# Agent — Cloud MCP Agent for Grok

Cloud-hosted **file + shell agent** exposed through a Streamable HTTP MCP endpoint. It is designed to run directly on Render, so it does not require Termux, Ubuntu/proot, ngrok, or Cloudflare Tunnel.

```
Grok → Render → MCP server → sandboxed workspace / shell
```

## Architecture

```
Agent/
├── core/
│   ├── workspace.py      # Path sandbox
│   ├── safety.py         # Risky command detection
│   └── tools/
│       ├── filesystem.py
│       ├── shell.py
│       └── __init__.py   # Tool registry
├── mcp_local/
│   └── server.py         # Streamable HTTP MCP server
├── security/
│   ├── confirmation.py   # Local-agent confirmation
│   └── audit.py          # JSONL audit logging
├── agent/                # Optional local Grok agent
├── config/settings.py
├── run_mcp_server.py
└── requirements.txt
```

## Render deployment

Use these Render settings:

- **Runtime:** Python
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `python run_mcp_server.py --http --host 0.0.0.0 --port $PORT`
- **Region:** Singapore
- **Plan:** Free (upgrade if you need persistent/high-throughput service)

Render supplies the `PORT` environment variable automatically.

After deployment, the MCP endpoint is:

`https://YOUR-SERVICE.onrender.com/mcp`

## Available MCP tools

| Tool | Description |
|---|---|
| `list_files` | List files/folders |
| `create_folder` | Create a folder |
| `create_file` | Create/replace a text file |
| `read_file` | Read a text file |
| `write_file` | Update a text file |
| `copy_file` | Copy a file |
| `move_file` | Move/rename a file or folder |
| `delete_path` | Delete a file/folder recursively |
| `run_command` | Run a shell command in the workspace |
| `agent_status` | Return service status |

Clipboard/Android/Termux integrations have been removed from the cloud version.

## Security model

Authentication is intentionally disabled as requested. The service therefore does not expect a Bearer token or OAuth flow.

The filesystem layer still enforces the workspace sandbox, and shell commands retain the project's risky-command detection. Audit logging remains enabled by default.

**Important:** an unauthenticated MCP endpoint with shell access should only be exposed to a trusted MCP client/network. If the service is public, anyone who can reach the endpoint may potentially invoke its tools.

## Workspace

By default the cloud service uses:

`/app/workspace`

You can override it with:

`AGENT_WORKSPACE=/some/path`

Additional allowed roots can be supplied through `AGENT_EXTRA_ROOTS` using the platform path separator.

## Optional local Grok agent

The `agent/` package remains available for running the xAI/Grok multi-step loop separately. The Render MCP service itself does not require an xAI API key.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_mcp_server.py --http --host 0.0.0.0 --port 8000
```

Then connect an MCP client to `http://localhost:8000/mcp`.

