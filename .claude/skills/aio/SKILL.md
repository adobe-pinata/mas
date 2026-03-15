---
name: aio
description: Manages Adobe I/O App Builder apps, OpenWhisk Runtime actions, Developer Console projects, and Adobe Events via the aio CLI. Use when user asks about deploying, building, or running Adobe I/O apps, App Builder, runtime actions, activations, console workspaces, or Adobe Events.
---

# Adobe I/O CLI (aio)

App Builder app lifecycle, Runtime serverless actions, Developer Console, and Adobe Events.

**Auth:** `aio login` (IMS OAuth). Check context with `aio where`.

## Commands

### App Builder
- `aio app init` — Scaffold a new App Builder app
- `aio app build` — Build the app
- `aio app deploy` — Deploy to I/O Runtime + CDN
- `aio app undeploy` — Remove deployed app
- `aio app run` — Run locally (dev server)
- `aio app dev` — Live-reload local dev mode
- `aio app logs` — Fetch app logs
- `aio app get-url` — Show deployed action URLs
- `aio app info` — Show current app config

### Runtime (OpenWhisk)
- `aio runtime action` — Create/invoke/list/delete actions
- `aio runtime activation` — List/get activation logs and results
- `aio runtime package` — Manage action packages
- `aio runtime namespace` — List/select namespaces
- `aio runtime trigger` — Manage triggers
- `aio runtime rule` — Manage rules
- `aio rt` — Alias for `aio runtime`

### Developer Console
- `aio console org` — List/select orgs
- `aio console project` — List/select projects
- `aio console workspace` — List/select/download workspaces
- `aio where` — Show selected org/project/workspace

### Events
- `aio event provider` — Manage event providers
- `aio event registration` — Manage event registrations
- `aio event eventmetadata` — Manage event metadata

### Auth & Config
- `aio login` / `aio logout` — Authenticate with Adobe IMS
- `aio config get` / `aio config set` — Read/write persistent config

## Docs (load when needed)
- [docs/workflow.md](docs/workflow.md) — Auth → Console setup → Build → Deploy → Logs; common gotchas, system limits, `app.config.yaml` reference
- [docs/app-builder-overview.md](docs/app-builder-overview.md) — App Builder concepts
- [docs/first-app-guide.md](docs/first-app-guide.md) — Step-by-step first app
- [docs/runtime-using.md](docs/runtime-using.md) — Runtime actions, web actions, triggers, rules
- [docs/aio-cli-readme.md](docs/aio-cli-readme.md) — Core CLI reference
- [docs/aio-cli-plugin-app.md](docs/aio-cli-plugin-app.md) — `aio app` command details
- [docs/aio-cli-plugin-runtime.md](docs/aio-cli-plugin-runtime.md) — `aio runtime` command details

> For flags: `aio <command> --help`. For workflows and concepts: read relevant doc above.
