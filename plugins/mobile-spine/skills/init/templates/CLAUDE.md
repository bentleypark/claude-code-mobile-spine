# mobile-spine — main session routing guide

> This file is **routing only**. Policy bodies live next to the things they
> govern (no duplication, no stale risk).

## What this repo is

`mobile-spine` is a **lightweight meta-repo** that sits next to your real code
repos: `myapp-android`, `myapp-ios`, `myapp-backend`. It carries no production
code — only markdown specs, policies, and run notes.

Outputs:
- `_context/api/*.md` — backend API specs (api-agent reads ../myapp-backend/ → writes here)
- `_context/design/{feature}/` — design assets per feature: Figma exports and/or HTML/CSS mockups (the recommended home for a `html` design source)
- `_tasks/{feature}.md` — the platform-neutral feature spec (pm-agent author; 1:1 with both repos' GitHub issues). Lean by design: ~150 lines, state-once, no per-repo code locations — those live in the GitHub issues, not here. See pm-agent.md §_tasks authoring discipline.
- `_tasks/{epic}/` — a multi-phase feature (an **epic**) is a directory, not a flat file: `00-overview.md` (phase list + status) plus numbered `NN-{phase}.md` phase files, each a normal `_tasks` spec. See pm-agent.md §Epic tasks / §Epic decomposition.
- `.claude/mobile-spine.config.yaml` — workspace-specific values (`org` / `app` / `baseBranch` / `figmaMcpNamespace` / `copyrightHolder`). Read by every agent at invocation. **Single source of truth** — if your branch convention or org changes, edit this file (no scattered substitutions across agent files).

Operational base:
- `SETUP.md` — phased adoption plan, week-1/2/3 entry criteria, validation checklist
- `_context/operations.md` — measurement items, retros, operational discoveries, next-step decisions (single source of truth for the run log)

## Directory map

```
mobile-spine/
├── CLAUDE.md                          # this file (routing)
├── SETUP.md                           # phased adoption / retro criteria
├── _context/
│   ├── operations.md                  # run log (retros, measurements, decisions)
│   ├── api/{domain}.md                # api-agent output
│   └── design/{feature}/              # design assets
├── _tasks/
│   ├── {feature}.md                   # pm-agent output — single-phase feature
│   └── {epic}/                        # multi-phase feature (epic): 00-overview.md + NN-{phase}.md
└── .claude/
    ├── commands/
    │   └── feat.md                    # thin stub → /mobile-spine:feat
    ├── mobile-spine.config.yaml       # workspace values (org/app/baseBranch/figma/copyright)
    └── settings.json                  # isolation guard (deny rules)
```

The four subagents (`api-agent` / `pm-agent` / `android-agent` / `ios-agent`) are **plugin primitives** — they live in `plugins/mobile-spine/agents/` (served globally by the plugin), not in your workspace's `.claude/agents/`. Plugin updates (`/plugin marketplace update claude-code-mobile-spine`) propagate agent improvements automatically. If you want to override an agent locally, create `.claude/agents/<name>.md` in this workspace — project-level agents take precedence over plugin-level.

## Subagent routing (4 agents — all plugin-provided)

| When | Subagent | Output / scope | Definition |
|---|---|---|---|
| Backend changed → spec refresh | `api-agent` | Writes `_context/api/*.md`. Read-only on myapp-backend | plugin: `plugins/mobile-spine/agents/api-agent.md` |
| New feature _tasks | `pm-agent` | Writes `_tasks/*.md`. Reads `_context/api/` + a design source (Figma MCP or HTML mockup). Does not grep platform code | plugin: `plugins/mobile-spine/agents/pm-agent.md` |
| Android implementation | `android-agent` | Modifies myapp-android only. Compose conventions | plugin: `plugins/mobile-spine/agents/android-agent.md` |
| iOS implementation | `ios-agent` | Modifies myapp-ios only. SwiftUI; honors `myapp-ios/CLAUDE.md` over spine rules | plugin: `plugins/mobile-spine/agents/ios-agent.md` |

Each agent reads `.claude/mobile-spine.config.yaml` at invocation to resolve workspace-specific values (`org`, `app`, `baseBranch`, etc.). Agent responsibilities, allowed paths, and pre-check procedures live in the plugin-side definition files. The table above is just an entry index.

## 4-case classification (pm-agent runs this on every call)

| Case | Condition | Handling |
|---|---|---|
| **A** | Existing domain + existing endpoint (already in `_context/api/{domain}.md`) | Proceed + after dry-run, confirm client-side implementation status |
| **B** | Existing domain + new endpoint (some not in _context) | Ask user for spec source (backend PR / OpenAPI / doc) for the new endpoints, then proceed |
| **C** | New domain (`_context/api/{domain}.md` does not exist) | Author with an external spec source (temporary). After backend merge, refresh _context via api-agent and replace the path |
| **D** | Backend not built + no spec source | Defer _tasks creation. Print message and stop |

Details in the plugin's `pm-agent.md` §Step 1 (`plugins/mobile-spine/agents/pm-agent.md` — or browse on GitHub).

## Slash commands

| Command | Use | Where the logic lives |
|---|---|---|
| `/feat [note]` | Workspace shortcut → delegates to `/mobile-spine:feat` | thin stub: `.claude/commands/feat.md` |
| `/mobile-spine:feat [note]` | Interview for a new feature → invoke pm-agent | plugin: `plugins/mobile-spine/commands/feat.md` |
| `/mobile-spine:init` | (Re-)scaffold a workspace | plugin: `plugins/mobile-spine/commands/init.md` + `skills/init/SKILL.md` |

`/feat` runs a 4-item interview (feature + domain / case auto-detect + confirm / spec source / design source) and constructs the pm-agent prompt. A rich one-line `/feat <note>` is parsed up front, so only the still-unanswered items are asked. The design source is Figma MCP, an HTML mockup, or none; spec source accepts "none — derive from design" for a design-only feature. Two early checks can divert before the case interview: an epic-sized requirement routes to phased decomposition, and a feature **already built on one platform but not the other** routes to cross-platform parity (the reference platform agent reverse-extracts a spec-term brief; pm-agent authors `_tasks` + a single issue for the lagging platform). Policy reminders (candidate-asset keywords only / case-A implementation-status check / no design source → no invention) fire automatically on each call.

## Auto-loaded channels

- **CLAUDE.md (this file)** — auto-loaded on session start. Routing and the directory map are immediately visible.
- **Subagent definitions** — plugin-provided agents are **discovered** at session start (their frontmatter is registered so Claude can invoke them) but their *bodies* are loaded on demand, not pinned into the main session's context. After a plugin update (`/plugin marketplace update`), run `/reload-plugins` to pick up the new definitions in the current session (or restart Claude Code).
- **`.claude/mobile-spine.config.yaml`** — not auto-loaded into context, but read by every agent at invocation to resolve workspace values. Edit this file directly if your org / app / branch / figma namespace changes.
- **User memory** (optional) — if your Claude Code setup uses a persistent memory directory, its index loads automatically. Useful for user / feedback / project / reference notes that should outlive a session.

## Safety rules / isolation guards (summary)

- Each subagent's **allowed paths** are stated in its definition. Out-of-scope writes abort immediately.
- `.claude/settings.json` deny rules should block writes to external repos like myapp-backend. Confirm in week 0 (SETUP.md §9, Item 3).
- The `Updated:` timestamp in `_context/api/*.md` is **only** refreshed by api-agent. Hand edits break stale-check reliability.
- pm-agent has read-only grep capability, but **intentionally does not grep platform repos** for the `## Candidate assets` section — codebase inventory is each platform agent's job, just before implementation.

## Retro / measurement flow

Before each weekly checkpoint, consult `_context/operations.md` §phase-transition triggers. Validation results land in §week-N pilot results. Next-step decisions live there too.
