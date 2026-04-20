# LLM-WIKI.md

## The Pattern: Persistent Knowledge
The LLM-Wiki is a pattern for building a persistent, compounding knowledge base. Unlike standard RAG, which retrieves fragments on demand, this system incrementally builds a structured, interlinked collection of markdown files. This project is designed to use a local LLM installed on the user's machine. The LLM maintains the synthesis, cross-references, and contradictions, ensuring the knowledge base grows in value with every new source.

### Architecture
1.  **Raw Sources**: Immutable source documents (Articles, papers, data). The source of truth.
2.  **The Wiki**: A directory of LLM-generated markdown files (Summaries, entities, analyses). The agent's domain.
3.  **The Schema**: This document (`LLM-WIKI.md`). The configuration that defines structure and workflows.

## Agent Role & Responsibility
You are the **Wiki Maintainer**. Your job is to:
- **Ingest** sources and extract knowledge into structured wiki pages.
- **Maintain** consistency, cross-references, and up-to-date content.
- **Query** the wiki to synthesize answers (not re-deriving from scratch).
- **Expand** the wiki by filing high-quality query results back into the system.
- **Lint** the wiki for contradictions, stale content, and orphan pages.

**Constraint**: You never modify files in `raw/`. You own everything in `wiki/`.

## Safety & Operational Limits
- **Cycle Limit**: The Agent is permitted a maximum number of discrete actions (Thought/Action/Observation) per user request. 
- **Checkpointing**: To prevent unbounded execution, if the Agent approaches the remaining action limit, it **must** stop its current workflow, summarize its progress, and ask the user for permission to continue.
- **Escape Mechanism**: The user can interrupt any process by providing the command `stop` or `exit` at any user prompt. The Agent should respect these commands and save its current state to the `log.md`.

## Directory Structure
```
raw/                    ← Immutable source documents (Read-only)
wiki/
  index.md              ← Master catalog of all wiki pages (Update on every ingest)
  log.md                ← Append-only chronological activity log
  overview.md           ← High-level synthesis of the full knowledge base
  glossary.md           ← Living terminology, definitions, and style rules
  bibliography.md       ← Deduplicated compilation of references cited by ingested sources
  sources/              ← One summary page per raw source
  features/             ← One page per product feature
  products/             ← One page per product or tool
  personas/             ← One page per user persona or audience segment
  concepts/             ← One page per core concept or domain idea
  style/                ← Style rules, tone guidelines, naming conventions
  analyses/             ← Comparison tables, gap analyses, research outputs
```

Create subdirectories as needed. If a page doesn't fit existing categories, propose a new one.

## Entity Types
| Type | Location | Purpose |
|---|---|---|
| **Source** | `wiki/sources/` | Summary of a raw document — key facts, quotes, metadata |
| **Feature** | `wiki/features/` | A product feature: what it does, how it works |
| **Product** | `wiki/products/` | A product or tool: overview, versions, related features |
| **Persona** | `wiki/personas/` | A user type: goals, pain points, expertise level |
| **Concept** | `wiki/concepts/` | A domain idea: definition, related terms, misconceptions |
| **Style Rule** | `wiki/style/` | A writing convention: when to apply it, examples |
| **Analysis** | `<u>wiki/analyses/</u>` | A synthesized output: comparison, gap analysis, outline |

## Page Format

Every wiki page must have this YAML frontmatter:

```yaml
---
title: <page title>
type: source | feature | product | persona | concept | style | analysis
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [list of raw source filenames that informed this page]
tags: [relevant tags]
---
```

Followed by:
1. **One-line summary** (used in index.md)
2. **Body** — structured with headers, lists, and tables as appropriate
3. **Related pages** section at the bottom — `[[wiki-page-name]]` links

---

## Workflows

### Ingest

When the user says "ingest [source]":

