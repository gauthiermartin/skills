---
name: anvil-develop-skills
description: Develop or adapt a local skill through evidence, focused design, proportional evaluation, and complete cutover.
disable-model-invocation: true
---

# Anvil Develop Skills

Develop local skills from real evidence, not generic advice. Keep every skill focused, concise, and predictable; evaluate behavior before adding ceremony.

## 1. Capture the work

Extract the reusable workflow from the current conversation, real task, project artifacts, correction history, execution traces, or upstream source. Establish:

- The outcome the skill must enable.
- The trigger or explicit invocation that reaches it.
- Input, output, dependencies, edge cases, and failure consequences.
- One or more realistic prompts that expose the behavior worth preserving.

Apply the agent-lack test to every candidate instruction: keep it only when the agent would otherwise get it wrong, miss a local convention, or take a materially worse path.

Completion criterion: the skill owns one coherent unit of work, with real evidence for its instructions and a concrete success signal.

## 2. Choose the name and invocation

Name the skill for the collection and action it owns:

- `foundry-*` — imported shared engineering practices.
- `anvil-*` — local skill-development workflows.
- `obsidian-*`, `github-*`, `gmail-*` — direct operations against those platforms.
- Otherwise, use an action-first name when no platform owns the operation.

Use lowercase kebab case. Keep the directory and frontmatter `name` identical. Preserve an existing name unless a deliberate migration is requested; a migration updates every caller and removes the old path.

Make the skill model-invoked only when the agent or another model-invoked skill must discover it autonomously. Otherwise set `disable-model-invocation: true` and keep the description a human-facing summary.

For a model-invoked skill, write a third-person description that states the outcome and distinct trigger branches. Calibrate it with realistic should-trigger, should-not-trigger, and near-miss prompts.

Completion criterion: the name, directory, invocation mode, and description make the skill's reach unambiguous.

## 3. Author the smallest working skill

Start with `SKILL.md`; add `scripts/`, `references/`, or `assets/` only when their file role requires them.

- Use steps for ordered work and reference for facts, definitions, and conditional detail.
- Give each consequential step a checkable completion criterion.
- Keep universally needed material inline; disclose branch-specific reference behind an explicit pointer that says when to read it.
- Use high freedom for contextual judgment, a default plus escape hatch when one approach usually wins, and exact commands or scripts for fragile work.
- Add a gotcha for each non-obvious correction, a template for constrained output, a checklist for dependent steps, and plan → validate → execute for destructive or batch work.
- Bundle a script only after repeated work proves deterministic automation is more reliable than re-explaining it. Scripts must be non-interactive, provide `--help`, fail clearly, and validate intermediate outputs when errors could propagate.
- Prune no-ops, duplication, sediment, and irrelevant detail. Prefer a reusable procedure over a one-off answer.

For externally derived skills, record the source without changing its source path:

```yaml
metadata:
  origin: owner/repository
  origin-path: path/in/upstream/SKILL.md
  origin-revision: <commit SHA or unknown>
  origin-status: verbatim # or adapted
```

Audit external scripts, network access, file access, and tool use. A skill must not do more than its stated purpose implies.

Completion criterion: the directory contains only live instructions and resources, every referenced file exists, and the skill explains a reusable method rather than one instance's answer.

## 4. Evaluate proportionally

For observable contracts, begin with two or three realistic prompts, including one boundary or near-miss. Compare the skill against no skill for a new workflow, or the prior skill snapshot for a revision.

Use objective assertions when possible: file exists, data parses, required sections appear, command exits successfully, or a count/invariant holds. Use human review for style, usability, and judgment. Read execution traces when outputs fail or the agent wastes work.

Do not create an evaluation scaffold for subjective or trivial changes. When repeated evaluations are needed, retain prompts, evidence, token/time cost, and feedback so later revisions can be compared honestly.

Completion criterion: evaluation demonstrates that the skill improves the intended behavior, or the skill is simplified until its value is clear.

## 5. Cut over cleanly

For a new skill, verify its frontmatter and exercise its core workflow once. For an update, preserve source provenance and verify the changed behavior. For a rename, migrate every invocation, relative path, hard-coded script path, and metadata name before removing the old directory.

Report the final name, invocation mode, provenance when applicable, and the evidence from the exercised path.

Completion criterion: every current caller reaches the new skill, no stale path remains, and the verification covers the behavior that changed.
