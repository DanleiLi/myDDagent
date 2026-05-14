#!/usr/bin/env python3
"""
File Format Converter
Converts documents (doc/docx/pptx/pdf/txt) to markdown
and spreadsheets (xlsx/csv) to JSON
"""

import sys
import json
import os
from pathlib import Path
from typing import Union, Dict, List, Any

def convert_file(input_path: str, output_format: str = None) -> str:
    """
    Convert a file from one format to another.
    
    Args:
        input_path: Path to the input file
        output_format: Target format (md or json). If None, infers from input file type.
        
    Returns:
        Path to the converted file
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Detect file type
    file_ext = input_path.suffix.lower()
    
    # Infer output format if not specified
    if output_format is None:
        if file_ext in ['.doc', '.docx', '.pptx', '.pdf', '.txt']:
            output_format = 'md'
        elif file_ext in ['.xlsx', '.xlsm', '.csv', '.tsv']:
            output_format = 'json'
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    # Route to appropriate converter
    if output_format.lower() == 'md':
        return convert_to_markdown(input_path)
    elif output_format.lower() == 'json':
        return convert_to_json(input_path)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def convert_to_markdown(input_path: Path) -> str:
    """Convert document to markdown."""
    from converters.document_converter import DocumentConverter
    
    converter = DocumentConverter()
    output_path = converter.convert(input_path)
    return str(output_path)


def convert_to_json(input_path: Path) -> str:
    """Convert spreadsheet to JSON."""
    from converters.spreadsheet_converter import SpreadsheetConverter
    
    converter = SpreadsheetConverter()
    output_path = converter.convert(input_path)
    return str(output_path)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python converter.py <input_file> [output_format]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = convert_file(input_file, output_format)
        print(f"✓ Conversion successful: {result}")
    except Exception as e:
        print(f"✗ Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)
