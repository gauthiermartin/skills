---
name: obsidian-book-add
description: Add a book to the exocortex vault's reading library (03-Resources/Books) with metadata and cover fetched from Google Books, matching the vault's book note schema. Use when the user says "add a book", "log a book", "I finished reading X", "add X to my reading list", or "track this book". Not for creating general notes or for querying the existing bookshelf.
metadata:
  origin: gauthiermartin/skills
  origin-status: local
---

# Add a book to the reading library

Maintain one book note in `03-Resources/Books/` and its local cover in
`05-Assets/Images/Books/`. Preserve the fixed schema: the Bookshelf base depends
on every book using the same properties and statuses.

1. **Parse the request.** Extract the title and any supplied author or ISBN. Infer
   reading state: map "finished" or "read" to `status: read` and set `finished` to
   today's ISO date; map "reading" or "started" to `status: reading` and set
   `started` to today's ISO date; otherwise use `status: to-read`. Preserve a
   user-provided 1–5 rating; otherwise leave `rating` empty. Do not infer a rating.

2. **Fetch and select metadata.** Query Google Books without an API key. For title
   and author searches, URL-encode supplied text and use this query form:
   ```sh
   curl -s "https://www.googleapis.com/books/v1/volumes?q=intitle:<title>+inauthor:<author>"
   ```
   For an ISBN, use `q=isbn:<isbn>`. Inspect `items[0].volumeInfo`. When leading
   candidates materially differ in work (not merely edition), show the first three
   as title, author, and year, then ask which one to add. When there are no results,
   retry with a plain `q=<title>` query. When that also returns no results, create
   the note with only user-provided fields, an empty `cover`, and state that no
   Google Books metadata was found.

3. **Download a local cover.** Build the cover filename exactly as
   `<Title> - <First Author>.jpg` and save it under
   `05-Assets/Images/Books/`. Take `volumeInfo.imageLinks.thumbnail`, remove
   `&edge=curl`, and replace `zoom=1` with `zoom=2` before downloading with
   `curl -sL -o`. When Google Books has no image, obtain the ISBN-13 from
   `industryIdentifiers` and try
   `https://covers.openlibrary.org/b/isbn/<isbn13>-L.jpg`; keep that response only
   when it exceeds 1 KB, because Open Library returns a tiny placeholder for
   unknown ISBNs. On success, set the frontmatter value exactly to
   `"[[05-Assets/Images/Books/<Title> - <First Author>.jpg]]"`. On failure, use
   `cover: ""`. Do not use a remote image URL in a note.

4. **Create or update the note.** Name the file
   `03-Resources/Books/<Title> - <First Author>.md`. Check whether it already
   exists before writing. For an existing note, update only `status`, the applicable
   `started` or `finished` date, and a user-supplied rating; preserve its metadata
   and notes. For a new note, write this canonical structure, replacing every
   angle-bracket value with the selected Google Books value (use the year portion
   of `publishedDate`, `pageCount`, the ISBN-13, and the description). Encode
   YAML strings safely; keep empty values empty.

   ```markdown
   ---
   title: "<Title>"
   subtitle: "<Subtitle>"
   author: ["<Author 1>", "<Author 2>"]
   category: ["<Category 1>"]
   publisher: "<Publisher>"
   published: <Year>
   pages: <Number>
   isbn13: "<ISBN-13>"
   cover: "[[05-Assets/Images/Books/<Title> - <First Author>.jpg]]"
   status: <to-read|reading|read>
   rating: <1-5 or empty>
   started: <YYYY-MM-DD or empty>
   finished: <YYYY-MM-DD or empty>
   ---

   # <Title>

   ## About

   <Google Books description>

   ## Summary

   ## Key Takeaways

   ## Quotes & Notes
   ```

   The fixed frontmatter schema is identical to
   `05-Assets/Templates/Book Note Template.md`. Change both files together when
   changing the schema. Keep body headings exactly as shown.

5. **Enrich only on request.** Leave `## Summary` and `## Key Takeaways` empty
   unless the request asks for either. When asked, add a 3–6 sentence summary and
   5–10 takeaway bullets based on model knowledge and, when necessary, web research.
   Do not present uncertain plot or argument details as fact.

6. **Confirm the result.** Report the note path, cover path (or that no cover was
   found), and the assigned status. Point to
   `03-Resources/Books/Bookshelf.base` as the visual shelf.
