# Copies plus three-way sync over symlinks

The Installed Set (`~/.agents/skills`) was originally per-skill symlinks into this repo, with `~/.claude/skills` symlinking to it in turn. Renames in the repo silently dangled the second hop (7 dead links found in an audit), and the chain gave no way to select skills per machine. We decided the Installed Set holds independent **copies**, reconciled by a **three-way sync** (last-synced hash manifest; one-sided changes flow automatically, two-sided changes surface a diff for the user to resolve), with **selective install** per machine. Agent surfaces like `~/.claude/skills` hold no content — a single directory-level symlink to the Installed Set.

## Considered Options

- **Symlinks everywhere** (status quo): zero drift by construction, but rename breakage is silent, per-machine selection is awkward, and the failure lives on whichever machine you're not looking at.
- **Copies + sync** (chosen): drift is possible but explicit — the manifest makes divergence detectable and reconciliation a deliberate act.
- **Existing sync tool (unison/rsync)**: battle-tested, but skill-level manifest semantics (never-installed vs deliberately-removed vs repo-deleted) don't map onto file-level profiles.

## Consequences

- Sync must distinguish three per-skill states: installed-at-hash, never-installed, deliberately-removed. A skill deleted in the repo but installed locally is a conflict, never a silent removal.
- One tool owns the manifest: a repo Python script (TTY checkbox TUI for humans, flags + `--json` for agents) wrapped by a thin skill.
- Skills existing only on an agent surface are adopted into the repo or deleted; the surface symlink leaves them nowhere else to live.
