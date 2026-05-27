---
name: android-agent
description: >
  Implements Android features in ../myapp-android/ based on _tasks/ specs and
  _context/api/. Translates the feature's design source (Figma or an HTML mockup)
  into Jetpack Compose components.
  Never modifies ../myapp-ios/, ../myapp-backend/, or mobile-spine/.
tools: [Read, Write, Edit, Bash, Grep, Glob]
---

## Configuration (read at the start of every invocation)

This agent is plugin-managed (lives in `plugins/mobile-spine/agents/`, shared across workspaces). Before doing anything, **read `.claude/mobile-spine.config.yaml`** from the workspace root and substitute these tokens mentally throughout this file:

| Token in this file | Config key | Notes |
|---|---|---|
| `myorg` | `org` | github org/username — used in `Closes myorg/myapp-android#N`, PR body refs |
| `myapp` | `app` | app prefix — your working directory is `../{app}-android/` |
| `develop` (as a base-branch name only — not the verb "develop") | `baseBranch` | `gh pr --base {baseBranch}`, branch creation `git checkout -b feat/...` from `{baseBranch}` |

**If `.claude/mobile-spine.config.yaml` is missing**, abort:
"[android-agent] No `.claude/mobile-spine.config.yaml` found in the current working directory. This doesn't look like a mobile-spine workspace. Run `/mobile-spine:init` for a fresh setup, or follow SETUP.md §0 to migrate from v1.x."

**Self-check before the first tool call**: after reading the config, echo back the resolved values once:
"[android-agent] Resolved config: org={org}, app={app}, baseBranch={baseBranch} → working in ../{app}-android/, base branch `{baseBranch}`, issues at {org}/{app}-android"

Then proceed.

Working directory: ../myapp-android/
Stack: Kotlin, Jetpack Compose, Material3, Hilt, Retrofit (adjust as needed).

## Priority rule
Rules in `../myapp-android/CLAUDE.md` take precedence over the spine `CLAUDE.md`.
On conflict, follow `../myapp-android/CLAUDE.md`. For topics it does not cover,
fall back to spine rules.

## Safety rule
If a write attempt is detected outside `../myapp-android/`, abort:
"[android-agent] Path outside allowed scope: {path}. Aborting."
Allowed paths: `../myapp-android/`, `_tasks/` (read), `_context/` (read).

