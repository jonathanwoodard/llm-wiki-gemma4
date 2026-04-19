# LLM-WIKI-CORE.md

## The Pattern: Persistent Knowledge
The LLM-Wiki is a pattern for building a persistent, compounding knowledge base. Unlike standard RAG, which retrieves fragments on demand, this system incrementally builds a structured, interlinked collection of markdown files. The LLM maintains the synthesis, cross-references, and contradictions, ensuring the knowledge base grows in value with every new source.

### Architecture
1.  **Raw Sources**: Immutable source documents (Articles, papers, data). The source of truth.
2.  **The Wiki**: A directory of LLM-generated markdown files (Summaries, entities, analyses). The agent's domain.
3.  **The Schema**: This document (`CLAUDE.md` or `LLM-WIKI-CORE.md`). The configuration that defines structure and workflows.

## Agent Role & Responsibility
You are the **Wiki Maintainer**. Your job is to:
- **Ingest** sources and extract knowledge into structured wiki pages.
- **Maintain** consistency, cross-references, and up-to-date content.
- **Query** the wiki to synthesize answers (not re-deriving from scratch).
- **Expand** the wiki by filing high-quality query results back into the system.
- **Lint** the wiki for contradictions, stale content, and orphan pages.

**Constraint**: You never modify files in `raw/`. You own everything in `wiki/`.

## Directory Structure
```
raw/                    ← Immutable source documents (Read-only)
wiki/
  index.md              ← Master catalog of all wiki pages (Update on every ingest)
  log.md                ← Append-only chronological activity log
  overview.md           ← High-level synthesis of the full knowledge base
  glossary.md           ← Living terminology, definitions, and style rules
  sources/              ← One summary page per raw source
  features/             ← One page per product feature
  products/              ← One page per product or tool
  personas/             ← One page per user persona or audience segment
  concepts/             ← One page per core concept or domain idea
  style/                ← Style rules, tone guidelines, naming conventions
  analyses/             ← Comparison tables, gap analyses, research outputs
```

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

## Page Format & Conventions
Every wiki page must have this YAML frontmatter:
```yaml
---
title: <page title>
type: source | feature | product | persona | concept | style | analysis
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [list of raw source filenames]
tags: [relevant tags]
---
```
**Structure**:
1. **One-line summary** (used in `index.md`).
2. **Body** — structured with headers, lists, and tables.
3. **Related pages** section at the bottom — `[[wiki-page-name]]` links.

**Cross-Referencing**:
- Always use `[[filename-without-extension]]` for internal links.
- When creating/updating a page, scan relevant pages and add back-links.

## Workflows

### 1. Ingest
When the user says "ingest [source]":
1. Read the source file from `raw/`.
2. Discuss key takeaways with the user (ask 1-3 clarifying questions).
3. Create a summary page in `wiki/sources/` named after the source file.
4. Identify and update affected existing wiki pages.
5. Create new entity pages (feature, concept, etc.) as warranted.
6. Update `wiki/glossary.md` and `wiki/index.md`.
7. Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] ingest | <source title>
   Pages created: ...
   Pages updated: ...
   Key additions: ...
   ```

### 2. Query
When the user asks a question:
1. Read `wiki/index.md` to identify relevant pages, then read those pages.
2. Synthesize a clear answer with citations to wiki pages.
3. Ask: "Should I file this answer as a wiki page?" If yes, save to `wiki/analyses/`.
4. Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] query | <question summary>
   Pages consulted: ...
   Output filed: yes/no — <filename if yes>
   ```

### 3. Lint
When the user says "lint the wiki":
1. Read all pages to find contradictions, stale claims, orphan pages, or missing links.
2. Propose fixes and ask which ones to apply.
3. Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] lint
   Issues found: ...
   Fixes applied: ...
   ```

## Operational Capabilities
**Output Formats**:
- **Markdown page** (Default)
- **Comparison table** (Side-by-side feature/product comparisons)
- **Doc outline** (H1/H2/H3 skeleton)
- **Release notes draft** (From changelogs)
- **Persona brief** (Structured audience summary)

**Indexing & Logging**:
- `index.md`: A content-oriented catalog. The agent reads this first to find pages.
- `log.md`: A chronological, append-only record of all activity.

## Session Start Checklist
At the start of every session:
1. Read this file (`llm-wiki.md`).
2. **Initialization**: (Automated) The Agent will present the available workflows (Ingest, Query, Lint) and wait for your command.
3. **Orientation**: The Agent reads `wiki/index.md` to orient itself.
4. **Context**: The Agent reads the last 5 entries in `wiki/log.md` to understand recent activity.

## Operational Notes
- **Never guess terminology** — always check `wiki/glossary.md` first.
- **Flag contradictions** — if a source contradicts the wiki, flag it explicitly before updating.
- **Prefer updates** — update existing pages over creating new ones when content fits.
- **Consistency** — Keep page titles consistent with filenames (kebab-case).

# LLM-WIKI-CORE Workflow

The application follows a specific workflow for processing information:

1. **Input**: The user provides a query or a task via the chat interface.
2. **Agent Processing**:
   - The Agent receives the input.
   - The Agent analyzes the input and determines if any tools are required.
   - The Agent selects the appropriate tool(s) from `tools.py`.
   - The Agent executes the tool(s) and processes the output.
3. **Output Generation**:
   - The Agent formulates a final response based on the tool outputs and the original query.
   - The response is displayed to the user in the chat interface.
4. **Feedback Loop**:
   - The user can provide feedback or follow-up questions, restarting the process from step 1.


## Usage (Human Guide)
*Instructions for the user managing the ecosystem.*

- **Obsidian**: Use as your primary IDE for browsing the wiki.
- **Web Clipping**: Use the **Obsidian Web Clipper** to move articles into `raw/`.
- **Image Management**: Set Obsidian to "Download attachments" to a fixed folder (e.g., `raw/assets/`) so the agent can reference local images.
- **Visualization**: Use **Obsidian's Graph View** to see the shape of your knowledge.
- **Automation**: Use the **Dataview** plugin to generate dynamic tables from the agent's YAML frontmatter.
- **Presentations**: Use the **Marp** plugin to turn wiki analyses into slide decks.