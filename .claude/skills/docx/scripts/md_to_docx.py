"""
md_to_docx.py — Convert AMP North markdown drafts into brand-styled .docx.

Used by the doc-enhancer agent. Input is a markdown file produced by dd-writer
(or any compatible source); output is a Word document styled per the AMP brand
guidelines documented in .claude/agents/doc-enhancer.md.

Usage:
    python md_to_docx.py <input.md> <output.docx>

Markdown subset supported:
    - YAML front-matter (between --- markers at the start)
    - Headings: # H1, ## H2, ### H3
    - Paragraphs (any non-empty line)
    - GFM tables (pipe-delimited, with --- separator row)
    - Bullets: lines starting with "- " or "* "
    - Inline **bold** and *italic*
    - [MISSING: ...], [FLAG: ...], [DATA REQUIRED] markers (highlighted yellow)

Dependencies: python-docx, pyyaml (both already in the project environment).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

# ─────────────────────────────────────────────────────────────────────────────
# Brand spec — sourced from .claude/agents/doc-enhancer.md (Brand Guidelines)
# ─────────────────────────────────────────────────────────────────────────────

PRIMARY_BLUE = RGBColor(0x0B, 0x1E, 0xEA)
VIOLET = RGBColor(0x3A, 0x0C, 0xA3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)
BORDER_GREY = "D0D0D0"
SUB_LAVENDER = "E5D4FF"  # light tint of lavender for alternating rows

FONT_FAMILY = "Calibri"

HEADING_SPEC = {
    1: {"size": Pt(20), "color": PRIMARY_BLUE, "bold": True},
    2: {"size": Pt(14), "color": VIOLET, "bold": True},
    3: {"size": Pt(11), "color": BLACK, "bold": True},
}

BODY_SIZE = Pt(10)
TABLE_HEADER_FILL = "0B1EEA"
TABLE_SUBROW_FILL = "3A0CA3"
HIGHLIGHT_MARKER_PATTERN = re.compile(r"\[(?:MISSING|FLAG|DATA REQUIRED)[^\]]*\]")
INLINE_PATTERN = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|\[(?:MISSING|FLAG|DATA REQUIRED)[^\]]*\])")


# ─────────────────────────────────────────────────────────────────────────────
# Markdown parsing
# ─────────────────────────────────────────────────────────────────────────────

def split_front_matter(text: str) -> tuple[dict, str]:
    """Strip a leading YAML front-matter block (--- ... ---) and return (meta, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta_block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    try:
        meta = yaml.safe_load(meta_block) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, body


def tokenize(body: str) -> list[dict]:
    """Walk the markdown body and emit a flat list of structural tokens.

    Token shapes:
        {"kind": "heading", "level": int, "text": str}
        {"kind": "paragraph", "text": str}
        {"kind": "bullet", "text": str}
        {"kind": "table", "header": list[str], "rows": list[list[str]]}
    """
    tokens: list[dict] = []
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not line.strip():
            i += 1
            continue

        # Heading
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            tokens.append({"kind": "heading", "level": len(m.group(1)), "text": m.group(2).strip()})
            i += 1
            continue

        # Bullet
        m = re.match(r"^[-*]\s+(.*)$", line)
        if m:
            tokens.append({"kind": "bullet", "text": m.group(1).strip()})
            i += 1
            continue

        # Table — current line and next look like GFM table
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1].lstrip()):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            rows = []
            j = i + 2  # skip header + separator
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                # pad/truncate to header width
                if len(cells) < len(header):
                    cells.extend([""] * (len(header) - len(cells)))
                rows.append(cells[:len(header)])
                j += 1
            tokens.append({"kind": "table", "header": header, "rows": rows})
            i = j
            continue

        # Paragraph — accumulate consecutive non-empty, non-special lines
        para_lines = [line]
        j = i + 1
        while j < len(lines) and lines[j].strip() and not re.match(r"^(#{1,3}\s|[-*]\s|\|)", lines[j].lstrip()):
            para_lines.append(lines[j].rstrip())
            j += 1
        tokens.append({"kind": "paragraph", "text": " ".join(para_lines).strip()})
        i = j

    return tokens


# ─────────────────────────────────────────────────────────────────────────────
# Brand-styled docx assembly (python-docx)
# ─────────────────────────────────────────────────────────────────────────────

