# Contributing

Thanks for your interest in `claude-code-mobile-spine`. This is a small
Claude Code plugin marketplace; contributions land best when they respect the
repo's discipline below.

## Repo structure (read first)

```
claude-code-mobile-spine/                            ← marketplace repo root
├── README.md, LICENSE, .gitignore, CONTRIBUTING.md
├── .github/{ISSUE_TEMPLATE/, PULL_REQUEST_TEMPLATE.md, workflows/lint.yml}
├── scripts/
│   └── lint.py                                     ← static consistency lint (CI + `python3 scripts/lint.py`)
├── .claude-plugin/
│   └── marketplace.json                            ← marketplace catalog
└── plugins/
    └── mobile-spine/                               ← the plugin
        ├── .claude-plugin/
        │   └── plugin.json                         ← plugin manifest (version = install cache key; bumped by a release PR, never in a feature PR)
        ├── agents/                                 ← plugin primitives — globally available subagents
        │   └── {api,pm,android,ios}-agent.md
        ├── commands/                               ← plugin primitives — globally available slash commands
        │   ├── init.md                             ← /mobile-spine:init
        │   └── feat.md                             ← /mobile-spine:feat
        └── skills/
            └── init/                               ← skill: invoked as /mobile-spine:init
                ├── SKILL.md                        ← skill behavior
                ├── README.md                       ← contributor-facing skill notes
                ├── smoke-test.sh                   ← scaffold smoke test (clean-temp-dir init)
                └── templates/                      ← scaffold source (workspace data only)
                    ├── CLAUDE.md, SETUP.md, README.md, LICENSE, .gitignore
                    ├── .claude/{settings.json, commands/feat.md (thin stub)}
                    └── _context/operations.md, _tasks/.gitkeep, etc.
```

Two distinct content classes live in this plugin:

1. **Plugin primitives** (`agents/`, `commands/`) — globally available, served by the Claude Code plugin system. `/plugin marketplace update` propagates changes to every workspace automatically. No per-workspace placeholder substitution; agents read `.claude/mobile-spine.config.yaml` at invocation.
2. **Scaffold templates** (`skills/init/templates/`) — copied to the user's workspace by `/mobile-spine:init`. Workspace-owned data. Once scaffolded, plugin updates do NOT modify these files; the user owns them.

## Tone and content rules

This repo went through a deliberate pass to remove personal-pilot anecdotes
and "verified" claims. New content should follow the same rules:

- **No personal results** like "verified in week 0", "(confirmed)", or
  verbatim error-message quotes. Frame behaviors as "should …; confirm in
  week 0 (§9, Item N)".
- **No internal identifiers** — repo names, branches, ticket numbers, or
  observation counts ("4 of 5 nodes missed in Q2 pilot"). Anonymize to
  general statements.
- **Stay placeholder-friendly (scaffold templates only)** — the init skill substitutes `myorg`, `myapp`, `<your name>` (LICENSE), and `develop` (whole-word, branch-name uses only) per `plugins/mobile-spine/skills/init/SKILL.md` §4-2. The Figma MCP namespace is **not** substituted in v2.0 — it lives in `.claude/mobile-spine.config.yaml` (written by init from Q4) and the plugin's agents read it at invocation. New scaffold-template content that adds any of `myorg`/`myapp`/`<your name>`/`develop` must declare its substitution behavior in SKILL.md.
- **Plugin primitives (`agents/`, `commands/`) — no init-time substitution.** Agents and `commands/feat.md` use literal token forms (`myorg`, `myapp`, `develop`, etc.) in their body and rely on the Configuration section to instruct mental substitution against the workspace's `.claude/mobile-spine.config.yaml`. Don't add init-time substitution rules for these files.

## Plugin primitives (`agents/`, `commands/`)

The four agent files (`plugins/mobile-spine/agents/*.md`) and the plugin-level `commands/feat.md` are loaded by Claude Code's plugin system at session start and available globally. If you change one:

1. Reinstall the plugin from the local checkout (or push to a test marketplace) so the cache picks it up.
2. Restart Claude Code in a scaffolded workspace.
3. Re-run the affected flow end-to-end (don't just inspect the new file).

Document the verification you performed in the PR description.

## Scaffold templates (`skills/init/templates/`)

These end up in the user's workspace at init time. After init they're user-owned — the plugin never modifies them. If you change one, future scaffolds get the new content but existing v2.0 workspaces don't (by design — those files are theirs to customize).

## Skill changes

If you change `plugins/mobile-spine/skills/init/SKILL.md`:
- Run a scaffold smoke test from a clean temp directory using the local
  plugin (e.g. `claude --plugin-dir ./plugins/mobile-spine ...`).
- Confirm the §4-3 sanity grep prints nothing (`myorg` / `myapp` substitution
  leakage).
- If you changed substitution rules (e.g. the `develop` whole-word recipe),
  add or update the example lines in SKILL.md §4-2 — the recipe is
  natural-language and stays correct only if the examples stay aligned with
  reality.

## Plugin manifest changes

### Versioning — bump on release, not in your PR

`plugins/mobile-spine/.claude-plugin/plugin.json`'s `version` is not a changelog
entry. It is the **cache key**. Installed plugins live at
`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, and a version path is
immutable: if the string doesn't change, `/plugin marketplace update` keeps serving
the cached copy no matter how many commits landed. Merged work reaches users only
when the version moves.

That makes the bump a **release** action, not a per-PR one:

- **Do not touch `version` in a feature PR.** Your PR changes behavior; it does not
  decide what ships together. Every user-visible PR would otherwise bump the same
  single line from the same base, so any two concurrent PRs conflict on a field
  neither of them disagrees about — a conflict that carries no information and has to
  be re-resolved whenever the merge order shifts.
- **Bump once, in its own PR, after the set of changes you want to ship together has
  merged.** That PR touches `version` and nothing else.

The consequence is deliberate and worth stating plainly: **`main` can carry merged
work that has not reached users yet.** Everything merged since the last version-bump
commit is queued; the bump publishes it. Before announcing a change, bump. To see
what is queued, diff `main` against the last commit that touched `version`.

### Renames and restructures

If you rename or restructure (skill name, plugin name, marketplace name),
update both manifests and call out the breaking change in the PR.

## Linting (pre-merge consistency)

```
python3 scripts/lint.py
```

A stdlib-only static lint, also run on every PR by `.github/workflows/lint.yml`.
It checks **structural** consistency — valid JSON manifests + semver, well-formed
agent/command frontmatter, resolvable markdown relative links, no dangling
`§section` references, and header-field enumerations (the `_tasks` output-format
block ↔ §Checklist update policy ↔ feat.md "standard header") staying in sync.

It deliberately does **not** check behavior or logical consistency — these are
LLM-interpreted instructions, so a contradiction like "exclude case D but still
offer it" is invisible to a static pass. That layer stays with the review agent
and the `SETUP.md §9` real-usage verification. A clean lint is necessary, not
sufficient.

## PR scope

One concern per PR. Don't bundle a policy change with a tone fix and a new
skill capability — they need different review attention. Cross-cutting
refactors are fine if every file is touched for the same reason.

## Commit messages

Short imperative subjects, no body unless something genuinely needs
explaining. The android/ios agent definitions (inside the scaffold) enforce
the same style for platform repos; this repo follows it for consistency.

```
docs(setup): reframe week-0 statements as verification, not promises
fix(skill): tighten develop substitution to whole-word matches
feat(pm-agent): add md design-spec input branch in pre-check 3
```

## License

By contributing you agree your contributions are licensed under the MIT
License (see `LICENSE`).
