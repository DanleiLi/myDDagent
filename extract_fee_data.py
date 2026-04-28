import json
from datetime import datetime

# Holdings data extracted from the Excel file
holdings_by_portfolio = {
    "Aurora Growth Managed Portfolio": [
        {"unit_id": "AAP0103", "allocation": 0.11, "management_fees": 0.0055, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.002},
        {"unit_id": "VAN0002", "allocation": 0.1, "management_fees": 0.0007, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0.0005, "sell_spread": 0.0005, "rebate": 0},
        {"unit_id": "VAN0003", "allocation": 0.1, "management_fees": 0.0018, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0.0005, "sell_spread": 0.0005, "rebate": 0},
        {"unit_id": "TGP0034", "allocation": 0.09, "management_fees": 0.00974, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.0015},
        {"unit_id": "MAQ0464", "allocation": 0.08, "management_fees": 0.0128, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.0053},
        {"unit_id": "ETL0060", "allocation": 0.07, "management_fees": 0.0077, "performance_fees": 0.205, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0},
        {"unit_id": "FID0010", "allocation": 0.07, "management_fees": 0.0115, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0.008, "sell_spread": 0.008, "rebate": 0.002},
        {"unit_id": "WHT1465", "allocation": 0.06, "management_fees": 0.0088, "performance_fees": 0.15, "cash_fee": 0, "trans_costs": 0.0003, "buy_spread": 0, "sell_spread": 0, "rebate": 0.001},
        {"unit_id": "ETL0463", "allocation": 0.06, "management_fees": 0.0107, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.002},
        {"unit_id": "MGE0005", "allocation": 0.05, "management_fees": 0.0075, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.001},
        {"unit_id": "BFL0020", "allocation": 0.05, "management_fees": 0.0087, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0.0005, "buy_spread": 0.002, "sell_spread": 0.002, "rebate": 0.0012},
        {"unit_id": "BTA0313", "allocation": 0.04, "management_fees": 0.009, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.0015},
        {"unit_id": "WHT3093", "allocation": 0.04, "management_fees": 0.0085, "performance_fees": 0.2, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.002},
        {"unit_id": "GSF0874", "allocation": 0.03, "management_fees": 0.011, "performance_fees": 0.15, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0},
        {"unit_id": "VAN0004", "allocation": 0.03, "management_fees": 0.0023, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0.0005, "sell_spread": 0.0005, "rebate": 0},
        {"unit_id": "CASHACCT", "allocation": 0.02, "management_fees": 0, "performance_fees": 0, "cash_fee": 0.014, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.0015},
    ],
    "Aurora Defensive Managed Portfolio": [
        {"unit_id": "BTA8657", "allocation": 0.11, "management_fees": 0.0035, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0.0011, "buy_spread": 0.003, "sell_spread": 0.003, "rebate": 0.0015},
        {"unit_id": "FRT0027", "allocation": 0.13, "management_fees": 0.005, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.001},
        {"unit_id": "UBS0003", "allocation": 0.11, "management_fees": 0.006, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.0015},
        {"unit_id": "SCH0028", "allocation": 0.13, "management_fees": 0.0045, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.0017},
        {"unit_id": "ETL0016", "allocation": 0.2, "management_fees": 0.0056, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.0005},
        {"unit_id": "MAQ3897", "allocation": 0.07, "management_fees": 0.00614, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0.0082, "sell_spread": 0.0082, "rebate": 0},
        {"unit_id": "CSA0038", "allocation": 0.11, "management_fees": 0.0077, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0.0005, "buy_spread": 0, "sell_spread": 0, "rebate": 0.0025},
        {"unit_id": "WPC1583", "allocation": 0.12, "management_fees": 0.0075, "performance_fees": 0, "cash_fee": 0, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.0015},
        {"unit_id": "CASHACCT", "allocation": 0.02, "management_fees": 0, "performance_fees": 0, "cash_fee": 0.014, "trans_costs": 0, "buy_spread": 0, "sell_spread": 0, "rebate": 0.0015},
    ]
}

# Function to calculate weighted average fees
def calc_weighted_fee(holdings, fee_type):
    total = sum(h['allocation'] * h[fee_type] for h in holdings)
    return round(total, 6)

