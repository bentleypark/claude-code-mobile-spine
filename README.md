# Claude Code — Mobile Spine

A **Claude Code** scaffold for mobile teams whose Android, iOS, and Backend
live in **separate repos**. A lightweight meta-repo sits next to the three
platform repos and coordinates four specialized subagents, a case
classification flow, three pre-checks, and a `/feat` slash-command interview
that drives the whole pipeline end to end.

Install the bundled Claude Code plugin and run `/mobile-spine:init`: a
6-question interview writes a fully customized spine in one command.

---

## What you get

- **Four subagents** with explicit responsibilities and allowed paths:
  - `api-agent` — reads the backend, writes `_context/api/{domain}.md`
  - `pm-agent` — reads a design source (Figma MCP or an HTML mockup) + API specs, writes `_tasks/{feature}.md`, opens GitHub issues per platform
  - `android-agent` — implements in `../myapp-android/`; also a read-only **parity mode** (reverse-extraction + scope cross-check) when porting a feature from the other platform
  - `ios-agent` — implements in `../myapp-ios/`; same read-only parity mode
- **Isolation model** — `settings.json` `deny` should block writes to the backend repo (verify in week 0 — see SETUP.md §9 Item 3); each agent's `description` + per-agent allowed-paths in the prompt body keep android↔ios mutually isolated (prompt-level — relies on the model's cooperation, not a hard technical block).
- **`/feat` slash command** — 4-item interview (feature + domain / case auto-detect + confirm / spec source / design source) → pm-agent prompt auto-built. A rich one-line `/feat <note>` is parsed up front (one-shot), so only the still-unanswered items are asked. Spec source accepts "none — derive from design" for a design-only (no requirements doc) feature. Three early checks divert before the case interview: an epic-sized requirement routes to phased decomposition, a feature **already built on one platform but not the other** routes to cross-platform parity, and a change that **alters no backend endpoint** routes to client-only.
- **Cross-platform parity flow** — when a feature already shipped on one platform (often outside the spine), the reference platform agent reverse-extracts a platform-neutral, spec-term brief; pm-agent authors `_tasks` from it and opens a GitHub issue for the **lagging platform only**. pm-agent still never reads platform source — the brief comes from the platform agent.
- **Case classification** for every new feature:
  - A: existing endpoint / B: new endpoint in existing domain / C: new domain / D: backend not built
  - client-only: the change alters no endpoint (a copy edit, hiding an existing element) — the spec pre-checks are skipped rather than argued away
- **Three pre-checks** before pm-agent writes anything:
  - 1) staleness (`_context/api/{domain}.md` Updated vs backend HEAD)
  - 2) scope vs context comparison (catches deprecated endpoints still in spec)
  - 3) design source availability — figma / html / none (no inventing UI sections when none)
- **Two-phase agent invocation** — phase 1 implements + reports diff; phase 2 (only after explicit user approval) commits and opens a Draft PR. No surprise pushes.
- **Self-contained GitHub issue bodies** — the platform sessions never need to know mobile-spine exists.
- **Post-merge close-out** — after both PRs merge, pm-agent finalizes `_tasks` and records the per-platform shipped client version in a `Release:` header field (Android and iOS may ship at different app versions).
- **Phased adoption guide** — week-0 verification (subagent reaches `../` paths, `develop` branch present, `/remove-dir` unsupported, settings deny works, Figma MCP namespace identified), week-1 api-agent only, week-2 + pm-agent, week-3 + android/ios.

---

## Why mobile-specific?

Most existing Claude Code subagent collections are role-based catalogs
(frontend / backend / SRE / data) and assume a single monorepo. Mobile teams
typically have 3 separate repos (Android, iOS, Backend), the same feature
implemented twice, Figma as the design source of truth, and back-and-forth
with backend specs. This scaffold encodes those constraints.

---

## Quick start

Inside any Claude Code session, install the plugin from this GitHub repo:

```
/plugin marketplace add bentleypark/claude-code-mobile-spine
/plugin install mobile-spine@claude-code-mobile-spine
```

Then run the skill:

```
/mobile-spine:init
```

The skill asks for: GitHub org · app prefix · base branch · Figma MCP
namespace · license holder · install location. It writes the scaffolded files
and stops — `git init` and the GitHub remote stay your call.

See [plugins/mobile-spine/skills/init/README.md](./plugins/mobile-spine/skills/init/README.md)
for details.

