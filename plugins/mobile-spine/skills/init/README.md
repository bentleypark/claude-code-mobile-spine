# `mobile-spine:init` (Claude Code Skill)

Interactive scaffold for a new mobile-spine workspace. Runs a 6-question
interview and writes the templated files into the directory of your choice
with placeholders replaced.

This skill is shipped inside the `mobile-spine` plugin in the
[`bentleypark/claude-code-mobile-spine`](https://github.com/bentleypark/claude-code-mobile-spine)
marketplace. End users install via `/plugin`; this README documents the
skill's behavior and is read mostly by contributors browsing the source.

## Install (end users)

```
/plugin marketplace add bentleypark/claude-code-mobile-spine
/plugin install mobile-spine@claude-code-mobile-spine
```

After install, the skill is callable as `/mobile-spine:init`.

## Use

```
/mobile-spine:init
```

The skill asks 6 questions:

1. GitHub org / username
2. App prefix
3. Base branch (`develop` / `main` / `master` / other)
4. Figma MCP namespace — options are populated by invoking `claude mcp list` (any server whose name contains "figma"). When no figma MCP is detected, falls back to a hardcoded `mcp__figma__*` / `mcp__figma-desktop__*` / `none` list.
5. License copyright holder
6. Install location — the spine must sit alongside `<app>-android` / `<app>-ios` / `<app>-backend` (agents reach them via `../`). The skill detects existing sibling repos and defaults to `<parent>/<app>-spine` when found; otherwise `$(pwd)/<app>-spine`.

Then writes the scaffolded files. Stops there — `git init` and remote setup
are intentionally left to the user.

## What gets created

A directory tree like:

```
<install location>/
├── CLAUDE.md, SETUP.md, README.md, LICENSE, .gitignore
├── .claude/
│   ├── settings.json
│   ├── mobile-spine.config.yaml         # runtime config (org/app/baseBranch/figma/copyright)
│   └── commands/feat.md                 # thin stub → /mobile-spine:feat
├── _context/
│   ├── operations.md
│   ├── api/.gitkeep
│   └── design/.gitkeep
└── _tasks/.gitkeep
```

The four subagents (`api-agent`, `pm-agent`, `android-agent`, `ios-agent`) and the full `/feat` command logic are **plugin primitives** (under `plugins/mobile-spine/agents/` and `plugins/mobile-spine/commands/`) — served globally by the plugin, not copied to the workspace. `/plugin marketplace update claude-code-mobile-spine` updates them in place.

## After scaffolding

Run `claude` from the new directory and walk through `SETUP.md` §9 Week 0
verification before relying on the isolation model.

## `/feat` slash command (in scaffolded workspaces)

Each scaffolded workspace ships a `/feat` slash command that runs a short
interview (feature + domain → case auto-detect & confirm → spec source for
new endpoints → design source) and then invokes `pm-agent` to author
`_tasks/{feature}.md`. The case auto-detector classifies the request as
A/B/C/D based on `_context/api/{domain}.md` presence, endpoint match, and an
explicit "backend not built" signal from the user.

Full workflow lives in the plugin's `commands/feat.md` (the real logic). The workspace's `.claude/commands/feat.md` is a 5-line delegation stub that forwards to `/mobile-spine:feat`. Plain `/feat` works ergonomically; plugin updates propagate automatically.

## Updating the skill

End users update via `/plugin marketplace update claude-code-mobile-spine`.
Contributors editing the skill source should update the `version` field in
the plugin's `plugin.json` so installed users receive the change.
