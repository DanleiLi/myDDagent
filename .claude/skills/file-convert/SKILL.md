---
name: file-convert
description: convert files to markdown
---
The agent converts a complex file to clean, readable markdown file.

# Workflow
1. is the file a supported file type?

Support file types: .doc, .docx, .pptx, .pdf, .txt, .xlsx, .xlsm, .csv, .tsv

When user procides picture, video, and audio files, reject politely.

## Versioning / Re-ingestion
Overwriting is now hash-gated and automatic. The script computes SHA256 of the source file and checks `.claude/wiki/manifest.json`:
- If the hash matches an existing entry → no change detected, file is skipped
- If the hash differs or is not in manifest → source file has changed, wiki file is overwritten and manifest is updated

No manual user prompts needed. Re-ingestion is idempotent — running the script twice on the same source does nothing the second time.

## Knowledge Index Auto-Population
After each conversion, append one line to the Knowledge Index section of `CLAUDE.md`:
```
- .claude/wiki/{filename}.md | category_tag(s) | 0-50 word summary
```

Example:
```
- .claude/wiki/IMQuestionnaire_SAA.md | strategic_asset_allocation | SAA min/target/max per asset class for all portfolios in the series
- .claude/wiki/holdings.md | holdings | Portfolio holdings, allocation weights, and unit IDs
```

2.  When ingesting files, run directly via Bash:
  `python .claude\skills\file-convert\scripts\alltomd.py <input_file>`

3. Report success or failure of the conversion and invoke data_auditor to check the quality of the converted file.