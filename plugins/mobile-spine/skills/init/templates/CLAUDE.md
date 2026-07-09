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

## Phase handoff discipline (main-session view)

When the main session invokes a platform agent (`android-agent` / `ios-agent`) for the implement flow, one routing decision and three handoff gates belong to the **main session** — not the agent. The agent's own prompt carries the agent-side constraint at each gate; this section spells out the **main-session-side** behavior, so abridged invocations and report-surfacing don't silently bypass the rule.

**0. Before invoking — decide whether to delegate at all.** A platform agent invocation is a fresh context. It has no memory of the previous one, so it must re-read the files it wrote last round before it can change a line. That cost is worth paying for judgment and worthless for typing.

**Delegate** when any of these holds:

- scope is open, or the repo must be inventoried to size the work
- it is the feature's first implementation
- a platform-convention call is needed — which UI framework the target screen actually uses, whether an existing component can be reused, what form an asset is in
- both platforms can proceed in parallel

**Implement inline** when *all* of these hold:

- every value is already decided — measurements, colors, copy: nothing to look up
- the change is small and mechanical
- the target files were already read in this session
- no convention judgment is required

The main session **may** edit the platform repos: `.claude/settings.json` pre-approves `Edit`/`Write` on `../myapp-android/` and `../myapp-ios/` (only the backend is denied). §Subagent routing names who owns the implement *flow*; it is not a write prohibition, and §Safety rules' allowed-path rule constrains each **subagent**, not this session.

**State the reason in the invocation.** Before handing work to a platform agent, print one line naming which of the four delegation criteria applies:

```
[main] Invoking android-agent — phase 1
       delegating because: scope open, repo inventory needed
```

This is a self-check, not a gate — nothing blocks an invocation with a weak reason. Its value is that a round of pure value-substitution has **no** criterion to name, and discovering that while writing the line is cheaper than discovering it after the agent has spent a context window re-reading its own output. A series of small design-correction rounds, each one a fresh agent rebuilding context to apply a number the coordinator already had, is the shape this exists to catch.

**Inline work carries its own obligation.** Declining to delegate means giving up the agent's phase-1 build/test gate. The main session then owes the same verification by hand: build the platform target, and review the diff, before reporting the change as done. Skipping delegation is not skipping verification.

**1. Phase 1 invocation prompt — include the git-baseline expectation.** The platform agent's §Phase 1 step 4 requires checking `git status --porcelain` (clean) and `git branch --show-current` (the integration branch — typically `develop`). The main session's Phase 1 prompt should explicitly remind the agent to run this baseline check first, so an abridged prompt ("phase 1 only — implement and report") does not silently skip step 4. On failure the agent stops and reports; the main session surfaces that report to the user and does not proceed without the user's resolution.

**2. After receiving Phase 1's report — do not synthesize the Phase 2 trigger phrase.** The platform agent's §Phase 2 description requires the trigger phrase ("approved, proceed with commit + Draft PR") to originate from the user — even when the Phase 1 report shows no concerns (clean build / passing tests / trivial diff), and even when the user previously expressed a blanket pre-authorization ("approve all clean phases"). The main session's job after Phase 1 is to surface the report to the user and wait. Asking "shall we proceed to Phase 2?" is fine; synthesizing the trigger phrase from a clean report is prohibited.

**3. After receiving Phase 2's "Draft PR opened" report — surface only spine-actionable next steps.** Once both platforms' Draft PRs exist (or the user confirms only one platform applies for this feature), the spine-actionable next-step ordering is:

- (a) user-triggered pm-agent §Cross-platform consistency review — before any Ready/merge, while both Draft surfaces still exist (post-merge runs cannot reconstruct the pre-merge surfaces).
- (b) Draft → Ready → reviewer approval → merge — user-driven.
- (c) after both merges, user-triggered pm-agent §Post-merge close-out.

Per-platform code review (`pr-review-toolkit:review-pr`, `code-review`, etc.) runs **inside each platform repo's own Claude session**, and therefore is **not** a spine-next-step. The reason is project context, not file access: a review is only as good as the repo's own `CLAUDE.md`, its conventions, its build. The spine session has none of those loaded, so a review it ran would be uninformed — even though it can read the files (see item 0). Mentioning it as "user's separate platform-session work" for signal is fine, but it is not in the spine's next-step ordering.

Policy bodies for the rule details live next to the things they govern:
- `agents/android-agent.md` / `agents/ios-agent.md` §Phase 1 step 4 (baseline check), §Phase 2 description (trigger ownership), §Phase 2 Final report (next-step ordering).
- `agents/pm-agent.md` §Cross-platform consistency review (after both PRs exist), §Post-merge close-out.

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
