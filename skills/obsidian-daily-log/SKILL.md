---
name: obsidian-daily-log
description: Daily log for Obsidian. Use when the user asks to create today's daily log, create an Obsidian journal note under Journal/YYYY/MMMM/YYYY-MM-DD, or import Google/Microsoft calendar tasks and meetings into Today's Events and Tomorrow.
metadata:
  origin: gauthiermartin/skills
  origin-revision: 70b53e358c6781b332391c7d5046fb2f75fdd6b2
  origin-status: verbatim
---

# Obsidian Daily Log

Create one dated Obsidian log note for a personal or work vault. Keep the note boring: the folder path is predictable, the template has no sample entries, and calendar items land only in the two event sections.

## Steps

### 1. Resolve the vault profile

Select exactly one profile before writing:

| Profile | Calendar source | Calendar days | Default journal root |
| --- | --- | --- | --- |
| `personal` | Google Calendar | 7 days/week | `02-Areas/Journal` when that folder exists, otherwise `Journal` |
| `work` | Microsoft calendar | Monday-Friday only | `Journal` unless the vault already uses another `Journal` root |

Infer the profile from an explicit user phrase, vault path, current working directory, or existing journal folder. Ask one question whenever either the profile or vault root remains ambiguous after checking those signals.

Completion criterion: exactly one vault root, profile, target date, and journal root are known.

### 2. Compute the log path

Default the target date to today in the user's local timezone unless the user names another date. Build the note path as:

```text
<journal-root>/<YYYY>/<MMMM>/<YYYY-MM-DD>.md
```

For the exocortex vault, preserve the observed convention:

```text
02-Areas/Journal/<YYYY>/<MMMM>/<YYYY-MM-DD>.md
```

Create missing year/month folders when writing the note. Keep the month as the full English month name, matching `July` in the existing log.

Completion criterion: the final path points at one dated Markdown file and its parent folder can be created.

### 3. Collect calendar items

Read `references/calendar-connectors.md` when calendar import is requested or implied by daily log creation.

Build four lists from the connector:

- `today_events`: meetings/events on the target date for `Today's Events`.
- `today_tasks`: dated tasks due on the target date for `Plan`.
- `tomorrow_events`: meetings/events on the next calendar day for personal, or next working day for work.
- `tomorrow_tasks`: dated tasks due on that same next-day date.

For work, the next-day date is Monday-Friday only, so Friday points to Monday.

Sort meetings/events by start time. Format timed meetings/events as:

```markdown
- HH:MM–HH:MM  Title
```

Format all-day meetings/events as:

```markdown
- All day  Title
```

Format dated tasks as:

```markdown
- [ ] Title
```

Use `- [ ] HH:MM  Title` when the task has a due time.

Do not invent items. If the needed connector is unavailable, mark the calendar result as skipped and retain the existing managed blocks unchanged. Only a newly created note gets empty managed blocks.

Completion criterion: all four calendar item lists are populated from a real connector, or calendar import is explicitly marked skipped without changing existing calendar content.

### 4. Render the note

Use `assets/daily-log-template.md` as the base template. Replace `{{today_events}}`, `{{today_tasks}}`, `{{tomorrow_events}}`, and `{{tomorrow_tasks}}` with their rendered lists. Replace each token with an empty string when that list is empty.

Leave `Notes`, `Manual Tasks`, and `Review` empty in a new note except for the two review prompts:

```markdown
- Learned:
- Carry forward:
```

If the note already exists, read it before writing. Refresh calendar items only when calendar import succeeded and every target has matching `<!-- obsidian-daily-log:<block>:start -->` and `<!-- obsidian-daily-log:<block>:end -->` markers; replace only content between each marker pair. Treat `today-tasks` as the `### Calendar Tasks` subsection only. Never alter the `### Manual Tasks` subsection or other text outside the managed blocks; if a target block is unmarked, leave it unchanged and report that it was not refreshed.

Completion criterion: rendered Markdown contains every required heading once, no sample entries or placeholder tokens, no duplicated calendar lines, and every managed block has a matching marker pair.

### 5. Write and report

Write the file at the computed path. Prefer direct file tools when the vault path is known; use the Obsidian CLI only when vault resolution or Obsidian-specific behavior requires it. Before writing into an unfamiliar vault, read its local `CLAUDE.md` if present.

Final response format:

```text
Created <path>
Calendar: <imported|skipped: reason>
```

Completion criterion: the file exists at the target path and the final response states the calendar result without claiming unavailable imports.

## References

- `assets/daily-log-template.md` — blank daily log template copied into new notes.
- `references/calendar-connectors.md` — Google/Microsoft connector contract and workday rules.
