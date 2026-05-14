# mobile-spine — main session routing guide

> This file is **routing only**. Policy bodies live next to the things they
> govern (no duplication, no stale risk).

## What this repo is

`mobile-spine` is a **lightweight meta-repo** that sits next to your real code
repos: `myapp-android`, `myapp-ios`, `myapp-backend`. It carries no production
code — only markdown specs, policies, and run notes.

Outputs:
- `_context/api/*.md` — backend API specs (api-agent reads ../myapp-backend/ → writes here)
- `_context/design/{feature}/` — Figma assets pulled per feature
- `_tasks/{feature}.md` — the platform-neutral feature spec (pm-agent author; 1:1 with both repos' GitHub issues). Lean by design: ~150 lines, state-once, no per-repo code locations — those live in the GitHub issues, not here. See pm-agent.md §_tasks authoring discipline.

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
├── _tasks/{feature}.md                # pm-agent output
└── .claude/
    ├── agents/                        # 4 subagent definitions
    │   ├── api-agent.md
    │   ├── pm-agent.md
    │   ├── android-agent.md
    │   └── ios-agent.md
    ├── commands/
    │   └── feat.md                    # /feat interview → pm-agent
    └── settings.json                  # isolation guard (deny rules)
```

## Subagent routing (4 agents)

| When | Subagent | Output / scope | Definition |
|---|---|---|---|
| Backend changed → spec refresh | `api-agent` | Writes `_context/api/*.md`. Read-only on myapp-backend | `.claude/agents/api-agent.md` |
| New feature _tasks | `pm-agent` | Writes `_tasks/*.md`. Reads `_context/api/` + Figma MCP. Does not grep platform code | `.claude/agents/pm-agent.md` |
| Android implementation | `android-agent` | Modifies myapp-android only. Compose conventions | `.claude/agents/android-agent.md` |
| iOS implementation | `ios-agent` | Modifies myapp-ios only. SwiftUI; honors `myapp-ios/CLAUDE.md` over spine rules | `.claude/agents/ios-agent.md` |

Each agent's responsibilities, allowed paths, and pre-check procedure live in
its own definition file. The table above is just an entry index.

## 4-case classification (pm-agent runs this on every call)

| Case | Condition | Handling |
|---|---|---|
| **A** | Existing domain + existing endpoint (already in `_context/api/{domain}.md`) | Proceed + after dry-run, confirm client-side implementation status |
| **B** | Existing domain + new endpoint (some not in _context) | Ask user for spec source (backend PR / OpenAPI / doc) for the new endpoints, then proceed |
| **C** | New domain (`_context/api/{domain}.md` does not exist) | Author with an external spec source (temporary). After backend merge, refresh _context via api-agent and replace the path |
| **D** | Backend not built + no spec source | Defer _tasks creation. Print message and stop |

Details in `.claude/agents/pm-agent.md` §Step 1.

## Slash commands

| Command | Use | Definition |
|---|---|---|
| `/feat [note]` | Interview for a new feature → invoke pm-agent | `.claude/commands/feat.md` |

`/feat` runs a 4-item interview (feature + domain / case auto-detect + confirm / spec source / Figma state) and constructs the pm-agent prompt. Policy reminders (candidate-asset keywords only / case-A implementation-status check / no-Figma → no invention) fire automatically on each call.

## Auto-loaded channels

- **CLAUDE.md (this file)** — auto-loaded on session start. Routing and the directory map are immediately visible.
- **Subagent definitions** — `.claude/agents/*.md` are loaded **only at session start**. After editing, restart Claude Code (see `_context/operations.md` §operational discoveries).
- **User memory** (optional) — if your Claude Code setup uses a persistent memory directory, its index loads automatically. Useful for user / feedback / project / reference notes that should outlive a session.

## Safety rules / isolation guards (summary)

- Each subagent's **allowed paths** are stated in its definition. Out-of-scope writes abort immediately.
- `.claude/settings.json` deny rules should block writes to external repos like myapp-backend. Confirm in week 0 (SETUP.md §9, Item 3).
- The `Updated:` timestamp in `_context/api/*.md` is **only** refreshed by api-agent. Hand edits break stale-check reliability.
- pm-agent has read-only grep capability, but **intentionally does not grep platform repos** for the `## Candidate assets` section — codebase inventory is each platform agent's job, just before implementation.

## Retro / measurement flow

Before each weekly checkpoint, consult `_context/operations.md` §phase-transition triggers. Validation results land in §week-N pilot results. Next-step decisions live there too.
