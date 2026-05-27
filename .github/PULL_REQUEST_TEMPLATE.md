## Summary

<!-- 1-3 sentences. What changed and why. Link the issue if applicable. -->

## Plugin / scaffold checklist

- [ ] Scaffold edits live under `plugins/mobile-spine/skills/init/templates/` (no root mirror)
- [ ] If user-visible behavior changed, `plugins/mobile-spine/.claude-plugin/plugin.json` `version` bumped
- [ ] If `SKILL.md` substitution rules changed, examples in §4-2 stay aligned with reality
- [ ] If a `tools:` field changed, you reloaded (`/reload-plugins`, or restarted Claude Code) and confirmed the agent still loads in a scaffolded workspace
- [ ] If the plugin / skill / marketplace was renamed, both manifests updated and the breaking change is called out

## Tone checklist

- [ ] No "verified in week 0" / "(confirmed)" / verbatim error messages added — behaviors are framed as "should …; confirm in week 0 (§9, Item N)"
- [ ] No internal repo names, ticket numbers, or specific observation counts in new content

## Week 0 impact

- [ ] No change to the verification matrix (`SETUP.md §9`)
- [ ] Verification matrix changed — `SETUP.md §9` updated accordingly

## Test plan

<!-- How a reviewer can validate this end-to-end. For agent or Skill changes,
     state the steps you actually ran. "Inspected the file" is not enough
     because agent definitions only load at session start. -->

## Anything else reviewers should know

<!-- Edge cases, follow-ups deferred to a future PR, known limitations. -->
