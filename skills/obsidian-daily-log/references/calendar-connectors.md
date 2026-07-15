# Calendar Connectors

Use this reference only while collecting calendar items for `obsidian-daily-log`.

## Calendar item contract

Normalize meetings, events, and dated tasks to this shape before rendering:

```json
{
  "title": "Event title",
  "start": "2026-07-10T09:00:00-04:00",
  "end": "2026-07-10T10:00:00-04:00",
  "all_day": false,
  "calendar": "Calendar name",
  "source": "google|microsoft",
  "kind": "event|task",
  "id": "optional stable id"
}
```

Drop cancelled events, declined invitations, and completed tasks. De-duplicate by stable `id` when present, otherwise by `source + title + start + end`. Keep private-event titles exactly as the connector returns them; do not expand or guess details.

For dated tasks with no duration, set `kind` to `task`, use the due date/time as `start`, leave `end` empty if the connector has no end time, and add the item to `today_tasks` or `tomorrow_tasks`. Render task list items as `- [ ] Title` or `- [ ] HH:MM  Title`.

## Date windows

Use half-open local date windows: `[date 00:00, next date 00:00)`.

- Personal: collect today and the next calendar day, including Saturday and Sunday.
- Work: collect today only on Monday-Friday. For the Tomorrow section, collect the next Monday-Friday date. Friday's next working day is Monday.

If a work log is explicitly requested for Saturday or Sunday, create the note but leave work calendar lists blank unless the user explicitly asks for weekend work items.

## Personal: Google Calendar

Use the first available real connector:

1. A configured calendar MCP/tool exposed in the session.
2. `gcalcli` or another installed Google Calendar CLI already authenticated for the user.
3. A user-provided Google Calendar export/ICS file.

Query all personal Google calendars and dated tasks unless the user names a subset. Do not ask for OAuth setup during a daily-log run; if no authenticated connector exists, skip import and say so.

## Work: Microsoft calendar

Microsoft support is planned, not required for the first version. Keep the same calendar item contract so implementation can be added later with Microsoft Graph, an authenticated `m365` CLI, or a work calendar MCP/tool.

Until a Microsoft connector is available, a work daily log still creates the note and skips calendar import with this reason: `Microsoft calendar connector unavailable`.
