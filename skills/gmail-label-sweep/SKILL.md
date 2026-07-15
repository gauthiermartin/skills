---
name: gmail-label-sweep
description: Sweep old Gmail newsletter labels. This skill should be used when the user asks to "sweep Gmail labels", "clean up AWS News", "clean up Newsletters AI", "archive old newsletter mail", or remove AWS/AI newsletter labels from Gmail messages older than today.
metadata:
  origin: gauthiermartin/skills
  origin-revision: 70b53e358c6781b332391c7d5046fb2f75fdd6b2
  origin-status: verbatim
version: 0.1.0
---

# Gmail Label Sweep

Sweep processed newsletter mail out of the active Gmail labels. For every target message older than today, remove the target newsletter label or labels and archive the message. Never delete mail.

## Defaults

- **Target labels:** `AWS News`, `Newsletters AI`
- **Alias:** accept `Newsletter AI` only when that exact Gmail label exists and `Newsletters AI` does not.
- **Cutoff:** local midnight at the start of today. "Older than today" means received before that cutoff, not older than 24 hours.
- **Action:** remove any target labels present, then archive by removing Gmail's `INBOX` label.
- **Do not touch:** Trash, Spam, non-target labels, stars, read/unread state, importance, or message contents.

## Sweep steps

### 1. Preflight write access

Detect `gmail_access` in one pass — don't guess at a Gmail mechanism:

- `gmail_mcp`: a Gmail/mail MCP or tool is available. Record `gmail_capabilities = read` or `read_write` from its operations.
- `browser_gmail`: the browser opens `https://mail.google.com/` and lands in an authenticated inbox. Treat as `read_write` only when the Gmail UI exposes the exact result set and bulk action controls this sweep needs.
- `mail_export`: user-supplied local `.mbox`/`.eml` files. Always `read`-only — never sufficient for a sweep.
- `missing`: none of the above.

This sweep requires `gmail_write`: a Gmail/mail MCP or tool that can modify labels/archive, or an authenticated Gmail browser where the result set and bulk action state are visible. Mail exports never satisfy it — stop and ask for a write-capable path. Never ask for a password, never invent Gmail CLI commands, and don't rely on Gmail search syntax until the access path is confirmed.

Prefer Gmail MCP/API access with message modify support. Use browser Gmail only when the visible result set and bulk action controls can be verified before applying changes.

Resolve target labels to label IDs — names with spaces are brittle in Gmail search syntax. If one target label is missing, warn and continue with the existing target label. If both target labels are missing, stop.

Use the local timezone for the cutoff: "older than today" means `received_at` before local midnight at the start of today, not older than 24 hours. For browser-only searches, prefer `before:YYYY/MM/DD` with today's local date once authentication is confirmed.

**Gate:** write-capable Gmail access exists, at least one target label ID is resolved, and the cutoff is set to today's local midnight.

### 2. Build the dry-run target set

Search for messages that have any target label and `received_at < cutoff`. Use label IDs when available. Exclude Trash and Spam. Deduplicate by Gmail message ID so a message carrying both target labels is modified once.

For each target message, capture:

- message ID
- received date
- subject
- sender
- target labels currently present
- whether `INBOX` is present

**Gate:** the target set contains every older-than-today message carrying either target label exactly once, with counts by label and overlap.

### 3. Preview and confirm

Show a dry-run preview before mutating Gmail:

- cutoff date/time
- resolved label names and IDs
- total unique messages
- counts for `AWS News`, `Newsletters AI`, and messages carrying both
- oldest and newest target dates
- up to 10 sample subjects/senders

Ask for explicit confirmation to apply the sweep. If the user declines or does not answer, stop without changing Gmail.

**Gate:** the user explicitly confirms the dry-run target set.

### 4. Apply the sweep idempotently

For each target message, remove only the target label IDs that are present plus `INBOX` when present. Use one modify operation per message or one safe batch modify operation if the Gmail access path supports it.

With browser Gmail, apply only when Gmail offers "select all conversations in this search" for the exact dry-run query and the visible result count matches the preview. If the UI cannot prove the same target set, stop and ask for MCP/API access instead.

**Gate:** every target message has been submitted for label removal/archive without deleting mail or changing non-target labels.

### 5. Verify the sweep

Re-query the target labels for `received_at < cutoff`. The expected count is zero for every processed target label. Spot-check modified message IDs when the access path supports ID lookup: target labels absent, `INBOX` absent, other labels unchanged.

If verification finds remaining target messages, rerun the dry-run for only those remaining messages and ask before applying another pass.

**Gate:** no older-than-today messages remain under processed target labels, or every remaining item is reported with the reason it could not be changed.

### 6. Report tersely

Return only the target labels processed, cutoff, number archived, number with labels removed, number skipped, and any verification limitation. Do not paste email bodies.
