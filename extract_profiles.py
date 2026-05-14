import json
from datetime import datetime
import os

# Manual extraction from the CSV structure
profile_config = {
    'Conservative': {
        'name': 'iShares Enhanced Strategic Conservative',
        'min_investment_options': '12 investment options across Australian equities, global equities, fixed income, listed property, infrastructure and cash',
        'max_investment_options': '28 investment options across Australian and international growth and defensive asset classes',
        'min_single_position': 0.0075,
        'max_single_position': 0.18,
        'min_new_position': 0.01,
        'target_volatility': '8.5% to 10.5% annualised volatility target range',
        'income_default': 'Reinvested',
        'min_cash_buffer': 0.015,
        'trading_preference': 'Active',
        'expected_turnover_pa': '25% to 40%',
        'active_stock_limits': '+/- 8%',
        'active_gics_limits': '+/- 12%',
        'tracking_error_target': '2.0% to 3.5%',
        'outperformance_target': 'CPI + 3.0% p.a. over rolling 7 years',
        'benchmark': 'Morningstar Australia Conservative Target Allocation NR AUD',
        'asset_class': 'Diversified',
        'min_investment_horizon': '3 years',
        'portfolio_income': 'Default - Reinvest',
        'risk_band': '3/Low to medium',
        'investment_objective': 'To match or outperform the benchmark over a rolling five-year period'
    },
    'Moderate': {
        'name': 'iShares Enhanced Moderate',
        'min_investment_options': '12 investment options across Australian equities, global equities, fixed income, listed property, infrastructure and cash',
        'max_investment_options': '28 investment options across Australian and international growth and defensive asset classes',
        'min_single_position': 0.0075,
        'max_single_position': 0.18,
        'min_new_position': 0.01,
        'target_volatility': '8.5% to 10.5% annualised volatility target range',
        'income_default': 'Reinvested',
        'min_cash_buffer': 0.015,
        'trading_preference': 'Active',
        'expected_turnover_pa': '25% to 40%',
        'active_stock_limits': '+/- 8%',
        'active_gics_limits': '+/- 12%',
        'tracking_error_target': '2.0% to 3.5%',
        'outperformance_target': 'CPI + 3.0% p.a. over rolling 7 years',
        'benchmark': 'Morningstar Australia Moderate Target Allocation NR AUD',
        'asset_class': 'Diversified',
        'min_investment_horizon': '5 years',
        'portfolio_income': 'Default - Reinvest',
        'risk_band': '4/Medium',
        'investment_objective': 'To match or outperform the benchmark over a rolling five-year period'
    },
    'Balanced': {
        'name': 'iShares Enhanced Balanced',
        'min_investment_options': '12 investment options across Australian equities, global equities, fixed income, listed property, infrastructure and cash',
        'max_investment_options': '28 investment options across Australian and international growth and defensive asset classes',
        'min_single_position': 0.0075,
        'max_single_position': 0.18,
        'min_new_position': 0.01,
        'target_volatility': '8.5% to 10.5% annualised volatility target range',
        'income_default': 'Reinvested',
        'min_cash_buffer': 0.015,
        'trading_preference': 'Active',
        'expected_turnover_pa': '25% to 40%',
        'active_stock_limits': '+/- 8%',
        'active_gics_limits': '+/- 12%',
        'tracking_error_target': '2.0% to 3.5%',
        'outperformance_target': 'CPI + 3.0% p.a. over rolling 7 years',
        'benchmark': 'Morningstar Australia Balanced Target Allocation NR AUD',
        'asset_class': 'Diversified',
        'min_investment_horizon': '5 years',
        'portfolio_income': 'Default - Reinvest',
        'risk_band': '4/Medium',
        'investment_objective': 'To match or outperform the benchmark over a rolling five-year period'
    },
    'Growth': {
        'name': 'iShares Enhanced Growth',
        'min_investment_options': '12 investment options across Australian equities, global equities, fixed income, listed property, infrastructure and cash',
        'max_investment_options': '28 investment options across Australian and international growth and defensive asset classes',
        'min_single_position': 0.0075,
        'max_single_position': 0.18,
        'min_new_position': 0.01,
        'target_volatility': '8.5% to 10.5% annualised volatility target range',
        'income_default': 'Reinvested',
        'min_cash_buffer': 0.015,
        'trading_preference': 'Active',
        'expected_turnover_pa': '25% to 40%',
        'active_stock_limits': '+/- 8%',
        'active_gics_limits': '+/- 12%',
        'tracking_error_target': '2.0% to 3.5%',
        'outperformance_target': 'CPI + 3.0% p.a. over rolling 7 years',
        'benchmark': 'Morningstar Australia Growth Target Allocation NR AUD',
        'asset_class': 'Diversified',
        'min_investment_horizon': '5 years',
        'portfolio_income': 'Default - Reinvest',
        'risk_band': '5/Medium to high',
        'investment_objective': 'To match or outperform the benchmark over a rolling five-year period'
    },
    'Aggressive': {
        'name': 'iShares Enhanced Aggressive',
        'min_investment_options': '12 investment options across Australian equities, global equities, fixed income, listed property, infrastructure and cash',
        'max_investment_options': '28 investment options across Australian and international growth and defensive asset classes',
        'min_single_position': 0.0075,
        'max_single_position': 0.18,
        'min_new_position': 0.01,
        'target_volatility': '8.5% to 10.5% annualised volatility target range',
        'income_default': 'Reinvested',
        'min_cash_buffer': 0.015,
        'trading_preference': 'Active',
        'expected_turnover_pa': '25% to 40%',
        'active_stock_limits': '+/- 8%',
        'active_gics_limits': '+/- 12%',
        'tracking_error_target': '2.0% to 3.5%',
        'outperformance_target': 'CPI + 3.0% p.a. over rolling 7 years',
        'benchmark': 'Morningstar Australia Aggressive Target Allocation NR AUD',
        'asset_class': 'Diversified',
        'min_investment_horizon': '5 years',
        'portfolio_income': 'Default - Reinvest',
        'risk_band': '6/High',
        'investment_objective': 'To match or outperform the benchmark over a rolling five-year period'
    },
    'All Growth': {
        'name': 'iShares Enhanced All Growth',
        'min_investment_options': '12 investment options across Australian equities, global equities, fixed income, listed property, infrastructure and cash',
        'max_investment_options': '28 investment options across Australian and international growth and defensive asset classes',
        'min_single_position': 0.0075,
        'max_single_position': 0.18,
        'min_new_position': 0.01,
        'target_volatility': '8.5% to 10.5% annualised volatility target range',
        'income_default': 'Reinvested',
        'min_cash_buffer': 0.015,
        'trading_preference': 'Active',
        'expected_turnover_pa': '25% to 40%',
        'active_stock_limits': '+/- 8%',
        'active_gics_limits': '+/- 12%',
        'tracking_error_target': '2.0% to 3.5%',
        'outperformance_target': 'CPI + 3.0% p.a. over rolling 7 years',
        'benchmark': 'Morningstar Australia Aggressive Target Allocation NR AUD',
        'asset_class': 'Diversified',
        'min_investment_horizon': '5 years',
        'portfolio_income': 'Default - Reinvest',
        'risk_band': '6/High',
        'investment_objective': 'To match or outperform the benchmark over a rolling five-year period'
    }
}

