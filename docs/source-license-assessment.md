# Source License Assessment

**Status:** License compatibility analysis  
**Date:** 2026-07-14  
**Scope:** Two upstream repositories with copied/adapted content  
**Disclaimer:** This report documents license facts and identifies obligations, but does not constitute legal advice. Consult a qualified attorney for binding legal interpretation.

---

## Executive Summary

This repository retains copied and adapted code from two MIT-licensed upstream repositories:

1. **`mattpocock/skills`** — 21 foundry skills (adapted)
2. **`iusztinpaul/ai-research-os-workshop`** — Research orchestration skill (adapted)

Both upstreams are licensed under the **MIT License**. The downstream repository intends to use the MIT License as well.

**Additional source reviewed:** `anthropics/skills`' `skill-creator` was used as an authoring reference. The local `anvil-develop-skills` skill has no Anthropic provenance declaration, and a comparison against the pinned upstream version found no shared normalized lines or five-word phrases. It is treated as independently authored inspiration, not redistributed Apache-2.0 content.

**Compatibility:** ✓ **MIT-to-MIT is compatible.** Adapted MIT-licensed material may be relicensed under MIT downstream with proper attribution preserved.

**Minimum compliance action:** Ensure that the upstream copyright notices and license text are preserved in each adapted file or component, accessible to downstream users.

---

## 1. Upstream Repository: `mattpocock/skills`

### License

