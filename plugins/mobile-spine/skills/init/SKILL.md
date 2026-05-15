---
name: init
description: Scaffold a new mobile-spine workspace (Claude Code subagent setup for Android + iOS + Backend across separate repos). Runs a short interview, replaces placeholders with the user's org / app / branch / Figma-MCP / license values, and writes the customized files into a chosen target directory. Trigger when the user asks to "set up mobile-spine", "scaffold the mobile multi-agent setup", "initialize a spine for mobile", or invokes /mobile-spine:init.
allowed-tools: [Read, Write, Bash, AskUserQuestion]
---

# mobile-spine:init

Bootstrap a new mobile-spine workspace by interviewing the user, then writing the user-customizable files into the chosen install location and a `.claude/mobile-spine.config.yaml` capturing the interview answers.

The static templates this skill consumes live next to this `SKILL.md` under `./templates/`. They are workspace-data only — CLAUDE.md, SETUP.md, README.md, LICENSE, .gitignore, .claude/settings.json, a thin `.claude/commands/feat.md` stub, _context/operations.md, plus `.gitkeep` files for empty directories.

**Not scaffolded** — the four subagents (`api-agent` / `pm-agent` / `android-agent` / `ios-agent`) and the full `/feat` command logic are **plugin primitives** (live in `plugins/mobile-spine/agents/` and `plugins/mobile-spine/commands/`, served globally by the plugin). The workspace's `.claude/commands/feat.md` is a thin delegation stub. The agents read `.claude/mobile-spine.config.yaml` at invocation to pick up the workspace's org / app / baseBranch / figma / copyright values. **This means `/plugin marketplace update claude-code-mobile-spine` propagates agent + `/feat` improvements to every workspace automatically — without modifying any workspace-owned file.**

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

**First, detect installed Figma MCP servers via the CLI.** As of Claude Code v2.x, `claude mcp list` prints one line per configured server in the shape `<name>: <url-or-cmd> - <status>`. The name portion is always followed by `: ` (colon-space), even when the name itself contains colons (e.g. `plugin:supabase:supabase`). Filter for lines containing "figma" (case-insensitive), then strip the `: <url>...` tail to recover the verbatim server name. The namespace is `mcp__<server-name>__*`.

```bash
DETECTED_FIGMA=$(claude mcp list 2>/dev/null \
  | grep -i figma \
  | sed -E 's/: .*$//')
DETECTED_FIGMA_COUNT=$(printf '%s' "$DETECTED_FIGMA" | grep -c .)
echo "DETECTED_FIGMA_COUNT=$DETECTED_FIGMA_COUNT"
# Emit each detected name on its own line, keyed so the executor can
# parse them as structured output alongside the count above.
[ "$DETECTED_FIGMA_COUNT" -gt 0 ] && printf '%s\n' "$DETECTED_FIGMA" | sed 's/^/DETECTED_FIGMA_NAME=/'
```

If the future Claude Code release changes this CLI format, detection degrades silently: `$DETECTED_FIGMA_COUNT` becomes 0 and the fallback option list (below) fires.

**Then build the question options dynamically:**

