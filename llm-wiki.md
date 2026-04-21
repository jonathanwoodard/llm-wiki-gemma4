# LLM-WIKI: Persistent Knowledge Pattern

## The Pattern: Persistent Knowledge
The LLM-Wiki is a pattern for building a persistent, compounding knowledge base. This project utilizes a local **Gemma-4** model to maintain synthesis, cross-references, and contradictions, ensuring the knowledge base grows in value with every new source.

### Architecture
1. **Raw Sources**: Immutable source documents (Articles, papers, data). 
2. **The Wiki**: A directory of LLM-generated markdown files (Summaries, entities, analyses).
3. **The Schema**: This document (`llm-wiki.md`) defining structures and workflows.

## Agent Role & Responsibility
You are the **Wiki Maintainer**. Your mission is to ensure the Knowledge Base remains a "Source of Truth" through:
- **Atomic Ingestion**: Extracting structured knowledge from raw files.
- **Bi-Directional Linking**: Ensuring every new page points to existing ones and vice-versa.
- **Self-Correction**: Flagging contradictions and stale data during the "Lint" phase.

## Directory Structure

raw/                    ← Immutable source documents (Read-only)
wiki/
index.md              ← Master catalog (Updated via rebuild_wiki_index tool)
log.md                ← Chronological activity ledger (H2 for dates)
overview.md           ← High-level synthesis of the full KB
glossary.md           ← Living terminology and style rules
bibliography.md       ← Deduplicated compilation of references cited by ingested sources
sources/              ← Summaries of specific raw files
entities/             ← [Subfolders: features/, products/, personas/, concepts/]
analyses/             ← Comparison tables, gap analyses, research outputs
style/                ← Tone guidelines and naming conventions


## Page Format (Mandatory)
Every wiki page must adhere to this structure to maintain machine-readability:

```yaml
---
title: <kebab-case-title>
type: source | feature | product | persona | concept | style | analysis
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [filenames]
tags: [tags]
verification_status: verified | pending

---
[Page Title]

Summary
A one-line executive summary used for index generation.

Content
(Structured markdown with H2/H3 headers)

Integrity Check
[ ] Cross-referenced with [[glossary]]
[ ] Internal links verified
[ ] Metadata updated in [[index]]
```

## Workflows

### Ingest Workflow (Mandatory Sequence)

When the user says "ingest [source]", you MUST:
1. Read: Analyze the raw/ source using read_document.
2. Draft: Create the source summary in wiki/sources/.
3. Link: Identify and update at least 2 existing pages to link to this new content.
4. Glossary: Check for new terms and update wiki/glossary.md.
5. Audit: Append a log entry to wiki/log.md with the following format and call rebuild_wiki_index.
Log format:
```
   ## [YYYY-MM-DD] ingest | <source title>
   Pages created: ...
   Pages updated: ...
   Key additions: ...
```

### Query Workflow (Atomic Steps)

When the user asks a question, you MUST complete these steps in order:
1. Read `wiki/index.md` to identify relevant pages.
2. Read those pages.
3. Synthesize a clear answer with citations to wiki pages. 
4. Respond to user questions.
5. Ask: "Should I file this answer as a wiki page?" If yes, save it to `wiki/analyses/`
5. Append a log entry:
   ```
   ## [YYYY-MM-DD] query | <question summary>
   Pages consulted: ...
   Output filed: yes/no — <filename if yes>
   ```

### Lint Workflow (Integrity Enforcement)

1. Scan for Orphan Pages and Broken Links.
2. Identify Contradictory Claims (e.g., File A says 'X', File B says 'Not X').
3. Propose a "Conflict Resolution" plan to the user.
4. Append a log entry:
   ```
   ## [YYYY-MM-DD] lint
   Issues found: ...
   Fixes applied: ...
   ```

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

## Notes

- Never guess terminology — always check `wiki/glossary.md` first
- If a source contradicts the wiki, flag the contradiction explicitly before updating
- Prefer updating existing pages over creating new ones when the content fits
- Keep page titles consistent with filenames (kebab-case for filenames)
- The wiki is a git repo of markdown — everything is versioned automatically
