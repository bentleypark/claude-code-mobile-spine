# mobile-spine — operations log (starter)

> A run log you keep updated as you adopt this scaffold. Tracks measurements,
> retros, operational discoveries, and next-step decisions in a single source
> of truth.

---

## Items to measure

### 1. Is parallel execution actually parallel?

android-agent runs in one go; ios-agent honors the per-repo Figma 5-step gates
when applicable (asymmetric on purpose). In practice:
- Does android-agent finish first and block while ios-agent waits for an approval gate?
- How often does "parallel invocation" degrade into sequential?

**Trigger**: 3+ sequential degradations → consider simplifying ios-agent to
"approve spec only, implement in one go".

---

### 2. Are api-agent's outputs actually consumed?

Are `_context/api/*.md` files referenced from the main session during
android/ios implementation?
- Stale-check trigger frequency: do you find yourself re-running api-agent on
  every feature in the early days of backend churn?
- If too frequent, consider relaxing the criterion (e.g. 24-hour TTL).

**Caution**: hand-editing `_context/api/*.md` breaks the Updated timestamp's
reliability. Refresh only via api-agent.

---

### 3. Is pm-agent's Figma handling redundant with any existing skill?

Compare pm-agent processing Figma directly vs delegating to a separate skill.
- Does delegation work inside a subagent? (verify in week 0)
- If yes, consider moving pm-agent's Figma handling to the skill.

---

### 4. Subagent-x4 cost vs single session

Measure actual token usage:
- 4-subagent context cost
- Single session cost (with routing rules in CLAUDE.md driving sequential calls)

**Trigger**: >2× cost difference → fold pm/android/ios back into the main
session and keep only api-agent as a subagent (Phase A regression).

---

### 5. Isolation guard violations

Frequency of android-agent attempting to modify ../myapp-ios/ etc.
- On occurrence: tighten the description guard.
- 2+ occurrences: consider adding the path to settings.json deny — but this
  may break the responsible agent. Verify before applying.

---

## Phase-transition triggers

| Condition | Transition |
|---|---|
| api-agent output quality verified | → Phase B (add pm-agent) |
| Frequent parallel degradation | → ios-agent simplification |
| Subagent cost > 2× single session | → keep api-agent only, fold the rest into main |
| Isolation violation 2+ times | → tighten description guard |
| Skill-delegation works inside subagent | → move pm-agent Figma to skill |

---

## Week 0 verification — record your results here

| Item | Result | Notes |
|---|---|---|
| Item 0: subagent inherits `/add-dir` | ☐ pass / ☐ fail | |
| Item 1: develop branch present | ☐ pass / ☐ fail | |
| Item 2: `/remove-dir` available | ☐ no (officially unsupported) | start a new session |
| Item 3: settings.json deny works | ☐ pass / ☐ fail | |
| Item 4: Figma MCP namespace identified | ☐ done | namespace: `_______` |

**Decision to enter week 1**: ☐ go / ☐ block

---

## Week 1 pilot result

**Scope**: N domains — `domain1`, `domain2`, ...

**Outputs**: `_context/api/{domain}.md` × N, total {KB}, {endpoint count}.

**Quality verification** (per SETUP.md §9 week-1 criteria):

| Item | Result |
|---|---|
| Header (Updated / Source / Last commit) | ☐ pass / ☐ fail |
| Endpoint count (md vs server grep) | ☐ pass / ☐ fail |
| DTO sample #1 — `___` | ☐ pass / ☐ fail |
| DTO sample #2 — `___` | ☐ pass / ☐ fail |
| Additional insights captured | |

**Cost**: {tokens / tool uses / wall time}.

**Verdict**: ☐ production ready → week 2 / ☐ block, refine

**Notes / micro-findings**:
- ...

---

## Week 2 pilot result — pm-agent

**Scope**: 1~2 domains, mix of cases.

**Verification points**:

| Item | Result |
|---|---|
| Case classification correct | ☐ pass / ☐ fail |
| Pre-checks 1/2/3 fire correctly | ☐ pass / ☐ fail |
| Header / banners / completion checklist correct | ☐ pass / ☐ fail |
| Issue dry-run → user approval → live creation | ☐ pass / ☐ fail |

**Cost**: {tokens / tool uses / wall time}.

**Verdict**: ☐ production ready → week 3 / ☐ block, refine

**Findings to fold back into pm-agent.md**:
- ...

---

## Week 3 pilot result — android-agent / ios-agent

**Scope**: one small feature implemented end-to-end on both platforms.

**Verification points**:

| Item | Result |
|---|---|
| android-agent stays in `../myapp-android/` | ☐ pass / ☐ fail |
| ios-agent stays in `../myapp-ios/` | ☐ pass / ☐ fail |
| Per-repo CLAUDE.md priority honored | ☐ pass / ☐ fail |
| Two-phase split (diff / commit-PR) honored | ☐ pass / ☐ fail |
| Self-contained issue/PR bodies | ☐ pass / ☐ fail |
| `/feat` interview → pm-agent prompt → end-to-end works | ☐ pass / ☐ fail |

**Cost**: {tokens / tool uses / wall time per platform}.

**Verdict**: ☐ production ready / ☐ block, refine

**Findings to fold back into the agent definitions**:
- ...

---

## Operational discoveries

### Subagents load only at session start

Changes to subagent definitions don't take effect mid-session — invoking the
new/edited agent may give a "not found" or stale-behavior result.
**Always restart Claude Code after agent definition or `settings.json` changes.**
This applies regardless of whether the change is to a plugin agent (after
`/plugin marketplace update`) or a workspace override at `.claude/agents/<name>.md`.
Plan session restarts at every phase transition (week 0 → 1, week 1 → 2, etc.).

---

## Run-log entries (append below)

### YYYY-MM-DD — short headline

What happened, what you measured, what you decided, what you'll watch next.
