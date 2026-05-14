'''
This script extract North manage portfolio key information from factsheets PDF.

'''

import pdfplumber
import pandas as pd
from pathlib import Path
import re

pdf_dir = Path(r"C:\Users\Sara\Downloads\AIagentproject\raw_document")

factsheets = [
    "iShares_Enhanced_Strategic_Aggressive_Monthly_Factsheet.pdf",
    "iShares_Enhanced_Strategic_All Growth_Monthly_Factsheet.pdf",
    "iShares_Enhanced_Strategic_Balanced_Monthly_Factsheet.pdf",
    "iShares_Enhanced_Strategic_Conservative_Monthly_Factsheet.pdf",
    "iShares_Enhanced_Strategic_Growth_Monthly_Factsheet.pdf",
    "iShares_Enhanced_Strategic_Moderate_Monthly_Factsheet.pdf",
]

extracted_data = []

for factsheet in factsheets:
    pdf_path = pdf_dir / factsheet
    
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        continue
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            
            # Extract fields from the text
            fund_name = re.search(r'ISHARES ENHANCED STRATEGIC (\w+)', text)
            fund_name = fund_name.group(1) if fund_name else "N/A"
            
            # Extract Code
            code_match = re.search(r'Code\s+([A-Z0-9_]+)', text)
            code = code_match.group(1) if code_match else "N/A"
            
            # Extract Benchmark
            benchmark_match = re.search(r'Benchmark\s+(.+?)(?=Manager name|Asset class)', text, re.DOTALL)
            benchmark = benchmark_match.group(1).strip() if benchmark_match else "N/A"
            benchmark = ' '.join(benchmark.split())  # Clean up whitespace
            
            # Extract Asset class
            asset_class_match = re.search(r'Asset class\s+(\w+)', text)
            asset_class = asset_class_match.group(1) if asset_class_match else "N/A"
            
            # Extract Minimum investment horizon
            horizon_match = re.search(r'Minimum investment horizon\s+([^\n]+)', text)
            min_horizon = horizon_match.group(1).strip() if horizon_match else "N/A"
            
            # Extract Portfolio income
            income_match = re.search(r'Portfolio income\s+([^\n]+)', text)
            portfolio_income = income_match.group(1).strip() if income_match else "N/A"
            if portfolio_income == "":
                income_match = re.search(r'Portfolio income\s+(\w+\s*-\s*\w+)', text)
                portfolio_income = income_match.group(1) if income_match else "N/A"
            
            # Extract Risk band/label
            risk_match = re.search(r'Risk band/label\s+(.+?)(?=as at)', text)
            risk_label = risk_match.group(1).strip() if risk_match else "N/A"
            
            # Extract Investment objective
            obj_match = re.search(r'Investment objective\s+(.+?)(?=inception)', text, re.DOTALL)
            investment_objective = obj_match.group(1).strip() if obj_match else "N/A"
            if investment_objective != "N/A":
                investment_objective = investment_objective.replace('\n', ' ')
            
            extracted_data.append({
                'Fund Name': fund_name,
                'Code': code,
               'Benchmark': benchmark,
                'Asset Class': asset_class,
                'Minimum Investment Horizon': min_horizon,
                'Portfolio Income': portfolio_income,
                'Risk Band/Label': risk_label,
                'Investment Objective': investment_objective,
                #'Source File': factsheet
            })
            
            print(f"✓ Extracted: {fund_name}")
            
    except Exception as e:
        print(f"✗ Error processing {factsheet}: {e}")

# Create DataFrame and save to Excel
if extracted_data:
    df = pd.DataFrame(extracted_data)
    output_path = pdf_dir.parent / "Factsheets_Extracted_Data.xlsx"
    df.to_excel(output_path, index=False, sheet_name='Factsheet Data')
    print(f"\n✓ Data saved to: {output_path}")
    print("\nExtracted Data:")
    print(df.to_string())
else:
    print("No data extracted.")