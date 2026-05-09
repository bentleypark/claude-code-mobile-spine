---
description: "Scaffold a new mobile-spine workspace via 6-question interview"
allowed-tools: [Read, Write, Bash, AskUserQuestion]
---

# /mobile-spine:init

Run the `mobile-spine:init` skill bundled with this plugin: a 6-question
interview that scaffolds a fully customized mobile-spine workspace
(`CLAUDE.md`, `SETUP.md`, `.claude/agents/`, `_context/`, etc.) with
placeholders replaced.

The skill body lives at `${CLAUDE_PLUGIN_ROOT}/skills/init/SKILL.md` — read
that file first and follow its instructions verbatim. The skill resolves the
templates directory via `${CLAUDE_PLUGIN_ROOT}/skills/init/templates/`,
interviews the user, applies substitutions, and writes the scaffold to the
chosen install location.

**Important**: do not deviate from the skill's substitution rules in §4-2 or
its sanity checks in §4-3 — they encode the placeholder discipline that keeps
the scaffold consistent across users.
