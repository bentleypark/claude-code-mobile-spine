# Contributing

Thanks for your interest in `claude-code-mobile-spine`. This is a small
Claude Code plugin marketplace; contributions land best when they respect the
repo's discipline below.

## Repo structure (read first)

```
claude-code-mobile-spine/                            ← marketplace repo root
├── README.md, LICENSE, .gitignore, CONTRIBUTING.md
├── .github/{ISSUE_TEMPLATE/, PULL_REQUEST_TEMPLATE.md}
├── .claude-plugin/
│   └── marketplace.json                            ← marketplace catalog
└── plugins/
    └── mobile-spine/                               ← the plugin
        ├── .claude-plugin/
        │   └── plugin.json                         ← plugin manifest (bump version on user-visible changes)
        └── skills/
            └── init/                               ← skill: invoked as /mobile-spine:init
                ├── SKILL.md                        ← skill behavior
                ├── README.md                       ← contributor-facing skill notes
                └── templates/                      ← scaffold source (single source of truth)
                    ├── CLAUDE.md, SETUP.md, README.md, LICENSE, .gitignore
                    ├── .claude/{settings.json, agents/, commands/}
                    └── _context/operations.md, _tasks/.gitkeep, etc.
```

The bundled scaffold (everything that ends up in a user's workspace when they
run `/mobile-spine:init`) lives under
`plugins/mobile-spine/skills/init/templates/`. There is **no root-level
mirror** — the templates directory is the single source of truth.

## Tone and content rules

This repo went through a deliberate pass to remove personal-pilot anecdotes
and "verified" claims. New content should follow the same rules:

- **No personal results** like "verified in week 0", "(confirmed)", or
  verbatim error-message quotes. Frame behaviors as "should …; confirm in
  week 0 (§9, Item N)".
- **No internal identifiers** — repo names, branches, ticket numbers, or
  observation counts ("4 of 5 nodes missed in Q2 pilot"). Anonymize to
  general statements.
- **Stay placeholder-friendly** — the skill substitutes `myorg`, `myapp`,
  `<your name>`, `mcp__figma__*`, and `develop` (whole-word, branch-name uses
  only) per `plugins/mobile-spine/skills/init/SKILL.md` §4-2. New content
  that adds any of these tokens must declare its substitution behavior in
  SKILL.md.

## Agent definitions inside templates

Agent files (`.../templates/.claude/agents/*.md`) are loaded **only at
session start** in the user's scaffolded workspace. If you change one, the
only way to test is to:

1. Re-run the skill into a temp directory.
2. Restart Claude Code in that scaffolded workspace.
3. Re-run the affected flow end-to-end (don't just inspect the new file).

Document the verification you performed in the PR description.

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

If you change anything users see (skill behavior, scaffold contents, install
flow), bump `plugins/mobile-spine/.claude-plugin/plugin.json`'s `version`
field so installed users get the update on `/plugin marketplace update`.

If you rename or restructure (skill name, plugin name, marketplace name),
update both manifests and call out the breaking change in the PR.

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
