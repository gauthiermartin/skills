<p align="center">
  <img src="assets/logo.svg" alt="Personal Agent Skills — a fanned deck of skill cards with a terminal prompt" width="360">
</p>

# Personal Agent Skills

Portable [Agent Skills](https://agentskills.io/specification.md), versioned here and installed into coding agents from one canonical source.

## Layout

```text
skills/
  <skill-name>/
    SKILL.md
    scripts/       # optional deterministic helpers
    references/    # optional on-demand documentation
    assets/        # optional templates and resources
```

Skills live directly beneath this directory; do not nest categories because OMP discovers only `skills/<name>/SKILL.md`.

## Authoring contract

- Keep `SKILL.md` portable: valid Agent Skills YAML frontmatter with a `name` matching its directory and a useful `description`.
- Keep tool-neutral instructions in the core skill. Add Claude Code or OMP-specific behavior only when it is required.
- Use relative paths for bundled resources.
- Add scripts only when a deterministic helper is necessary. Python is the default scripting language for this collection; require `uv` only for a skill that needs it.

## Installation strategy

This repository is the source of truth; it does not ship an installer yet.

For local development, link each skill directory into:

| Agent | Target |
| --- | --- |
| OMP | `~/.agents/skills/<skill-name>` |
| Claude Code | `~/.claude/skills/<skill-name>` |

Both locations use the same `SKILL.md` directory layout. Link rather than copy so future edits stay synchronized.

For public multi-agent distribution, use the existing `skills` installer first:

```sh
npx skills@latest add gauthiermartin/skills
```

It avoids maintaining a Node or Python installer. Revisit a small Python installer only if OMP or a future target needs installation behavior that this tool cannot provide.

## Sources and attribution

- Skills adapted from [Matt Pocock's skills](https://github.com/mattpocock/skills) and [Paul Iusztin's AI Research OS workshop](https://github.com/iusztinpaul/ai-research-os-workshop) record their origin in each skill's `metadata:` frontmatter (`origin`, `origin-path`, `origin-revision`, `origin-status`).
- `NOTICE` preserves both upstream MIT notices; `LICENSE` covers this repository's original contributions.

## Deferred

- No Node package, Python package, Claude Code plugin, or tool-specific adapters are included.
