# mobile-spine

A scaffolded **Claude Code mobile-spine workspace** — a lightweight meta-repo
that sits next to your `myapp-android`, `myapp-ios`, and `myapp-backend` repos.
It carries no production code, only markdown specs, agent definitions, and run
notes that orchestrate Claude Code across all three.

---

## Next steps

```bash
# 1. Move into this workspace
cd <this-dir>

# 2. (Optional) put it under version control
git init

# 3. Make sure the sibling repos exist:
#      ../myapp-android/
#      ../myapp-ios/
#      ../myapp-backend/
#    Clone them manually, or paste the snippet from SETUP.md §3-2.

# 4. Run claude from inside this workspace
claude

# 5. Walk through SETUP.md §9 → Week 0 verification before relying on the
#    isolation model (settings.json deny / subagent cwd inheritance / Figma MCP).

# 6. Kick off your first feature
> /feat
```

---

## What's in here

| Path | Role |
|---|---|
| `CLAUDE.md` | Routing-only entry point. Auto-loaded on session start. |
| `SETUP.md` | Phased adoption guide (week 0 verification → week 3 full rollout). |
| `.claude/settings.json` | Isolation guard: `deny` should block writes to `../myapp-backend/` (verify in week 0 — see SETUP.md §9 Item 3). |
| `.claude/agents/` | The four subagent definitions (api / pm / android / ios). |
| `.claude/commands/feat.md` | `/feat` slash command — 4-item interview before pm-agent. |
| `_context/api/{domain}.md` | Backend API specs authored by api-agent. |
| `_context/design/{feature}/` | Per-feature Figma assets (when MCP not connected). |
| `_context/operations.md` | Run log: weekly retros, measurements, decisions. |
| `_tasks/{feature}.md` | Per-feature implementation specs (pm-agent author; 1:1 with GitHub issues in both platform repos). |

---

## Daily workflow

```
/feat
  └─ 4-item interview (feature + domain / case auto-detect / spec source / Figma state)
      └─ pm-agent
           ├─ pre-checks (staleness / scope / Figma)
           ├─ GitHub issue dry-run × 2 (android + ios) → user approval → live create
           └─ writes _tasks/{feature}.md
                └─ android-agent ∥ ios-agent (parallel)
                     ├─ phase 1: implement + diff report
                     └─ phase 2 (after explicit approval): commit + Draft PR
```

When the backend changes, refresh the relevant `_context/api/*.md` via
api-agent before pm-agent runs (pm-agent's stale-check enforces this).

---

## Origin

Generated from [bentleypark/claude-code-mobile-spine](https://github.com/bentleypark/claude-code-mobile-spine)
via the `/mobile-spine:init` Claude Code skill. Built on Anthropic's
[Claude Code](https://code.claude.com/) subagent / slash-command primitives.
See the upstream README's *Acknowledgements* for prior art on the broader
meta-repo coordination pattern.

---

## License

[MIT](./LICENSE)