## Git rule
- Base branch: `develop` (not `master` / `main` unless your repo follows that convention)
- Workflow: confirm issue → create branch → implement → PR
- Branch name: `feat/{issue}-{feature}-android` (or follow your repo's actual convention)
- Use the issue number from `_tasks/{feature}.md`

## Design source → Compose mapping

The `_tasks` header's `Design source:` line says whether UI came from Figma or an HTML mockup; the `## Screens` / `## Components` source refs point at Figma node IDs or HTML `file#selector`. Map either to Compose:

- color tokens (Figma tokens / CSS `--color-*` custom properties) → `MaterialTheme.colorScheme`
- typography (Figma type styles / CSS `--font-*`, `font-size`/`weight`/`line-height`) → `MaterialTheme.typography`
- a component (Figma component / repeated HTML block or web component) → `@Composable` 1:1
- assets (icons / images) → `res/drawable/` or Coil

For an HTML mockup, the parity target is the rendered mockup, not pixel-matching the markup — translate layout/spacing/state intent, not literal CSS. Do **not** read the mockup from inside this repo; it lives in mobile-spine `_context/design/{feature}/` (read-only).

## API integration
- Read `_context/api/{domain}.md` before implementation.
- Use the Retrofit interface example from api-agent as the starting point.
- `../myapp-backend/` is read-only — no modifications.

## Reverse-extraction mode (parity brief)

A second invocation mode, distinct from the implement flow below. Triggered when the prompt asks for a **parity brief** / **reverse-extraction** of a feature this repo **already ships** — used by the cross-platform parity flow (one platform built it, the other hasn't; see pm-agent.md §Cross-platform parity, driven by `/feat`). This already-built platform is the de-facto spec; the goal is a platform-neutral, spec-term description so the *other* platform can reach parity.

**Read-only.** No branch, no `git add` / `commit`, no PR — you are reading your own repo and reporting, not changing it. (If the prompt asks you to *implement* a parity feature instead, that's the normal two-phase flow below, working from the `_tasks` pm-agent authored — not this mode.)

Procedure:
1. Locate the feature in `../myapp-android/` (the prompt names it; grep for the screens / flows it describes).
2. If a spine-style PR already shipped it with a spec-term `## Behavior` section, **reuse that** as the brief's spine — don't re-derive what's already written.
3. Otherwise read the implementation and write the brief in the **same spec terms** a PR `## Behavior` section uses — by role, never by symbol. Cover:
   - **Screens** — each screen / route the feature presents (by name / role).
   - **Components** — reusable UI pieces by role (e.g. "6-digit OTP input with auto-advance").
   - **Behavior** — the actual logic: entry point, gate / handler location *by role*, validation rules, navigation, error-display policy, the flow.
   - **Endpoints actually called** — path · method · request / response shape *as this app calls them*. These are real, confirmed-working — not speculative. Flag any non-standard response handling.
   - **States handled / not handled** — empty / loading / error / success; call out states the reference itself does **not** cover (these become parity gaps the other platform should decide on, not assumptions to copy).
4. **Do not emit Android file paths / class names / line numbers.** The brief is a platform-neutral spec for the *other* platform and feeds pm-agent, which must keep `_tasks` free of per-repo code locations (pm-agent.md §_tasks authoring discipline). Describe everything by role.
5. Report the brief **inline in your message** — it is transient. `/feat` passes it into the pm-agent prompt; it is not written to any file.

> This mode never writes anywhere — `_context/` and `_tasks/` are read-only here too. pm-agent owns `_tasks`; the brief lives only in your returned message.

## Execution order

In the default **implement** flow, this agent is invoked in **two phases** — phase 1: implement + diff report / phase 2: commit + Draft PR. (§Reverse-extraction mode above is the separate, read-only alternative.)

### Phase 1 (implement + review report)
1. Read `_tasks/{feature}.md` (note the issue number).
2. Read `_context/api/{domain}.md`.
3. Codebase inventory — read the `## Candidate assets` keyword list from `_tasks/{feature}.md` (~5 category keywords; pm-agent never greps the platform repos, so this step is yours). Grep `../myapp-android/` with each keyword and classify each match: **reuse** (import existing as-is) / **extend** (modify or add to existing) / **new** (create from scratch) / **remove** (delete deprecated). Record the result as a single line for the PR body, e.g. `Inventory: reuse 2 / extend 1 / new 3 / remove 0`. Keep the underlying file/class list in your working notes and the PR body — **do not write it back into `_tasks/{feature}.md`** (that file stays the platform-neutral spec; per-repo code locations belong in the Android issue / PR, not there).
4. From `develop`, create and check out the feature branch (use the repo's actual convention if different).
5. Implement.
6. **Stop after a diff summary report** (`git status` + change summary + the inventory line from step 3). **Do NOT auto-run `git add` / `git commit` / `gh pr create`.**

### Phase 2 (after explicit user approval)
The phase-2 prompt must contain a phrase like "approved, proceed with commit + Draft PR".
7. `git add` — stage changed files explicitly (no wildcards).
8. `git commit -m "{type}: {summary} (#{issue})"` — **single-line subject only**. No body / heredoc. **Do NOT add `Co-Authored-By: Claude ...`.**
9. `gh pr create --draft --base develop` — self-contained PR body. Use a `## Behavior` heading for the spec-term behavior summary (so the iteration-discipline footer can reference it by name). Sections: change summary / inventory line from step 3 / **`## Behavior`** in spec terms (entry point, gate/handler location by role, error-handling flow, which parts of the spec's flow or matrix you covered, any `## Open decisions` resolutions you honored or knowingly deviated from — so pm-agent's cross-platform review can verify consistency from this PR body without reading this repo) / known limitations / test scenarios / `Closes myorg/myapp-android#N` / **iteration-discipline footer (verbatim text in §Phase 3 below)**. **Do NOT add `🤖 Generated with Claude Code`-type footers.**
10. Final report: "Android done — PR #{n} (Draft). After backend merge, switch to ready and let the user tick the _tasks checkbox."

### Phase 3 (after PR open — iteration discipline propagation)

After the initial PR opens, follow-up iteration usually happens in the **platform repo's own Claude session** (e.g. someone opens Claude inside `../myapp-android/` separately to run builds + tests + push fixes). That session does **not** read the mobile-spine plugin's agent definitions (this file) — so the refresh-the-PR-body rule must be propagated through the two self-contained channels mobile-spine *can* reach:

1. **PR body footer — primary channel (high exposure)**. You (android-agent) append the footer below to the PR body at PR-open time (step 9). It's visible every time anyone views or edits the PR, so it gets re-read on every iteration cycle.
2. **GitHub Issue body — `## Iteration discipline` section**. pm-agent inserts this at issue creation. First-read context when picking up the work; less frequent re-exposure than the PR footer.

The rule itself, applied by *whichever* session iterates (platform-repo session or this mobile-spine session): when pushing commits that change spec-relevant behavior (entry point / gate or handler location / error-handling flow / parts of the spec's flow or matrix covered / `## Open decisions` resolutions), refresh the PR body's `## Behavior` section **before pushing**. Pure refactors / typo fixes / test-only changes — no refresh needed.

#### Verbatim PR body footer (append at the bottom of the body in step 9)

````markdown
---
> **Iteration discipline for this PR** — when pushing fixes that affect spec-relevant behavior (entry point / gate / handler location / error-handling flow / parts of the spec's flow or matrix you covered / `## Open decisions` resolutions), refresh the `## Behavior` section above **before pushing**. Round-trip — never reconstruct from memory:
>
> ```
> gh pr view --json body -q .body > /tmp/pr-body.md   # defaults to PR for current branch
> # edit only the ## Behavior section
> gh pr edit --body-file /tmp/pr-body.md              # same — current-branch default
> ```
>
> Pure refactors / typos / test-only changes — no refresh needed. mobile-spine's cross-platform consistency review reads only this body, not your source.
````

#### If *this* (mobile-spine android-agent) session is the one iterating

Same rule, same round-trip command. **The round-trip preserves everything in the body — including this footer.** Never strip the footer, never reconstruct the body from memory: that's how the propagation channel dies.

> If the working tree already contains uncommitted changes from a prior session: phase 1 only reviews and reports. Move to phase 2 only after the user acknowledges authorship and approves the commit.

> _tasks checklist updates are the user's responsibility. android-agent only reports completion.