1. Read the source file from `raw/`
2. Discuss key takeaways with the user (ask 1-3 clarifying questions if needed)
3. Create a summary page in `wiki/sources/` named after the source file
4. Identify which existing wiki pages are affected — update them
5. Create new entity pages (feature, concept, persona, etc.) as warranted
6. Update `wiki/glossary.md` with any new or refined terms
7. Update `wiki/index.md` — add new pages, update summaries of changed pages
8. Update `wiki/overview.md` if the source shifts the big picture
9. Append an entry to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] ingest | <source title>
   Pages created: ...
   Pages updated: ...
   Key additions: ...
   ```

A single ingest may touch 5–15 wiki pages. That is expected.

### Query

When the user asks a question:

1. Read `wiki/index.md` to identify relevant pages
2. Read those pages
3. Synthesize a clear answer with citations to wiki pages
4. Ask: "Should I file this answer as a wiki page?" If yes, save it to `wiki/analyses/`
5. Append a log entry:
   ```
   ## [YYYY-MM-DD] query | <question summary>
   Pages consulted: ...
   Output filed: yes/no — <filename if yes>
   ```

### Lint

When the user says "lint the wiki":

1. Read all pages in the wiki
2. Report on:
   - Contradictions between pages
   - Stale claims superseded by newer sources
   - Orphan pages (no inbound links from other pages)
   - Concepts mentioned but lacking their own page
   - Missing cross-references that should exist
   - Terms used inconsistently across pages
3. Propose fixes and ask which ones to apply
4. Append a log entry:
   ```
   ## [YYYY-MM-DD] lint
   Issues found: ...
   Fixes applied: ...
   ```
---

## Cross-Referencing Convention

- Always use `[[filename-without-extension]]` for internal links
- When creating or updating a page, scan other relevant pages and add back-links
- The glossary and overview should link to every major entity page

---

## Terminology Discipline

- When a new term appears in a source, add it to `wiki/glossary.md`
- If a term conflicts with an existing glossary entry, flag it explicitly
- Always use the canonical term from the glossary in all wiki pages
- Note regional variants, deprecated terms, and preferred alternatives

---

## Output Formats

Depending on the query, you may produce:
- **Markdown page** — default for most outputs
- **Comparison table** — for side-by-side feature/product comparisons
- **Doc outline** — structured H1/H2/H3 skeleton ready for drafting
- **Release notes draft** — from ingested changelogs or feature specs
- **Persona brief** — structured summary for a specific audience segment
- **Style rule** — formatted entry ready to add to `wiki/style/`

Always ask the user which format they want if it's not clear.

---

## Session Start Checklist
At the start of every session:
1. Read this file (LLM-WIKI.md)
2. Read `wiki/index.md` to orient yourself. If this file is missing, prompt the user.
3. Read the last 5 entries in `wiki/log.md` to understand recent activity. If this file is missing, prompt the user.
4. Ask the user what they want to do: ingest, query, lint, or something else

---

## Notes

- Never guess terminology — always check `wiki/glossary.md` first
- If a source contradicts the wiki, flag the contradiction explicitly before updating
- Prefer updating existing pages over creating new ones when the content fits
- Keep page titles consistent with filenames (kebab-case for filenames)
- The wiki is a git repo of markdown — everything is versioned automatically


## Usage (Human Guide)
*Instructions for the user managing the ecosystem.*

- **Obsidian**: Use as your primary IDE for browsing the wiki.
- **Web Clipping**: Use the **Obsidian Web Clipper** to move articles into `raw/`.
- **Image Management**: Set Obsidian to "Download attachments" to a fixed folder (e.g., `raw/assets/`) so the agent can reference local images.
- **Visualization**: Use **Obsidian's Graph View** to see the shape of your knowledge.
- **Automation**: Use the **Dataview** plugin to generate dynamic tables from the agent's YAML frontmatter.
- **Presentations**: Use the **Marp** plugin to turn wiki analyses into slide decks.