**Primary source:** [LICENSE file at `mattpocock/skills`/main](https://github.com/mattpocock/skills/blob/main/LICENSE)

```text
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Scope of Adaptation

The following 21 skills in `skills/foundry-*` are marked with `origin: mattpocock/skills` in their YAML frontmatter metadata:

1. `foundry-ask-matt`
2. `foundry-code-review`
3. `foundry-codebase-design`
4. `foundry-diagnosing-bugs`
5. `foundry-domain-modeling`
6. `foundry-grill-me`
7. `foundry-grill-with-docs`
8. `foundry-grilling`
9. `foundry-handoff`
10. `foundry-implement`
11. `foundry-improve-codebase-architecture`
12. `foundry-prototype`
13. `foundry-research`
14. `foundry-setup-matt-pocock-skills`
15. `foundry-tdd`
16. `foundry-teach`
17. `foundry-to-spec`
18. `foundry-to-tickets`
19. `foundry-triage`
20. `foundry-wayfinder`
21. `foundry-writing-great-skills`

Each file's YAML metadata documents:
- `origin: mattpocock/skills`
- `origin-path`: original skill location in upstream repo
- `origin-revision`: upstream commit SHA
- `origin-status: adapted`

**Example (from `skills/foundry-code-review/SKILL.md`):**

```yaml
---
name: foundry-code-review
metadata:
  origin: mattpocock/skills
  origin-path: skills/engineering/code-review/SKILL.md
  origin-revision: e9fcdf95b402d360f90f1db8d776d5dd450f9234
  origin-status: adapted
---
```

### Attribution Obligations

**MIT License requirement:** The copyright notice and license text must be included in all copies or substantial portions of the software.

**Current compliance:**

1. Each adapted skill file carries explicit upstream reference via YAML frontmatter metadata (`origin`, `origin-path`, `origin-revision`).
2. The root `NOTICE` preserves Matt Pocock's complete MIT copyright and permission notice for all adapted `foundry-*` skills.
3. The metadata format and `NOTICE` let downstream users trace each skill to its upstream source and commit.

---

## 2. Upstream Repository: `iusztinpaul/ai-research-os-workshop`

### License

**Primary source:** [LICENSE file at `iusztinpaul/ai-research-os-workshop`/main](https://github.com/iusztinpaul/ai-research-os-workshop/blob/main/LICENSE)

```text
MIT License

Copyright (c) 2026 Paul Iusztin, Towards AI Inc

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Scope of Adaptation

The `skills/anvil-obsidian-research/` skill is adapted from the upstream workshop repository.

**Upstream mapping:**
- Source repo: `iusztinpaul/ai-research-os-workshop`
- Upstream commit: `dc6660555266239cd36483cf51b5ab39febacf02`
- Adapted files include:
  - `SKILL.md` (skill orchestration logic)
  - `CONVENTIONS.md` (research directory data contract)
  - Agent templates in `agents/` subdirectory
  - Utility scripts in `scripts/` subdirectory

**Metadata (from `skills/anvil-obsidian-research/SKILL.md`):**

```yaml
---
name: anvil-obsidian-research
metadata:
  origin: iusztinpaul/ai-research-os-workshop
  origin-path: .
  origin-revision: dc6660555266239cd36483cf51b5ab39febacf02
  origin-status: adapted
---
```

**Attribution line (at end of `SKILL.md`):**
```
*Adapted from [iusztinpaul/ai-research-os-workshop](https://github.com/iusztinpaul/ai-research-os-workshop) @ `dc6660555266239cd36483cf51b5ab39febacf02` (MIT).*
```

### Attribution Obligations

**MIT License requirement:** Same as above — copyright notice and license text must be preserved in copies or substantial portions.

**For this repository's compliance:**

1. ✓ **In place:** Explicit upstream reference in YAML frontmatter metadata
2. ✓ **In place:** Attribution line at the end of `SKILL.md`
3. ✓ **In place:** `skills/anvil-obsidian-research/LICENSE-upstream` file preserving the MIT license text with the proper copyright holder (`Copyright (c) 2026 Paul Iusztin, Towards AI Inc`)

**Compliance status:** ✓ **Complete.** The `anvil-obsidian-research` skill fully satisfies MIT License obligations.

---

## 3. License Compatibility Analysis

### MIT-to-MIT Compatibility

Both upstreams are licensed under the **MIT License (Expat License)**, one of the most permissive open-source licenses.

**Key terms of MIT License:**
- Permits: commercial use, modification, distribution, private use
- Requires: inclusion of copyright notice and license text
- Provides: "as-is" with no warranty or liability

**Downstream licensing decision:**
This repository intends to be licensed under the **MIT License**.

**Compatibility assessment:** ✓ **Fully compatible.**

An MIT-licensed downstream repository may:
1. Copy MIT-licensed code from upstream
2. Adapt MIT-licensed code
3. Redistribute under the MIT License downstream
4. Relicense MIT code to another MIT-compatible license (but not restrictive licenses like GPL)

**No conflict exists between the two upstream licenses and this repository's intended MIT license.**

---

## 4. Minimum Compliance Actions

### Already Implemented ✓

| Component | Obligation | Status | Evidence |
|-----------|-----------|--------|----------|
| `mattpocock/skills` (21 skills) | Metadata and license preservation | ✓ Implemented | YAML frontmatter plus the complete MIT notice in root `NOTICE` |
| `anvil-obsidian-research` | Metadata and license preservation | ✓ Implemented | YAML metadata, attribution line, `LICENSE-upstream`, and root `NOTICE` |

### Exact Compliance Checklist

**For `mattpocock/skills` (21 skills):**
- ✓ Each skill carries upstream metadata.
- ✓ Root `NOTICE` retains the complete upstream MIT copyright and permission notice.

**For `iusztinpaul/ai-research-os-workshop` (listed research skills):**
- ✓ Skills retain provenance metadata and explicit attribution.
- ✓ `anvil-obsidian-research/LICENSE-upstream` and root `NOTICE` preserve the complete MIT notice.

---

## 5. Uncertainty and Caveats

### Scope Limitation

This assessment covers **file-level attribution** found in the repository. It does not:
- Exhaustively analyze every line of code for upstream provenance (would require word-level tracing)
- Evaluate whether adaptations are "substantial" enough to create derivative works (legal question)
- Review code licenses of any dependencies or bundled tools

### File-level vs. Line-level Attribution

The repository tracks upstream sources at the file level (SKILL.md, agent templates, scripts). If individual paragraphs or functions were extracted from upstream sources without file-level attribution, they may not be discoverable by this audit. A more granular analysis would require line-by-line comparison.

### Copyright Year

Both upstream repositories list copyright as `2026`. If the actual original work predates 2026, the copyright year may need review. This should be verified directly with the upstream authors.

### Derivative Work Status

Under U.S. and most copyright law, creating a "derivative work" (modification) of licensed code typically requires compliance with the original license. Both upstreams use MIT, which permits modification. Whether the adaptations in this repository rise to the level of "derivative works" is a legal interpretation question best answered by counsel familiar with the specific adaptations.

---

## 6. References and Primary Sources

### Upstream Repository Links

1. **mattpocock/skills**
   - Repository: https://github.com/mattpocock/skills
   - License: https://github.com/mattpocock/skills/blob/main/LICENSE
   - License text: MIT License, Copyright (c) 2026 Matt Pocock

2. **iusztinpaul/ai-research-os-workshop**
   - Repository: https://github.com/iusztinpaul/ai-research-os-workshop
   - License: https://github.com/iusztinpaul/ai-research-os-workshop/blob/main/LICENSE
   - License text: MIT License, Copyright (c) 2026 Paul Iusztin, Towards AI Inc

### Local Documentation

- Metadata references: See YAML frontmatter in each adapted skill file
- Attribution example: `skills/anvil-obsidian-research/SKILL.md` (line 944)
- License preservation: `skills/anvil-obsidian-research/LICENSE-upstream`

---

## 7. Conclusion

This repository may lawfully retain and distribute the copied and adapted content from both upstream repositories under the MIT License, provided:

1. **Attribution and license text are preserved** in skill metadata and the root `NOTICE`.
2. **Downstream users can trace upstream sources** through metadata, source revisions, and `NOTICE`.

**No legal blockers exist to adding an MIT license to this downstream repository.** Both upstream sources are MIT-licensed, making them fully compatible with MIT downstream licensing.

**Current status:** `NOTICE` is the shared, top-level record of upstream license and copyright notices.

## 8. Post-assessment updates

- The root `NOTICE` now preserves the complete MIT notices for `mattpocock/skills` and `iusztinpaul/ai-research-os-workshop`; this fulfills the report's recommended shared-notice action.
- `anvil-develop-skills` was compared with `anthropics/skills`' `skill-creator` at commit `9d2f1ae187231d8199c64b5b762e1bdf2244733d`. No copied expression was identified, so its Apache-2.0 `LICENSE.txt` is not redistributed here. The README credits it as inspiration only.
- If future work copies or adapts `skill-creator`, retain its Apache-2.0 license, all applicable notices, and a prominent modification notice in the affected files. See [the upstream license](https://github.com/anthropics/skills/blob/main/skills/skill-creator/LICENSE.txt).

---

**Report prepared:** 2026-07-14  
**Primary sources verified:** https://github.com/mattpocock/skills/blob/main/LICENSE, https://github.com/iusztinpaul/ai-research-os-workshop/blob/main/LICENSE, https://github.com/anthropics/skills/blob/main/skills/skill-creator/LICENSE.txt  
**Not legal advice.**