# SAA data - Strategic Asset Allocation
saa_data = {
    'Conservative': {
        'Growth': {
            'Australian Equities': {'min': 0.0, 'max': 0.40},
            'International Equities': {'min': 0.0, 'max': 0.45},
            'Domestic Property and Infrastructure': {'min': 0.0, 'max': 0.12},
            'International Property and Infrastructure': {'min': 0.0, 'max': 0.10},
            'Alternatives': {'min': 0.0, 'max': 0.10}
        },
        'Defensive': {
            'Australian Fixed Interest': {'min': 0.10, 'max': 0.60},
            'International Fixed Interest': {'min': 0.08, 'max': 0.60},
            'Cash (1% minimum required)': {'min': 0.01, 'max': 0.40}
        }
    },
    'Moderate': {
        'Growth': {
            'Australian Equities': {'min': 0.30, 'max': 0.45},
            'International Equities': {'min': 0.35, 'max': 0.55},
            'Domestic Property and Infrastructure': {'min': 0.0, 'max': 0.10},
            'International Property and Infrastructure': {'min': 0.0, 'max': 0.08},
            'Alternatives': {'min': 0.0, 'max': 0.10}
        },
        'Defensive': {
            'Australian Fixed Interest': {'min': 0.0, 'max': 0.40},
            'International Fixed Interest': {'min': 0.0, 'max': 0.40},
            'Cash (1% minimum required)': {'min': 0.01, 'max': 0.40}
        }
    },
    'Balanced': {
        'Growth': {
            'Australian Equities': {'min': 0.30, 'max': 0.45},
            'International Equities': {'min': 0.35, 'max': 0.55},
            'Domestic Property and Infrastructure': {'min': 0.0, 'max': 0.10},
            'International Property and Infrastructure': {'min': 0.0, 'max': 0.08},
            'Alternatives': {'min': 0.0, 'max': 0.10}
        },
        'Defensive': {
            'Australian Fixed Interest': {'min': 0.0, 'max': 0.40},
            'International Fixed Interest': {'min': 0.0, 'max': 0.30},
            'Cash (1% minimum required)': {'min': 0.01, 'max': 0.20}
        }
    },
    'Growth': {
        'Growth': {
            'Australian Equities': {'min': 0.30, 'max': 0.70},
            'International Equities': {'min': 0.35, 'max': 0.70},
            'Domestic Property and Infrastructure': {'min': 0.0, 'max': 0.30},
            'International Property and Infrastructure': {'min': 0.0, 'max': 0.10},
            'Alternatives': {'min': 0.0, 'max': 0.10}
        },
        'Defensive': {
            'Australian Fixed Interest': {'min': 0.0, 'max': 0.12},
            'International Fixed Interest': {'min': 0.0, 'max': 0.10},
            'Cash (1% minimum required)': {'min': 0.01, 'max': 0.10}
        }
    },
    'Aggressive': {
        'Growth': {
            'Australian Equities': {'min': 0.30, 'max': 0.70},
            'International Equities': {'min': 0.35, 'max': 0.70},
            'Domestic Property and Infrastructure': {'min': 0.0, 'max': 0.35},
            'International Property and Infrastructure': {'min': 0.0, 'max': 0.35},
            'Alternatives': {'min': 0.0, 'max': 0.30}
        },
        'Defensive': {
            'Australian Fixed Interest': {'min': 0.0, 'max': 0.12},
            'International Fixed Interest': {'min': 0.0, 'max': 0.10},
            'Cash (1% minimum required)': {'min': 0.01, 'max': 0.10}
        }
    },
    'All Growth': {
        'Growth': {
            'Australian Equities': {'min': 0.30, 'max': 0.85},
            'International Equities': {'min': 0.35, 'max': 0.99},
            'Domestic Property and Infrastructure': {'min': 0.0, 'max': 0.30},
            'International Property and Infrastructure': {'min': 0.0, 'max': 0.30},
            'Alternatives': {'min': 0.0, 'max': 0.30}
        },
        'Defensive': {
            'Australian Fixed Interest': {'min': 0.0, 'max': 0.12},
            'International Fixed Interest': {'min': 0.0, 'max': 0.10},
            'Cash (1% minimum required)': {'min': 0.01, 'max': 0.10}
        }
    }
}

