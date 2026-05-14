'''
This script break each tab to csv. 
'''
from openpyxl import load_workbook                                                                                                                                                                                                                                                                 
import json                                                                                                                                                                                                                                                                                        
from datetime import datetime                                                                                                                                                                                                                                                                   

file_path = "raw_document/IMQuestionnaire.xlsx"
output_path = "wiki/IMQuestionnaire.clean.json"

wb = load_workbook(file_path, data_only=True)

for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]
    csv_filename = f"{sheet_name}cvt.csv"
    csv_path = os.path.join("raw_document", csv_filename)
    with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        for row in sheet.iter_rows(values_only=True):
            writer.writerow([cell if cell is not None else "" for cell in row])
    print(f"Saved CSV: {csv_path}")

cleaned_data = {
    'source_file': file_path,
    'ingestion_timestamp': datetime.now().isoformat(),
    'cleanup_timestamp': datetime.now().isoformat(),
    'document_label': 'IM Questionnaire',
    'sheets': {}
}

for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]
    rows = []
    for row in sheet.iter_rows(values_only=True):
        if any(v is not None for v in row):
            rows.append(list(row))
    cleaned_data['sheets'][sheet_name] = rows

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(cleaned_data, f, indent=2, default=str)

print(f"Saved cleaned JSON: {output_path}")

for sheet_name, content in cleaned_data['sheets'].items():
    print(f"  {sheet_name}: {len(content)} rows")