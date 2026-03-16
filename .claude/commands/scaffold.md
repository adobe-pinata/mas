---
allowed-tools: Agent, Skill, Write, Edit, Read, Bash, Glob, Grep
description: Scaffold a new Adobe Experience app under apps/ using Spectrum S2 components from a wireframe/POC spec
argument-hint: [app-codename] [wireframe-or-high-level-prompt]
model: opus
disable-model-invocation: true
---

# Purpose

Scaffold a new React SPA boilerplate for an Adobe Experience app under `apps/$1/`, using Adobe Spectrum S2 components. This command reads a wireframe/POC specification or high-level prompt, uses the `adobe-spectrum` agent to look up correct S2 component imports, props, and patterns, scaffolds the full directory structure mirroring `apps/experience-qa/client/`, and then invokes `/experts:frontend:plan` to elaborate an implementation plan. Follow the `Instructions` and `Workflow` sections below.

## Variables

APP_CODENAME: $1
WIREFRAME_SPEC: $2
APP_ROOT: apps/$1
CLIENT_ROOT: apps/$1/client

## Instructions

- The new app lives at `apps/$1/` — never modify anything under `apps/experience-qa/` or any other existing app.
- Mirror the directory structure of `apps/experience-qa/client/` (src/pages, src/components, src/hooks, src/lib, etc.) but do NOT copy any business logic — only create the boilerplate skeleton.
- Use the `adobe-spectrum` agent (subagent_type: `adobe-spectrum`) to look up every S2 component referenced in the wireframe. Confirm correct import paths, required props, and usage patterns before writing any component file.
- All components must use React Spectrum S2 imports (e.g., `@react-spectrum/s2`). Do NOT use Spectrum 1 or raw HTML for components that have S2 equivalents.
- Use Vite as the bundler (match `apps/experience-qa/client/` config).
- Use inline CSS conventions consistent with the existing QA client (no CSS modules, no Tailwind).
- Each page identified in the wireframe gets its own file under `src/pages/`.
- Each reusable component gets its own file under `src/components/`.
- Create a minimal `App.tsx` with React Router routes for all pages identified in the wireframe.
- Create a minimal `main.tsx` entry point.
- Do NOT add server-side code — this command only scaffolds the client.
- After scaffolding, invoke `/experts:frontend:plan` to produce a detailed implementation plan for the new app based on the wireframe spec.

## Workflow

1. **Read the existing client structure** — Glob and Read `apps/experience-qa/client/` to understand the directory layout, Vite config, package.json, and App.tsx patterns to mirror.
2. **Parse the wireframe** — Analyze the `WIREFRAME_SPEC` to identify all pages, components, layouts, and S2 component needs.
3. **Look up S2 components** — Use the `adobe-spectrum` agent to look up every Spectrum S2 component referenced or implied by the wireframe. Collect import paths, required props, and usage examples.
4. **Create directory structure** — Create the folder tree:
   ```
   apps/$1/
   └── client/
       ├── index.html
       ├── package.json
       ├── vite.config.ts
       ├── tsconfig.json
       └── src/
           ├── main.tsx
           ├── App.tsx
           ├── vite-env.d.ts
           ├── pages/
           ├── components/
           ├── hooks/
           └── lib/
   ```
5. **Scaffold config files** — Write `package.json` (with `@react-spectrum/s2`, `react-router-dom`, `react`, `vite` deps), `vite.config.ts`, `tsconfig.json`, and `index.html`. Set the package name to `$1`.
6. **Scaffold pages** — For each page in the wireframe, create a stub file in `src/pages/` with the correct S2 component imports and a basic layout skeleton.
7. **Scaffold components** — For each reusable component in the wireframe, create a stub file in `src/components/` using the S2 patterns retrieved in step 3.
8. **Scaffold App.tsx and main.tsx** — Wire up React Router with all page routes and wrap in the S2 Provider.
9. **Invoke /experts:frontend:plan** — Call the `frontend` expert plan skill to elaborate a full implementation plan for the new app based on the wireframe, referencing the newly scaffolded files.

## Report

After completion, report back with:
- The app codename used: `$1`
- A tree listing of all files created under `apps/$1/`
- A summary of S2 components used and their import sources
- Any wireframe elements that could NOT be mapped to an S2 component (with suggested alternatives)
- The implementation plan output from `/experts:frontend:plan`
