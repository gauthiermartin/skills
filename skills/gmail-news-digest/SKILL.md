---
name: gmail-news-digest
description: Digest Gmail newsletters into catch-up Obsidian News Digest pages. This skill should be used when the user asks to "run the news digest", "summarize AWS News", "summarize Newsletters AI", or catch up missed daily digest pages from Gmail labels with duplicate links.
metadata:
  origin: gauthiermartin/skills
  origin-revision: 70b53e358c6781b332391c7d5046fb2f75fdd6b2
  origin-status: verbatim
version: 0.1.0
---

# Gmail News Digest

Create Obsidian digest pages from Gmail messages labeled `AWS News` or `Newsletters AI`. Keep each digest skimmable: one page per local received day, one topic card per topic, 2-3 summary lines per card, and all source links grouped under that card so duplicates help rather than clutter.

## Default inputs

- **Vault:** `~/Documents/Vaults/exocortex`
- **Output folder:** `00-Inbox/`
- **Output filename:** `News Digest YYYY-MM-DD.md`, one file per received date.
- **Labels:** `AWS News`, `Newsletters AI`
- **Default run:** catch up all still-labeled messages, grouped by local received date; include previous days and today.
- **Explicit run:** if the user names a date or range, process only those dates.
- **Template:** `assets/news-digest-template.md`

## Digest steps

### 1. Preflight Gmail access and date plan

Detect `gmail_access` in one pass — don't guess at a Gmail mechanism:

- `gmail_mcp`: a Gmail/mail MCP or tool is available. Record `gmail_capabilities = read` or `read_write` from its operations. In this environment that's the `mcp__claude_ai_Gmail__*` tool family (claude.ai's connected Gmail account) — load it via `ToolSearch` with `select:mcp__claude_ai_Gmail__list_labels,mcp__claude_ai_Gmail__search_threads,mcp__claude_ai_Gmail__get_thread,mcp__claude_ai_Gmail__get_message` and use it without asking; the user has already confirmed claude.ai has Gmail access.
- `browser_gmail`: the browser opens `https://mail.google.com/` and lands in an authenticated inbox.
- `mail_export`: user-supplied local `.mbox`/`.eml` files. Treat as `read`-only.
- `missing`: none of the above.

This digest requires `gmail_read`: a Gmail/mail MCP or tool that can search/read messages, an authenticated Gmail browser, or user-supplied `.mbox`/`.eml` files. Prefer Gmail MCP/API access with label IDs — names with spaces are brittle in Gmail search syntax. Browser Gmail and mail exports are read-capable fallbacks.

If read-capable access is missing, ask for exactly one path: enable a Gmail MCP/tool, use an authenticated Gmail browser session, or provide a mail export. Never ask for a password, never invent Gmail CLI commands, and don't rely on Gmail search syntax until the access path is confirmed.

Build the date plan using the local timezone for received dates and windows. If the user names a date or range, use that explicit window. Otherwise run in catch-up mode: scan still-labeled messages for both labels, group them by local received date, and create or update one digest page for each date found, including previous days. If catch-up finds more than 14 dates, preview date counts and ask for a start date before writing pages.

Before writing to Obsidian, read the vault's `CLAUDE.md` if present and follow its note conventions.

**Gate:** read-capable Gmail access exists, the date plan is explicit, and the vault write target is known.

### 2. Collect labeled messages

With `mcp__claude_ai_Gmail__*`: call `list_labels` once to confirm label names exist, but query `search_threads` with the quoted display name (`label:"AWS News"`) — the numeric `labelId` does not work as a query token even though `list_labels` returns one. `get_message`/`get_thread` on an HTML newsletter routinely exceeds the tool's inline token limit and gets written to a scratch file instead; when that happens, use `jq -r '.plaintextBody'` on that file for prose and `jq -r '.htmlBody' | grep -oE 'href="[^"]*"'` for links rather than retrying the call.

Fetch messages for the date plan from both labels. Assign every message to exactly one local received date. For each message, capture only digest inputs:

- Gmail message id
- received date
- label
- sender/publication
- subject
- body links with nearby title/context

Ignore unsubscribe, preference-center, tracking-pixel, social-share, logo/image, and mailto links. Do not expose raw email bodies in the final response.

**Gate:** every matching message is represented once in exactly one date group, or the digest says no matching mail was found.

### 3. Canonicalize links

For each candidate article link:

1. Follow safe redirects when possible, especially newsletter and Gmail redirect wrappers.
2. Normalize host case, remove fragments, remove trailing slash noise, and drop tracking parameters such as `utm_*`, `fbclid`, `gclid`, `mc_cid`, `mc_eid`, `ck_subscriber_id`, and email-recipient ids.
3. Keep both the display URL and canonical URL; use canonical URL for matching, display URL for the note when it is cleaner.

**Gate:** every candidate has a canonical key or has been discarded as non-article noise.

### 4. Deduplicate into topic cards

Deduplicate in this order:

1. **Same canonical URL:** merge into one source link entry.
2. **Same article title on the same host:** merge as duplicate links.
3. **Same story/topic from different sources:** cluster as one topic card when the titles clearly refer to the same announcement, release, model, paper, funding event, security issue, outage, or policy change.

Keep all distinct article links in the card. Mark the clearest/original item as `Primary`; put the rest under `Duplicate topic links`. Do not create a second card for a duplicate topic.

For each date, check the current digest file if it already exists and merge into it instead of appending duplicate cards. Across older digest pages, avoid repeating the exact same canonical URL; fresh articles about a continuing story may get a new card.

**Gate:** each canonical URL appears in only one card, and duplicate topic links remain visible under that card.

### 5. Write the Obsidian pages

For each date group, use the template in `assets/news-digest-template.md`. Keep every page optimized for reading:

- Frontmatter for date, labels, message count, and topic count.
- A `Quick scan` list linking to topic headings.
- One `Topics` section with one card per topic.
- 2-3 lines maximum per topic summary.
- Source links under each topic, with duplicate topic links repeated as extra bullets only when they exist.
- Hidden canonical URL comments per topic so future runs can merge instead of duplicate.
- A short `Skipped` section only when messages or links were excluded for a useful reason.

If a date has no topics after filtering, write a short digest page saying no labeled newsletter items were found for that date only when the user explicitly requested that date.

**Gate:** every date group has a readable `00-Inbox/News Digest YYYY-MM-DD.md` file, and no page contains duplicate topic cards for the same canonical URL.

### 6. Report tersely

Return only the created/updated vault paths, topic count per date, source message count per date, and any access limitation that affected coverage. Do not paste the whole digest unless asked.

**Gate:** the user can open each page and follow every interesting topic through its links.