# Build portfoliofee.json
portfolio_fee_data = {
    "_meta": {
        "schema_version": "1.0",
        "description": "Portfolio fee data extracted from Fee Analysis Excel",
        "source": "output/Fee Analysis - Aurora - 20260427.xlsx",
        "extracted_date": "2026-04-27"
    },
    "portfolios": [
        {
            "modelid": "NTH0620",
            "portfolio_name": "Aurora Growth Managed Portfolio",
            "fees": {
                "investment_management_fee": None,
                "estimated_underlying_management_fees_and_costs": calc_weighted_fee(holdings_by_portfolio["Aurora Growth Managed Portfolio"], "management_fees"),
                "estimated_managed_portfolio_cash_investment_fee": calc_weighted_fee(holdings_by_portfolio["Aurora Growth Managed Portfolio"], "cash_fee"),
                "performance_fee": None,
                "estimated_underlying_performance_fee": calc_weighted_fee(holdings_by_portfolio["Aurora Growth Managed Portfolio"], "performance_fees"),
                "estimated_gross_transaction_costs": calc_weighted_fee(holdings_by_portfolio["Aurora Growth Managed Portfolio"], "trans_costs"),
                "estimated_underlying_buy_spread": calc_weighted_fee(holdings_by_portfolio["Aurora Growth Managed Portfolio"], "buy_spread"),
                "estimated_underlying_sell_spread": calc_weighted_fee(holdings_by_portfolio["Aurora Growth Managed Portfolio"], "sell_spread"),
            },
            "flags": []
        },
        {
            "modelid": None,
            "portfolio_name": "Aurora Defensive Managed Portfolio",
            "fees": {
                "investment_management_fee": None,
                "estimated_underlying_management_fees_and_costs": calc_weighted_fee(holdings_by_portfolio["Aurora Defensive Managed Portfolio"], "management_fees"),
                "estimated_managed_portfolio_cash_investment_fee": calc_weighted_fee(holdings_by_portfolio["Aurora Defensive Managed Portfolio"], "cash_fee"),
                "performance_fee": None,
                "estimated_underlying_performance_fee": calc_weighted_fee(holdings_by_portfolio["Aurora Defensive Managed Portfolio"], "performance_fees"),
                "estimated_gross_transaction_costs": calc_weighted_fee(holdings_by_portfolio["Aurora Defensive Managed Portfolio"], "trans_costs"),
                "estimated_underlying_buy_spread": calc_weighted_fee(holdings_by_portfolio["Aurora Defensive Managed Portfolio"], "buy_spread"),
                "estimated_underlying_sell_spread": calc_weighted_fee(holdings_by_portfolio["Aurora Defensive Managed Portfolio"], "sell_spread"),
            },
            "flags": []
        }
    ]
}

# Build holdingfee.json
holding_fee_data = {
    "_meta": {
        "schema_version": "1.0",
        "description": "Holding-level fee data extracted from Fee Analysis Excel",
        "source": "output/Fee Analysis - Aurora - 20260427.xlsx",
        "extracted_date": "2026-04-27"
    },
    "holdings": []
}

for portfolio_name, holdings in holdings_by_portfolio.items():
    for holding in holdings:
        holding_fee_data["holdings"].append({
            "portfolio_name": portfolio_name,
            "unit_id": holding["unit_id"],
            "allocation_percent": holding["allocation"],
            "fees": {
                "management_fees_and_costs": holding["management_fees"],
                "cash_investment_fee": holding["cash_fee"],
                "performance_fees": holding["performance_fees"],
                "gross_transaction_costs": holding["trans_costs"],
                "buy_spread": holding["buy_spread"],
                "sell_spread": holding["sell_spread"],
                "rebate": holding["rebate"]
            }
        })

# Write files
with open(r".claude/dataset/portfoliofee.json", "w") as f:
    json.dump(portfolio_fee_data, f, indent=2)

with open(r".claude/dataset/holdingfee.json", "w") as f:
    json.dump(holding_fee_data, f, indent=2)

print("[OK] Extracted 25 holdings across 2 portfolios")
print("[OK] Updated .claude/dataset/portfoliofee.json")
print("[OK] Updated .claude/dataset/holdingfee.json")
