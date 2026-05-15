---
description: "Scaffold a new mobile-spine workspace via 6-question interview"
allowed-tools: [Read, Write, Bash, AskUserQuestion]
---

# /mobile-spine:init

Run the `mobile-spine:init` skill bundled with this plugin: a 6-question interview that scaffolds a mobile-spine workspace. The scaffold writes workspace-owned data only — `CLAUDE.md`, `SETUP.md`, `README.md`, `LICENSE`, `.gitignore`, `.claude/settings.json`, `.claude/mobile-spine.config.yaml` (from the interview), `.claude/commands/feat.md` (thin stub → `/mobile-spine:feat`), `_context/operations.md`, and `.gitkeep` placeholders under `_context/api/`, `_context/design/`, `_tasks/`.

The four subagents (`api-agent`, `pm-agent`, `android-agent`, `ios-agent`) and the full `/feat` command logic are **not** scaffolded — they're plugin primitives served globally from `plugins/mobile-spine/agents/` and `plugins/mobile-spine/commands/`. `/plugin marketplace update claude-code-mobile-spine` propagates updates to them automatically.

The skill body lives at `${CLAUDE_PLUGIN_ROOT}/skills/init/SKILL.md` — read that file first and follow its instructions verbatim. The skill resolves the templates directory via `${CLAUDE_PLUGIN_ROOT}/skills/init/templates/`, interviews the user, applies the (now-reduced v2.0) substitution scope to the doc templates, writes `.claude/mobile-spine.config.yaml` from the interview answers, and scaffolds to the chosen install location.

**Important**: do not deviate from the skill's substitution rules in §4-2, the config-write step in §4-3, or the sanity checks in §4-4 — they encode the placeholder discipline that keeps the scaffold consistent across users.
