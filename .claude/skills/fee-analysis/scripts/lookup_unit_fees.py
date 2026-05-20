"""
Lookup unit fee data from CSV reference file.

Usage:
  python lookup_unit_fees.py <unit_id_1> <unit_id_2> ...

  Searches .claude/skills/fee-analysis/references/UnitFee.csv for each unit ID.
  Returns JSON with found units (fee data) and missing units (for manual lookup).

Example:
  python lookup_unit_fees.py VAS GLIN IVV UNKNOWN

Output (JSON):
  {
    "found": {
      "VAS": {
        "unit_id": "VAS",
        "unit_name": "iShares Core S&P/ASX 200 ETF",
        "mgmt": 0.0008,
        "cash_inv": 0.0,
        ...
      }
    },
    "missing": ["UNKNOWN"]
  }
"""

import sys
import json
import csv
import os
from pathlib import Path

def load_unit_fee_csv():
    """Load the UnitFee.csv reference file."""
    script_dir = Path(__file__).parent
    csv_path = script_dir.parent / 'references' / 'UnitFee.csv'

    if not csv_path.exists():
        raise FileNotFoundError(f"UnitFee.csv not found at {csv_path}")

    units = {}
    with open(csv_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)
        for row in reader:
            unit_id = row.get('Unit ID', '').strip()
            if unit_id:  # Skip empty rows
                units[unit_id] = row

    return units

def convert_percentage_str(pct_str):
    """Convert percentage string (e.g., '0.07%') to fee value (0.07)."""
    if not pct_str or pct_str.strip() == '':
        return 0.0
    # Remove '%' and convert to float (CSV "0.07%" -> 0.07)
    # generate_fee_analysis.py divides by 100, so store as-is
    return float(pct_str.replace('%', '').strip())

def lookup_units(unit_ids):
    """
    Lookup fee data for given unit IDs.
    Returns dict with 'found' and 'missing' keys.
    """
    units = load_unit_fee_csv()

    found = {}
    missing = []

    for unit_id in unit_ids:
        unit_id = unit_id.strip().upper()

        if unit_id in units:
            row = units[unit_id]
            found[unit_id] = {
                'unit_id': unit_id,
                'unit_name': row['Unit Name'],
                'mgmt': convert_percentage_str(row['Management fees and costs %']),
                'cash_inv': convert_percentage_str(row['Cash investment fee %']),
                'perf': convert_percentage_str(row['Performance fees %']),
                'transaction': convert_percentage_str(row['Gross transaction costs %']),
                'buy_spread': convert_percentage_str(row['Buy spread %']),
                'sell_spread': convert_percentage_str(row['Sell spread %']),
                'rebate': convert_percentage_str(row['Rebate %']),
                'pds_url': row['PDS URL'].strip() if row['PDS URL'] else '',
            }
        else:
            missing.append(unit_id)

    return {
        'found': found,
        'missing': missing,
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Error: Usage: python lookup_unit_fees.py <unit_id_1> <unit_id_2> ...")
        sys.exit(1)

    unit_ids = sys.argv[1:]
    result = lookup_units(unit_ids)
    print(json.dumps(result, indent=2))
