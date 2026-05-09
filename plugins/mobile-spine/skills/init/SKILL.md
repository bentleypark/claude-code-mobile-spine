---
name: init
description: Scaffold a new mobile-spine workspace (Claude Code subagent setup for Android + iOS + Backend across separate repos). Runs a short interview, replaces placeholders with the user's org / app / branch / Figma-MCP / license values, and writes the customized files into a chosen target directory. Trigger when the user asks to "set up mobile-spine", "scaffold the mobile multi-agent setup", "initialize a spine for mobile", or invokes /mobile-spine:init.
allowed-tools: [Read, Write, Bash, AskUserQuestion]
---

# mobile-spine:init

Bootstrap a new mobile-spine workspace by interviewing the user, then writing
the templated files into the chosen install location with placeholders
replaced.

The static templates this skill consumes live next to this `SKILL.md` under
`./templates/`. They are full mobile-spine artifacts (CLAUDE.md, SETUP.md,
README.md, LICENSE, .gitignore, .claude/settings.json, .claude/agents/*.md,
.claude/commands/feat.md, _context/operations.md, plus `.gitkeep` files for
empty directories).

## Step 1 — Locate the templates directory

Resolve in three tiers. The harness *should* set `$CLAUDE_PLUGIN_ROOT` for
plugin-installed runs, but in practice this is not guaranteed (e.g. for
`directory`-typed marketplaces or older Claude Code versions). The cache and
working-tree fallbacks make the skill robust to either case.

```bash
TEMPLATES_DIR=""

# Tier 1 — plugin-installed via $CLAUDE_PLUGIN_ROOT (canonical when set).
# Skip when unset to avoid expanding to "/skills/init/templates" (absolute,
# never matches).
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  cand="$CLAUDE_PLUGIN_ROOT/skills/init/templates"
  if [ -f "$cand/CLAUDE.md" ] && [ -f "$cand/SETUP.md" ]; then
    TEMPLATES_DIR="$cand"
  fi
fi

# Tier 2 — known plugin cache (versioned glob). Picks the first matching
# version under $HOME/.claude/plugins/cache/.../mobile-spine/<ver>/.
if [ -z "$TEMPLATES_DIR" ]; then
  for cand in "$HOME/.claude/plugins/cache/claude-code-mobile-spine/mobile-spine"/*/skills/init/templates; do
    if [ -f "$cand/CLAUDE.md" ] && [ -f "$cand/SETUP.md" ]; then
      TEMPLATES_DIR="$cand"
      break
    fi
  done
fi

# Tier 3 — source-tree fallbacks (plugin development from a working checkout).
if [ -z "$TEMPLATES_DIR" ]; then
  for cand in \
    "$(pwd)/plugins/mobile-spine/skills/init/templates" \
    "$(pwd)/skills/init/templates" \
    "$(pwd)/templates"; do
    if [ -f "$cand/CLAUDE.md" ] && [ -f "$cand/SETUP.md" ]; then
      TEMPLATES_DIR="$cand"
      break
    fi
  done
fi

echo "TEMPLATES_DIR=$TEMPLATES_DIR"
```

If `TEMPLATES_DIR` is empty, abort with a clear message:
"[mobile-spine:init] templates/ directory not found. Install the `mobile-spine`
plugin via `/plugin install mobile-spine@claude-code-mobile-spine`, or run this
skill from the plugin's source repo working tree."

## Step 2 — Interview

Collect answers in this order. Use **plain-text questions for free-form
answers** (one question per turn). Use `AskUserQuestion` only for the choice
questions (base branch, Figma MCP).

### Q1. GitHub org or username (free text)
> What GitHub org / username should I use for the platform repos?
> Example: `acme` (resulting issue paths will look like `acme/<app>-android`).

### Q2. App prefix (free text)
> What is the app prefix? It will be applied to repo names and paths.
> Example: `cool-app` → `cool-app-android`, `cool-app-ios`, `cool-app-backend`.

### Q3. Base branch (`AskUserQuestion`)
- Question: "Which base branch convention does your team use?"
- Header: "Base branch"
- Options:
  - `develop` — integration branch; releases cut from `main`/`master` (Recommended for app-store release flows)
  - `main` — single trunk
  - `master` — legacy single trunk
  - `other` — type the branch name

### Q4. Figma MCP namespace (`AskUserQuestion`)
- Question: "Which Figma MCP server are you using? (this affects pm-agent's `tools` whitelist)"
- Header: "Figma MCP"
- Options:
  - `mcp__figma__*` — generic placeholder (replace after MCP setup via `/mcp`)
  - `mcp__figma-desktop__*` — official Figma Dev Mode MCP (selection-based; requires Figma paid plan + Desktop app)
  - `none` — skip Figma integration for now (UI sections will always be deferred)

### Q5. License copyright holder (free text)
> Who is the copyright holder for the LICENSE file? (your name, org, or "n/a" to leave the placeholder.)

### Q6. Install location (free text, default suggested)
> Where should the new spine be created?
> Default: `$(pwd)/<app>-spine` (replace `<app>` with your Q2 answer).
> Hit enter to accept the default, or paste an absolute path.

## Step 3 — Confirm and substitute

Build a substitution map from the answers:

| Placeholder | Replacement |
|---|---|
| `myorg` | Q1 |
| `myapp` | Q2 |
| `develop` (whole-word branch refs in `.claude/agents/*.md`, `SETUP.md`, `_context/operations.md` — see precise rule in §4-2) | Q3 |
| `mcp__figma__*` (literal, in code) | Q4 — see §4-2 for branch-on-value handling |
| `<your name>` (LICENSE only) | Q5 (skip if "n/a") |
| Install location | Q6 |

Print a summary back to the user (plain text, not AskUserQuestion):

```
[mobile-spine:init] Ready to scaffold:
  Target:    <Q6>
  GitHub:    <Q1>/<Q2>-android  /  <Q1>/<Q2>-ios  /  <Q1>/<Q2>-backend
  Branch:    <Q3>
  Figma MCP: <Q4>
  License:   <Q5>

Proceed? (yes / no)
```

If the user says no, stop without writing anything.

## Step 4 — Scaffold

Create the target directory and write each templated file.

### 4-1. Create root and subdirectories
```bash
mkdir -p "<TARGET>/.claude/agents" "<TARGET>/.claude/commands" \
         "<TARGET>/_context/api" "<TARGET>/_context/design" "<TARGET>/_tasks"
```

### 4-2. Process every file in `$TEMPLATES_DIR`

For each source file (preserve relative path):
1. Read with the Read tool.
2. Apply substitutions:
   - Global text: `myorg` → Q1, `myapp` → Q2.
   - Figma MCP namespace (literal-string match `mcp__figma__*`, including the trailing `*`):
     - If Q4 = `mcp__figma__*` (default): no-op (already correct).
     - If Q4 = `mcp__figma-desktop__*`: replace literal `mcp__figma__*` with `mcp__figma-desktop__*`.
     - If Q4 = `none`: **skip substitution** and emit a warning at Step 5 (the `mcp__figma__*` reference in `pm-agent.md` and the SETUP.md §6 Figma block need manual cleanup — see §Notes).
   - In LICENSE only: `<your name>` → Q5 (skip if "n/a").
   - In agent files (`.claude/agents/*.md`), `SETUP.md`, and `_context/operations.md` only: replace the **whole word** `develop` when it refers to the base branch (i.e. as a literal Git branch name) with Q3. Concretely, substitute every occurrence matching the patterns below:
     - `Base branch: develop` (table cells / inline)
     - `--base develop` (gh / git CLI)
     - `` `develop` `` (backticked branch reference, e.g. "From `develop`" / "off `develop`")
     - `checkout -b develop` / `branch -a | grep develop` / standalone `develop` after `git ` commands
     - `feat/{n}-{feature}-{platform} off develop` and similar branch-name shapes ending in `off develop` (suffix in flow diagrams)
     - `develop branch present` (e.g. in operations.md week-0 result rows)
     **Do NOT** substitute: `develop` inside `figma-developer-mcp`, the words "development" / "developer", or any prose meaning "to develop". When unsure on a given line, leave it as-is — false positives break the file, false negatives only need a manual touch-up.
3. Write to the corresponding path under `<TARGET>`.

For `.gitkeep` files: copy as-is (no substitution).

The full list of files to process:

- `CLAUDE.md`
- `SETUP.md`
- `README.md`
- `LICENSE`
- `.gitignore`
- `.claude/settings.json`
- `.claude/agents/api-agent.md`
- `.claude/agents/pm-agent.md`
- `.claude/agents/android-agent.md`
- `.claude/agents/ios-agent.md`
- `.claude/commands/feat.md`
- `_context/operations.md`
- `_context/api/.gitkeep` (copy as-is)
- `_context/design/.gitkeep` (copy as-is)
- `_tasks/.gitkeep` (copy as-is)

### 4-3. Sanity verify

```bash
# Confirm critical files exist + no placeholder leakage outside docs
test -f "<TARGET>/CLAUDE.md" && \
test -f "<TARGET>/SETUP.md" && \
test -f "<TARGET>/.claude/settings.json" && \
test -f "<TARGET>/.claude/agents/pm-agent.md" && \
echo "OK: core files written"

grep -l "myorg\|myapp" \
     "<TARGET>/.claude/agents"/*.md \
     "<TARGET>/.claude/commands"/*.md \
     "<TARGET>/.claude/settings.json" \
     "<TARGET>/CLAUDE.md" \
     "<TARGET>/SETUP.md" \
     "<TARGET>/README.md" \
     "<TARGET>/_context/operations.md" \
     2>/dev/null | head
# (Should print nothing — every placeholder across templates must be substituted.)
```

## Step 5 — Final report

Print to the user:

```
[mobile-spine:init] Scaffold complete.

Location: <TARGET>

Next steps:
  1. cd <TARGET>
  2. git init   # (optional — version control)
  3. Make sure these sibling repos exist:
       <PARENT>/<Q2>-android
       <PARENT>/<Q2>-ios
       <PARENT>/<Q2>-backend
     (clone manually, or copy the setup.sh starter snippet from SETUP.md §3-2)
  4. cd <TARGET> && claude
  5. Inside the session, run /mcp to confirm the Figma MCP namespace if you set one.
  6. Walk through SETUP.md §9 Week 0 verification before relying on isolation.
```

## Notes

- **No git init / no GitHub repo creation.** This skill stops at file creation, by design (per the user's preference). Version control and remote setup are deliberate user actions.
- **Figma MCP namespace**: if Q4 is `none`, the `mcp__figma__*` reference in `pm-agent.md` `tools` field is left as-is. The user should remove the line manually if they truly do not plan to use Figma MCP.
- **Stack-specific tweaks (Spring / Nest / FastAPI / Express)**: `api-agent.md` keeps all stacks listed. After scaffolding, the user can prune the unused entries.
- **License copyright placeholder**: if Q5 is "n/a", `<your name>` remains in the LICENSE — the user fills it in later.
