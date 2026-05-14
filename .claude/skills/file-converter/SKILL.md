---
name: file-converter
description: Convert documents and data files between formats. Use this skill whenever the user wants to convert .doc, .docx, .pptx, .pdf, .txt files to Markdown (.md), or convert spreadsheet files (.xlsx, .csv) to JSON (.json). Trigger on explicit format conversion requests, bulk file transformation workflows, or when the user mentions needing a different file format for their data. Always use this skill for any document/data format conversion task.
compatibility: Requires python-docx, python-pptx, PyPDF2, pandas, openpyxl
---

# File Converter Skill

Converts documents and spreadsheets between common formats with intelligent handling of structure and content.

## Supported Conversions

### Documents → Markdown
- **Word Documents** (.doc, .docx) → .md
  - Preserves heading hierarchy, bold/italic formatting, lists, tables
  - Embeds images as base64 or file references
  - Maintains document structure

- **PowerPoint Presentations** (.pptx) → .md
  - Creates sections for each slide with slide titles as headers
  - Captures text content, bullet points, and speaker notes
  - Includes slide number references

- **PDF Documents** (.pdf) → .md
  - Extracts text content and structure
  - Handles scanned PDFs via OCR (when available)
  - Attempts to preserve headings and paragraphs

- **Plain Text** (.txt) → .md
  - Minimal conversion (mostly pass-through with basic markdown syntax)
  - Useful for consistency in workflows

### Spreadsheets → JSON
- **Excel Files** (.xlsx, .xlsm) → .json
  - Converts each sheet to separate JSON file
  - Cleans and validates output with metadata
  - Detects headers from first row
  - Removes empty rows and trailing empty columns
  - Normalizes data types consistently per column
  - File naming: `filename_SheetName.json` for each sheet
  - Output includes quality metrics and row count statistics

- **CSV Files** (.csv, .tsv) → .json
  - Parses CSV/TSV with proper delimiter detection
  - Headers become object keys
  - Removes empty rows and cleans whitespace
  - Normalizes data types across columns
  - Includes cleanup metadata in output

  Voice, picture, video, and audio files are not supported for conversion. Please provide a document or spreadsheet file for conversion.

## Usage

### Basic Conversion
The skill handles file conversion automatically. Simply:
1. Provide the input file path
2. Specify desired output format (or let the skill infer from context)
3. The skill converts and saves to output directory

### Options
- **Preserve Structure**: For documents, maintain heading levels and hierarchy (default: yes)
- **Include Images**: For document conversions, embed images or save separately (default: embed as base64)
- **Data Types**: For CSV→JSON, attempt to infer types (numbers, dates) vs treat all as strings (default: infer)

## Implementation Notes

### Document Conversion Process
1. **Parse** input file to extract content and structure
2. **Transform** elements to markdown equivalents
3. **Format** with proper markdown syntax
4. **Validate** output for correctness

### Spreadsheet Conversion Process
1. **Load** spreadsheet with header detection
2. **Convert** each row to object using headers as keys
3. **Type-cast** values when appropriate
4. **Clean** the data:
   - Remove empty rows (all values are None)
   - Trim whitespace from string values
   - Remove columns that are entirely empty
   - Normalize data types consistently per column
5. **Validate** output and calculate quality metrics
6. **Serialize** to JSON with metadata (row counts, quality score, column info)

## Error Handling
Review the extracted artifact. Your goal is to reduce noise in the extraction, turn it into a semantic structure instead of a workbook dump. Do not change data format, do not creat new file, work on the existing files.

The skill handles:
- Missing or corrupted files → clear error messages
- Unsupported file types → informative feedback
- Encoding issues in text files → automatic detection and conversion
- Complex formatting → best-effort preservation with fallbacks

## Output Paths

Converted files are saved to:
- `.claude/wiki/<original_filename>.<new_extension>`

Example: `report.docx` → `report.md`, `data.xlsx` → `data_SheetName.json`

## JSON Output Format

For spreadsheet conversions, JSON files include two top-level keys:

```json
{
  "data": [
    {"column1": "value", "column2": 42, ...},
    ...
  ],
  "metadata": {
    "original_count": 1500,
    "cleaned_count": 1480,
    "rows_removed": 20,
    "columns": ["column1", "column2", ...],
    "column_count": 5,
    "flags": ["Missing ABN", "Missing benchmark", ...],
  }
}
```

- **data**: Array of cleaned records
- **metadata**: 
  - `flags`: List of any issues detected during cleanup (e.g. missing critical fields)