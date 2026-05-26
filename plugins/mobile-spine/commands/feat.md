---
description: Kick off _tasks creation for a new feature (4-item interview before invoking pm-agent; an epic-sized requirement routes to phased decomposition instead)
argument-hint: [optional short note — e.g. "push notification settings - alarm domain"]
allowed-tools: [Read, AskUserQuestion, Agent]
---

# /mobile-spine:feat — New feature kickoff interview

Run a 4-item interview, then invoke pm-agent automatically. The main session asks the user the 4 questions in order, collects answers, and constructs the pm-agent prompt. (For a requirement too large for one PR cycle, an early epic check — Item 1b — routes instead to pm-agent's phased decomposition, skipping Items 2–4.)

The workspace's `/feat` is a thin stub that delegates here — both invocations end up running this same command.

## Workspace prerequisite

This command operates on a scaffolded mobile-spine workspace. Before running the interview, verify `.claude/mobile-spine.config.yaml` exists in the current directory — if not, abort:

"[/feat] No `.claude/mobile-spine.config.yaml` found in the current working directory. This doesn't look like a mobile-spine workspace. Run `/mobile-spine:init` for a fresh setup, or follow SETUP.md §0 to migrate from v1.x."

(pm-agent reads the same config at invocation; the check here is a fast-fail so the user doesn't sit through the 4-item interview before discovering the workspace isn't set up.)

**User argument**: $ARGUMENTS

## Interview procedure

For each item, do not guess on a missing answer — ask explicitly. Do not advance
to the next item before getting an answer.

### Item 1: feature name + domain key

Try to extract feature/domain from `$ARGUMENTS`. If unclear, ask in plain text:

> [/feat] What is the feature name and the domain key?
> Examples: "Email verification - auth" / "Phone verification - auth" / "Push settings - alarm"

### Item 1b: epic check

Before the case interview, assess whether the requirement is too large for a single PR cycle — an **epic** (see pm-agent.md §Epic tasks). Signals: the feature note describes multiple distinct screens *and* multiple new endpoints, names several separable deliverables, or has explicit internal sequencing ("first the data model, then the list UI, then composition").

- If it does **not** look epic-sized → continue to Item 2 (the normal single-feature flow).
- If it **does** → confirm via `AskUserQuestion`:

  ```
  Question: "This looks larger than one PR cycle. Handle it as an epic? pm-agent proposes a phased breakdown; each phase is then authored and shipped on its own cycle."
  Header: "Epic?"
  Options:
  - "Yes — decompose into phases" — invoke pm-agent in decomposition mode
  - "No — single feature" — continue the normal 4-item interview
  ```

  If **Yes** → **skip Items 2–4** (case classification, spec source, and design source are decided per phase when that phase is authored, not upfront) and invoke pm-agent using the §"pm-agent prompt construction — epic decomposition" template below. If **No** → continue to Item 2.

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
> One of: backend PR URL / OpenAPI file path / external doc URL / **"none — derive from design"**.

Case A: spec is `_context/api/{domain}.md` (skip).
Case D: pm-agent will defer (skip).

> **Design-only (no API spec)**: if the user answers "none — derive from design"
> (case C with a design source but no spec doc — the "no requirements doc" path),
> pm-agent runs design-driven analysis: it inventories the design source as Phase 0
> and derives UI-implied endpoints into `## Open decisions` flagged for backend
> confirmation, rather than inventing a finalized spec. Pass this through to pm-agent
> in the Context block (see the prompt template). Requires a real design source in
> Item 4 — "no API spec **and** no design" leaves nothing to analyze, so steer the
> user to case D instead.

### Item 4: design source

Ask via `AskUserQuestion`:

```
Question: "What is the design source for UI sections?"
Header: "Design source"
Options:
- "Figma — desktop multi-select" — pm-agent uses selection-based MCP (recommended)
- "Figma — provide nodeIds" — supply nodeId list in the next ping
- "HTML mockup" — supply a path to .html / .css files in the next ping
- "No design" — UI sections will be deferred per pre-check policy
```

- If "Figma — provide nodeIds" is chosen, collect the comma-separated list ("1:1075, 1:1208, ...").
- If "HTML mockup" is chosen, collect the path. Recommend `_context/design/{feature}/`; any non-platform-repo path is accepted (pm-agent reads it directly — no MCP needed). It must **not** live inside `../myapp-android/` / `../myapp-ios/` / `../myapp-backend/` — ask the user to copy it into `_context/design/{feature}/` if it does.

## pm-agent prompt construction

Plug the 4 answers into the template below and invoke pm-agent (Agent tool, subagent_type: pm-agent):

```
## Target
- Feature: {item 1}
- Domain: {extracted from item 1}
- Pre-classified: case {item 2}

## Context
{case B/C: spec source — item 3 (URL / path / doc), OR "none — derive from design" (design-only path: derive UI-implied endpoints into ## Open decisions, do not fabricate a finalized spec — see pm-agent.md §Step 4 "Design-driven requirements")}
{case A: spec — `_context/api/{domain}.md` (Updated: {time})}
{case D: backend not built — pm-agent prints the deferred message and stops}
{Design source — item 4: figma multi-select / figma nodeIds {list} / html {path} / none}

## Procedure
Follow pm-agent.md execution order (steps 1~10):
- Pre-checks 1·2·3 → Phase 0 design-source inventory (figma multi-node OR html files) → extraction / gap / conflict identification → single ping if needed → write _tasks → issue dry-run

## Policy reminders
- Follow §_tasks authoring discipline in pm-agent.md: `_tasks` is a spec, not a log — length budget ~150 lines, state each fact once (reference by §), platform-neutral by default with Android/iOS-specific notes confined to `## Android` / `## iOS` (never interleaved), and **no platform-repo file paths / line numbers / class names** anywhere in `_tasks`. On a re-run, edit sections in place and bump `Updated:` — never append `📌 update` / `갱신` blocks.
- The `## Candidate assets` section in _tasks lists ~5 category keywords only (no codebase grep, no code locations). Platform agents' inventory results stay in their PR body / issue — they don't flow back into `_tasks`.
- For case A, after the dry-run, confirm whether the feature is already implemented on both platforms (skip issue creation + add Status header on yes)
- Use the standard header (Case / Status / Android Issue / iOS Issue / Created / Updated / API Spec / Design source)
- Design source `none` or incomplete assets: do not invent UI sections — leave a single placeholder line. `html`/`figma`: fill UI sections from the inventory.

## Outputs
- _tasks/{feature}.md saved
- Case classification + pre-check results
- Design-source inventory summary (figma multi-select or html files)
- Identified gaps / conflicts
- GitHub issue dry-run bodies × 2 (android / ios) — not yet created

For case B/C, mark the new-endpoint spec source ({item 3}) on the API Spec line of _tasks (temporary annotation). For case C, add the warning banner; for case B, mark the new endpoints distinctly. For the design-only path, the API Spec line reads `temporary — derived from design`.
```

## pm-agent prompt construction — epic decomposition

When the epic check (Item 1b) routed to decomposition, invoke pm-agent (Agent tool, subagent_type: pm-agent) with this template instead of the 4-item one above:

```
## Target
- Epic: {item 1 — feature name}
- Domain hint: {extracted from item 1}

## Procedure
This is an epic. Run §Epic decomposition → "Decomposition (first invocation)" in pm-agent.md:
propose an ordered phase breakdown for the user's approval, then on approval
create _tasks/{epic}/ + 00-overview.md and author phase 1 in full mode.
Do NOT author phases 2+ — those are authored just-in-time on later
next-phase invocations.

## Notes
- Case classification, spec source, and design source are decided per phase
  when that phase is authored — not upfront. Phase 1's full-mode run does
  its own Step 1–9 pre-checks.
- Follow §_tasks authoring discipline for every phase file and 00-overview.md.
```

## Pre-invocation note

Just before invoking pm-agent, print a one-liner:

```
[/feat] Invoking pm-agent — case {X}, domain {domain}, design source {figma multi-select | figma nodeIds | html {path} | none}
```

For the epic-decomposition path, instead print:

```
[/feat] Invoking pm-agent — epic decomposition for {epic}
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

## Example session

A case-C run (new domain), Figma connected. (`<` lines are your input; the prompts below are paraphrased for brevity — see the procedure above for exact wording.)

```
> /feat push notification settings - alarm domain

[/feat] What is the feature name and the domain key?
  Examples: "Email verification - auth" / "Push settings - alarm"
< Push notification settings — alarm

[/feat] Auto-detected: case C
  _context/api/alarm.md does not exist → new domain. Correct?
  [ Correct / Specify a different case ]
< Correct

[/feat] Where is the spec source for the new endpoint(s) / domain?
  One of: backend PR URL / OpenAPI file path / external doc URL.
< https://github.com/myorg/myapp-backend/pull/NNN

[/feat] What is the design source for UI sections?
  [ Figma — desktop multi-select / Figma — provide nodeIds / HTML mockup / No design ]
< Figma — desktop multi-select

[/feat] Invoking pm-agent — case C, domain alarm, design source figma multi-select
```

pm-agent then:
- Runs case-C pre-checks: no `_context/api/alarm.md` → uses the supplied PR as a temporary spec source, adds the case-C warning banner to `_tasks`
- Phase 0: inventories the multi-selected Figma nodes
- Writes `_tasks/push-notification-settings.md` with the standard header (Case: C / API Spec: temporary — `https://github.com/myorg/myapp-backend/pull/NNN`, replace with `_context/api/alarm.md` after backend merge / Design source: figma — connected) and a `## Candidate assets` keyword list
- Prints two GitHub issue dry-run bodies (android / ios) — not yet created

You approve issue creation, then hand `_tasks/push-notification-settings.md` to android-agent and ios-agent: each runs phase 1 (inventory via the `## Candidate assets` keywords → implement → diff report), then phase 2 after your explicit approval (commit + Draft PR).

### Variant — HTML mockup, no API spec yet (design-only)

Same flow, two answers differ — the "no requirements doc" path:

```
[/feat] Where is the spec source for the new endpoint(s) / domain?
  One of: backend PR URL / OpenAPI file path / external doc URL / "none — derive from design".
< none — derive from design

[/feat] What is the design source for UI sections?
  [ Figma — desktop multi-select / Figma — provide nodeIds / HTML mockup / No design ]
< HTML mockup
  → path? < _context/design/push-notification-settings/

[/feat] Invoking pm-agent — case C, domain alarm, design source html _context/design/push-notification-settings/
```

pm-agent then inventories the HTML/CSS files as Phase 0 (each file ≈ a screen, `:root` custom properties ≈ tokens), derives the UI-implied endpoints into `## Open decisions` flagged `derived from design — needs backend confirmation`, and writes the header with `API Spec: temporary — derived from design` / `Design source: html — _context/design/push-notification-settings/`. After a backend spec is agreed, re-invoke to replace the derived endpoints.
