#!/usr/bin/env python3
"""Static consistency lint for the mobile-spine plugin.

These are LLM-interpreted markdown instructions, so this lint targets
*structural* consistency, not behavior. It catches the drift class —
invalid manifests, broken relative links, malformed frontmatter,
header-field enumerations out of sync, dangling `§section` references —
deterministically. It does NOT catch logical contradictions or behavioral
correctness; those still need the review agent and real-usage verification.

Run locally:  python3 scripts/lint.py
Exit code 0 = clean, 1 = at least one error.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "mobile-spine"
AGENTS_DIR = PLUGIN / "agents"
COMMANDS_DIR = PLUGIN / "commands"

errors: list[str] = []


def err(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


# --------------------------------------------------------------------------
# 1. JSON manifests parse, and carry the expected shape.
# --------------------------------------------------------------------------

def check_json_manifests() -> None:
    plugin_json = PLUGIN / ".claude-plugin" / "plugin.json"
    marketplace_json = REPO / ".claude-plugin" / "marketplace.json"

    for path in (plugin_json, marketplace_json):
        if not path.exists():
            err(rel(path), "manifest missing")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err(rel(path), f"invalid JSON — {e}")

    if plugin_json.exists():
        try:
            data = json.loads(plugin_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        for key in ("name", "version", "description"):
            if not data.get(key):
                err(rel(plugin_json), f"missing required key `{key}`")
        version = data.get("version", "")
        if version and not re.fullmatch(r"\d+\.\d+\.\d+", version):
            err(rel(plugin_json), f"version `{version}` is not semver (X.Y.Z)")
        # Directory keys must point at real dirs.
        for key in ("skills", "commands"):
            ref = data.get(key)
            if ref and not (PLUGIN / ref).is_dir():
                err(rel(plugin_json), f"`{key}` points to missing dir `{ref}`")


# --------------------------------------------------------------------------
# 2. Agent / command frontmatter is well-formed.
# --------------------------------------------------------------------------

def read_frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip("\n")
    fields: dict[str, str] = {}
    current_key = None
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            current_key = m.group(1)
            fields[current_key] = m.group(2)
        elif current_key is not None and line.startswith(" "):
            fields[current_key] += " " + line.strip()
    return fields


def check_frontmatter() -> None:
    for path in sorted(AGENTS_DIR.glob("*.md")):
        fm = read_frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            err(rel(path), "missing or unterminated YAML frontmatter")
            continue
        for key in ("name", "description", "tools"):
            if key not in fm:
                err(rel(path), f"frontmatter missing `{key}`")
        # Accept inline `[a, b]` or a YAML block list (continuation lines collapse
        # to "- a - b", so a leading "-" marks the block form).
        if "tools" in fm:
            tools_val = fm["tools"].lstrip()
            if tools_val and tools_val[0] not in "[-":
                err(rel(path), "frontmatter `tools` should be a list ([...] or `- item`)")

    for path in sorted(COMMANDS_DIR.glob("*.md")):
        fm = read_frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            err(rel(path), "missing or unterminated YAML frontmatter")
            continue
        if "description" not in fm:
            err(rel(path), "frontmatter missing `description`")


# --------------------------------------------------------------------------
# 3. Markdown relative links resolve (skipping links inside code fences).
# --------------------------------------------------------------------------

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def check_markdown_links() -> None:
    for path in sorted(REPO.rglob("*.md")):
        if "/node_modules/" in str(path):
            continue
        in_fence = False
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for raw_target in LINK_RE.findall(line):
                parts = raw_target.split()  # drop optional "title"
                if not parts:
                    continue
                target = parts[0]
                if re.match(r"^(https?:|mailto:|#)", target):
                    continue
                clean = target.split("#", 1)[0]
                if not clean:
                    continue
                resolved = (path.parent / clean).resolve()
                if not resolved.exists():
                    err(f"{rel(path)}:{lineno}", f"broken relative link `{target}`")


# --------------------------------------------------------------------------
# Heading collection for §-reference resolution.
# --------------------------------------------------------------------------

HEADING_RE = re.compile(r"^#{1,4}\s+(.*?)\s*$")


def normalize_heading(text: str) -> list[str]:
    """A §-ref is `heading name + trailing prose`; cut the heading at the
    first colon / em-dash / paren so the *name* is what we match on."""
    text = re.split(r"\s+—\s+|\s+-\s+|:|\(", text, maxsplit=1)[0]
    return re.findall(r"[a-z0-9]+", text.lower())


def leading_numbers(toks: list[str]) -> list[str]:
    """Leading numeric tokens — `9. Phased…` → [9], `4-2. Process…` → [4, 2].
    Numbered sections (SETUP.md §9, SKILL.md §4-2) are cited by number only,
    so the number is the anchor and the rest is prose."""
    out: list[str] = []
    for t in toks:
        if t.isdigit():
            out.append(t)
        else:
            break
    return out


def collect_headings() -> tuple[list[list[str]], set[tuple[str, ...]]]:
    """Headings across the whole plugin (agents, commands, skills, templates) —
    including those inside ```markdown fences (the `_tasks` output-format
    sections like ## Shared behavior), but NOT `#` comment lines inside `bash`
    / `yaml` / other code fences (those are not headings — e.g. `# 1. Read …`).
    Returns (full-name token lists, set of leading-number anchors)."""
    names: list[list[str]] = []
    numbers: set[tuple[str, ...]] = set()
    for path in sorted(PLUGIN.rglob("*.md")):
        fence_lang: str | None = None  # None = not in a fence
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.lstrip()
            if stripped.startswith("```"):
                lang = stripped[3:].strip().lower()
                fence_lang = None if fence_lang is not None else (lang or "plain")
                continue
            # Inside a non-markdown fence, `#` lines are code comments, not headings.
            if fence_lang is not None and fence_lang not in ("markdown", "md"):
                continue
            if not stripped.startswith("#"):
                continue
            m = HEADING_RE.match(stripped)
            if not m:
                continue
            toks = normalize_heading(m.group(1))
            if toks:
                names.append(toks)
            nums = leading_numbers(toks)
            if nums:
                numbers.add(tuple(nums))
    return names, numbers


SECTION_REF_RE = re.compile(r"§\s*([^\n.,;)]+)")


def is_prefix(prefix: list[str], seq: list[str]) -> bool:
    return len(prefix) <= len(seq) and seq[: len(prefix)] == prefix


def check_section_refs() -> None:
    names, numbers = collect_headings()
    for path in sorted(AGENTS_DIR.glob("*.md")) + sorted(COMMANDS_DIR.glob("*.md")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for raw in SECTION_REF_RE.findall(line):
                stripped = raw.strip()
                # Literal placeholders like "§<section name>".
                if stripped.startswith("<"):
                    continue
                ref_toks = re.findall(r"[a-z0-9]+", raw.lower())
                if not ref_toks:
                    continue
                # Placeholders like "§X" / "§N" (single-letter stand-ins).
                if len(ref_toks[0]) == 1 and ref_toks[0].isalpha():
                    continue
                # Numbered cross-file ref (SETUP.md §9, SKILL.md §4-2): match
                # on the leading number, which is the actual anchor.
                lead = leading_numbers(ref_toks)
                if lead and tuple(lead) in numbers:
                    continue
                # Otherwise: the heading name is a prefix of the ref (ref carries
                # trailing prose), or the ref is a prefix of the heading (ref was
                # truncated, e.g. at a "." in `_tasks/{feature}.md`).
                if any(is_prefix(h, ref_toks) or is_prefix(ref_toks, h) for h in names):
                    continue
                err(f"{rel(path)}:{lineno}", f"dangling section ref `§{stripped}`")


# --------------------------------------------------------------------------
# 5. Header-field enumerations stay in sync with the canonical output block.
# --------------------------------------------------------------------------

def output_format_fields() -> set[str]:
    """Field names from pm-agent.md's `_tasks` output-format fence (the
    block whose first content line is `# {feature}`).

    Positional: keys off the first ```markdown fence starting with `# {feature}`,
    and reads `Field:` lines until the first `##` body section. A field name
    containing a digit/hyphen would be missed by the `[A-Za-z ]+` pattern — none
    exist today; widen the pattern if one is added."""
    text = (AGENTS_DIR / "pm-agent.md").read_text(encoding="utf-8")
    fields: set[str] = set()
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("```") and "markdown" in lines[i]:
            # Is this the {feature} output block?
            block: list[str] = []
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                block.append(lines[j])
                j += 1
            if block and block[0].strip() == "# {feature}":
                for bl in block:
                    m = re.match(r"^([A-Za-z][A-Za-z ]+):\s", bl)
                    if m:
                        fields.add(m.group(1).strip())
                    elif bl.strip().startswith("##"):
                        break  # header block ends at the first body section
                return fields
            i = j
        i += 1
    return fields


def check_header_enumerations() -> None:
    fields = output_format_fields()
    if not fields:
        err("plugins/mobile-spine/agents/pm-agent.md",
            "could not locate the `# {feature}` output-format block")
        return

    # §Checklist update policy — backticked field names must exist in the block.
    pm_text = (AGENTS_DIR / "pm-agent.md").read_text(encoding="utf-8")
    m = re.search(r"## Checklist update policy\n(.*?)(?:\n## |\Z)", pm_text, re.S)
    if m:
        for field in re.findall(r"`([A-Za-z][A-Za-z ]+):`", m.group(1)):
            if field not in fields:
                err("plugins/mobile-spine/agents/pm-agent.md",
                    f"§Checklist update policy names `{field}:` "
                    f"absent from the output-format block")

    # feat.md "standard header (A / B / ... )" list must exist in the block.
    feat_text = (COMMANDS_DIR / "feat.md").read_text(encoding="utf-8")
    m = re.search(r"standard header \(([^)]+)\)", feat_text)
    if m:
        for field in (f.strip() for f in m.group(1).split("/")):
            if field and field not in fields:
                err("plugins/mobile-spine/commands/feat.md",
                    f"standard-header list names `{field}` "
                    f"absent from the output-format block")


def main() -> int:
    check_json_manifests()
    check_frontmatter()
    check_markdown_links()
    check_section_refs()
    check_header_enumerations()

    if errors:
        print(f"✗ lint: {len(errors)} error(s)\n")
        for e in errors:
            print(f"  {e}")
        return 1
    print("✓ lint: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
