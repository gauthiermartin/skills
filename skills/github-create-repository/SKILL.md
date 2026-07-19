---
name: github-create-repository
description: Create a new GitHub repository via gh with README and gitignore.
metadata:
  origin: gauthiermartin/skills
  origin-status: local
disable-model-invocation: true
---

# Create a GitHub repository

Create a new GitHub repository with `gh`, initialized with a README and a language-appropriate gitignore.

## Steps

1. **Ask** — collect everything in ONE prompt (never serialize questions):
   - Repository name
   - Purpose (one or two sentences)
   - Target language
   - Visibility: public or private
   - License: None, MIT, Apache-2.0, or GPL-3.0

2. **Derive**:
   - Repo description: condense the purpose into one sentence (≤ 120 chars, no trailing period).
   - Gitignore template: map the language to a template name from `gh api /gitignore/templates` (e.g. Python, Node, Go, Rust). No match → omit `--gitignore` and tell the user.

3. **Create** — one command, cloned into the current directory:

   ```bash
   gh repo create <name> --description "<desc>" --<visibility> \
     [--gitignore <Template>] [--license <key>] --clone
   ```

4. **README** — in the clone, write `README.md`: `# <name>` heading plus the purpose as one paragraph. No placeholder sections. Then:

   ```bash
   git add README.md && git commit -m "Add README" && git push
   ```

5. **Verify** — done only when all three checks exit 0:

   ```bash
   test "$(gh repo view "$owner/$name" --json description --jq .description)" = "$desc"
   test "$(gh api "repos/$owner/$name/readme" --jq .name)" = README.md
   test -f .gitignore   # only when a template was applied
   ```

   Any check fails → fix it before reporting done. Report the repo URL to the user.
