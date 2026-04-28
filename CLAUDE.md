# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This is a Claude Code agent project for automating AMP North managed portfolio onboarding documentation. It orchestrates document intake, data extraction, portfolio profiling, fee analysis, and due diligence workflows.

## Core Principles

- **Agent-First** — route work to the right specialist as early as possible.
- **Fact-Driven** — sense-check fact before trusting dataset updates.
- **Immutability** — prefer explicit state transitions over mutation.
- **Plan Before Execute** — complex changes should be broken into deliberate phases.
- **NEVER synthesize, assume, fabricate, or make up information** — if data is missing, say "missing" and ask the user.

## Skills Architecture

Skills live in `.claude/skills/<skill-name>/` with:

| Skill | Purpose |
|-------|---------|
| `portfolio-profile` | Generates comprehensive portfolio profiles from IM questionnaires |
| `fee-analysis` | Calculates portfolio fees from PDS documents and fund holdings |

| `docx` | Utilities for reading, validating, manipulating, and converting markdown→Word documents (`md_to_docx.py`) |
| `verify-abn` | Validates ABN details for responsible entities |

Each skill contains:
- `SKILL.md` — trigger description, workflow, and business rules
- `scripts/` — Python script(s) that process data and generate outputs
- `template/` — `.docx` template files that scripts populate
- `output/` — generated deliverables

## Running Scripts

### Prerequisites

Install Python dependencies:
```bash
pip install python-docx lxml openpyxl
```

### Script Commands

```bash
# Portfolio Profile Generation
python .claude/skills/portfolio-profile/scripts/generate_portfolio_profiles.py

# Fee Analysis Calculation
python .claude/skills/fee-analysis/scripts/generate_fee_analysis.py

# Markdown → brand-styled .docx (used by doc-enhancer)
python .claude/skills/docx/scripts/md_to_docx.py <input.md> <output.docx>
```

The DD paper is no longer produced by a single script — see the workflow below.

**Important:** Hardcoded paths in scripts point to `C:\Users\Sara\Downloads\AIagentproject\`. Update `BASE_DIR`, `TEMPLATE_PATH`, and `OUTPUT_DIR` constants if the project moves.

## Database Structure

```
.claude/
├── schema/
│   ├── modelportfolio.schema.json    
│   ├── IM.schema.json
│   ├── portfoliofee.schema.json
│   └── holdingfee.schema.json
│
└── dataset/
    ├── modelportfolio.json           
    ├── IM.json                       
    ├── portfoliofee.json            
    └── holdingfee.json               
```

### Key Principles

- **modelportfolio.schema.json** defines the canonical structure for all portfolio records
- Each portfolio has: `onboarding` status, `profile`, `benchmark`, `asset_allocation`, `investment_manager`, `documents`, `flags`, and `dd_outcome`
- Dataset updates are state transitions: `intake` → `document_review` → `due_diligence` → `approval` → `onboarding` → `live`

## Agents

Agents handle specialized tasks:

- **doc-ingestion** — When delegating task to this agent, always tell it which dataset you need it to update.
- **dd-writer** (`.claude/agents/doc-writer/doc-writer.md`) — Drafts the due diligence paper as a markdown file at `.claude/output/DD_<series>_<date>.md`. Reads all dataset JSON, writes narratives + GFM tables + `[MISSING:]` markers. Does **not** produce `.docx`.
- **doc-enhancer** — Reviews drafts (writing quality, fact sense-check) then applies brand styling. When the source is `.md`, runs `md_to_docx.py` to produce the brand-styled `.docx`.

## Key Commands

- `/new_project` — Reset dataset, output folders, and project memory for a new onboarding engagement
- Check `.claude/commands/new_project.md` for exact behavior

## Workflow Overview

1. **Intake** — Raw documents (questionnaires, PDFs) go into `raw_document/`
2. **Document Conversion** — doc-ingestion agent extracts data into `converted_documents/` (CSV format) and updates `.claude/dataset/`
3. **Portfolio Profiling** — `portfolio-profile` skill generates Word documents in `output/`
4. **Fee Analysis** — `fee-analysis` skill calculates fees and produces Excel workbooks
5. **DD drafting (markdown)** — `dd-writer` agent reads all dataset JSON and writes a complete board-register markdown to `.claude/output/DD_<series>_<date>.md`. Markdown is the durable, reviewable intermediate — analysts can edit it directly before styling.
6. **Brand styling and conversion** — `doc-enhancer` agent reviews the markdown for writing quality and fact integrity, then converts it via `python .claude/skills/docx/scripts/md_to_docx.py`. Final output: `.claude/output/DD_<series>_<date>.docx`.
7. **Approval** — Portfolio records updated with compliance flags and final status

## Important Notes

- All CSV conversions are stored in `converted_documents/` for audit trail
- Original PDFs and Excel files remain in `raw_document/` (never deleted)
- Output documents are versioned by date in `output/`
- The database is the source of truth for portfolio status and metadata
