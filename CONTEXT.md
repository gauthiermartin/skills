# Personal Agent Skills

The lifecycle of portable agent skills: authored in one canonical repository, distributed to the machines' agent tooling, and captured back when created locally.

## Language

**Canonical Source**:
This repository — the versioned home of every skill. A skill not present here is not yet part of the collection.
_Avoid_: upstream, master copy

**Installed Set**:
The contents of `~/.agents/skills` — the skills actually available to agents on a machine, as independent copies of Canonical Source skills.
_Avoid_: local skills, live skills

**Agent Surface**:
A location an agent reads skills from (`~/.claude/skills`, future agents). Surfaces expose the Installed Set; they hold no content of their own.
_Avoid_: target, mirror

**Install**:
Copying a skill from the Canonical Source into the Installed Set.
_Avoid_: link, deploy

**Adopt**:
Capturing a skill that exists only in the Installed Set (or on a Surface) into the Canonical Source, making it part of the collection.
_Avoid_: import (reserved for bringing in skills from third-party repos), upstream

**Drift**:
Content divergence between a skill's Canonical Source copy and its Installed Set copy. Expected between Syncs; never silently resolved.

**Sync**:
The three-way reconciliation of Canonical Source and Installed Set against their last-synced state. A change on one side flows automatically; changes on both sides are a conflict — Sync shows the diff and the user decides. Sync never merges content on its own.
_Avoid_: refresh, update
