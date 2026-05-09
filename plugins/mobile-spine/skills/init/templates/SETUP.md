# Mobile Spine — Subagent multi-agent setup guide

> A complete guide for configuring PM, API, Android, and iOS agents using
> Claude Code Subagents and a meta-repo coordination pattern, when Android
> (`myapp-android`), iOS (`myapp-ios`), and Backend (`myapp-backend`) live in
> **separate repos**.

---

## Table of contents

1. [Concepts](#1-concepts)
2. [Directory layout](#2-directory-layout)
3. [Initial setup](#3-initial-setup)
4. [Agent definition files](#4-agent-definition-files)
5. [CLAUDE.md — routing rules](#5-claudemd--routing-rules)
6. [Figma integration](#6-figma-integration)
7. [Backend API integration](#7-backend-api-integration)
8. [End-to-end workflow](#8-end-to-end-workflow)
9. [Phased adoption plan](#9-phased-adoption-plan)
10. [Reference — Agent Teams comparison](#10-reference--agent-teams-comparison)

---

## 1. Concepts

### What is the spine?

A **lightweight meta-repo** that sits next to the actual code repos. Not a
monorepo, not a git submodule. Each platform repo stays independent while
agent definitions, specs, and shared context are centrally managed in the
spine.

```
Problem:  With repos split apart, you need to repeat the same context to each agent every time.
Solution: Run claude inside the spine. From the spine's cwd, subagents can reach
          ../myapp-*/ via relative paths. Confirm this in your week 0 (§9, Item 0).
```

This scaffold applies the meta-repo coordination idea specifically to
**mobile multi-platform development** — see the README's *Acknowledgements*
for prior art on the broader pattern.

### Agent layout

| Agent | Role | Working location |
|---|---|---|
| api-agent | Read backend code, produce client-facing API specs | `../myapp-backend/` (read-only) |
| pm-agent | Author `_tasks/` from Figma + API specs; create GitHub issues; final review | `mobile-spine/_tasks/` |
| android-agent | Kotlin/Compose implementation; honors `myapp-android/CLAUDE.md` | `../myapp-android/` |
| ios-agent | Swift/SwiftUI implementation; honors `myapp-ios/CLAUDE.md` | `../myapp-ios/` |

### Subagent vs Agent Teams

| | Subagent | Agent Teams |
|---|---|---|
| Stability | Stable | Experimental (since v2.1.32~) |
| Model | Sonnet supported | Opus required |
| Cost | Lower | 3~4× higher |
| Inter-agent comms | Through main session | Direct |
| Directory isolation | ⚠️ backend deny should block (verify week 0); android↔ios is tools + description (prompt-level) | ❌ Same |
| Recommended start | ✅ Start here | Consider when scope grows |

> **Isolation strategy**
> - **myapp-backend write**: `settings.json` `deny` should block writes technically (Claude can attempt, the harness rejects). Confirm in your week 0 (§9, Item 3).
> - **myapp-android ↔ myapp-ios mutual isolation**: `tools` whitelist + `description` guard = **prompt-level guard**. Not a hard technical block — relies on the model's cooperation. Plan to verify with humans periodically.

---

## 2. Directory layout

> The diagram shows the **steady-state** layout after a few features land.
> `/mobile-spine:init` only writes the structural files (CLAUDE.md, SETUP.md,
> README.md, LICENSE, .gitignore, `.claude/agents/`, `.claude/commands/`,
> `.claude/settings.json`, `_context/operations.md`, plus `.gitkeep`
> placeholders for `_context/api/`, `_context/design/`, `_tasks/`). Everything
> else (`setup.sh`, `_context/architecture.md`, `_context/design/figma-links.md`,
> per-domain `_context/api/*.md`, per-feature `_tasks/*.md`) accumulates as
> you use the spine — api-agent / pm-agent / users add them over time.

```
~/dev/
├── mobile-spine/          ← claude runs here (new)
│   ├── CLAUDE.md          ← routing rules, shared conventions
│   ├── setup.sh           ← repo clone helper (not auto-generated; copy from §3-2 if needed)
│   ├── .claude/
│   │   ├── settings.json  ← system-level deny permissions (core)
│   │   └── agents/
│   │       ├── api-agent.md
│   │       ├── pm-agent.md
│   │       ├── android-agent.md
│   │       └── ios-agent.md
│   ├── _tasks/            ← per-feature specs (pm-agent author; tied to GitHub issues)
│   │   ├── login.md
│   │   └── profile.md
│   └── _context/
│       ├── architecture.md
│       ├── operations.md  ← retro after week 1
│       ├── api/           ← api-agent output (with Updated timestamp)
│       │   ├── auth.md
│       │   └── user.md
│       └── design/
│           └── figma-links.md
│
├── myapp-android/         ← existing Android repo (independent git)
├── myapp-ios/             ← existing iOS repo (independent git)
└── myapp-backend/         ← existing backend repo (independent git)
```

> The platform repos do not need to know mobile-spine exists.
> The spine is operator-level tooling.

---

## 3. Initial setup

### 3-1. Create the spine repo

```bash
mkdir ~/dev/mobile-spine && cd ~/dev/mobile-spine
git init

mkdir -p .claude/agents .claude/commands _tasks _context/design _context/api
```

### 3-2. setup.sh — clone helper for fresh environments

Skip if your repos already exist. Use this when bootstrapping a new machine.

```bash
cat > setup.sh << 'EOF'
#!/bin/bash
# Run on a fresh environment to clone the platform repos next to mobile-spine.
git clone https://github.com/myorg/myapp-android ../myapp-android
git clone https://github.com/myorg/myapp-ios ../myapp-ios
git clone https://github.com/myorg/myapp-backend ../myapp-backend
EOF
chmod +x setup.sh
```

### 3-3. settings.json — system-level deny permissions

`mobile-spine/.claude/settings.json` (project-scoped, commit to share with team).

> **settings file types**
> - `~/.claude/settings.json` — global (every project)
> - `mobile-spine/.claude/settings.json` — project-shared (team)
> - `mobile-spine/.claude/settings.local.json` — personal local
>
> Spine isolation is project-scoped, so put it in `mobile-spine/.claude/settings.json`.

```json
{
  "permissions": {
    "allow": [
      "Edit(../myapp-android/**)",
      "Write(../myapp-android/**)",
      "Edit(../myapp-ios/**)",
      "Write(../myapp-ios/**)"
    ],
    "deny": [
      "Edit(../myapp-backend/**)",
      "Write(../myapp-backend/**)"
    ]
  }
}
```

> **⚠️ deny scope is `myapp-backend` only**: Claude Code's settings.json
> permissions are project-scoped and inherited by subagents. Adding the android/ios
> repos to deny would block their dedicated agent from working at all. Mutual
> isolation between android and ios is reinforced via the `tools` field on each
> agent (next section).

### 3-4. Reinforce isolation via the agent `tools` field

The `tools` field in subagent frontmatter restricts which tools the agent can
call. Simpler and stricter than path deny rules.

| Agent | tools | Effect |
|---|---|---|
| api-agent | `Read, Grep, Glob, Bash, Write` | myapp-backend write blocked by settings.json deny |
| pm-agent | `Read, Write, Edit, Bash, Grep, Glob, mcp__figma__*` | Figma MCP tools included |
| android-agent | `Read, Write, Edit, Bash, Grep, Glob` | base implementation tools |
| ios-agent | `Read, Write, Edit, Bash, Grep, Glob` | base implementation tools |

> **pm-agent MCP tools**: Figma MCP registers under a namespace like
> `mcp__figma__*`. If you do not list it explicitly in `tools`, MCP tool calls
> are blocked. The exact namespace varies by MCP server name — check it via
> `/mcp` after setup and adjust.
>
> Omitting the `tools` field entirely allows all tools. If you are unsure of
> the MCP namespace at first, you can omit `tools` for pm-agent and rely on
> the description guard until you confirm.

Each agent's frontmatter looks like:

```markdown
---
name: pm-agent
description: >
  ...
tools: [Read, Write, Edit, Bash, Grep, Glob, "mcp__figma__*"]
---
```

### 3-5. Run Claude Code

```bash
# Always run from mobile-spine/
cd ~/dev/mobile-spine
claude
```

> **`/add-dir` policy** — confirm in week 0 (§9, Item 0) whether subagents can
> reach `../myapp-*/` from the spine's cwd without `/add-dir`. If yes, you may
> omit `/add-dir` from the normal workflow. If no, invoke `/add-dir` explicitly.
> `/remove-dir` is not officially supported — start a new session to clean up
> context.

---

## 4. Agent definition files

The four agent definitions live under `.claude/agents/`:

- `api-agent.md` — backend → spec extraction
- `pm-agent.md` — Figma + spec → _tasks; case classification; pre-checks; issue dry-run
- `android-agent.md` — Android implementation (two-phase: implement + diff / commit + Draft PR)
- `ios-agent.md` — iOS implementation (two-phase, with optional per-repo Figma 5-step procedure)

Open the files for full responsibilities, allowed paths, and execution order.
The summary table in [§1](#1-concepts) is just an entry index.

---

## 5. CLAUDE.md — routing rules

`mobile-spine/CLAUDE.md` carries routing only. The full content is in this
scaffold — open it directly. Highlights:

```markdown
# mobile-spine — main session routing guide

## Directory ownership
- api-agent:     ../myapp-backend/ read-only, _context/api/ write
- pm-agent:      _tasks/ read+write, _context/design/ scope
- android-agent: ../myapp-android/ scope (_tasks/ read-only)
- ios-agent:     ../myapp-ios/ scope (_tasks/ read-only)

System-level isolation: backend write blocked technically by settings.json deny.
Mutual android↔ios isolation: tools whitelist + description = prompt-level guard.

## Priority
Per-repo CLAUDE.md > spine CLAUDE.md
android-agent: ../myapp-android/CLAUDE.md takes precedence
ios-agent:     ../myapp-ios/CLAUDE.md takes precedence

## Feature flow
1. api-agent: analyze ../myapp-backend/ → write _context/api/{domain}.md (Updated)
2. pm-agent: stale check → Figma + spec → GitHub issue → _tasks/{feature}.md
3. android-agent · ios-agent: parallel implementation → user approval → commit → user approval → PR → done
4. [user] After each PR merges, tick the _tasks checkbox manually. pm-agent only does the cross-platform final review.

## Parallel rule
Android · iOS always run in parallel.
android-agent runs in one go. ios-agent honors the per-repo CLAUDE.md
Figma 5-step approval gates if defined (asymmetric on purpose).
On backend API change, api-agent refreshes _context/api/ → pm-agent stale check fires.

## /add-dir policy
Confirm in week 0 (§9, Item 0) whether subagents reach ../myapp-* from the
spine's cwd without /add-dir. If they do, the workflow may omit /add-dir.
Otherwise, invoke /add-dir explicitly. /remove-dir is unsupported — start a
new session.
```

---

## 6. Figma integration

### 6-1. Figma MCP connected (recommended)

When Figma MCP is connected to Claude Code, pm-agent can fetch components and
styles directly.

```bash
# claude settings.json — add the Figma MCP server
{
  "mcpServers": {
    "figma": {
      "command": "npx",
      "args": ["-y", "figma-developer-mcp", "--figma-api-key", "${FIGMA_API_KEY}"]
    }
  }
}
```

> Set `FIGMA_API_KEY` in `~/.zshrc` or `~/.bashrc`. The exact MCP server
> command may differ; consult the MCP server you choose.

### 6-2. No Figma MCP (asset export approach)

Manage links and exports under `_context/design/figma-links.md`:

```markdown
# Figma design links

## Login
- Figma URL: https://figma.com/file/xxx/Login
- Export location: _context/design/login/
  - login-android.png (1x, 2x, 3x)
  - login-ios.png (1x, 2x, 3x)
  - color-tokens.json
  - typography.json
```

### 6-3. Future direction — markdown design specs

A growing pattern (mostly English-speaking ecosystem, 2025–2026) treats
markdown as the source of truth that AI agents consume, with Figma kept for
visual exploration. This template **does not yet support** an md-spec input
path in pm-agent — Figma MCP is the only first-class design source today.

If md-based design specs become your team's primary input, the natural
extension is to add a parallel branch in pm-agent's pre-check 3 ("design
source: Figma MCP / `_context/design/{feature}/DESIGN.md` / none"). The
underlying specs are still alpha, so verify before adopting:

- [Google Labs `DESIGN.md` (Apache-2.0, v0.1.0, 2026-04)](https://github.com/google-labs-code/design.md) — 9-section schema with YAML token frontmatter
- [W3C Design Tokens Format Module (stable, 2025-10)](https://www.designtokens.org/tr/drafts/format/) — `$value` / `$type` token shape
- [Figma Blog — Agents, Meet the Figma Canvas (2026-03)](https://www.figma.com/blog/the-figma-canvas-is-now-open-to-agents/) — Figma's own framing as a hybrid (MCP for structure, markdown skills for conventions)

Community PRs that wire an md-spec branch into pm-agent are welcome.

---

## 7. Backend API integration

### 7-1. How api-agent works

api-agent reads `../myapp-backend/` and writes a client-facing spec under
`_context/api/`. The output starts with an `Updated:` timestamp so pm-agent
can decide whether the spec is stale.

```
myapp-backend/
  └─ src/.../AuthController       →  api-agent  →  _context/api/auth.md (Updated: 2026-05-08)
  └─ src/.../UserController       →  api-agent  →  _context/api/user.md (Updated: 2026-05-08)
```

### 7-2. When backend code does not exist yet

api-agent can author a draft spec under `_context/api/` and update it once
backend implementation lands.

```
api-agent: Draft a spec for the login API.
           Backend code does not exist yet, plan is REST + JWT.
           Write _context/api/auth.md.
```

### 7-3. Refreshing a spec

```
api-agent: Re-read auth-related code in ../myapp-backend/
           and update _context/api/auth.md.
```

pm-agent compares the `Updated:` timestamp against the backend's last commit
and refuses to proceed if stale.

---

## 8. End-to-end workflow

### Full flow (Figma + backend API)

```
Implement the login screen.
Figma: https://figma.com/file/xxx/Login

Order:
1. api-agent analyzes ../myapp-backend/ auth → writes _context/api/auth.md
2. pm-agent reads Figma + _context/api/auth.md → creates GitHub issue → writes _tasks/login.md
3. android-agent · ios-agent implement in parallel (off `develop`)
```

### Feature request (no Figma yet)

```
Implement the login screen.
api-agent first, pm-agent next (with issues), android · ios in parallel.
```

### Internal sequence

```
user request
  ├─ api-agent
  │    └─ analyze ../myapp-backend/ → _context/api/auth.md (Updated)
  └─ [continue or new session]
       └─ pm-agent
            ├─ stale check: git log ../myapp-backend vs Updated
            ├─ gh issue create → issue #N (in each platform repo)
            └─ _tasks/login.md (Issue: #N)
                 ├─ android-agent ∥ ios-agent  ← run in parallel
                 │    ├─ [android] feat/{n}-login-android off develop
                 │    │    └─ implement → user approval → commit → user approval → PR → done
                 │    └─ [ios] feat/{n}-login-ios off develop
                 │         ├─ Figma 5-step procedure (start at 3 if pm-agent spec is present)
                 │         └─ implement → user approval → commit → user approval → PR → done
                 └─ [user] After each PR merges, tick _tasks checkboxes
                      └─ pm-agent: cross-platform final review (on user request)
```

> **/add-dir omission is conditional**: this flow omits `/add-dir` assuming
> subagents reach `../myapp-*` from the spine's cwd. Confirm in week 0 (§9,
> Item 0); if it fails, insert an explicit `/add-dir` step before pm-agent.
>
> **Asymmetric parallelism**: android-agent runs end-to-end; ios-agent honors
> the per-repo CLAUDE.md Figma 5-step approval gates. android may finish while
> ios is still waiting for an approval step.

---

## 9. Phased adoption plan

Don't deploy all four agents at once. Validate week by week.

### Week 0: pre-flight (mandatory before adoption)

| Item | Verify |
|---|---|
| **Item 0**: subagent inherits `/add-dir` | api-agent reads `../myapp-backend/README.md` without `/add-dir`. If it works, you can omit `/add-dir` from the workflow |
| **Item 1**: `develop` branch present in each repo | `git -C ../myapp-android branch -a \| grep develop` etc. |
| **Item 2**: `/remove-dir` available? | Officially unsupported — start a new session instead |
| **Item 3**: settings.json `deny` blocks writes | api-agent attempts a write under `../myapp-backend/` (e.g. a temporary marker file) → the harness must reject the tool use |
| **Item 4**: Figma MCP namespace | Confirm the actual `mcp__*` pattern via `/mcp` after MCP setup |

#### Week 0 verification snippets

```bash
# Verify develop branches exist
git -C ../myapp-android branch -a | grep develop
git -C ../myapp-ios branch -a | grep develop

# If missing, create them
git -C ../myapp-android checkout -b develop
git -C ../myapp-ios checkout -b develop
```

```bash
# Item 0 — in claude session:
# Ask api-agent to Read ../myapp-backend/README.md (single attempt, no /add-dir).
# ✅ Reads → pass. ❌ Cannot reach → fall back to /add-dir.
```

```bash
# Item 3 — in claude session:
# Ask api-agent to Write a temporary marker file under ../myapp-backend/.
# ✅ Harness rejects the write → pass. ❌ File created → re-check settings.json path/syntax.
```

### Week 1: api-agent only

Goal: validate output quality of `_context/api/`.

```
api-agent: Analyze the entire ../myapp-backend/ and write _context/api/.
# (omit /add-dir if week 0 Item 0 passed; otherwise add it explicitly)
```

Human verification (sample):

```bash
# 1. Compare controller list vs _context/api/ files
ls ../myapp-backend/src/**/controller/    # adjust to your stack
ls _context/api/
# → confirm no domain is missing

# 2. Endpoint count cross-check (Spring example)
grep -r "@GetMapping\|@PostMapping\|@PutMapping\|@DeleteMapping" ../myapp-backend/src/ | wc -l
grep -c "| GET\|POST\|PUT\|DELETE" _context/api/*.md
# → numbers should be in the same order
```

Sample 1~2 DTOs by reading the actual class side-by-side with the generated
spec. Block week 2 if this verification fails.

### Week 2: add pm-agent

Goal: validate per-repo CLAUDE.md integration + GitHub issue lifecycle.

Pass criteria:
- GitHub issues are created in both platform repos.
- Issue numbers are recorded in `_tasks/{feature}.md`.
- Stale check fires when `_context/api/` is out of date.

### Week 3: add android-agent and ios-agent in parallel

Goal: real isolation behavior on a small feature (e.g. login).

Pass criteria:
- android-agent does not touch myapp-ios / myapp-backend.
- ios-agent's per-repo Figma procedure (if any) gates user approvals correctly.
- "Add Files to Target in Xcode" notice prints when a new Swift file is created.
- Branches are created off `develop` correctly.
- No build is auto-run.

---

## 10. Reference — Agent Teams comparison

Subagents should be enough for most teams. Consider Agent Teams if scope grows.

### Activate Agent Teams

`~/.claude/settings.json`

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### When to switch

| Situation | Recommendation |
|---|---|
| Android · iOS in parallel (this scaffold's scope) | Subagent |
| Agents need direct inter-agent comms | Agent Teams |
| 3+ platforms simultaneously | Agent Teams |
| Cost-sensitive | Stay on Subagent |

> Agent Teams requires Opus and costs 3~4× more.
> Don't migrate while Subagent suffices.

---

*Targeted at Claude Code v2.1.32+*