# Fees
investment_manager_fee = 0.0045  # 0.4500%

# Create the comprehensive extraction
extracted = {
    'source_file': 'raw_document/profiles.csv',
    'format': 'CSV',
    'ingestion_timestamp': datetime.utcnow().isoformat() + 'Z',
    'document_label': 'Portfolio Profiles',
    'description': 'Managed portfolio profiles with six variants (Conservative, Moderate, Balanced, Growth, Aggressive, All Growth) containing configuration parameters, strategic asset allocation, and investment terms',
    'portfolios': []
}

for variant, config in profile_config.items():
    portfolio_obj = {
        'variant': variant,
        'portfolio_name': config['name'],
        'configuration': {
            'investment_options': {
                'minimum': config['min_investment_options'],
                'maximum': config['max_investment_options']
            },
            'position_limits': {
                'minimum_single_position_pct': config['min_single_position'],
                'maximum_single_position_pct': config['max_single_position'],
                'minimum_new_position_pct': config['min_new_position']
            },
            'risk_targets': {
                'target_volatility': config['target_volatility'],
                'tracking_error_target': config['tracking_error_target'],
                'outperformance_target': config['outperformance_target']
            },
            'trading_parameters': {
                'expected_turnover_pa': config['expected_turnover_pa'],
                'active_stock_limits': config['active_stock_limits'],
                'active_gics_sector_limits': config['active_gics_limits'],
                'trading_preference': config['trading_preference']
            },
            'cash_and_income': {
                'minimum_cash_buffer_pct': config['min_cash_buffer'],
                'income_default': config['income_default']
            }
        },
        'profile': {
            'benchmark': config['benchmark'],
            'asset_class': config['asset_class'],
            'minimum_investment_horizon': config['min_investment_horizon'],
            'portfolio_income': config['portfolio_income'],
            'risk_band_label': config['risk_band'],
            'investment_objective': config['investment_objective']
        },
        'strategic_asset_allocation': saa_data[variant],
        'fees': {
            'investment_manager_fee_pct': investment_manager_fee * 100
        }
    }
    extracted['portfolios'].append(portfolio_obj)

# Write preprocessed JSON
os.makedirs('wiki', exist_ok=True)
with open('wiki/Profiles.preprocessed.json', 'w', encoding='utf-8') as f:
    json.dump(extracted, f, indent=2, ensure_ascii=False)

print("Preprocessed JSON created: wiki/Profiles.preprocessed.json")
print(f"Extracted {len(extracted['portfolios'])} portfolio variants")