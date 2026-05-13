---
description: Kick off _tasks creation for a new feature (4-item interview before invoking pm-agent)
argument-hint: [optional short note — e.g. "push notification settings - alarm domain"]
allowed-tools: [Read, AskUserQuestion, Agent]
---

# /feat — New feature kickoff interview

Run a 4-item interview, then invoke pm-agent automatically. The main session
asks the user the 4 questions in order, collects answers, and constructs the
pm-agent prompt.

**User argument**: $ARGUMENTS

## Interview procedure

For each item, do not guess on a missing answer — ask explicitly. Do not advance
to the next item before getting an answer.

### Item 1: feature name + domain key

Try to extract feature/domain from `$ARGUMENTS`. If unclear, ask in plain text:

> [/feat] What is the feature name and the domain key?
> Examples: "Email verification - auth" / "Phone verification - auth" / "Push settings - alarm"

### Item 2: case auto-detection + user confirmation

Once the domain key is set, the main session auto-detects (before invoking pm-agent):

1. Check whether `_context/api/{domain}.md` exists (absent → **case C candidate**).
2. If present, grep the user-listed endpoints:
   - All listed → **case A candidate**
   - Some / none listed → **case B candidate**
3. If the user explicitly stated "backend not built" → **case D candidate**.

Report the auto-detection result and confirm via `AskUserQuestion`:

```
[/feat] Auto-detected: case {X}
- case A: "Existing domain + existing endpoint. Correct?"
- case B: "Existing domain but {endpoints} are not in _context (new endpoints). Correct?"
- case C: "_context/api/{domain}.md does not exist → new domain. Correct?"
- case D: "Backend not built → _tasks creation deferred. Correct?"

Options: ["Correct", "Specify a different case"]
```

If "Specify a different case" is chosen, ask the user which of A/B/C/D applies.

### Item 3: spec source (case B/C only — skip for A/D)

For case B/C only:

> [/feat] Where is the spec source for the new endpoint(s) / domain?
> One of: backend PR URL / OpenAPI file path / external doc URL.

Case A: spec is `_context/api/{domain}.md` (skip).
Case D: pm-agent will defer (skip).

### Item 4: Figma node state

Ask via `AskUserQuestion`:

```
Question: "What is the Figma input state?"
Header: "Figma state"
Options:
- "Desktop multi-select ready" — pm-agent uses selection-based MCP (recommended)
- "Provide nodeIds" — supply nodeId list in the next ping
- "No Figma" — UI sections will be deferred per pre-check policy
```

If "Provide nodeIds" is chosen, collect the comma-separated list ("1:1075, 1:1208, ...").

## pm-agent prompt construction

Plug the 4 answers into the template below and invoke pm-agent (Agent tool, subagent_type: pm-agent):

```
## Target
- Feature: {item 1}
- Domain: {extracted from item 1}
- Pre-classified: case {item 2}

## Context
{case B/C: spec source — item 3 (URL / path / doc)}
{case A: spec — `_context/api/{domain}.md` (Updated: {time})}
{case D: backend not built — pm-agent prints the deferred message and stops}
{Figma state — item 4: multi-select / nodeIds / not connected}

## Procedure
Follow pm-agent.md execution order (steps 1~10):
- Pre-checks 1·2·3 → Phase 0 multi-select inventory → extraction / gap / conflict identification → single ping if needed → write _tasks → issue dry-run

## Policy reminders
- Follow §_tasks authoring discipline in pm-agent.md: `_tasks` is a spec, not a log — length budget ~150 lines, state each fact once (reference by §), platform-neutral by default with Android/iOS-specific notes confined to `## Android` / `## iOS` (never interleaved), and **no platform-repo file paths / line numbers / class names** anywhere in `_tasks`. On a re-run, edit sections in place and bump `Updated:` — never append `📌 update` / `갱신` blocks.
- The `## Candidate assets` section in _tasks lists ~5 category keywords only (no codebase grep, no code locations). Platform agents' inventory results stay in their PR body / issue — they don't flow back into `_tasks`.
- For case A, after the dry-run, confirm whether the feature is already implemented on both platforms (skip issue creation + add Status header on yes)
- Use the standard header (Case / Status / Android Issue / iOS Issue / Created / Updated / API Spec / Figma)
- When Figma is not connected or assets look incomplete: do not invent — leave a single placeholder line

## Outputs
- _tasks/{feature}.md saved
- Case classification + pre-check results
- Figma inventory summary (when multi-select)
- Identified gaps / conflicts
- GitHub issue dry-run bodies × 2 (android / ios) — not yet created

For case B/C, mark the new-endpoint spec source ({item 3}) on the API Spec line of _tasks (temporary annotation). For case C, add the warning banner; for case B, mark the new endpoints distinctly.
```

## Pre-invocation note

Just before invoking pm-agent, print a one-liner:

```
[/feat] Invoking pm-agent — case {X}, domain {domain}, Figma {state}
```

## Interview abort conditions

- User explicitly says "cancel" / "stop" / "abort" → end the interview, summarize the answers collected so far, no pm-agent call.
- Item 1 missing → cannot proceed, re-ask.
- Case D confirmed → before invoking pm-agent, ask once more: "Case D will defer _tasks creation. Still invoke?" (yes → invoke / no → end).

## After invocation

Report all of the following back to the user in one shot:
- _tasks file path
- Case classification / pre-check results
- Identified gaps / conflicts (if any)
- Issue dry-run bodies × 2 (android / ios)
- Next action (create issues yes/no; for case A, the implementation-status answer applied)
