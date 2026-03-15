# Adobe I/O CLI — End-to-End Workflow Guide

## Prerequisites

- Node.js 18+ and npm
- `aio` CLI installed: `npm install -g @adobe/aio-cli`
- Access to Adobe Developer Console (org with App Builder entitlement)

---

## 1. Authenticate

```bash
aio login
# Opens browser → Adobe IMS OAuth flow
# Token stored in local config (~/.config/@adobe/aio-cli/config.json)
```

Verify:
```bash
aio auth ctx        # Show current IMS context
aio where           # Should show nothing yet (no project selected)
```

---

## 2. Select Org → Project → Workspace

App Builder requires a Developer Console workspace to deploy into.

```bash
# List and select org
aio console org list
aio console org select <org-id>

# List and select project
aio console project list
aio console project select <project-id>

# List and select workspace (default: Stage or Production)
aio console workspace list
aio console workspace select <workspace-name>
```

Verify selection:
```bash
aio where
# → Shows: Org: Acme Corp | Project: My App | Workspace: Stage
```

---

## 3. Initialize a New App

```bash
aio app init my-app
# Interactive wizard:
#   - Select components (Actions, Web Assets, Events)
#   - Choose templates
#   - Downloads .env with workspace credentials
cd my-app
```

Key files created:
```
my-app/
├── app.config.yaml       # Action definitions, hooks, extensions
├── .env                  # AIO_RUNTIME_NAMESPACE, AIO_RUNTIME_AUTH, etc.
├── actions/              # OpenWhisk action source files
└── web-src/              # Optional React frontend (SPA)
```

---

## 4. Local Development

```bash
aio app run
# Starts:
#   - Local action server (port 9080 by default)
#   - Vite dev server for web-src (port 9000)
#   - Proxies /api calls to local actions
```

Or with live reload:
```bash
aio app dev
```

Invoke an action locally:
```bash
aio rt action invoke <action-name> --param key value --blocking
```

View local activation logs:
```bash
aio app logs
# or
aio rt activation list
aio rt activation get <activation-id>
```

---

## 5. Build

```bash
aio app build
# Bundles actions with webpack/parcel
# Output: dist/
```

---

## 6. Deploy

```bash
aio app deploy
# Uploads actions to I/O Runtime namespace
# Deploys web-src to CDN (if present)
# Prints deployed URLs
```

Get deployed URLs anytime:
```bash
aio app get-url
```

---

## 7. View Production Logs

```bash
aio app logs
# or directly via runtime:
aio rt activation list --limit 20
aio rt activation logs <activation-id>
```

---

## 8. Undeploy

```bash
aio app undeploy
# Removes Runtime actions and CDN assets
```

---

## Common Gotchas

| Problem | Fix |
|---|---|
| `aio where` shows nothing | Run `aio console org/project/workspace select` |
| `.env` missing credentials | Run `aio app use` to re-import workspace config |
| Token expired | Run `aio login` again |
| Action timeout | Check `app.config.yaml` — default timeout is 1000ms; max is 3600000ms |
| Deploy fails with 401 | Namespace/auth mismatch — verify `.env` matches selected workspace |
| `aio app run` port conflict | Kill existing process or set `PORT` in `.env` |

---

## System Limits (Runtime)

| Resource | Default | Max |
|---|---|---|
| Action timeout | 1 min | 60 min |
| Memory | 256 MB | 4 GB |
| Payload (request) | 1 MB | 5 MB |
| Payload (response) | 1 MB | 5 MB |
| Concurrent activations | 1000 | — |

Full limits: https://developer.adobe.com/app-builder/docs/overview/system_settings/

---

## Key Config: `app.config.yaml`

```yaml
application:
  actions: actions          # actions source dir
  web: web-src              # frontend source dir
  runtimeManifest:
    packages:
      my-app:
        license: Apache-2.0
        actions:
          my-action:
            function: actions/my-action/index.js
            web: 'yes'          # web action (no auth required)
            annotations:
              require-adobe-auth: true   # enforce IMS auth
            limits:
              timeout: 60000    # ms
              memory: 512       # MB
```

---

## Useful One-Liners

```bash
aio info                          # Dev environment versions
aio plugins                       # Installed CLI plugins
aio app info                      # Current app config summary
aio rt namespace list             # Available namespaces
aio rt action list                # All deployed actions
aio rt action get <name>          # Action details + code
aio console workspace download    # Re-download .env credentials
```