def shade_cell(cell, fill_hex: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    tc_pr.append(shd)


def set_cell_borders(cell, color: str = BORDER_GREY) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_borders = OxmlElement("w:tcBorders")
    for edge in ("top", "bottom"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:color"), color)
        tc_borders.append(b)
    for edge in ("left", "right"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "nil")
        tc_borders.append(b)
    tc_pr.append(tc_borders)


def add_inline_runs(paragraph, text: str, base_color: RGBColor = BLACK) -> None:
    """Split text into runs, applying bold/italic and yellow-highlighting flag markers."""
    if not text:
        return
    parts = INLINE_PATTERN.split(text)
    for part in parts:
        if not part:
            continue
        run = paragraph.add_run()
        run.font.name = FONT_FAMILY
        run.font.size = BODY_SIZE
        run.font.color.rgb = base_color

        if part.startswith("**") and part.endswith("**") and len(part) >= 4:
            run.text = part[2:-2]
            run.bold = True
        elif part.startswith("*") and part.endswith("*") and len(part) >= 2 and not part.startswith("**"):
            run.text = part[1:-1]
            run.italic = True
        elif HIGHLIGHT_MARKER_PATTERN.fullmatch(part):
            run.text = part
            highlight = OxmlElement("w:highlight")
            highlight.set(qn("w:val"), "yellow")
            run._element.get_or_add_rPr().append(highlight)
            run.bold = True
        else:
            run.text = part


def add_heading(doc, level: int, text: str) -> None:
    spec = HEADING_SPEC[level]
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = FONT_FAMILY
    run.font.size = spec["size"]
    run.font.color.rgb = spec["color"]
    run.bold = spec["bold"]
    p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(6)


def add_paragraph(doc, text: str) -> None:
    p = doc.add_paragraph()
    add_inline_runs(p, text)


def add_bullet(doc, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    add_inline_runs(p, text)


def add_table(doc, header: list[str], rows: list[list[str]]) -> None:
    if not header:
        return
    table = doc.add_table(rows=1, cols=len(header))
    table.autofit = True

    # Header row
    hdr = table.rows[0].cells
    for i, label in enumerate(header):
        cell = hdr[i]
        cell.text = ""
        shade_cell(cell, TABLE_HEADER_FILL)
        set_cell_borders(cell)
        p = cell.paragraphs[0]
        run = p.add_run(label)
        run.font.name = FONT_FAMILY
        run.font.size = BODY_SIZE
        run.font.color.rgb = WHITE
        run.bold = True
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    # Body rows
    for r_idx, row in enumerate(rows):
        cells = table.add_row().cells
        # Heuristic: a row with content only in column 0 acts as a sub-category divider — render as violet sub-row.
        non_empty = [c for c in row if c.strip()]
        is_subrow = len(non_empty) == 1 and row[0].strip()
        for c_idx, value in enumerate(row):
            cell = cells[c_idx]
            cell.text = ""
            set_cell_borders(cell)
            if is_subrow:
                shade_cell(cell, TABLE_SUBROW_FILL)
                run_color = WHITE
                bold = True
            elif r_idx % 2 == 1:
                shade_cell(cell, SUB_LAVENDER)
                run_color = BLACK
                bold = False
            else:
                run_color = BLACK
                bold = False
            p = cell.paragraphs[0]
            add_inline_runs(p, value, base_color=run_color)
            if bold:
                for run in p.runs:
                    run.bold = True

    doc.add_paragraph()  # breathing room after the table


def add_header_block(doc, meta: dict) -> None:
    """Render the YAML front-matter as a document header block."""
    if not meta:
        return
    title = meta.get("title")
    if title:
        add_heading(doc, 1, str(title))

    fields = [
        ("Document", meta.get("title")),
        ("Series", meta.get("series")),
        ("Portfolios", ", ".join(meta.get("modelids", [])) if isinstance(meta.get("modelids"), list) else meta.get("modelids")),
        ("Prepared by", meta.get("author")),
        ("Author title", meta.get("author_title")),
        ("Date", meta.get("date")),
        ("Status", meta.get("status")),
    ]
    rows = [[label, str(value)] for label, value in fields if value]
    if rows:
        table = doc.add_table(rows=len(rows), cols=2)
        for i, (label, value) in enumerate(rows):
            for j, text in enumerate((label, value)):
                cell = table.rows[i].cells[j]
                cell.text = ""
                set_cell_borders(cell)
                p = cell.paragraphs[0]
                run = p.add_run(text)
                run.font.name = FONT_FAMILY
                run.font.size = BODY_SIZE
                if j == 0:
                    run.bold = True
        doc.add_paragraph()

    missing = meta.get("missing")
    if missing:
        add_heading(doc, 3, "Outstanding data items")
        for item in missing:
            add_bullet(doc, f"[MISSING: {item}]" if not str(item).startswith("[MISSING") else str(item))
        doc.add_paragraph()


def render(meta: dict, tokens: list[dict], output_path: Path) -> None:
    doc = Document()

    # Default body font
    style = doc.styles["Normal"]
    style.font.name = FONT_FAMILY
    style.font.size = BODY_SIZE

    add_header_block(doc, meta)

    for tok in tokens:
        if tok["kind"] == "heading":
            add_heading(doc, tok["level"], tok["text"])
        elif tok["kind"] == "paragraph":
            add_paragraph(doc, tok["text"])
        elif tok["kind"] == "bullet":
            add_bullet(doc, tok["text"])
        elif tok["kind"] == "table":
            add_table(doc, tok["header"], tok["rows"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: python md_to_docx.py <input.md> <output.docx>", file=sys.stderr)
        return 2

    src = Path(argv[1])
    dst = Path(argv[2])

    if not src.exists():
        print(f"ERROR: input file not found: {src}", file=sys.stderr)
        return 1

    text = src.read_text(encoding="utf-8")
    meta, body = split_front_matter(text)
    tokens = tokenize(body)
    render(meta, tokens, dst)

    print(f"Wrote {dst}")
    print(f"  headings: {sum(1 for t in tokens if t['kind'] == 'heading')}")
    print(f"  paragraphs: {sum(1 for t in tokens if t['kind'] == 'paragraph')}")
    print(f"  tables: {sum(1 for t in tokens if t['kind'] == 'table')}")
    print(f"  bullets: {sum(1 for t in tokens if t['kind'] == 'bullet')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
