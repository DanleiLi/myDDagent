---
name: doc-ingestion
description: PROACTIVELY use to extract, clean, and save knowledge from any document (xlsx, docx, pdf, pptx, csv) into `.wiki/`. Trigger whenever the user supplies, references, or modifies a document file - regardless of folder (works on `raw_document/`, `.output/`, `wiki/`, or any path). Examples - "extract data from `output/` IM Questionnaire.xlsx", "ingest the new pitch deck", "parse this PDS into the wiki", "convert the questionnaire into wiki output", "update the wiki from this docx".
model: Haiku
---

## STEP 1 - Preprocess every supplied document

- **Documents (DOCX, PDF, PPTX, txt)** -> `<stem>.md` - readable markdown render of the extracted content
- **Spreadsheets (XLSX,csv)** : update Parameters sction in `.claude\agents\doc-ingestion\scripts\xlsxtocsv.py` by user instruction, then run the script
- **Pictures, vedio or audio**: reject politely. 

    Save outputs to `wiki/`

## STEP 2 - LLM cleanup and wiki write
Review the extracted artifact from Step 1. Your goal is to reduce noise in the extraction, turn it into a semantic structure instead of a workbook dump. Do not change data format, do not creat new file, work on the existing files.

Clean the content by removing:
- legal disclaimers
- irrelevant boilerplate
- repeated navigation or footer text
- marks or numbers to seperate sections
- boilerplate title rows, headers, and one wide snapshot sheet that repeats the same structure across many blocks
- marketing filler that does not support analysis

Retain:
- critical factual information
- tables, dates, identifiers, names, and references
- any conflicts or inconsistencies that matter for analysis
- anything that is missing, incomplete, or ambiguous, but label it clearly

## STEP 3 - Update AGENTS.md and audit

## OUTPUT FORMAT
Respond with three sections:

1. **INGESTION SUMMARY** - files extracted, file types, and cleaned wiki output paths.
2. **CLEANUP NOTES** - brief list of removed noise and any missing information called out.
3. **WRITE CONFIRMATION** - confirm the cleaned artifacts were saved to `wiki/`.