To pull later agent/command improvements, run `/plugin marketplace update claude-code-mobile-spine`, then `/reload-plugins` to apply the new agent/command definitions in the current session — no full restart needed. (Restarting Claude Code also works, and is still the fallback for `settings.json` or workspace `.claude/agents/` override changes, which `/reload-plugins` does not cover.)

After scaffolding, run the week-0 verification (the scaffolded workspace's
`SETUP.md` §9 → Week 0) before relying on the isolation model.

> **If you can't use the plugin** (e.g. older Claude Code, scripted setup):
> clone this repo, copy `plugins/mobile-spine/skills/init/templates/` next to
> your platform repos manually, and follow the substitution rules in
> [plugins/mobile-spine/skills/init/SKILL.md](./plugins/mobile-spine/skills/init/SKILL.md)
> §4-2 by hand. The skill exists precisely to automate these substitutions
> across `myorg`, `myapp`, the base branch, the Figma MCP namespace, and the
> LICENSE copyright — expect 10+ minutes of careful editing if you go this
> route.

---

## Repository layout

### This repo (Claude Code plugin marketplace)

```
claude-code-mobile-spine/
├── README.md, LICENSE, .gitignore, CONTRIBUTING.md
├── .github/{ISSUE_TEMPLATE/, PULL_REQUEST_TEMPLATE.md, workflows/lint.yml}
├── scripts/
│   └── lint.py                                     ← static consistency lint (CI + local)
├── .claude-plugin/
│   └── marketplace.json                            ← marketplace catalog
└── plugins/
    └── mobile-spine/
        ├── .claude-plugin/
        │   └── plugin.json                         ← plugin manifest
        ├── agents/{api,pm,android,ios}-agent.md    ← plugin primitives (the four subagents)
        ├── commands/{init,feat}.md                 ← plugin primitives (slash commands)
        └── skills/
            └── init/
                ├── SKILL.md                        ← the interactive skill
                ├── README.md, smoke-test.sh
                └── templates/                      ← scaffold source the skill copies
                    ├── CLAUDE.md, SETUP.md, README.md, LICENSE, .gitignore
                    ├── .claude/{settings.json, commands/}   ← no agents/ (agents are plugin-provided)
                    ├── _context/{api/.gitkeep, design/.gitkeep, operations.md}
                    └── _tasks/.gitkeep
```

### Scaffolded workspace (after running `/mobile-spine:init`)

```
~/dev/
├── <your-app>-spine/
│   ├── CLAUDE.md, SETUP.md, LICENSE, .gitignore
│   ├── README.md                                  ← workspace-flavored (operator guide, not this repo's README)
│   ├── .claude/{settings.json, commands/, mobile-spine.config.yaml}   ← agents are plugin-provided, not scaffolded here
│   ├── _context/{api/.gitkeep, design/.gitkeep, operations.md}
│   └── _tasks/.gitkeep
├── <your-app>-android/
├── <your-app>-ios/
└── <your-app>-backend/
```

The scaffolded workspace's `README.md` is a short operator guide for the
spine itself (next steps / what's in here / daily workflow / origin link),
distinct from this repo's outward-facing README you're reading now.

---

## Status

- Targets Claude Code v2.1.32+ (requires plugin marketplace, `AskUserQuestion`, and subagent definitions).
- Plugin name: `mobile-spine`. Skill name: `init`. Slash command: `/mobile-spine:init`.
- Placeholder names used inside the bundled scaffold: `myorg`, `myapp`, `myapp-{android,ios,backend}` — substituted at scaffold time by the skill.
- The skill defaults to `mcp__figma__*` for the Figma MCP namespace; pick a different option (or replace later) if your Figma MCP server uses a different namespace.
- A static-consistency lint (`scripts/lint.py`) runs on every PR via GitHub Actions — it checks manifest validity, agent/command frontmatter, markdown links, header-field enumerations, and `§section` references (structure, not behavior). Run it locally with `python3 scripts/lint.py`.

---

## License

[MIT](./LICENSE)

---

## Acknowledgements

- [Spine Pattern](https://tsoporan.com/blog/spine-pattern-multi-repo-ai-development/) — Titus Soporan, 2026-01-26
- [Anthropic Claude Code](https://code.claude.com/) — subagent and slash-command primitives this scaffold builds on