- If `DETECTED_FIGMA_COUNT > 0`, build options as follows:
  - One option per detected server (up to 3 — `AskUserQuestion` accepts at most 4 options total, and we reserve the 4th slot for `none`). If more than 3 figma servers are detected, keep the first 3 and append a single-sentence note in the question text: "Showing first 3 of N detected — others are still usable; edit `.claude/mobile-spine.config.yaml` after scaffolding."
  - Each option label: `mcp__<server-name>__*`. Description: "detected via `claude mcp list`".
  - **Recommended preference**: if `figma-desktop` is among the detected names, mark it `(Recommended)` (it's the official Figma Dev Mode MCP). Otherwise leave none marked — first-detected order is just whatever `claude mcp list` emitted, not an editorial signal.
  - Final option: `none` — "skip Figma integration for now (UI sections will always be deferred)".
- If `DETECTED_FIGMA_COUNT == 0` (no figma servers installed, or `claude mcp list` unavailable), fall back to the hardcoded options:
  - `mcp__figma__*` — generic placeholder (replace after MCP setup via `/mcp`)
  - `mcp__figma-desktop__*` — official Figma Dev Mode MCP (selection-based; requires Figma paid plan + Desktop app) **(Recommended)**
  - `none` — skip Figma integration for now (UI sections will always be deferred)

Question parameters for `AskUserQuestion`:
- Question: "Which Figma MCP server are you using? (this affects pm-agent's `tools` whitelist)"
- Header: "Figma MCP"

**After the user answers, check the pm-agent compatibility window.** The plugin-shipped `pm-agent.md` has a fixed `tools` whitelist of `mcp__figma__*, mcp__figma-desktop__*` (see SETUP.md §3-4). If the selected namespace is neither of those (e.g. a detected custom server), MCP calls from pm-agent will be blocked at runtime. Print a one-line note to the user:

> Note: the selected namespace is outside pm-agent's default tool whitelist. After scaffolding, see SETUP.md §3-4 to override pm-agent at workspace level (create `.claude/agents/pm-agent.md` with your namespace added to `tools`).

Skip the note when the selection is `mcp__figma__*`, `mcp__figma-desktop__*`, or `none`.

### Q5. License copyright holder (free text)
> Who is the copyright holder for the LICENSE file? (your name, org, or "n/a" to leave the placeholder.)

### Q6. Install location (free text, default suggested)

The spine must be a **sibling** of the platform repos (`<app>-android`, `<app>-ios`, `<app>-backend`). Agents reach them via relative paths like `../<app>-android/` from the spine's cwd — if the spine is not in the same parent directory, every agent run will fail to find the repos (or need `/add-dir` each time).

**Detect existing sibling repos to pick a smart default:**

```bash
APP="<Q2>"
CWD_PARENT=$(dirname "$(pwd)")
# Guard against filesystem-root edge case ($(pwd) == "/") which makes
# dirname return "/" and would propose /<app>-spine. Fall back to $(pwd).
[ "$CWD_PARENT" = "/" ] && CWD_PARENT="$(pwd)"

SIBLINGS_FOUND=0
for p in android ios backend; do
  if [ -d "$CWD_PARENT/$APP-$p" ]; then
    SIBLINGS_FOUND=$((SIBLINGS_FOUND+1))
  fi
done

if [ "$SIBLINGS_FOUND" -gt 0 ]; then
  DEFAULT_TARGET="$CWD_PARENT/$APP-spine"
  echo "Detected $SIBLINGS_FOUND existing platform repo(s) under $CWD_PARENT/ — defaulting spine to sit alongside them."
else
  DEFAULT_TARGET="$(pwd)/$APP-spine"
  echo "No sibling platform repos detected under $CWD_PARENT/ — defaulting spine under $(pwd)."
fi
echo "DEFAULT_TARGET=$DEFAULT_TARGET"
```

Then ask the user (plain text, not `AskUserQuestion`):

> Where should the new spine be created?
>
> **Important:** the spine must live in the **same parent directory** as your platform repos, so agents can reach them via `../<app>-android/` etc. Target layout:
>
> ```
> <parent>/
>   ├── <app>-spine/      ← this scaffold
>   ├── <app>-android/
>   ├── <app>-ios/
>   └── <app>-backend/
> ```
>
> Default: `<DEFAULT_TARGET>`
> Hit enter to accept, or paste an absolute path.

**After the user answers, normalize and validate the sibling layout:**

```bash
# Normalize the user input so `dirname` works on relative paths or
# tilde-prefixed paths. Avoid `realpath` here — macOS ships BSD realpath
# which (a) lacks GNU's `-m` flag and (b) errors on non-existent paths
# (the common case for Q6 since the target dir is about to be created).
# Plain shell handles the two cases we care about: tilde expansion and
# relative-to-absolute conversion.
RAW_TARGET="<user-answer-or-DEFAULT_TARGET>"
# Tilde expansion for bare "~" or "~/..." only. Skips "~user" (POSIX shell
# can't reliably expand other-user homes, and AskUserQuestion users almost
# always paste either their own ~ or an absolute path anyway).
case "$RAW_TARGET" in
  "~"|"~/"*) RAW_TARGET="${HOME}${RAW_TARGET#\~}" ;;
esac
# Make the path absolute (prefix with $(pwd) when relative).
case "$RAW_TARGET" in
  /*) TARGET="$RAW_TARGET" ;;
  *)  TARGET="$(pwd)/$RAW_TARGET" ;;
esac

TARGET_PARENT=$(dirname "$TARGET")
[ "$TARGET_PARENT" = "/" ] && TARGET_PARENT="$TARGET"

SIBLINGS_AT_TARGET=0
for p in android ios backend; do
  if [ -d "$TARGET_PARENT/$APP-$p" ]; then
    SIBLINGS_AT_TARGET=$((SIBLINGS_AT_TARGET+1))
  fi
done
echo "TARGET=$TARGET"
echo "SIBLINGS_AT_TARGET=$SIBLINGS_AT_TARGET (out of 3) at $TARGET_PARENT/"
```

If `SIBLINGS_AT_TARGET` is `0`, warn the user once (plain text):

> **Warning:** none of `<app>-android` / `<app>-ios` / `<app>-backend` exist under `<TARGET_PARENT>/`. The spine will still be created, but you must clone the platform repos there before any agent run can succeed (see SETUP.md §3-2 for a `setup.sh` snippet that clones all three). Continue? (yes / no)

If the user declines, re-ask Q6.

## Step 3 — Confirm and substitute

The 5 substituted Qs (`org` / `app` / `baseBranch` / `figmaMcpNamespace` / `copyrightHolder`) flow into **two** outputs:

1. **`.claude/mobile-spine.config.yaml`** (single source of truth — agents read at runtime)
2. Inline substitution in workspace-owned **doc files** (CLAUDE.md / SETUP.md / README.md / LICENSE / `_context/operations.md` / `.claude/settings.json`) so docs read naturally with the user's specific values.

Build a substitution map for the doc-file inlining:

| Placeholder | Replacement | Substitution scope |
|---|---|---|
| `myorg` | Q1 | All processed template files |
| `myapp` | Q2 | All processed template files |
| `develop` (whole-word base-branch refs only) | Q3 | `SETUP.md` and `_context/operations.md` only — see precise rule in §4-2 |
| `<your name>` | Q5 | LICENSE only (skip if "n/a") |
| Install location | Q6 | Used as the write target, not substituted as text |

> Q4 (`figmaMcpNamespace`) is **not** substituted into any file — the agents read it from `.claude/mobile-spine.config.yaml` at invocation and adapt their figma tool calls accordingly. (v1.x substituted `mcp__figma__*` into agent files at init time; v2.0 ships agents as plugin primitives so that approach no longer applies.)

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

Create the target directory, write the templated doc files, and write the runtime config.

### 4-1. Create root and subdirectories
```bash
mkdir -p "<TARGET>/.claude/commands" \
         "<TARGET>/_context/api" "<TARGET>/_context/design" "<TARGET>/_tasks"
```

> `.claude/agents/` is **not** created — the four subagents are plugin primitives, served from `plugins/mobile-spine/agents/`. If the user later wants to override an agent at workspace level, they can create `.claude/agents/` themselves and add a file; project-level agents take precedence over plugin-level.

### 4-2. Process every file in `$TEMPLATES_DIR`

For each source file (preserve relative path):
1. Read with the Read tool.
2. Apply substitutions:
   - Global text: `myorg` → Q1, `myapp` → Q2.
   - In LICENSE only: `<your name>` → Q5 (skip if "n/a").
   - In `SETUP.md` and `_context/operations.md` only: replace the **whole word** `develop` when it refers to the base branch (i.e. as a literal Git branch name) with Q3. Concretely, substitute every occurrence matching the patterns below:
     - `Base branch: develop` (table cells / inline)
     - `--base develop` (gh / git CLI)
     - `` `develop` `` (backticked branch reference, e.g. "From `develop`" / "off `develop`")
     - `checkout -b develop` / `branch -a | grep develop` / standalone `develop` after `git ` commands
     - `feat/{n}-{feature}-{platform} off develop` and similar branch-name shapes ending in `off develop` (suffix in flow diagrams)
     - `develop branch present` (e.g. in operations.md week-0 result rows)
     **Do NOT** substitute: `develop` inside `figma-developer-mcp`, the words "development" / "developer", or any prose meaning "to develop". When unsure on a given line, leave it as-is — false positives break the file, false negatives only need a manual touch-up.
3. Write to the corresponding path under `<TARGET>`.

For `.gitkeep` files: copy as-is (no substitution).

For the workspace's thin `.claude/commands/feat.md` stub: copy as-is — the stub has no placeholders (it just delegates to `/mobile-spine:feat`).

The full list of files to process:

- `CLAUDE.md`
- `SETUP.md`
- `README.md`
- `LICENSE`
- `.gitignore`
- `.claude/settings.json`
- `.claude/commands/feat.md` (thin stub, copy as-is)
- `_context/operations.md`
- `_context/api/.gitkeep` (copy as-is)
- `_context/design/.gitkeep` (copy as-is)
- `_tasks/.gitkeep` (copy as-is)

### 4-3. Write the runtime config

After the file-processing loop, write `.claude/mobile-spine.config.yaml`. The agents (`pm-agent` / `api-agent` / `android-agent` / `ios-agent`) read this file at every invocation — it's the source of truth for workspace-specific values.

Normalize Q4 and Q5 first:

- `figmaMcpNamespace`: pass through the selected `mcp__<server-name>__*` namespace verbatim (whether detected dynamically or chosen from the hardcoded fallback list). If Q4 was `none`, set to YAML null (`null`, not the string `"none"`).
- `copyrightHolder`: pass through Q5 verbatim. If Q5 was `n/a`, set to YAML null.

Then write (note the single-quoted heredoc terminator `'EOF'` — prevents shell expansion of any `$` in Q values):

```bash
cat > "<TARGET>/.claude/mobile-spine.config.yaml" <<'EOF'
mobileSpineSchemaVersion: 1
org: <Q1>
app: <Q2>
baseBranch: <Q3>
figmaMcpNamespace: <Q4-normalized>
copyrightHolder: <Q5-normalized>
EOF
```

### 4-4. Sanity verify

```bash
# Core files written
test -f "<TARGET>/CLAUDE.md" && \
test -f "<TARGET>/SETUP.md" && \
test -f "<TARGET>/.claude/settings.json" && \
test -f "<TARGET>/.claude/mobile-spine.config.yaml" && \
test -f "<TARGET>/.claude/commands/feat.md" && \
echo "OK: core files written"

# No placeholder leakage in workspace docs
grep -l "myorg\|myapp" \
     "<TARGET>/.claude/settings.json" \
     "<TARGET>/.claude/commands"/*.md \
     "<TARGET>/CLAUDE.md" \
     "<TARGET>/SETUP.md" \
     "<TARGET>/README.md" \
     "<TARGET>/_context/operations.md" \
     2>/dev/null | head
# (Should print nothing — every placeholder in the workspace-owned docs must be substituted.)
```

> The thin `feat.md` stub may legitimately match `myorg`/`myapp` if its text mentions placeholder examples — exclude it from the grep above if needed. Currently the v2.0 stub has no such references, so the simple grep above works.

## Step 5 — Final report

Print to the user:

```
[mobile-spine:init] Scaffold complete.

Location: <TARGET>

Next steps:
  1. cd <TARGET>
  2. git init   # (optional — version control)
  3. Make sure these sibling repos exist:
       <TARGET_PARENT>/<Q2>-android
       <TARGET_PARENT>/<Q2>-ios
       <TARGET_PARENT>/<Q2>-backend
     (clone manually, or copy the setup.sh starter snippet from SETUP.md §3-2)
  4. cd <TARGET> && claude
  5. Inside the session, run /mcp to confirm the Figma MCP namespace if you set one.
  6. Walk through SETUP.md §9 Week 0 verification before relying on isolation.
```

## Notes

- **No git init / no GitHub repo creation.** This skill stops at file creation, by design (per the user's preference). Version control and remote setup are deliberate user actions.
- **Figma MCP namespace**: stored in `.claude/mobile-spine.config.yaml`. Agents read it at invocation; `null` means "skip all Figma steps". The plugin's `pm-agent` frontmatter lists both `mcp__figma__*` and `mcp__figma-desktop__*` in its `tools` array so either namespace works without per-workspace customization. If your namespace is something else entirely, you can override `pm-agent` at workspace level by creating `.claude/agents/pm-agent.md` with your `tools` list (project-level agents take precedence over plugin-level).
- **Stack-specific tweaks (Spring / Nest / FastAPI / Express)**: `api-agent.md` keeps all stacks listed. Since the agent is plugin-managed in v2.0, you can't prune unused entries at init time — but you also don't need to. The agent only acts on stacks it finds in `../<app>-backend/`.
- **License copyright placeholder**: if Q5 is "n/a", `<your name>` remains in the LICENSE and `copyrightHolder` is `null` in the config — the user fills it in later.
