'''
This script reads an XLSX and saves each visible worksheet as a CSV in wiki/.
'''

import os
import csv
import json
from datetime import datetime
from openpyxl import load_workbook

file_path = "raw_document/IMQuestionnaire.xlsx"
output_dir = "wiki"
metadata_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}.json"
doc_label = 'IM Questionnaire'

os.makedirs(output_dir, exist_ok=True)

cleaned_data = {
    'source_file': file_path,
    'ingestion_timestamp': datetime.now().isoformat(),
    'cleanup_timestamp': datetime.now().isoformat(),
    'document_label': doc_label,
    'sheets': {}
}


def sanitize_sheet_name(name):
    safe_name = ''.join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in name).strip()
    safe_name = safe_name.replace(' ', '_')
    return safe_name or 'sheet'


def read_csv_file(path):
    rows = []
    with open(path, 'r', newline='', encoding='utf-8-sig') as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            rows.append([cell if cell is not None else '' for cell in row])
    return rows


if file_path.lower().endswith('.csv'):
    sheet_name = os.path.splitext(os.path.basename(file_path))[0]
    cleaned_data['sheets'][sheet_name] = read_csv_file(file_path)
else:
    wb = load_workbook(file_path, data_only=True)
    for sheet in wb.worksheets:
        if sheet.sheet_state != 'visible':
            continue

        sheet_name = sheet.title
        rows = []
        for row in sheet.iter_rows(values_only=True):
            rows.append([cell if cell is not None else '' for cell in row])
        cleaned_data['sheets'][sheet_name] = rows

for sheet_name, rows in cleaned_data['sheets'].items():
    safe_name = sanitize_sheet_name(sheet_name)
    csv_filename = f"{safe_name}.csv"
    csv_path = os.path.join(output_dir, csv_filename)

    with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        for row in rows:
            writer.writerow(row)

    print(f"Saved CSV: {csv_path}")

metadata_path = os.path.join(output_dir, metadata_filename)
with open(metadata_path, 'w', encoding='utf-8') as f:
    json.dump(cleaned_data, f, indent=2, default=str)

print(f"Saved cleaned JSON: {metadata_path}")
for sheet_name, content in cleaned_data['sheets'].items():
    print(f"  {sheet_name}: {len(content)} rows")