---
name: obsidian-curate-trending-repositories
description: Digest trending GitHub repositories into a daily Obsidian Inbox note. Use when the user asks to "run the trending repos digest", "get today's GitHub trending", "what's trending on GitHub", or mentions Trendshift, OSSInsight, or Star History rankings.
metadata:
  origin: gauthiermartin/skills
  origin-revision: 70b53e358c6781b332391c7d5046fb2f75fdd6b2
  origin-status: verbatim
version: 0.1.0
---

# GitHub Trending Digest

Create one dated Obsidian note ranking the day's trending GitHub repositories, capped at 15 entries, focused on AI and on four languages: Python, HCL (Terraform), TypeScript/JavaScript (Node), and Rust.

## Default inputs

- **Vault:** `~/Documents/Vaults/exocortex`
- **Output folder:** `00-Inbox/`
- **Output filename:** `GitHub Trending YYYY-MM-DD.md`, one file per run date.
- **Cap:** 15 repositories per digest, no more.
- **Focus:** AI repos (any language) plus Software Engineering repos whose primary language is Python, HCL, TypeScript, JavaScript, or Rust.
- **Default run:** today, `period=past_24_hours`. An explicit user date/window overrides this.
- **Template:** `assets/trending-repository-template.md`

## Steps

### 1. Resolve the run scope

Confirm the target date (default today) and vault write target. Before writing to Obsidian, read the vault's `CLAUDE.md` if present and follow its note conventions.

Completion criterion: target date, vault path, and the 15-repo cap are known.

### 2. Collect candidates from three sources

Prefer real APIs over scraping rendered pages — see `Source notes` below for why.

1. **OSSInsight trends API.** For each language in `All, Python, HCL, TypeScript, Rust`, call:
   `https://api.ossinsight.io/v1/trends/repos/?period=past_24_hours&language=<L>`
   Rows arrive pre-ranked by `total_score`. If a language query returns fewer than 3 rows, retry once with `period=past_week` before treating it as sparse.
2. **Trendshift.io.** Read `https://trendshift.io/` (default Daily view). Extract each listed repo's `owner/repo`, one-line description, and any topic tag shown.
3. **Star-history.com.** Read `https://www.star-history.com/`. Extract the "Coding AI Leaderboard" (Weekly) entries as AI-focused candidates — `owner/repo` and star-growth count.

For every candidate capture: `owner/repo`, description, primary language (if known), source label, and whatever ranking signal that source provides (`total_score`, list position, or star growth).

Completion criterion: every source that responded contributes at least one candidate, or is recorded as empty/unreachable for the report in step 6.

### 3. Classify and deduplicate

Keep a candidate only if it matches at least one of:
- **AI-relevant** — name or description matches AI vocabulary: `LLM, agent, RAG, MCP, GPT, transformer, inference, embedding, vector, diffusion, copilot, chatbot, prompt, fine-tun`. Language-agnostic.
- **Target-language Software Engineering** — primary language is Python, HCL, TypeScript, JavaScript, or Rust.

Drop everything else (e.g., a trending C# game repo with no AI angle).

Deduplicate by exact `owner/repo` (case-insensitive): merge into one entry, unioning the contributing source labels.

Completion criterion: every kept entry has exactly one `owner/repo` key, tagged AI and/or its language, listing every source that surfaced it.

### 4. Rank and cap at 15 with balanced coverage

Group kept entries into buckets: `AI`, `Python`, `HCL`, `TypeScript/JavaScript`, `Rust` — an entry can sit in more than one bucket (an AI repo written in Rust counts in both). Within each non-empty bucket, order entries by: multi-source hit first, then highest available ranking signal (OSSInsight `total_score`, else star growth, else list position).

Fill the 15 slots by round-robin across non-empty buckets, one unpicked entry per bucket per round, skipping exhausted buckets and entries already placed from another bucket. This matters because OSSInsight's `total_score` tracks raw GitHub event volume, not per-language rank: a slow day for HCL can score 30-40 while TypeScript scores 200+, so a plain global sort silently drops Terraform every run. Round-robin guarantees every non-empty bucket — including the low-volume ones — lands at least one entry before any bucket gets a second.

Completion criterion: exactly ≤15 entries; every non-empty bucket contributed at least one entry before any bucket contributed a second.

### 5. Write the Obsidian note

Render `assets/trending-repository-template.md` into `00-Inbox/GitHub Trending YYYY-MM-DD.md`: one line per repo with its link, one-line description, language/AI tag, and source list. If the file for that date already exists, overwrite it — this is a point-in-time snapshot, not an append log.

Completion criterion: the file exists at the target path with ≤15 repo lines, each carrying a link, description, tag, and source list.

### 6. Report tersely

Return the vault path, repo count, and any source that came back empty or unreachable. Do not paste the digest body.

Completion criterion: the user can open the file and see exactly what step 5 wrote, and knows which sources (if any) were skipped.

## Source notes

- **OSSInsight** — use the public API (`api.ossinsight.io/v1/trends/repos/`), not the `ossinsight.io/trending` or `ossinsight.io/trending/ai` pages: both render their tables client-side and have been observed returning "No repositories found" even after the page finishes loading. The API needs no auth and is rate-limited to 600 req/hour per IP.
- **Terraform** maps to GitHub's `primary_language` value `HCL`, not `Terraform`.
- **Star-history.com** has no plain "trending repos" list; its homepage "Coding AI Leaderboard" (star growth over the last week) is the usable trending signal from that source.
